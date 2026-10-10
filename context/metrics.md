---
title: Metric dictionary
type: metric-definition
systems: [allocation, tracking, eta]
verticals: [all]
source: egregiously-miscalibrated-promises metric definitions (2026-07-30), early-delivery-analysis (2026-07-04, 2026-06-19), pba-integration plan v4 (2026-05-22), adherence-vs-ontime (2026-08-25), courier-allocation-revamp system workflow (2026-06-08)
updated: 2026-10-09
---

# Metric dictionary

One definition per metric. Where projects defined the same name differently, each variant is listed with its project and the conflict is marked CONFLICT in the row. **Do not pick between variants silently: ask Tejas, then collapse the entry.**

Conventions: `A` is the promise, `B` the actual. Date comparisons use `DATE()` on both. Timestamp comparisons use the full timestamp. Unless a row says otherwise, "Early / On-Time / Late" means `A > B`, `A = B`, `A < B`. Orders missing either input (for example no `delivery_attempt_time`) are excluded.

## 1. Delivery leg

| Metric | Definition | Variants and caveats |
|--------|------------|----------------------|
| **Delivery E/OT/L** | `A = DATE(digitised_delivery_promise)`, `B = DATE(delivery_attempt_time)`. Offset = `B - A` in days: Early if less than 0, On-Time if 0, Late if more than 0. | Consistent across EMP and early-delivery. Uses first attempt, not `actual_delivery_date`. Strips time: a 20:00 promise and 13:04 attempt on the same day is On-Time. |
| **Delivery TAT E/OT/L** | `A = DATE(digitised_delivery_promise) - DATE(digitised_dispatch_promise)`, `B = DATE(delivery_attempt_time) - DATE(pickup_time)`. | All four timestamps non-NULL. Measures courier transit only. |
| **Shipping Delivery TAT E/OT/L** | `A = shipping_delivery_promise` (days), `B = DATE(delivery_attempt_time) - DATE(pickup_time)`. | `A` is the TAT of the courier that actually shipped; differs from the digitised promise after a reroute. |
| **Egregiously miscalibrated order** | `ABS(DATE(digitised_delivery_promise) - DATE(delivery_attempt_time)) >= 2`. Early variant: promise minus attempt `>= 2`. Late variant: attempt minus promise `>= 2`. | Subset of Delivery Early/Late. Anchor is the digitised promise, not any later shipping promise. |

## 2. Upstream legs

| Metric | Definition | Variants and caveats |
|--------|------------|----------------------|
| **Dispatch E/OT/L** | `A = DATE(digitised_dispatch_promise)`, `B = DATE(pickup_time)`. | Consistent across projects. |
| **Doctor leg** | `A = digitised_dr_promise`. `B` is the project-specific actual below. | **CONFLICT.** EMP "Doctor": `B = dr_confirm_ts`, exact timestamp. EMP "Doctor Ops": `B = actual_doctor_call_time`, exact timestamp (an exact match is vanishingly rare). early-delivery View 1: `B = dr_confirm_ts` with a +/-60 second On-Time band. View 2: `B = actual_doctor_call_time` with the same band. `dr_confirm_ts` and `actual_doctor_call_time` are different events. |
| **Warehouse leg** | `A` and `B` are project-specific. | **CONFLICT.** EMP: `A = digitised_wh_promise`, `B = awb_sticker_printed_ts`, exact timestamp (AWB print is the proxy for packing complete). early-delivery View 1/2: `A = digitised_dispatch_promise`, `B = invoice_create_ts`, matched to the minute; deliberately benchmarked against the dispatch promise. early-delivery Axis 1 v2: promised window `digitised_wh_promise - digitised_dr_promise` vs actual window `invoice_create_ts - processing_start_ts`, +/-1 minute buffer; excludes `wh_processing_mins = 0`. EMP also compared invoice-based vs AWB-based deviation (requests #45 to #47). |

## 3. Courier performance and allocation

| Metric | Definition | Variants and caveats |
|--------|------------|----------------------|
| **Adherence (PBA analysis)** | Bucket each delivered order by `CEIL((delivery_attempt_time - pickup_time) in days)` vs the promised TAT days: Early / On-Time / Late, plus Not Picked Up, Not Delivered, Excluded. | Computed in scripts, not in queries. Shadow mode: both regimes are measured against actual delivery by the Internal courier. |
| **Adherence percentage (production, nightly job)** | Cumulative share of the 9 delivery buckets from Early 4+ day rightwards, stopping when the cumulative share reaches the `percentile_value` (80%). Variant 2 (`base_adherence_percentage`) stops at On-Time and never includes breach buckets. | **Known flaw:** counts early parcels as hits, so it ranges only 0.8 to 1.0 and rewards early couriers. Proposed replacement is **On-time %** below. |
| **On-time %** | Share of orders delivered on the promised date (excludes early). Range 0 to 1. | Proposed replacement for adherence in the selection score (single-field swap). Not yet live. |
| **Promise TAT / Final TAT / Delay Days** | Promise TAT = Ideal TAT (configured). Final TAT = Ideal TAT shifted to the bucket where the adherence threshold is reached. Delay Days = Final TAT minus Ideal TAT (negative = early). Customer TAT = Promise TAT + Delay Days. | If no Ideal TAT exists, `Supposed TAT` is true and 5 days is used. |
| **Final allocation score** | `(Final TAT / Adherence) + schedule_time_flag + Pickup Buffer + Drop Buffer`; lowest wins. | The TAT/Adherence division prices a day at about 42 percentage points on fast lanes and 17 on slow lanes (unintended). |
| **Calibration (PBA)** | Signed error = actual TAT minus promised TAT. Positive means the promise was too optimistic; negative, too conservative. Buckets: ACCURATE / OVERESTIMATED / UNDERESTIMATED. | Same-courier cohort only unless stated. |

## 4. Cohorts used across projects

| Cohort | Definition |
|--------|------------|
| Segment | `digitised_is_sdd` x `digitised_is_inventory` (four segments: SDD Inventory, SDD Non-Inventory, Non-SDD Inventory, Non-SDD Non-Inventory) |
| Same-courier cohort | PBA-selected courier equals Internal-selected courier |
| Different-courier cohort | The two differ |
| Promise direction | PBA_FASTER / SAME / INTERNAL_FASTER, by comparing PBA and Internal promised TAT |
