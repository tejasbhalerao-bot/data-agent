# Courier Allocation Revamp — Data Sanity Checks v3

**Date:** 2026-06-08
**Reference:** [System Workflow](../context/2026-06-08-system-workflow-v1.md) | [PRD](https://docs.google.com/document/d/1HxILz8W8_UxLKXkaaoACFW8WPpAHTxESysn6Rjaq-Bc/edit)

---

## Approach

For each check: independently derive the expected value from raw delivery data and compare against what the system stored. Match = correct. Mismatch = bug to root-cause before proceeding.

Checks follow pipeline order: nightly job first, then allocation engine.

---

## Part A — Nightly Adherence Job

### A1: Did the system use the right order statuses for the 7-day lookback?

Before any cascade or computation check, verify the input pool is clean.

Pull all orders from the source table for the last 7 days. Check which delivery statuses are present — delivered, cancelled, RTO, in-transit, returned. The bucket computation must use only successfully delivered orders. Cancelled, RTO, and in-transit orders must not appear in the pool.

**Compare against:** The set of statuses actually included in the nightly job's input query. If non-delivered statuses are present, every downstream bucket distribution is wrong regardless of other checks passing.

---

### A2: Did the system pick the right cascade level?

For a sampled WH × pincode × courier combination, independently count raw deliveries in the last 7 days at every geographic level:
- WH × pincode × courier
- WH × city × courier (city from `m_city_master`)
- WH × state × courier (state from `m_state_master`)
- WH × courier
- courier

Walk the cascade from pincode upward — first level where count >= n_threshold is the expected level. If none qualify, expected = default.

**Compare against:** `cascade_level_reached` in the nightly store for each of the 3 n_threshold rows (n=10, n=15, n=20).

**Cross-threshold monotonicity check:** For the same combination, cascade level at n=10 must be at the same or lower geographic level as n=15, which must be the same or lower than n=20. A lower threshold means more combinations qualify at pincode level. Flag any combination where cascade level at n=10 is higher (more aggregated) than at n=20 — that is a computation error.

**Prerequisite:** Verify the pincode resolves in `m_city_master` and `m_state_master` before expecting a city or state level to be reachable. An unmapped pincode must skip directly to warehouse or courier cascade.

---

### A3: Did the system calculate the right number of orders at each cascade level?

Using the same raw counts from A2, independently produce `orders_per_cascade` = `{pincode: x, city: y, state: z, warehouse: a, courier: b}` for the sampled combination.

**Compare against:** `orders_per_cascade` JSON in the instrumentation row.

Also verify: the count at `cascade_level_reached` equals the count actually used to derive the bucket distribution (A4). If the system cascaded to city but used a pincode-sized pool for bucket computation, the cascade logic and computation are decoupled — that is a bug.

---

### A4: Did the system compute the right bucket distribution at the resolved cascade level — and independently per threshold?

Pull all raw deliveries at the cascade-resolved geographic pool. For each delivery:

```
delivery_delta = Actual Delivery Date - Ideal TAT date
```

**Drop buffer pre-adjustment:** For orders where a drop buffer was applied, use `Adjusted Actual TAT = Actual TAT - Drop Buffer`. The drop buffer used must be the value that was applied to that specific historical delivery at dispatch time — not the current configured value. If drop buffer values changed during the 7-day window, using today's value would misclassify those deliveries.

Classify into 9 buckets:

| Bucket | Condition |
|---|---|
| Early 4+day | delivery_delta <= -4 |
| Early 3day | delivery_delta = -3 |
| Early 2day | delivery_delta = -2 |
| Early 1day | delivery_delta = -1 |
| Orders On-Time | delivery_delta = 0 |
| SLA Breach 1day | delivery_delta = 1 |
| SLA Breach 2day | delivery_delta = 2 |
| SLA Breach 3day | delivery_delta = 3 |
| SLA Breach 4+day | delivery_delta >= 4 |

Compute % for each bucket = count / total orders in pool.

**What Ideal TAT to use for classification:** Each historical delivery needs an Ideal TAT to compute delivery_delta. If Ideal TAT was unconfigured for a historical WH × pincode × courier at delivery time, note what the system does — uses 5-day default or skips the order entirely. Either decision silently distorts the distribution. Verify the system's behavior matches expectation and that it is consistent for all historical orders in the pool.

**Compare against:** Per-bucket values in `adherence_metadata` for that combination.

**Cross-threshold independence check:** For a combination that cascades differently across thresholds (e.g., pincode at n=10 but city at n=15), the bucket distribution in the n=10 row must be computed from the pincode pool and the n=15/n=20 rows must be computed from the city pool. Pull `adherence_metadata` for all three threshold rows and verify that the distributions differ when the cascade levels differ. If all three rows show identical bucket distributions despite cascading to different levels, the system computed once and copied — that is wrong.

---

### A5: Did both computation variants run?

For each WH × pincode × courier × n_threshold combination, the nightly store must have exactly two rows — one for Computation 1 and one for Computation 2 — giving 6 rows total per combination.

**Compare against:** `computation_variant` field. Flag any combination with fewer than 6 rows and identify which variant × threshold is missing.

---

### A6: Did the system calculate the right adherence value for each computation variant?

Using the bucket %s derived in A4, independently apply both computation rules:

**Computation 1 — `adherence_adjusted_80_perc_plus`:**
- Accumulate bucket %s left to right starting from Early 4+day.
- Stop at the first bucket where cumulative % >= 80%. SLA breach buckets are included.
- Expected adherence = cumulative % at stopping bucket.
- Expected Final TAT direction = determined by the stopping bucket (see below).

**Computation 2 — `base_adherence_percentage`:**
- Accumulate bucket %s left to right starting from Early 4+day.
- Stop at Orders On-Time regardless of whether 80% is reached. Breach buckets never included.
- Expected adherence = cumulative % at On-Time.
- Expected Final TAT direction = determined by the stopping bucket — which can only be an Early bucket or On-Time. Therefore Final TAT from Comp2 must always be <= Ideal TAT. Delay Days from Comp2 must never be positive. Flag any Comp2 row where Delay Days > 0 — that is a computation error.

**Compare against:** `final_adherence_considered` for each variant row.

**Derived checks from the same computation:**

- **Final TAT correctness:** Expected Final TAT from above vs. stored `final_tat`. Verify for both variants.
- **Delay Days arithmetic:** `delay_days` = `final_tat` - `ideal_tat`. Spot-check 100% of sampled rows.
- **Supposed TAT flag:** If Ideal TAT is unavailable in the config tables for a WH × pincode × courier, the system uses 5 days and sets `supposed_tat_flag = true`. Verify the flag is set if and only if Ideal TAT was missing. Verify `ideal_tat` stored in those rows equals 5.
- **Final TAT >= 0 guardrail:** Compute un-clamped Final TAT using the formula above. For rows where un-clamped value would be negative, verify the system stored `final_tat = 0` and not the negative value.

---

### A7: Zero-regression check (Stage 1A exit criterion)

For combinations where pincode-level count >= 20, cascade level is pincode for all three thresholds. For these combinations, the system is not pooling — it is using raw pincode-level data. The stored adherence and bucket distribution must exactly match what direct computation from that pincode pool gives.

**Compare against:** Independently compute adherence from raw pincode-level deliveries for these combinations and verify stored values match to within rounding tolerance (±0.1pp). Any divergence here means the pooling logic introduced a regression even on lanes with sufficient data — a hard blocker for Stage 1A exit.

---

### A8: Did the system write rows for all combinations, including those with zero recent deliveries?

A WH × pincode × courier combination that had deliveries last month but zero in the last 7 days will have no data to build a score from. The system must still produce a row for this combination (using the default 80% score) so the allocation engine has something to look up.

**Check:** Identify combinations present in orders from 8–30 days ago but absent from the last 7 days. Verify whether the nightly store has rows for these combinations. If missing, the allocation engine will have no score to fetch for those courier × lane pairs, and allocation could fail silently.

---

### A9: Job failure fallback

On any night the nightly job did not complete within its SLA window: pull instrumentation rows from orders placed the following day. The `cascade_level_reached`, `final_adherence_considered`, and `final_tat` values used must match the previous night's job output — not a fresh computation from that day.

For orders placed before the job window (before 3:00 AM FC / 3:30 AM MFC), verify they also used the previous night's scores even on nights the job completed successfully.

If no job failure occurred in the observation window, this check is deferred — note it for opportunistic verification.

---

## Part B — Order Allocation Engine

### B1: Did the system fetch the right cascade adherence score for each courier?

For a sampled order: given the order's WH × pincode × courier and the computation variant × n_threshold of each shadow mode, look up the corresponding row in the nightly store. Compare the adherence % and Final TAT stored there against what appears in the instrumentation row for that order × mode.

**Compare against:** `final_adherence_considered` and `final_tat` in the instrumentation row vs. the nightly store row for the same combination × variant × threshold.

---

### B2: Did the system apply the schedule time flag correctly?

For each courier in the recommendation list, check whether the order was placed after that courier's specific cutoff time at that warehouse. Cutoff times are per warehouse per courier — not a global value.

**Compare against:** `schedule_time_flag` in the instrumentation row per courier. Expected 1 if order placed after that carrier's cutoff at that warehouse, 0 otherwise.

---

### B3: Did the system compute the final allocation score correctly?

Two-level check:

**Level 1 — Pre-buffer score:**
```
tat_adherence_score = final_tat / final_adherence_considered
```
Verify per courier.

**Level 2 — Final score with buffers:**
```
tat_adherence_score_with_buffer = tat_adherence_score + schedule_time_flag + pickup_buffer + drop_buffer
```
Verify per courier.

**Compare against:** `tat_adherence_score` and `tat_adherence_score_with_buffer` in the instrumentation row.

---

### B4: Did the system rank couriers correctly?

Sort all eligible couriers for the order by `tat_adherence_score_with_buffer` ascending. Lowest score = Rank 1.

**Compare against:** `rank_in_allocation` per courier in the instrumentation row.

---

### B5: Does the selected courier match Rank 1 on live runs? Is it null on shadow runs?

For live allocation rows: `selected_courier_partner` must equal the courier with `rank_in_allocation = 1`.

For all shadow mode rows: `selected_courier_partner` must be null, regardless of which courier ranked first.

---

### B6: Did all expected runs produce instrumentation rows, at every order stage?

Allocation is triggered at 4 stages: Order Placed, Order Confirmed, Picking, Invoice Generated. For each unique order × order_stage, the expected instrumentation rows are:

- 1 row for the existing algorithm run
- 6 rows for the 6 shadow modes (Comp1 × n10, Comp1 × n15, Comp1 × n20, Comp2 × n10, Comp2 × n15, Comp2 × n20)
- 1 row for PBA run (if PBA rollout % > 0)

Total = 7 rows minimum per order × stage (8 when PBA active).

**Compare against:** Count of instrumentation rows grouped by order_id × order_stage × computation_variant × n_threshold. Flag any order × stage with fewer rows than expected. A missing row at Invoice Generated but present at Order Placed would pass a per-order check but fail a per-order-stage check.

Shadow modes must cover 100% of orders regardless of whether the order was routed to PBA or existing allocation for the live decision.

---

### B7: Does adherence_metadata contain scores for all couriers in the recommendation list — not just the winner?

The entire value of instrumentation for shadow analysis is comparing what each mode assigned to each courier. If `adherence_metadata` and `final_adherence_considered` only store values for the selected courier, post-analysis is impossible.

**Check:** For each sampled order, cross-reference the couriers listed in `recommendation_metadata` against the couriers present in `final_adherence_considered`. Every courier in the recommendation list must have a score. No courier should be scored that was not in the recommendation list.

---

## Sampling Strategy

All checks run on the same sample:

**For Part A:** 50 WH × pincode × courier combinations — 10 expected at each cascade level (pincode, city, state, warehouse, courier/default). For A7, additionally pull all combinations where pincode count >= 20. For A8, pull combinations present 8–30 days ago but absent in last 7 days.

**For Part B:** 20 orders — 10 placed before warehouse cutoff, 10 placed after. Cover both PBA-routed and non-PBA-routed orders. Cover at least 2 of the 4 order stages per order.
