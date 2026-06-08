# Courier Allocation Revamp — Data Sanity Check Plan

**Initiative:** Courier Allocation Revamp (Nightly Adherence Job + Shadow Mode)
**Date:** 2026-06-08
**Reference:** [System Workflow](../context/2026-06-08-system-workflow-v1.md) | [PRD](https://docs.google.com/document/d/1HxILz8W8_UxLKXkaaoACFW8WPpAHTxESysn6Rjaq-Bc/edit)

---

## Objective

Verify that the system is computing and storing data correctly before any impact analysis begins. Every section here is a gate — if a check fails, root-cause before proceeding to the next section.

Checks are structured in pipeline order: job execution → cascade logic → computation correctness → TAT/buffer handling → instrumentation completeness → cross-system consistency.

---

## Section 1: Nightly Job Execution

**Core question:** Did the job run, complete on time, and write the expected volume of rows?

### 1.1 Job completion rate
- Did the job complete within the 45-minute SLA window (FC by 3:45 AM, MFC by 4:15 AM)?
- What % of nights completed on time over the observation window?
- On nights where the job did not complete — was the fallback (previous night's scores) correctly picked up by the allocation engine?

### 1.2 Row volume written
- How many WH × pincode × courier combinations exist in the source data (last 7 days)?
- How many rows were written to the nightly store?
- Expected: 6 rows per combination (2 variants × 3 thresholds). Flag any combination with fewer than 6.
- Are there combinations present in the source data that produced zero rows?

### 1.3 Coverage across warehouses
- Are all active FCs and MFCs represented in the nightly output?
- Are there warehouses with zero rows written? (Would mean all their orders fall through to fallback.)

---

## Section 2: Cascade Logic

**Core question:** Is the cascade firing at the right level — not too high (losing lane signal unnecessarily), not too low (running on meaningless thin data)?

### 2.1 Cascade level distribution (overall)
- For the full universe of WH × pincode × courier combinations: what % land at each cascade level (pincode / city / state / warehouse / courier / default)?
- Baseline this distribution across all three thresholds (n=10, n=15, n=20). As n increases, more combinations should cascade upward.

### 2.2 Cascade sensitivity check
- At n=10: what % reach pincode level? At n=20: what % reach pincode level?
- The gap between n=10 and n=20 pincode-level resolution rates must be meaningful (not near-zero). If both thresholds produce nearly identical distributions, it signals the threshold is having no effect — investigate.

### 2.3 Default (80%) fallback rate
- What % of WH × pincode × courier combinations land at Cascade 5 (default 80%)? 
- What % of orders are served by a default score?
- High default rate (>5% of orders) is a flag — means couriers have insufficient national-level data.

### 2.4 Pincode mapping coverage
- What % of pincodes in the last 7 days of orders resolve in `m_city_master`?
- What % resolve in `m_state_master`?
- List all unmapped pincodes. These pincodes can never reach city or state cascade — they skip directly to warehouse or courier cascade. Flag if any unmapped pincode handles material order volume.

### 2.5 Cascade level consistency across thresholds
- For a given WH × pincode × courier combination, cascade level at n=10 should be <= cascade level at n=20 (you can't cascade higher at a lower threshold). Verify no inversions exist.

---

## Section 3: Computation Correctness

**Core question:** Are the 9 buckets adding up correctly and are both computation variants producing valid adherence values?

### 3.1 Bucket distribution completeness
- For every row in the nightly store: do the 9 bucket percentages sum to 100%? Flag any row where sum != 100% (within rounding tolerance of ±0.1pp).
- Are there any rows where all 9 buckets are 0? (Would mean zero orders at that cascade level — should not be possible if cascade logic is correct.)

### 3.2 Computation 1 adherence floor
- Computation 1 (`adherence_adjusted_80_perc_plus`) sums until >=80% is reached. Therefore, its adherence value must always be >=80%.
- What % of Computation 1 rows have adherence < 80%? Expected: 0%. Any non-zero rate is a computation bug.

### 3.3 Computation 2 adherence ceiling
- Computation 2 (`base_adherence_percentage`) stops at On-Time and never includes breach days. It can be < 80%.
- Distribution of Computation 2 adherence values: what % are below 80%? What % are above?
- For lanes where Computation 2 is above 80%: it means early deliveries alone crossed 80% — verify these rows look reasonable (extremely early-delivery couriers).

### 3.4 Computation 1 vs Computation 2 relationship
- Computation 1 adherence >= Computation 2 adherence for any given combination, because Comp1 may include breach-day orders that push the count higher. Verify no rows where Comp1 < Comp2.
- What is the distribution of the gap (Comp1 - Comp2) across all combinations?

### 3.5 Worked example spot-check
- Pick 3 WH × pincode × courier combinations (one thin lane, one city-cascaded, one warehouse-cascaded). Pull raw delivery data and manually verify bucket counts and adherence values match what the system computed.

---

## Section 4: TAT and Buffer Handling

**Core question:** Are Ideal TAT, Final TAT, and Delay Days computed and stored correctly?

### 4.1 Supposed TAT flag rate
- What % of WH × pincode × courier combinations have no Ideal TAT configured and fall back to the 5-day default?
- Break this down by warehouse. A warehouse with >20% of combinations on Supposed TAT may have gaps in the TAT configuration.

### 4.2 Delay Days arithmetic
- For every row: verify Delay Days = Final TAT - Ideal TAT. Sample 1,000 rows and check. Any mismatch = computation error.
- Distribution of Delay Days: what % are negative (early), zero, positive (late)?

### 4.3 Final TAT >= 0 guardrail
- How many rows had the guardrail fire (Final TAT was clamped to 0)?
- What % of total rows? Which WH × pincode × courier combinations trigger it most?
- For guardrail-fired rows: what was the un-clamped Final TAT (i.e., how negative would it have been)?

### 4.4 Drop buffer pre-adjustment
- For orders where a drop buffer was applied: verify Adjusted Actual TAT = Actual TAT - Drop Buffer before bucket classification.
- Compare bucket distribution for buffered vs non-buffered orders. If the distributions are identical, the adjustment likely did not apply.

### 4.5 Final allocation score formula
- For a sample of orders: verify Final score = (Final TAT / Adherence) + schedule_time_flag + Pickup Buffer + Drop Buffer.
- For orders after cutoff: verify schedule_time_flag = 1. For orders before cutoff: verify = 0.

---

## Section 5: Instrumentation Completeness

**Core question:** Is every order producing the expected number of instrumentation rows, with all fields populated?

### 5.1 Row count per order
- Expected: up to 8 rows per order per allocation trigger (1 existing + 6 shadow modes + 1 PBA if applicable).
- Distribution of instrumentation row counts per order. Flag orders with fewer rows than expected.
- Are there any orders with zero instrumentation rows?

### 5.2 Shadow mode coverage
- For each of the 6 shadow modes: are rows present for all orders?
- Are there modes that have materially lower row counts than others? (Would indicate a specific mode variant is failing silently.)

### 5.3 Field completeness
- For the following fields, null is never expected: order_id, warehouse_id, pincode, cascade_level_reached, final_adherence_considered, final_tat, tat_adherence_score_with_buffer, rank_in_allocation.
- What % of rows have nulls in each of these fields?
- city and state should resolve for all rows where pincode is mapped. Cross-reference against Section 2.4 unmapped pincodes — if city/state is null for a mapped pincode, it's a join bug.

### 5.4 selected_courier_partner nullability
- For shadow mode rows: selected_courier_partner must be null (no live selection happens in shadow).
- For live allocation rows: selected_courier_partner must be non-null.
- What % of shadow rows have a non-null selected_courier_partner? Expected: 0%.
- What % of live allocation rows have a null selected_courier_partner? Expected: 0%.

### 5.5 orders_per_cascade JSON structure
- Verify all 6 keys present in every row: {pincode, city, state, warehouse, courier, default}.
- Are any keys missing for some rows?

### 5.6 Rank 1 consistency
- For every order's live allocation run: exactly one courier should have rank_in_allocation = 1 and it must match selected_courier_partner.
- What % of live orders violate this?

---

## Section 6: Cross-System Consistency

**Core question:** Does the system behave correctly at the seams — PBA routing, shadow vs live separation, job failure handoff?

### 6.1 PBA routing split
- At current PBA rollout %: what fraction of orders went to PBA vs existing allocation (live)?
- Does (PBA orders + existing live orders) / total orders = 100%? Any orders unaccounted for?

### 6.2 Shadow mode runs on 100% of orders
- Total shadow mode instrumentation rows / total orders should = 6 (one per mode).
- If PBA is at X%, shadow rows should still cover 100% of orders — not just the non-PBA %.
- Verify shadow coverage is flat across PBA and non-PBA routed orders.

### 6.3 Job failure fallback verification
- On any night the job did not complete: pull instrumentation rows from the following day. The cascade scores and adherence values used should match the previous night's job output, not a fresh computation.
- If no job failures occurred in the observation window, this check can be deferred.

### 6.4 Threshold variant tagging
- For Stage 1A, threshold_variant must be one of {10, 15, 20} — never null.
- What % of rows have null threshold_variant? Expected: 0% during Stage 1A.
- Stage 3 steady state (not yet applicable): threshold_variant must be null for all rows.

---

## Sequencing and Gate Logic

Run sections in order. Each section is a gate:

| Section | Gate condition to proceed |
|---|---|
| 1 — Job Execution | Job completing on >=12/14 nights within SLA. Fallback verified. |
| 2 — Cascade Logic | No unmapped pincodes with material volume. No cascade inversions. Default rate <5% of orders. |
| 3 — Computation | Bucket sums = 100%. Comp1 adherence always >=80%. No Comp1 < Comp2 inversions. Spot-checks pass. |
| 4 — TAT/Buffer | Delay Days arithmetic exact. Guardrail fire rate documented. Buffer adjustment verified. |
| 5 — Instrumentation | Row count per order matches expected. Null rates on mandatory fields = 0. Shadow nullability correct. |
| 6 — Cross-System | PBA split adds to 100%. Shadow covers 100% of orders. Threshold tagging clean. |
