---
project: pba-cr
job: analyse
status: brief
awaiting: []
assumptions: []
signed_off: false
as_of: 2026-10-13
---

# How do PBA's soft promises compare with internal's, and how well does each hold?

**My reading of the flow:** At cart and summary, logistics builds a promise both ways, PBA and internal. One is served, and the customer sees a dispatch date and a delivery date. Hard allocation then picks the courier that ships. Both sides are recorded in `ETA_INSTRUMENTATION` / `HARD_ALLOCATION_INSTRUMENTATION` (MR2). Actuals are in `Order TAT Details`.

**Assumptions and rules applied:** none

## Answer
Pending. Waiting for engineering's extract against the column spec below.

## Approved brief
**Job:** analyse · **Project:** `pba-cr` · **Rules applied:** none

**My reading of the flow:**
- At cart and summary, logistics builds a promise two ways, PBA and internal. It serves one, and the customer sees a dispatch date and a delivery date.
- At dispatch, hard allocation picks the courier that actually ships.
- Where it's recorded:
  - both sides of each soft call: `ETA_INSTRUMENTATION` (MR2);
  - the shipping pick: `HARD_ALLOCATION_INSTRUMENTATION` (MR2);
  - pickup and first attempt: `Order TAT Details`;
  - the date the customer saw: `Delivery Date Tracker`.

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
| M1 | Promise Comparison | PBA: PBA TAT in days, soft. Internal: internal TAT in days, soft | Overall; Matched; Unmatched | On Overall: PBA cache used; Express; Is cold chain |
| M2 | Dispatch Adjusted Promise Comparison | PBA: PBA soft TAT in days − days from WH promise to dispatch promise. Internal: internal soft TAT in days, dispatch to delivery | Overall; Matched; Unmatched | — |
| M3 | Adherence Comparison | PBA: soft promise in days vs actuals in days. Internal: the same | Matched; Unmatched | — |
| M4 | Dispatch Adjusted Adherence Comparison | PBA: dispatch-adjusted soft promise vs actuals in days. Internal: internal TAT (dispatch to delivery) vs actuals in days | Matched; Unmatched | — |
| M5 | Courier Allocation Mix (Soft Allocation) | PBA vs internal | — | — |

Matched means the PBA partner and the internal partner are the same; Unmatched means they differ.

The hard-allocation columns (7, 10, 11, 13, 16, 17) are context only; none of M1–M5 uses them.

### Output
The engineering spec, one reconcile query, the M1–M5 scripts, and a note in `archives/pba-cr/insights/`.

---

### Column spec for engineering

**One Excel sheet, one row per order.**
- Courier-flow forward orders, in or outside the PBA rollout.
- Timestamps in IST ISO format.
- IDs as integers.
- Missing values blank, never 0.
- A second sheet listing the source, filters and window, and how the soft call was chosen.

**Terms used below:**
- **Soft call:** the order's last `ETA_INSTRUMENTATION` record with `eta_context = PRE_OP`, at or before order placement.
- **Hard call:** the order's last `HARD_ALLOCATION_INSTRUMENTATION` record.
- **PBA:** the `COURIER_PBA` candidate.
- **Internal:** at soft, whichever of `COURIER_LEGACY_TAT_ADHERENCE` / `COURIER_DDB_TAT_ADHERENCE` was evaluated. At hard, the same, or `COURIER_CLICKPOST_FALLBACK`.
- **Pick:** rank 1 in a side's `buffer_adjusted_candidates[]`.
- **Dispatch and delivery promise dates:** after pickup and drop buffers.

| # | Column | Meaning | Source (DRAFT layout) |
|---|---|---|---|
| 1 | order_id | Order id | `reference_id` |
| 2 | wh_id | Warehouse | soft `request.warehouseId` |
| 3 | pincode | Delivery pincode | soft `request.deliveryPincode` |
| 4 | pba_in_rollout | TRUE / FALSE / NOT_EVALUATED | soft `configurations.pba_rollout.in_rollout` |
| 5 | promised_wh_processing_date | WH-ready promise used by the soft call | soft `facts.projected_wh_processing_time` |
| 6 | pba_soft_delivery_partner | PBA's pick at soft | soft `cand[PBA]` pick `.delivery_partner_id` |
| 7 | pba_hard_delivery_partner | PBA's pick at hard | hard `cand[PBA]` pick `.delivery_partner_id` |
| 8 | pba_dispatch_promise_date | PBA soft dispatch promise | soft `cand[PBA]` pick `.dispatch_time` |
| 9 | pba_delivery_promise_date | PBA soft delivery promise | soft `cand[PBA]` pick `.delivery_time` |
| 10 | pba_hard_partner_array | Every partner PBA returned at hard, each with `rank`, `delivery_partner`, `dispatch_time`, `warehouse_time`, `pba_tat_in_minutes` | hard `cand[PBA].evaluated_candidates[]` (rank from `buffer_adjusted_candidates[]`) |
| 11 | pba_hard_delivery_days | PBA pick's TAT at hard, in days | hard `cand[PBA]` pick `.delivery_tat_in_minutes` |
| 12 | internal_soft_delivery_partner | Internal's pick at soft | soft `cand[Internal]` pick `.delivery_partner_id` |
| 13 | internal_hard_delivery_partner | Internal's pick at hard | hard `cand[Internal]` pick `.delivery_partner_id` |
| 14 | internal_dispatch_promise_date | Internal soft dispatch promise | soft `cand[Internal]` pick `.dispatch_time` |
| 15 | internal_delivery_promise_date | Internal soft delivery promise | soft `cand[Internal]` pick `.delivery_time` |
| 16 | internal_hard_partner_array | Every partner internal evaluated at hard, each with `rank`, `delivery_partner`, `dispatch_time`, `warehouse_time`, `internal_tat_in_minutes` | hard `cand[Internal].evaluated_candidates[]` (rank from `buffer_adjusted_candidates[]`) |
| 17 | internal_hard_delivery_days | Internal pick's TAT at hard, in days | hard `cand[Internal]` pick `.delivery_tat_in_minutes` |
| 18 | pba_soft_selected_type | PBA_CACHE / PBA_API | soft `cand[PBA].source` |
| 19 | pba_is_cold_chain | Cold-chain order | soft `facts.is_cold_chain` |
| 20 | pba_is_express | PBA's soft pick is express | soft `cand[PBA]` pick `.is_express` |
| 21 | pba_pickup_buffer | Pickup buffer on PBA's soft pick, in minutes | soft `cand[PBA]` pick `.pickup_buffer_in_minutes` |
| 22 | pba_drop_buffer | Drop buffer on PBA's soft pick, in minutes | soft `cand[PBA]` pick `.drop_buffer_in_minutes` |
| 23 | internal_pickup_buffer | Pickup buffer on internal's soft pick, in minutes | soft `cand[Internal]` pick `.pickup_buffer_in_minutes` |
| 24 | internal_drop_buffer | Drop buffer on internal's soft pick, in minutes | soft `cand[Internal]` pick `.drop_buffer_in_minutes` |
| 25 | box_verified_ts | When the box was verified at the warehouse | **Not in instrumentation; please name the source table** |
| 26 | pickup_time | When the courier marked the order picked up | Order TAT Details: Pickup Time |
| 27 | delivery_attempt_time | First delivery attempt | Order TAT Details: Delivery Attempt Time |
| 28 | soft_served_type | Side shown to the customer: PBA / INTERNAL | soft `results.selected_candidate_type` |
| 29 | soft_call_ts | When the soft call was made | soft `created_at` |
| 30 | flow | COURIER / SDD / NONE | soft `facts.flow` |

Equivalents in the artifact's layout: `context/2026-10-13-tracking-question-field-map-v1.md`.

**I pull myself (Metabase):** the promised delivery date from Delivery Date Tracker, to check the soft-call choice.

**Asks for engineering:**
1. The date MR2 records started in production, and which layout shipped.
2. Confirm the soft-call and hard-call rules, or give the right ones.
3. Confirm that when CR flag 2 is on, PBA's delivery promise = WH processing time + PBA TAT.
4. In columns 10 and 16, define `warehouse_time` (WH processing time or pickup slot), and send TAT in minutes. In columns 11 and 17, state how minutes are rounded to days.
5. The source table for column 25.

## Queries to run
Pending.

## Scripts and outputs
Pending.

## Definitions and filters
Pending.

## Caveats and confidence
- The MR2 instrumentation records are proposed and not yet confirmed live. The window can't be fixed until engineering confirms their go-live date (ask 1).
- `logistics_instrumentation` is not in `context/schema.md`. Box verified has no documented source table.

## Next check
Engineering's answers to the five asks above.
