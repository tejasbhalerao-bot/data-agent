---
project: pba-cr
job: analyse
status: brief
awaiting: []
assumptions: []
signed_off: false
as_of: 2026-10-14
---

# How do PBA's soft promises compare with internal's, and how well does each hold?

**My reading of the flow:** At cart and summary, logistics builds a promise both ways, PBA and internal. One is served, and the customer sees a dispatch date and a delivery date. Hard allocation then picks the courier that ships.

**Assumptions and rules applied:** none

## Answer
Pending. Waiting for engineering's extract against the tables below.

## Approved brief
**Job:** analyse · **Project:** `pba-cr` · **Rules applied:** none

**Schema details:** [PBA instrumentation schema details](../context/2026-10-14-pba-instrumentation-schema-details-v1.md)

**My reading of the flow:**
- At cart and summary, logistics builds a promise two ways, PBA and internal. It serves one, and the customer sees a dispatch date and a delivery date.
- At dispatch, hard allocation picks the courier that actually ships.

### Objective
On the same orders, compare the soft promise PBA builds with the one internal builds, and how well each holds against actuals.

### Scope
- **Window:** 10 days of soft promises, starting on the later of MR2 go-live and CR flag 2 go-live. The extract is pulled at least 7 days after the window ends.
- **Cohort:** forward orders in the courier flow, where both sides were evaluated, in or outside the rollout.
  - Orders left out (SDD/hyperlocal, a side not evaluated, no PBA promise) are tallied by reason.
  - That shows the base the comparison covers against all orders in the window.
- **Comparison:** PBA vs internal on the same order.

### Metrics, cuts and sub-cuts
| ID | Metric | Definition | Cuts | Sub-cuts |
|---|---|---|---|---|
| M1 | Promise Comparison | PBA: PBA TAT in days, soft. Internal: internal TAT in days, soft | Overall; Matched; Unmatched | PBA cache used; Express; Is cold chain |
| M2 | Dispatch Adjusted Promise Comparison | PBA: PBA soft TAT in days − days from WH promise to dispatch promise. Internal: internal soft TAT in days, dispatch to delivery | Overall; Matched; Unmatched | PBA cache used; Express; Is cold chain |
| M3 | Adherence Comparison | PBA: soft promise in days vs actuals in days. Internal: the same | Matched; Unmatched | PBA cache used; Express; Is cold chain |
| M4 | Dispatch Adjusted Adherence Comparison | PBA: dispatch-adjusted soft promise vs actuals in days. Internal: internal TAT (dispatch to delivery) vs actuals in days | Matched; Unmatched | PBA cache used; Express; Is cold chain |
| M5 | Courier Allocation Mix (Soft Allocation) | PBA vs internal | — | — |

Matched means the PBA partner and the internal partner are the same; Unmatched means they differ.

### Output
The engineering spec, one reconcile query, the M1–M5 scripts, and a note in `archives/pba-cr/insights/`.

---

## Data asks for engineering, by metric

**Grain:** one row per order in every table. The tables share `order_id`, so they join one to one.

### M1 and M2: Promise Comparison and Dispatch Adjusted Promise Comparison
| # | Column |
|---|---|
| 1 | order_id |
| 2 | wh_id |
| 3 | pincode |
| 4 | pba_in_rollout |
| 5 | order_placed_date |
| 6 | promised_wh_processing_time |
| 7 | pba_soft_selected_delivery_partner |
| 8 | pba_soft_selected_partner_tat_in_days |
| 9 | pba_projected_dispatch_time |
| 10 | pba_projected_delivery_time |
| 11 | internal_soft_selected_delivery_partner |
| 12 | internal_soft_selected_partner_tat_in_days |
| 13 | internal_projected_dispatch_time |
| 14 | internal_projected_delivery_time |
| 15 | internal_drop_buffer |
| 16 | internal_pickup_buffer |
| 17 | pba_drop_buffer |
| 18 | pba_pickup_buffer |
| 19 | pba_is_cold_chain |
| 20 | pba_is_express_eligible |
| 21 | pba_soft_selected_type (Cache / API) |
| 22 | pba_soft_preference_array [partner, tat, dispatch_time] |
| 23 | internal_soft_preference_array [partner, tat, dispatch_time] |
| 24 | flow (COURIER / SDD) |

### M3 and M4: Adherence Comparison and Dispatch Adjusted Adherence Comparison
| # | Column |
|---|---|
| 1 | order_id |
| 2 | pba_hard_selected_delivery_partner |
| 3 | pba_hard_partner_tat_in_days |
| 4 | pba_hard_projected_dispatch_time |
| 5 | pba_hard_projected_delivery_time |
| 6 | pba_hard_preference_array [partner, tat, dispatch_time] |
| 7 | internal_hard_selected_delivery_partner |
| 8 | internal_hard_partner_tat_in_days |
| 9 | internal_hard_projected_dispatch_time |
| 10 | internal_hard_projected_delivery_time |
| 11 | internal_hard_preference_array [partner, tat, dispatch_time] |
| 12 | box_verified_ts |
| 13 | awb_print_ts |
| 14 | pickup_time |
| 15 | delivery_attempt_time |

M5 (Courier Allocation Mix) is covered by the tables above.

### Not requested now
- **Old vs new construction marker:** dropped, as agreed.

## Queries to run

| ID | Purpose | Serves | Latest file | Save the CSV as |
|----|---------|--------|-------------|-----------------|
| Q1 | Base extract: one row per order with soft (PBA, internal), hard (PBA, internal) and actuals | M1, M2, M3, M4, M5 | `archives/pba-cr/queries-dump/2026-10-15-pba-cr-promise-adherence-base-query-v2.md` | `archives/pba-cr/raw-data/pba-cr-promise-adherence-base.csv` |

Q1 has open items listed in its file. v1 is superseded. No probe query yet.

## Scripts and outputs
Pending.

## Definitions and filters
Pending.

## Caveats and confidence
- The MR2 instrumentation records are proposed and not yet confirmed live. The window can't be fixed until engineering confirms their go-live date.
- `logistics_instrumentation` is not in `context/schema.md`. Box verified has no documented source table.

## Next check
Engineering's extract against the tables above, and the source of `box_verified_ts`.
