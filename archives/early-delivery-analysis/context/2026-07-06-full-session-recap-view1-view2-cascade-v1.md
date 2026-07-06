# Full Session Recap — View 1/View 2 Cascade & Courier Reallocation Investigation

Complete, sequential record of a multi-day session on `early-delivery-analysis`. Written so a future session can resume with zero context loss. Every number below is validated by a paired test script (see File Index) unless noted otherwise.

---

## 1. Source data & schema

`archives/early-delivery-analysis/raw-data/early-delivery-raw-may-2026.csv` — 813,499 rows × 29 cols, one row per order, May 2026 cohort (Metabase export). 260MB, gitignored, local only.

**Columns:** order_id, digitised_ts, dr_confirm_ts, invoice_create_ts, processing_start_ts, digitised_dr_promise, digitised_wh_promise, digitised_dispatch_promise, digitised_delivery_promise, digitised_wh_process_mins, digitised_delivery_tat_mins, digitised_doctor_tat, digitised_dispatch_tat, digitised_is_sdd, digitised_is_inventory, digitised_wh_id, digitised_order_category, digitised_is_mfc, digitised_delivery_pincode, digitised_delivery_partner, actual_doctor_call_time, actual_warehouse_processing, pickup_time, delivery_attempt_time, shipping_pincode, shipping_delivery_partner, shipping_delivery_promise, shipping_warehouse, shipping_is_sdd, shipping_is_inventory.

Two parallel snapshots per order: `digitised_*` (state captured at digitisation, promise-side) and actual/`shipping_*` (what really happened / state at shipping time) — built for promise-vs-actual delta analysis.

### Discovered schema quirks (see `data-sources.md` for canonical record)
- `shipping_delivery_promise` is an **integer TAT in days** (courier's promised delivery TAT at shipping time), NOT a timestamp — unlike `digitised_delivery_promise`. Comparable digitised-side quantity: `date(digitised_delivery_promise) − date(digitised_dispatch_promise)`.
- `digitised_is_sdd`/`digitised_is_inventory` use `true`/`false` strings; `shipping_is_sdd` uses `1`/`0`; `shipping_is_inventory` uses `true`/`false`. Normalize before comparing: `{"true":True,"1":True,"false":False,"0":False}`.
- `digitised_delivery_partner` has ~4.8% blanks in the base population; `shipping_delivery_partner` essentially always populated.

---

## 2. Base population (locked, mandatory for every script in this project)

**Rule:** `digitised_ts > 8 May 2026` AND `delivery_attempt_time` not null.

| Stage | Rows | % of total |
|---|---|---|
| Total raw rows | 813,499 | 100% |
| + digitised_ts > 8 May 2026 | 624,288 | 76.7% |
| + delivery_attempt_time not null | 522,808 | 64.3% |
| after order_id dedup (15 dupes) | 522,793 | — |

Script: `scripts/2026-07-04-structure-base-population-filter-v1.py` → `outputs/base-population.csv`. Doc: `context/2026-07-04-base-population-filter-v1.md`.

---

## 3. View 1 / View 2 cascade — locked leg definitions

Two lenses on the same Doctor → Warehouse → Dispatch → Delivery cascade. **View 1 = customer-experienced** (what the customer actually saw). **View 2 = ops-execution** (how operations performed, isolated from customer-facing lag). Doctor and Delivery legs differ by view; Warehouse and Dispatch legs are **identical in both** (intentional — warehouse/dispatch ops expected to operate customer-backwards regardless of view).

| Leg | View 1 | View 2 | Classification rule |
|---|---|---|---|
| Doctor | `digitised_dr_promise` vs `dr_confirm_ts` | `digitised_dr_promise` vs `actual_doctor_call_time` | timestamp, ±60s buffer → Early/On-Time/Late |
| Warehouse | `digitised_dispatch_promise` vs `invoice_create_ts` | same as View 1 | matched to the minute → less=Early, equal=On-Time, greater=Late. **Deliberately benchmarked against the dispatch promise, not `digitised_wh_promise`** — warehouse should optimize for orders out the door by the promised dispatch time, not just "processed and ready" |
| Dispatch | `digitised_dispatch_promise` vs `pickup_time` | same as View 1 | calendar-date diff → <0 Early, 0 On-Time, >0 Late |
| Delivery | `digitised_delivery_promise` vs `delivery_attempt_time`, calendar-date diff | `promise_duration_days = date(delivery promise) − date(dispatch promise)`; `actual_duration_days = date(delivery attempt) − date(pickup)`; compare the two integers | less=Early, equal=On-Time, greater=Late |

**Doctor buffer confirmed to apply identically in both views** (±60s), per Tejas confirmation.

Each view further drops rows missing its own required fields (own Doctor-actual column + all shared fields); final N reported per view — **the two views do not share the same N**.

| View | Final N | % of base population |
|---|---|---|
| View 1 (`dr_confirm_ts` populated) | 515,465 | 98.6% |
| View 2 (`actual_doctor_call_time` populated) | 515,400 | 98.6% |

Reconciled: 69 orders in View 1 only (missing `actual_doctor_call_time`), 4 orders in View 2 only (missing `dr_confirm_ts`); net −65 explains the N gap exactly. Verified Warehouse/Dispatch legs are byte-identical on the 515,396 common orders (0 mismatches) — this became relevant later when Tejas questioned why View 1 vs View 2 "ALL" tables showed different Warehouse numbers (they didn't — rounding coincidence at 1 decimal, verified with exact integer counts).

Doc: `context/2026-07-04-view1-view2-cascade-definitions-v1.md`. Scripts: `2026-07-04-aggregate-view-cascade-v1/v2/v3.py` → `outputs/view1-orders-all.csv` (515,465 rows, all raw cols + computed doctor_leg/warehouse_leg/dispatch_leg/delivery_leg) and `outputs/view2-orders-all.csv` (515,400 rows, same shape).

### Cuts (both views)
4-way cross + ALL, sliced on `digitised_is_sdd` × `digitised_is_inventory` at digitise time: `all`, `sdd-inventory`, `sdd-noninventory`, `nonsdd-inventory`, `nonsdd-noninventory`. Per-cohort N differs slightly between View 1 and View 2 for the same reason as above.

### v1 build mistake (corrected)
First attempt built a Doctor×Warehouse×Dispatch **cross-tab** with Delivery folded into % columns — wrong. Tejas: "your leg column does not have row entries for delivery leg... I wanted early/on-time/late for each leg." Corrected to a **per-leg marginal table**: one row per leg (Doctor/Warehouse/Dispatch/Delivery), each with its own independent E/OT/L split, same shape for all 5 cuts × 2 views. This is the version in `view1-orders-all.csv`/`view2-orders-all.csv`'s `*_leg` columns and all downstream work.

### View 1 ALL results (n=515,465)
| Leg | Early | On-Time | Late |
|---|---|---|---|
| Doctor | 47.7% | 29.4% | 22.9% |
| Warehouse | 95.4% | 0.0% | 4.5% |
| Dispatch | 24.3% | 68.5% | 7.2% |
| Delivery | 32.6% | 51.8% | 15.6% |

### View 2 ALL results (n=515,400)
| Leg | Early | On-Time | Late |
|---|---|---|---|
| Doctor | 73.0% | 22.5% | 4.5% |
| Warehouse | 95.4% | 0.0% | 4.5% |
| Dispatch | 24.3% | 68.5% | 7.2% |
| Delivery | 22.9% | 55.2% | 21.9% |

Key reads: **Doctor looks far better in View 2** (73.0% Early vs 47.7%) — confirmation-lag (`dr_confirm_ts`), not call-scheduling, drives View 1's Doctor Late rate. **Delivery gets *worse* in View 2** (21.9% vs 15.6% Late) — isolating last-mile duration reveals a real execution gap that View 1's absolute-date comparison was masking with upstream slack, especially severe in SDD segments (SDD+Non-Inventory: 4.4%→47.4% Late).

### Per-cut results (View 1)
| Cut | N | Delivery Early | On-Time | Late |
|---|---|---|---|---|
| ALL | 515,465 | 32.6% | 51.8% | 15.6% |
| SDD+Inventory | 133,151 | 11.5% | 80.6% | 7.9% |
| SDD+Non-Inventory | 32,437 | 64.3% | 31.3% | 4.4% |
| NonSDD+Inventory | 292,113 | 32.6% | 46.4% | 21.0% |
| NonSDD+Non-Inventory | 57,764 | 63.5% | 24.1% | 12.4% |

NonSDD+Inventory (56.7% of population) is the worst and largest segment (worst Dispatch too: 6.6% Early/10.9% Late). SDD+Inventory is the calibration benchmark (tightest Dispatch, lowest Delivery-Early — meaning tightly matched promises).

---

## 4. Dispatch × Delivery crosstab (View 1 only)

Script: `2026-07-04-aggregate-dispatch-delivery-crosstab-v1.py` → `outputs/view1-dispatch-delivery-crosstab.csv` (9 rows, n=515,465).

| Dispatch | Delivery | n | % |
|---|---|---|---|
| Early | Early | 77,223 | 15.0% |
| Early | On-Time | 42,935 | 8.3% |
| Early | Late | 5,233 | 1.0% |
| On-Time | Early | 88,213 | 17.1% |
| **On-Time** | **On-Time** | **214,729** | **41.7%** |
| On-Time | Late | 50,146 | 9.7% |
| Late | Early | 2,574 | 0.5% |
| Late | On-Time | 9,291 | 1.8% |
| **Late** | **Late** | **25,121** | **4.9%** |

Dispatch Late is the strongest single predictor of Delivery Late (67.9% conversion). Dispatch Early doesn't guarantee Delivery Early (only 15.0% Early/Early vs 8.3% Early/On-Time). Dispatch On-Time still leaks 9.7% into Delivery Late — largest absolute Late contributor, pointing at the last-mile leg itself.

Tejas's read (agreed as fair): cohorts 1(Early/Early)+2(Early/OnTime)+5(OnTime/Late) attributable to dispatch mishaps; 3(OnTime/Early)+4(OnTime/Late)... [refined further below]. On-Time/On-Time (41.7%) called "best" cohort — agreed, since it reflects calibration not just speed (Early can reflect promise padding, a recurring theme).

---

## 5. Dispatch × Delivery(View1) × Delivery(View2) — the 13-row table

Script: `2026-07-04-aggregate-dispatch-delivery-v1v2-v1.py` → `outputs/view1-dispatch-delivery-v1v2-crosstab.csv`. Population: **515,396** orders common to both views (View1 ∩ View2). Dispatch asserted identical in both views (0 mismatches, hard-fails otherwise).

**Algebraic proof (test-validated on all 515,396 orders' raw dates):** let x = date(pickup)−date(dispatch_promise) [sign = Dispatch bucket], D1 = date(delivery_attempt)−date(delivery_promise) [sign = View1 Delivery]. View2 Delivery = sign(D1 − x), always. So whenever Dispatch=On-Time (x=0), View2 Delivery = View1 Delivery exactly — **18 of 27 possible (Dispatch,DeliveryV1,DeliveryV2) combos are structurally impossible**, only 13 exist. This explains a wave of "why are there zeros" questions resolved cleanly by this proof.

Full 13-row table (n=515,396), sorted by n:

| Dispatch | Delivery V1 | Delivery V2 | n | % |
|---|---|---|---|---|
| On-Time | On-Time | On-Time | 214,703 | 41.70% |
| On-Time | Early | Early | 88,201 | 17.10% |
| Early | Early | On-Time | 52,235 | 10.10% |
| On-Time | Late | Late | 50,137 | 9.70% |
| Early | On-Time | Late | 42,930 | 8.30% |
| Late | Late | On-Time | 17,535 | 3.40% |
| Early | Early | Early | 16,813 | 3.30% |
| Late | On-Time | Early | 9,290 | 1.80% |
| Early | Early | Late | 8,167 | 1.60% |
| Late | Late | Late | 6,550 | 1.30% |
| Early | Late | Late | 5,232 | 1.00% |
| Late | Early | Early | 2,573 | 0.50% |
| Late | Late | Early | 1,030 | 0.20% |

### "Amazing" vs "not amazing" cohort split (Tejas's framing, agreed)
- **Cohorts 1, 3, 6** (rows where Delivery-V2 = On-Time: OnTime/OnTime/OnTime=214,703; Early/Early/OnTime=52,235; Late/Late/OnTime=17,535) = **284,473 orders (55.2%)** — delivery ops hit its own duration target exactly. Called "amazing"/"ops not breaking." Agreed philosophically: On-Time (calibrated + reliable) is the right definition of good, not Early (often reflects padding). Nuance: "amazing" describes the delivery leg's own job, not necessarily the end-to-end customer outcome (e.g. Late/Late/OnTime still ends in a Late customer experience — leg is innocent, order still failed).
- **All other 10 rows = 230,923 orders (44.8%)** — the "not amazing" cohort, the primary investigation subject for the rest of the session.

Tejas's original grouping check confirmed exhaustive both ways (ops-not-breaking = all Delivery-V2=OnTime cells; masked-from-customer = all Delivery-V1=OnTime cells). Two additions I flagged: OnTime/Late/Late (50,137, 9.7%) is the cleanest **pure delivery-leg-fault** cohort (Dispatch fine, both views agree Late, no confound) — the best target for "isolate the delivery leg." Early/Early/Late (8,167, 1.6%) is a **deeper-masked** hidden ops failure (customer saw Early, not just On-Time, while ops missed its own target).

---

## 6. The 230,923-order "not amazing" cohort — day-diff exploration

**v1 mistake:** built exploded-cohort day-diff histogram using **View 1's** delivery date-diff for these 10 rows — produced 22.6% at day_diff=0, which is **impossible** since all 10 rows are defined by Delivery-V2 ≠ On-Time. Tejas caught this exactly: "we took only cohorts where delivery (view 2, ops) was not on-time... how can you have 22.6% orders as On-Time?" Root cause: used wrong leg's diff (View1 vs View2).

**v2 fix:** used **View 2's** duration-diff (`actual_duration − promise_duration`) instead. Result: **0 orders at day_diff=0**, confirmed structurally required. Total 230,923 matches exactly (also matches complement of the 3 "amazing" rows: 515,396−284,473=230,923; also matches independent claim-check against 10-row sum — Tejas's original number was 230,932, off by 9, a likely digit-transposition typo, confirmed 230,923 is correct two ways).

Full 37-row v2 histogram, key groups:
| Bucket | n | % |
|---|---|---|
| Early total | 117,907 | 51.1% |
| 1 day ahead of target | 94,980 | 41.1% |
| Late total | 113,016 | 48.9% |
| 1 day over target | 91,968 | 39.8% |

Nearly 50/50 split beat-vs-miss target; 81% of the whole cohort concentrated at exactly ±1 day.

**Tejas's "80.9% within ±1 day = decent" claim (from earlier v1-based framing then re-verified on v2):** agreed math (my precise recompute: 80.96% of cohort, 36.27% of 515,396 overall, combined with 55.2% "amazing" = 91.47% "fine", remainder 8.53%) but **pushed back on the "decent" framing** — the ±1 day band conflates 94,980 orders that *beat* target (genuinely good) with 91,968 that *missed* target by exactly 1 day (still a real miss, just small). Recommended re-cutting by SDD.

### SDD vs Non-SDD split of the day-diff histogram
Script: `2026-07-04-aggregate-exploded-cohort-day-diff-sdd-v1.py`. SDD n=54,383, Non-SDD n=176,540 (sum=230,923 ✓).

- **SDD: 89.5% (48,666) at exactly "1 day over target"** — near-uniform systematic miss, courier-agnostic.
- **Non-SDD: 64.9% beat target, 24.5% miss by 1 day** — closer to the "roughly balanced" earlier read.
- Headline: the earlier "decent, roughly 50/50" story was being carried by Non-SDD volume; SDD is a near-total systematic 1-day miss.

---

## 7. Switch hypothesis testing (4 factors: courier, inventory, SDD, warehouse)

Script: `2026-07-04-aggregate-focus-area-switch-hypotheses-v1.py`. Population split within the 230,923 cohort: **focus** = |day_diff|≥2 (n=43,975), **control** = |day_diff|=1 (n=186,948), using View2's duration-diff.

| Hypothesis | Focus switch rate | Control switch rate | Enrichment | Verdict |
|---|---|---|---|---|
| Courier partner | 37.7% | 19.2% | ~2x | **Proven — volume driver** |
| Warehouse | 8.2% | 1.6% | ~5x | Real but small volume |
| SDD state | 2.5% | 0.2% | ~12x | Real ratio, negligible standalone volume (never appears alone — always co-occurs with courier switch) |
| Inventory state | 6.4% | 6.9% | ~1x | **Ruled out** — same rate both groups |

Overlap (n=38,983 fully-determinable focus orders): **58.6% (22,858) have NONE of the 4 switches** — majority of the tail unexplained by these hypotheses. **34.1% (13,301) = courier switch alone** — dominant single explained driver. Overlap between hypotheses is minimal (single-cause when explained).

### Courier distribution in the unexplained 22,858 "no switch" remainder
Script: `2026-07-04-aggregate-focus-noswitch-courier-distribution-v1.py`. Indexed against control-group "no switch" distribution (n=133,723).

| Courier | Focus % | Control % | Index |
|---|---|---|---|
| 195 | 34.7% | 23.6% | 1.47 |
| 225 | 14.0% | 8.7% | 1.61 |
| 286 | 7.4% | 4.9% | 1.51 |
| 686 | 1.5% | 0.8% | 1.88 |
| **287** | 5.8% | **29.1%** | **0.20** |

Couriers 195, 185, 225, 286 (index ≥1.3) = 72.5% of the unexplained tail concentrated in 4 couriers. **Courier 287 is the standout protective outlier** (index 0.20, best performer).

### Investigating "why" (philosophical, no build)
- **SDD-mix hypothesis for courier variance: ruled out and inverted.** Verified courier 287 = 100% SDD, all others (195/225/286/247/246/686/185) = 0% SDD except 608 (84% SDD). Since 287 is exclusively SDD and still the *best* performer, SDD-mix can't explain why 195/225/286 are worse.
- **Pincode/geography confound: can't be cleanly separated.** Pincode overlap between courier 287 and others is tiny (2-27%) — couriers operate largely disjoint territories, so courier identity and geography are nearly inseparable in this data.
- **Best-supported alternative (not conclusively provable from this data): network breadth/delivery model.** 195/185/225/286 (broad third-party courier networks, 4,000-10,000 distinct pincodes) are over-indexed in the bad tail; 287/608 (narrow, dense, SDD-heavy, ~600-1,000 pincodes) perform best. Framed as delivery-model difference (broad dispersed network → more transit variance), not courier "skill." Courier 686 is an exception to this pattern (small footprint, still bad index) — not explained.

### Course-correction checkpoint
Tejas flagged the conversation was "getting lost" chasing unfalsifiable geography/network theories. Agreed — redirected to 3 already-proven high-leverage findings not yet acted on: SDD's systematic 1-day miscalibration, Dispatch leg as biggest lever on Delivery outcome, courier 195's volume concentration. Tejas then asked to step back further (see §8).

---

## 8. Circling back — Hypothesis 1: Courier Switch (formal funnel)

Re-anchored on the 13-row table from §5. Tejas: "cohorts to look into = all except 1, 3, 6" (i.e. the 230,923 "not amazing" cohort, reconfirmed).

### Funnel v1 → v2: courier-switch-promise-funnel
Scripts: `2026-07-05-aggregate-courier-switch-promise-funnel-v1.py` (courier-switch branch only) → `-v2.py` (adds symmetric courier-unchanged branch).

Full 13-row funnel (all % of 230,923):

| Step | n | % cohort |
|---|---|---|
| 1. Total orders | 230,923 | 100.00% |
| 2. Courier switched | 48,756 | 21.10% |
| 2a. Switch indeterminate (blank) | 14,386 | 6.20% |
| 3. Courier unchanged | 167,781 | 72.70% |
| 4. Courier switched AND promise changed ("Row 4") | 38,598 | 16.70% |
| 5. Courier switched AND promise unchanged | 10,158 | 4.40% |
| 6. Courier unchanged AND promise changed ("Row 6") | 110,586 | 47.90% |
| 7. Courier unchanged AND promise unchanged ("Row 7") | 57,195 | 24.80% |

Row 6 (47.9%) is the single largest row — biggest problem is promise instability, not courier switching (only 21.1% of cohort even involves a switch). Tejas prioritization call (agreed): Row 6 > Row 4 as ranked problems within-hypothesis; **Row 7 (24.8%) is NOT a "3rd problem" of the same kind — it's evidence the courier/promise hypothesis doesn't apply to a quarter of the cohort at all**, needs separate explanation.

### Shipping-promise-actual-performance (rows 4/6/merged) — "after" picture
Script: `2026-07-05-aggregate-shipping-promise-actual-performance-v1.py`. Grades actual duration (`delivery_attempt − pickup`) against **`shipping_delivery_promise`** (the true, final TAT given to the shipping partner) rather than the stale digitised promise.

| View | n | Early | On-Time | Late |
|---|---|---|---|---|
| Row 4 | 38,598 | 35.6% | 64.3% | 0.1% |
| Row 6 | 110,586 | 15.5% | 84.3% | 0.2% |
| Merged | 149,184 | 20.7% | 79.1% | 0.2% |

**"Too good to be true" recheck (Tejas challenge):** verified independently against the **full 515,462-order population** (not just rows 4/6) with fresh, non-reused code: On-Time 55.8%, Early 43.9%, **Late only 0.3%** — confirms not a selection-specific artifact, holds universally. Also confirmed 3 blank `shipping_delivery_promise` rows correctly excluded (not silently zeroed), both in original script and recheck.

**Caveat surfaced during the recheck:** near-zero Late doesn't mean flawless execution — `shipping_delivery_promise` is itself a loosely-set target (same promise-padding pattern as Warehouse leg elsewhere in this project). Flagged an artifact: `shipping_delivery_promise=15` is a suspicious outlier value (19,249 orders, jumps from single digits straight to 15) driving large spurious "14-15 days early" clusters (~15,760 orders) — possibly a default/fallback TAT, not a genuine promise. Not yet resolved.

### Promise-change-direction (rows 4/6)
Script: `2026-07-05-aggregate-promise-change-direction-v1.py`.

| Row | n | Increased | Decreased |
|---|---|---|---|
| Row 4 | 38,598 | 76.6% | 23.4% |
| Row 6 | 110,586 | 78.0% | 22.0% |

~77-78% of all promise changes **increase** (loosen) the promise, regardless of courier-switch status.

### Merged: promise-direction × actual-performance (4 cells)
Script: `2026-07-05-aggregate-promise-direction-actual-performance-v1.py`. Late stays negligible (≤0.4%) in every cell.

| Cell | n | Early | On-Time | Late |
|---|---|---|---|---|
| Row4 × Increased | 29,569 | 37.1% | 62.8% | 0.1% |
| Row4 × Decreased | 9,029 | 30.8% | 69.1% | 0.1% |
| Row6 × Increased | 86,203 | 12.2% | 87.7% | 0.1% |
| Row6 × Decreased | 24,383 | 27.4% | 72.2% | 0.4% |

**Tejas's honest read (agreed as sharpest framing of the session):** it doesn't matter whether promise increased/decreased or courier changed/didn't — overwhelmingly Early or On-Time everywhere. Neither hypothesized variable does explanatory work; the dominant fact is ops almost never breaches the shipping-time promise, period.

**"No new patterns beyond this, need to circle back" — agreed.** This specific hypothesis thread (courier-switch × promise-direction) had hit its ceiling.

### Digitised-promise-graded performance for rows 4/6 (the "before" picture)
Script: `2026-07-05-aggregate-digitised-promise-actual-performance-v1.py`. Same orders, graded against the **stale digitised promise** instead (reuses View 2's `delivery_leg` field directly, cross-validated via independent recompute — 0 mismatches).

| View | n | Early | On-Time | Late |
|---|---|---|---|---|
| Row 4 | 38,598 | 36.3% | 0.0%* | 63.7% |
| Row 6 | 110,586 | 25.4% | 0.0%* | 74.6% |
| Merged | 149,184 | 28.2% | 0.0%* | 71.8% |

*On-Time = 0% is **structural**, not a bug — rows 4/6 are drawn from the 230,923 cohort that excludes Delivery-V2=On-Time by construction.

**The core "inaccurate promise → inaccurate performance read" finding:** same 149,184 orders swing from 71.8% Late (digitised promise) to 0.2% Late (shipping promise) — a 71.6-point swing from measurement benchmark alone.

### Late-magnitude vs promise-delta (within rows 4/6's digitised-Late orders)
Script: `2026-07-05-aggregate-late-magnitude-vs-promise-delta-v1.py`. n_late: row4=24,603, row6=82,450, merged=107,053.

| View | Late by 1 day | Late by 2+ days | Promise ↑ by 1 | Promise ↑ by 2+ | Promise ↓ |
|---|---|---|---|---|---|
| Row 4 | 64.9% | 35.1% | 46.6% | 53.4% | 0.0% |
| Row 6 | **86.4%** | 13.6% | **79.1%** | 20.9% | 0.0% |
| Merged | 81.5% | 18.5% | 71.6% | 28.4% | 0.0% |

Row 6's "lateness" is almost mechanically the promise-update lag (86.4% miss by 1 day, 79.1% had promise increase by exactly 1 day — near 1:1 correspondence). Row 4 is messier (courier switches introduce more variable jumps). **Zero orders from a promise decrease** — structurally required (can't be late against a bigger promise while promise also shrank, without also being late against the shipping promise, which we know is near-zero).

### Row 4 dominant courier switch pairs
Script: `2026-07-05-aggregate-row4-courier-switch-pairs-v1.py`. 116 distinct pairs, n=38,598.

Top: 185→195 (9.4%), 286→195 (6.5%), 247→195 (6.4%), 185→225 (5.3%), 246→195 (3.8%). **Courier 195 is the dominant destination overall: 34.8% of all row-4 switches land on 195** (from 185/286/247/246/686 combined). **Courier 185 is the dominant source: 24.1%** of switches originate there. Directly explains why 195 carries so much of the unexplained tail volume from §7 — it's the default landing spot when other couriers get swapped out.

---

## 9. Philosophical strategy discussion (no builds, pure reasoning)

Tejas's hypothesis: if the system could pick a shipping courier as reliable/fast as the digitised-time courier, performance should normalize; then improve individual courier promise-selection reliability.

**My critique (v1):** doesn't survive Row 6 (biggest row, courier never changes, still 74.6% "Late" against digitised promise) — courier continuity alone doesn't fix it. Couriers execute near-flawlessly against their *own* real promise everywhere — the couriers aren't broken, the promise-setting is. Row 7 invisible to this theory. Redirect: fix digitisation-time promise-setting, not shipping-time courier selection.

**Tejas's refinement:** system independently re-selects "best courier by speed/reliability score" at both digitisation and shipping, with no memory of the earlier selection — that's the actual mechanism, and it explains Row 6 too (same courier re-scored fresh can still get a different TAT).

**My response:** stronger, does explain Row 6. But two pushbacks: (1) the ~77-78% directional skew toward promise *increases* is too one-directional for pure "memoryless independent re-optimization" (which predicts symmetric noise) — points instead to a **systematic optimism bias** in the digitisation-time estimate specifically, a calibration problem not a memory problem. (2) Row 7 (nothing changed) sits entirely outside this theory. Honest limitation stated: no visibility into the actual scoring model, only downstream TAT outcomes.

**Sequencing debate:** Tejas proposed Phase 1 = stabilize/anchor shipping promise to digitised (maximize On-Time), Phase 2 = improve digitisation-time prediction accuracy after. **My pushback:** this risks converting today's "measurement-artifact lateness" into real physical lateness, since the digitised number is the one that's systematically too optimistic — forcing ops to hold it before fixing its accuracy could make outcomes worse, not better. Recommended reversing: fix accuracy first, then anchor.

**Tejas's correction (accepted, materially changes the analysis):** the shipping promise may be tracked internally, but **the customer only ever sees/tracks against the digitised promise**. This means the ~70% "Late" measured against the digitised number **is the real customer experience**, not a benign internal artifact — my prior framing was wrong on this point. Sequencing (fix what the customer feels first) is correct given this. One retained nuance: not all promise-increases are "avoidable drift" (fixable by policy/anchoring) — some may reflect genuine, newly-discovered constraints (courier capacity, route feasibility) that no anchoring policy can override; needs a split before assuming full anchoring is achievable. This "Type A (avoidable) vs Type B (genuine constraint)" split was explained in detail on request but **parked, not yet built**.

---

## 10. Row 7 deep dive

Script: `2026-07-05-aggregate-row7-performance-deep-dive-v1.py`. n=57,195, graded against `shipping_delivery_promise` (== digitised promise here since promise unchanged; cross-validated against View2's own `delivery_leg` — 0 mismatches, confirms the mathematical identity holds).

**On-Time = 0.0% is structural** (same reason as elsewhere in the 230,923 cohort).

| Outcome | n | % |
|---|---|---|
| Early | 57,034 | **99.7%** |
| Late | 161 | 0.3% |

**90.0% of the entire row is "1 day early"** — flips the story from rows 4/6 entirely (this is not a lateness problem). Courier breakdown: uniform across all 11 couriers (99.5-100% Early, 0-0.5% Late) — no courier stands out. **Reframed conclusion:** Row 7 isn't operationally broken at all — it's a **promise-padding problem**, same shape as WH-leg and SDD-leg over-padding found earlier. Nothing changed (courier/promise/warehouse/SDD all constant) yet ops beats the stable promise by ~1 day uniformly — points at a structural/formulaic bias in how the promise is calculated, not an operational/behavioral cause.

---

## 11. Geographic concentration (rows 4/6/7 vs 515,396 baseline)

Script: `2026-07-05-aggregate-row4-6-7-geo-concentration-v1.py`. City via pgeocode (GeoNames India, county_name — not canonical Truemeds master).

| Population | Top-10 city cumulative % |
|---|---|
| Baseline | 22.6% |
| Row 4 | 12.7% (less concentrated) |
| **Row 6** | **34.1% (more concentrated)** |
| Row 7 | 11.7% (less concentrated) |

**Row 6 concentrates in Mumbai (1.8x baseline index), Bengaluru (2.0x), Thane (1.6x), Ghaziabad (1.8x)** — real, metro-specific signal. Rows 4 and 7 show no geographic pattern (below-baseline concentration, spread roughly everywhere). Pincode-level concentration is mild everywhere (~2.3-4.2%), no sharp signal.

---

## 12. Hypothesis 2: Warehouse switch — debunked

Script: `2026-07-05-aggregate-warehouse-switch-funnel-v1.py`. 13-row funnel per spec (asymmetric as given — rows 12/13 split warehouse-same+courier-changed by promise, but no equivalent split exists for row 11 warehouse-same+courier-unchanged, 167,670 orders, 72.6% — flagged as a gap, not filled without explicit request).

**Warehouse changed = 2.8% (6,494 orders)** of the 230,923 cohort — every combination touching a warehouse change caps under 1,000 orders. Cross-validated: row6(327)+row12(38,271)=38,598 (original courier-funnel row 4 total); row7(43)+row13(10,115)=10,158 (original row 5 total) — both exact. **Debunked as prime driver** — two orders of magnitude smaller than courier switching.

---

## 13. Hypothesis 3: SDD state shift — debunked

Script: `2026-07-05-aggregate-sdd-shift-funnel-v1.py`.

| Step | n | % |
|---|---|---|
| SDD → Non-SDD | 125 | 0.1% |
| Non-SDD → SDD | 1,325 | 0.6% |
| No shift | 229,473 | 99.4% |

**Debunked** — combined shift is 0.7% of the cohort, structurally too small to be a prime driver.

---

## 14. "Where do we go from here" — reframing beyond the 4 hypotheses

Tejas: only 4 things should influence delivery ops (wrong courier, wrong promise, delivery-type change, source-location change) — 3 of 4 now ruled out or negligible (warehouse, SDD tiny; courier/promise parked). Asked for what else could be breaking things.

**Key reasoning move:** Row 7's evidence (nothing changed, still near-universal courier-agnostic ~1-day-early pattern) points **away from "switching" event-hunting entirely** and toward a **structural bias in the promise-generation formula itself** — the strongest lead, since by definition nothing "switched" in Row 7 yet the pattern persists.

Other candidates named, ranked: (1) formula/calibration bias (strongest, explains Row 7), (2) elapsed time between digitisation and shipping (staleness), (3) day-of-week/calendar effects, (4) inventory switch (already tested in §7, ruled out, but in a different population framing — flagged as lower priority, not re-verified in this exact row4/6/7 lens).

### Day-of-week concentration check
Script: `2026-07-05-aggregate-cohort-day-of-week-concentration-v1.py`. Anchor: `digitised_ts` weekday. Overall n=515,465 (all View 1 orders, not the 515,396 common set — explicit Tejas spec), cohort n=230,923.

All 7 weekday indices between **0.96 and 1.04** — no signal, essentially identical distribution. **Debunked.**

---

## 15. Invoice-timing data check (digitised→invoice 3-24h gap)

Script: `2026-07-05-aggregate-invoice-timing-performance-v1.py`. Population: all 515,465 View 1 orders (not the 230,923 cohort — a fresh, broader check). Note: this 3-24h window later turned out to match **exactly** the Payment Pending bucket duration described in the PRD (see §17) — a load-bearing coincidence/connection.

Assumption stated (not corrected when asked): "courier_id" for cuts = `shipping_delivery_partner` (the executing courier), not the digitised one.

| Step | n | % |
|---|---|---|
| 1. Total orders | 515,465 | 100.0% |
| 2. Digitised→invoice gap 3-24h | 263,117 | 51.0% |

3. Delivery E/OT/L (of step 2, date(delivery_attempt_time) vs date(digitised_delivery_promise)): Early 89,874 (34.2%), On-Time 130,505 (49.6%), Late 42,738 (16.2%).
4. Dispatch E/OT/L (of step 2, digitised_dispatch_promise vs pickup_time): Early 49,699 (18.9%), On-Time 194,919 (74.1%), Late 18,499 (7.0%).

5. Cut: couriers 246/247 vs all others excluding 287 (287 excluded from both groups entirely):

| | n | Early | On-Time | Late |
|---|---|---|---|---|
| Delivery — 246/247 | 45,159 | 36.3% | 43.6% | 20.0% |
| Delivery — others (excl. 287) | 160,525 | 36.7% | 44.1% | 19.1% |
| **Dispatch — 246/247** | 45,159 | 14.9% | 67.9% | **17.2%** |
| **Dispatch — others (excl. 287)** | 160,525 | 15.0% | 78.6% | **6.4%** |

**Finding: 246/247 have a real, specific Dispatch-leg problem (17.2% vs 6.4% Late, ~2.7x), not a Delivery-leg one** (nearly identical Delivery Late rates, 20.0% vs 19.1% — no signal there).

### Courier switch rate for this window vs overall
Script: `2026-07-05-aggregate-invoice-window-courier-switch-rate-v1.py`.

| Population | n | Switched | Same | Indeterminate |
|---|---|---|---|---|
| All orders | 515,465 | 14.6% | 80.7% | 4.8% |
| 3-24h window | 263,117 | 16.4% | 80.2% | 3.4% |

Mild elevation (1.13x) — not a big gap on its own.

### Cohort 1 (switched) vs Cohort 2 (not switched) within the window — Delivery outcome
Script: `2026-07-05-aggregate-invoice-window-courier-switch-delivery-v1.py`. Delivery def: date(delivery_attempt_time) vs date(digitised_delivery_promise).

| Cohort | n | Early | On-Time | Late |
|---|---|---|---|---|
| Cohort 1: Courier switched | 43,081 | 37.4% | 33.0% | **29.6%** |
| Cohort 2: Courier not switched | 211,000 | 33.0% | 53.6% | **13.5%** |

**This is the strongest single quantified finding of the whole invoice-timing thread: switching the courier during this window more than doubles the Late rate (29.6% vs 13.5%) and nearly halves On-Time (33.0% vs 53.6%).**

---

## 16. PRD collaboration — "Reallocation of Courier Post Payment Pending"

Google Doc: `https://docs.google.com/document/d/1C5jtDbICU7bVkvYIJS1Fuc3GJs_Dkia4EMvN66jaTRA/edit` (read via Drive MCP; no edit-content tool available, so all rewrites were handed back as text for Tejas to paste in).

**PRD's core argument (as read from the doc):** Courier allocation happens at two points — Doctor Order Confirmation, and Order Confirmed (Invoice Generation). If allocated to Bluedart/Shiprocket at Order Confirmed and payment is Prepaid+unpaid, order enters **Payment Pending bucket for 3-24 hours** (matches our invoice-timing window exactly). After that, a scheduler converts Prepaid→COD if still unpaid. Once paid or converted, AWB generates and the order ships to whichever courier was **originally selected — never re-checked**. The doc already embeds our §15 numbers (funnel steps 1-4, 246/247 cut) directly.

### Recommendations given to strengthen the case
1. **Cohort 1 vs 2 finding (§15) is the single strongest missing number** — direct quantified cost of the current gap (29.6% vs 13.5% Late), should headline over the switch-rate numbers alone.
2. **Methodology gap flagged:** the 3-24h invoice gap is a *proxy* for Payment Pending, not the literal flag — recommended checking schema for an actual payment-status/COD-conversion field for a cleaner, harder-to-argue-with population.
3. **For empty "Use Case 4: Promise Buffers"** — the digitised-vs-shipping-promise divergence (§8: 71.8%→0.2% Late swing) directly argues reallocation must refresh the *promise*, not just re-pick a courier.
4. **Reinforcing caveat for Use Case 4:** Row 6 (§8, 47.9% of the 230,923 cohort) proves promise drifts even without a courier switch — courier reallocation alone won't close the biggest single row.
5. **For empty "Rollout & Stage Gates"** — courier 195 as dominant switch destination (34.8%, §8) suggested as the highest-leverage validation target before full rollout.
6. **Honest caveat for Metrics:** Row 7 (§10, 57,195 orders, ~1-day universal padding regardless of courier) is a structural residual this initiative won't touch — should be stated explicitly so the initiative isn't judged against a bar it can't clear.

### "Why Now?" section — rewritten
Full replacement text drafted (see chat log for verbatim; not reproduced here in full to avoid duplication) incorporating: current-process description (Tejas's own text, cleaned up), the "never re-checked" gap, the 51.0% population-scale stat, the 16.4% vs 14.6% switch-rate baseline, the Cohort 1 vs 2 headline finding (29.6% vs 13.5% Late — described as the direct, measurable cost), and the 246/247 Dispatch-Late finding (17.2% vs 6.4%) as evidence that which courier ends up shipping matters. Closing paragraph ties these into the reallocation-check proposal.

### Day-over-day courier share at digitisation (geography-agnostic)
Tejas's ask: prove that by holding one courier fixed for 24h, we ignore how "best courier" shifts day to day — and that this shift, aggregated across **all** orders/geographies, has geography "removed as a bias" (national aggregation dilutes any city-specific mix effect, so residual day-to-day movement reflects real courier-standing change, not order-mix).

Script: `2026-07-05-aggregate-digitised-courier-share-by-day-v1.py` → `outputs/digitised-courier-share-by-day.csv`. Population: all 515,465 View 1 orders, all 24 dates (May 8-31 2026), top-8 couriers (287, 195, 185, 247, 246, 225, 286 — only 7 non-blank distinct top couriers existed) + Other + blank buckets, share % per day.

Key day-to-day moves: **courier 225 nearly doubles** (~5.6%→~9.2% over the period, steady climb); **courier 185 declines** (~15-17%→~12-14%); **247 and 246 both dip sharply on May 10** (247: 9.0%→4.9%, 246: 6.9%→4.6%) then recover; **287 stays dominant but trends down slightly** (~28-29%→~24-26%). Blank rate jumps from ~0% (May 8-11) to 5-6% from May 12 onward — a separate data/instrumentation artifact, not part of the courier-share story.

Two Chart.js line-chart visualizations built via the visualize tool: (1) all 7 top couriers including 287, no point labels; (2) at Tejas's request, **287 removed** and **value labels added on every data point** (courier: 195, 185, 247, 246, 225, 286 only).

---

## File index (all created/modified this session)

### Context / locked-rule docs
- `context/2026-07-04-base-population-filter-v1.md`
- `context/2026-07-04-view1-view2-cascade-definitions-v1.md`
- `context/data-sources.md` (updated repeatedly: base population rule, View1/View2 cascade rule, discovered quirks section)

### Scripts (`scripts/`)
- `2026-07-04-structure-base-population-filter-v1.py`
- `2026-07-04-aggregate-view-cascade-v1.py` / `v2.py` / `v3.py`
- `2026-07-04-aggregate-dispatch-delivery-crosstab-v1.py`
- `2026-07-04-aggregate-dispatch-delivery-v1v2-v1.py`
- `2026-07-04-aggregate-exploded-cohort-day-diff-v1.py` (wrong, View1 diff) / `v2.py` (fixed, View2 diff)
- `2026-07-04-aggregate-exploded-cohort-day-diff-sdd-v1.py`
- `2026-07-04-aggregate-focus-area-switch-hypotheses-v1.py`
- `2026-07-04-aggregate-focus-noswitch-courier-distribution-v1.py`
- `2026-07-05-aggregate-courier-switch-promise-funnel-v1.py` / `v2.py`
- `2026-07-05-aggregate-shipping-promise-actual-performance-v1.py`
- `2026-07-05-aggregate-promise-change-direction-v1.py`
- `2026-07-05-aggregate-promise-direction-actual-performance-v1.py`
- `2026-07-05-aggregate-digitised-promise-actual-performance-v1.py`
- `2026-07-05-aggregate-late-magnitude-vs-promise-delta-v1.py`
- `2026-07-05-aggregate-row4-courier-switch-pairs-v1.py`
- `2026-07-05-aggregate-row7-performance-deep-dive-v1.py`
- `2026-07-05-aggregate-row4-6-7-geo-concentration-v1.py`
- `2026-07-05-aggregate-warehouse-switch-funnel-v1.py`
- `2026-07-05-aggregate-sdd-shift-funnel-v1.py`
- `2026-07-05-aggregate-cohort-day-of-week-concentration-v1.py`
- `2026-07-05-aggregate-invoice-timing-performance-v1.py`
- `2026-07-05-aggregate-invoice-window-courier-switch-rate-v1.py`
- `2026-07-05-aggregate-invoice-window-courier-switch-delivery-v1.py`
- `2026-07-05-aggregate-digitised-courier-share-by-day-v1.py`

### Tests (`tests/`) — one paired test per script above, same filename prefix (`test-aggregate-...`). Every test independently recomputes from the raw order-detail files (never trusts the script's own output blindly) and checks totals against previously-published numbers where a cross-file dependency exists.

### Key output CSVs (`outputs/`, gitignored)
`base-population.csv`, `view1-orders-all.csv`, `view2-orders-all.csv`, `view{1,2}-cascade-*.csv` (5 cuts), `view{1,2}-orders-*.csv` (5 cuts), `view1-dispatch-delivery-crosstab.csv`, `view1-dispatch-delivery-v1v2-crosstab.csv`, `exploded-cohorts-delivery-day-diff-histogram*.csv`, `exploded-cohorts-delivery-day-diff-{sdd,nonsdd}.csv`, `focus-area-switch-hypotheses-summary.csv`, `focus-area-switch-overlap.csv`, `focus-noswitch-courier-distribution.csv`, `courier-switch-promise-funnel-v2.csv`, `shipping-promise-actual-performance.csv`, `promise-change-direction.csv`, `promise-direction-actual-performance.csv`, `digitised-promise-actual-performance.csv`, `late-magnitude-vs-promise-delta.csv`, `row4-courier-switch-pairs.csv`, `row7-shipping-promise-performance.csv`, `row7-late-early-magnitude.csv`, `row7-courier-breakdown.csv`, `geo-concentration-pincode.csv`, `geo-concentration-city.csv`, `warehouse-switch-funnel.csv`, `sdd-shift-funnel.csv`, `cohort-day-of-week-concentration.csv`, `invoice-timing-performance.csv`, `invoice-window-courier-switch-rate.csv`, `invoice-window-courier-switch-delivery.csv`, `digitised-courier-share-by-day.csv`.

---

## Open threads / not yet built

1. **Type A (avoidable) vs Type B (genuine-constraint) split** of the promise-increase population in rows 4/6 — explained conceptually, parked, not built.
2. **`shipping_delivery_promise=15` artifact** — suspected default/fallback TAT value distorting Early-magnitude counts, not investigated further.
3. **Payment-status/COD-conversion field check** — recommended to replace the 3-24h invoice-gap proxy with the true Payment Pending flag if one exists in schema; not yet checked.
4. **Inventory-switch re-verification** in the exact row4/6/7 framework (only tested in the earlier focus/control framing, §7).
5. Google Doc PRD sections beyond "Why Now?" (Use Cases 1-4 bodies, Metrics, Rollout & Stage Gates) — recommendations given, not drafted.
