# Courier Allocation Revamp — Data Sanity Checks v2

**Date:** 2026-06-08
**Reference:** [System Workflow](../context/2026-06-08-system-workflow-v1.md) | [PRD](https://docs.google.com/document/d/1HxILz8W8_UxLKXkaaoACFW8WPpAHTxESysn6Rjaq-Bc/edit)

---

## Approach

For each check: independently derive the expected value from raw delivery data and compare it against what the system stored. A match = correct. A mismatch = bug to root-cause before proceeding.

Checks follow the system's pipeline order: nightly job first, then allocation engine.

---

## Part A — Nightly Adherence Job

### A1: Did the system pick the right cascade level?

For a sampled WH × pincode × courier combination:
- Count raw deliveries in the last 7 days at every geographic level: WH × pincode × courier, WH × city × courier, WH × state × courier, WH × courier, courier.
- Walk the cascade from pincode upward — the first level where count >= n_threshold is the expected cascade level. If no level qualifies, expected = default.

**Compare against:** `cascade_level_reached` in the nightly store.

**Prerequisite:** Verify pincode resolves in `m_city_master` and `m_state_master` before checking city/state levels. A pincode that doesn't resolve can never land at city or state — it must skip to warehouse or above.

---

### A2: Did the system calculate the right number of orders at each cascade level?

For the same combination, independently count deliveries at every geographic level (same counts computed in A1).

**Compare against:** `orders_per_cascade` JSON: `{pincode: x, city: y, state: z, warehouse: a, courier: b}`.

Each key must match the raw count independently computed. Also verify that the count at `cascade_level_reached` equals the count the system used to derive adherence (i.e., the system did not use a different pool than the cascade logic selected).

---

### A3: Did the system compute the right values of all early, on-time, and late fields at the resolved cascade level?

Pull all raw deliveries at the resolved cascade level (the geographic pool selected in A1). For each delivery compute:

```
delivery_delta = Actual Delivery Date - Ideal TAT date
```

Note: for orders where a drop buffer was applied by the selected courier, use `Adjusted Actual TAT = Actual TAT - Drop Buffer` before computing delivery_delta.

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

**Compare against:** Per-bucket values in `adherence_metadata` for that combination.

**Additional check on drop buffer pre-adjustment:** Pull a sample of orders where drop buffer > 0. Verify the system reclassified them using adjusted TAT, not raw TAT. If drop buffer was not applied, the bucket distribution for buffered orders will skew late relative to what raw delivery dates show.

---

### A4: Did the system run both computation variants?

For each WH × pincode × courier × n_threshold combination, check the nightly store has exactly two rows — one for Computation 1 and one for Computation 2.

**Compare against:** `computation_variant` field. Expected: both values present for every combination, across all three threshold values (n=10, n=15, n=20), giving 6 rows total per combination.

If any combination has fewer than 6 rows, identify which variant × threshold is missing.

---

### A5: Did the system calculate the right value of adherence for each computation variant?

Using the bucket %s independently derived in A3, apply both computation rules:

**Computation 1 — `adherence_adjusted_80_perc_plus`:**
- Accumulate bucket %s left to right starting from Early 4+day.
- Stop at the first bucket where cumulative % >= 80%. SLA breach buckets are included.
- Expected adherence = cumulative % at the stopping bucket.
- Expected Final TAT = Ideal TAT adjusted by the direction of the stopping bucket (negative if early, 0 if on-time, positive if breach).

**Computation 2 — `base_adherence_percentage`:**
- Accumulate bucket %s left to right starting from Early 4+day.
- Stop at Orders On-Time regardless of whether 80% was reached. Never include breach buckets.
- Expected adherence = cumulative % at On-Time.
- Expected Final TAT = Ideal TAT adjusted by the direction of the stopping bucket (cannot be positive since breach buckets never included).

**Compare against:** `final_adherence_considered` for each variant row.

**Derived checks from the same computation:**

- **Was Final TAT calculated correctly?** Expected Final TAT from above vs. stored `final_tat`. Must match.
- **Was Delay Days calculated correctly?** `delay_days` = `final_tat` - `ideal_tat`. Verify arithmetic for every sampled row.
- **Was the Supposed TAT fallback applied correctly?** If Ideal TAT is unavailable for a WH × pincode × courier, system uses 5 days and sets `supposed_tat_flag = true`. Verify the flag is set if and only if Ideal TAT was missing from the config tables.
- **Did the Final TAT >= 0 guardrail fire when needed?** Identify rows where the un-clamped Final TAT (computed above) would be negative. Verify the system stored Final TAT = 0 for those rows, not the negative value.

---

## Part B — Order Allocation Engine

### B1: Did the system fetch the right cascade adherence score for each courier?

For a sampled order: given the order's WH × pincode × courier combination and the computation variant / n_threshold of each shadow mode, verify the system read the adherence score and Final TAT from the correct row in the nightly store.

**Compare against:** `final_adherence_considered` and `final_tat` in the instrumentation row vs. the corresponding nightly store row for that combination × variant × threshold.

---

### B2: Did the system apply the schedule time flag correctly?

For each courier in the recommendation list, check if the order was placed after the warehouse cutoff time for that courier.

**Compare against:** `schedule_time_flag` in the instrumentation row. Expected 1 if after cutoff, 0 if before or at cutoff.

---

### B3: Did the system compute the final allocation score correctly?

Using values from the instrumentation row, verify:

```
tat_adherence_score_with_buffer = (final_tat / final_adherence_considered) + schedule_time_flag + pickup_buffer + drop_buffer
```

**Compare against:** `tat_adherence_score_with_buffer` in the instrumentation row for each courier.

---

### B4: Did the system rank couriers correctly?

For an order, independently sort all eligible couriers by `tat_adherence_score_with_buffer` ascending. Lowest score = Rank 1.

**Compare against:** `rank_in_allocation` per courier in the instrumentation row.

---

### B5: For live allocation runs, does the selected courier match Rank 1?

**Compare against:** `selected_courier_partner` must equal the courier with `rank_in_allocation = 1` on the live allocation row.

For shadow mode rows: `selected_courier_partner` must be null regardless of ranking.

---

### B6: Did all 6 shadow modes run for every order?

For every order, the instrumentation table should have 6 shadow mode rows (one per mode: Comp1×n10, Comp1×n15, Comp1×n20, Comp2×n10, Comp2×n15, Comp2×n20) plus the existing algorithm row — independent of whether the order was routed to PBA or existing allocation for the live decision.

**Compare against:** Count of instrumentation rows per order, grouped by `computation_variant` × `n_threshold`. Any order with fewer than 6 shadow rows has a gap.

---

## Sampling Strategy

Run all checks on the same 50-combination sample:
- 10 combinations that should resolve at pincode level
- 10 at city level
- 10 at state level
- 10 at warehouse level
- 10 at courier or default level

For Part B checks, pick 20 orders — 10 pre-cutoff, 10 post-cutoff — and cover both PBA-routed and non-PBA-routed orders.
