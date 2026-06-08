# Courier Allocation Revamp — Data Sanity Checks

**Initiative:** Courier Allocation Revamp (Nightly Adherence Job + Shadow Mode)
**Date:** 2026-06-08
**Reference:** [System Workflow](../context/2026-06-08-system-workflow-v1.md) | [PRD](https://docs.google.com/document/d/1HxILz8W8_UxLKXkaaoACFW8WPpAHTxESysn6Rjaq-Bc/edit)

---

## Approach

For every check: **independently compute the expected value from raw delivery data, then compare against what the system stored.** A match = system behaved correctly. A mismatch = bug.

Raw input: last 7 days of deliveries from the source tables.
System output: nightly adherence store (one row per WH × pincode × courier × computation_variant × n_threshold).

---

## Check 1: Did the system pick the right cascade level?

**What we do:**
- For a given WH × pincode × courier combination, pull the raw delivery count at each geographic level from the source tables:
  - Level 1 (pincode): count of deliveries for WH × pincode × courier in last 7 days
  - Level 2 (city): count of deliveries for WH × city × courier in last 7 days (city resolved from m_city_master)
  - Level 3 (state): count of deliveries for WH × state × courier in last 7 days (state resolved from m_state_master)
  - Level 4 (warehouse): count of deliveries for WH × courier in last 7 days
  - Level 5 (courier): count of deliveries for courier in last 7 days
- Apply cascade decision rule: starting from pincode, take the first level where count >= n_threshold. If none qualify, cascade = default.

**What we compare against:**
- `cascade_level_reached` stored in the nightly adherence output for that combination.

**Pass condition:** Our independently derived cascade level matches `cascade_level_reached` for every sampled combination.

---

## Check 2: Did the system calculate the right number of orders at each cascade level?

**What we do:**
- For the same WH × pincode × courier combination, independently count deliveries at every geographic level (same counts as Check 1).
- Produce expected `orders_per_cascade` = {pincode: x, city: y, state: z, warehouse: a, courier: b, default: 0 or 80}.

**What we compare against:**
- `orders_per_cascade` JSON stored in the instrumentation row for that order.

**Pass condition:** Every key in `orders_per_cascade` matches our independently computed count.

---

## Check 3: Did the system compute the right values for all early, on-time, and late fields at the resolved cascade level?

**What we do:**
- Pull all raw deliveries at the resolved cascade level (the geographic pool that was selected in Check 1).
- For each delivery, compute bucket classification:
  - delivery_days = Actual TAT - Ideal TAT (negative = early, 0 = on-time, positive = late)
  - Early 4+day: delivery_days <= -4
  - Early 3day: delivery_days = -3
  - Early 2day: delivery_days = -2
  - Early 1day: delivery_days = -1
  - Orders On-Time: delivery_days = 0
  - SLA Breach 1day: delivery_days = 1
  - SLA Breach 2day: delivery_days = 2
  - SLA Breach 3day: delivery_days = 3
  - SLA Breach 4+day: delivery_days >= 4
- Compute % for each bucket = count in bucket / total orders at cascade level.

**Note on drop buffer:** For orders where a drop buffer was applied, use Adjusted Actual TAT = Actual TAT - Drop Buffer before computing delivery_days.

**What we compare against:**
- Per-bucket percentages stored in `adherence_metadata` for that WH × pincode × courier combination.

**Pass condition:** All 9 bucket % values match our independently computed values (within rounding tolerance of ±0.1pp). Bucket %s must also sum to 100%.

---

## Check 4: Did the system run both computation variants?

**What we do:**
- For each WH × pincode × courier × n_threshold combination, check that two rows exist in the nightly adherence store — one for Computation 1 and one for Computation 2.

**What we compare against:**
- `computation_variant` field in the nightly store.

**Pass condition:** Both variants exist for every combination. No combination has only one variant or zero variants.

---

## Check 5: Did the system calculate the right adherence value for each computation variant?

**What we do:**
- Take the bucket % values computed in Check 3.
- Apply Computation 1 logic independently:
  - Start from Early 4+day, accumulate % left to right.
  - Stop at the first bucket where cumulative % >= 80%.
  - Record: adherence = cumulative % at that stopping bucket, and which bucket it stopped at.
- Apply Computation 2 logic independently:
  - Start from Early 4+day, accumulate % left to right.
  - Stop at Orders On-Time regardless of whether 80% is reached.
  - Record: adherence = cumulative % at On-Time.

**What we compare against:**
- `final_adherence_considered` stored for Computation 1 and Computation 2 rows respectively.

**Pass condition:** Our independently derived adherence % matches `final_adherence_considered` for each variant (within rounding tolerance of ±0.1pp).

---

## Sampling Strategy

Run all 5 checks on the same sample set:

- Pick 50 WH × pincode × courier combinations: 10 that should land at pincode level, 10 at city, 10 at state, 10 at warehouse, 10 at courier or default.
- Run all checks end-to-end for each combination.
- If any check fails for a combination, flag and trace the root cause before treating it as a systemic issue.
