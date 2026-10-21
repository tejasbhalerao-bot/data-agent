---
project: dispatch-aware-picking
job: model
status: brief
awaiting: []
assumptions: []
signed_off: false
as_of: 2026-10-21
---

# How much dispatch adherence is lost because the courier changes after picking starts?

**My reading of the flow:** Courier allocation runs at Order Placed, Doctor Order Confirmed, Processing, Invoice and Post Payment Pending, each time setting a dispatch time (the courier's pickup cutoff). The warehouse starts picking right after Processing against the dispatch time it holds then. If the courier, and so the dispatch time, changes at Invoice or Post Payment Pending, the order was picked against the wrong time and waits in the warehouse, or leaves late. This rests on the PM agent's allocation docs and `schema.md`. The per-stage courier and dispatch time are not documented in `schema.md`; engineering supplies them in the data dump.

**Assumptions and rules applied:** none

## Answer
Pending.

## Approved brief
**DRAFT: awaiting Tejas's approval. Nothing is built until he approves.**

### Objective
Size how much on-time dispatch the company would gain if the warehouse picked each order against the dispatch time the customer was promised, instead of the time held at Processing.

### Hunch to test
Courier often changes between Order Placed, Doctor Order Confirmed, Processing and Invoice. This causes wasted picking and early or late dispatch. Solving it gives more timely dispatch for the customer.

### Scope
- Window: orders placed in the last 30 days ending yesterday (2026-09-21 to 2026-10-20), so the figures are current.
- Cohort: all orders, excluding cancelled and scrapped (`final_order_status`).
- Comparison: orders whose courier did not change after Processing, against orders whose courier did.
- Out of scope: delivery time and customer delivery promise. This initiative moves dispatch adherence only.

### Metrics and cuts
To be established later.

### Grain and output columns
- One row is: one order.
- Columns (36, requested from engineering):

| # | Field |
|---|-------|
| 1 | order_id |
| 2 | order_placed_at |
| 3 | promised_wh_processing_time |
| 4 | promised_dispatch_time |
| 5 | op_is_inventory |
| 6 | op_is_sdd |
| 7 | op_delivery_partner_id |
| 8 | doctor_confirmed_ts |
| 9 | doctor_confirmed_delivery_partner_id |
| 10 | doctor_confirmed_dispatch_time |
| 11 | processing_ts |
| 12 | processing_delivery_partner_id |
| 13 | processing_dispatch_time |
| 14 | invoice_created_ts |
| 15 | shipping_delivery_partner_id |
| 16 | shipping_is_sdd |
| 17 | shipping_dispatch_time |
| 18 | pickup_time |
| 19 | shipping_is_inventory |
| 20 | payment_pending_flag |
| 21 | awb_print_ts |
| 22 | pick_start_ts |
| 23 | pick_complete_ts |
| 24 | actual_dispatch_ts (handover or manifest) |
| 25 | op_warehouse_id |
| 26 | shipping_warehouse_id |
| 27 | payment_pending_ts |
| 28 | payment_pending_delivery_partner_id |
| 29 | payment_pending_dispatch_time |
| 30 | payment_type (COD or prepaid) |
| 31 | final_order_status |
| 32 | is_air |
| 33 | is_cold_chain |
| 34 | pickup_buffer |
| 35 | wh_assigned_ts |
| 36 | wh_fulfilled_ts |

### Open points for engineering
- Is `processing_ts` the moment picking starts, or does picking start separately (fields 22 and 23)?
- Is `dispatch_time` the courier's pickup cutoff, plus any buffer?
- Do `is_sdd` and `is_inventory` change between stages? If they do, we need them at Doctor Confirmed and Processing as well.
- Is the courier and dispatch time recorded at each of the five stages, or only the final one?

### Sizing assumptions (Tejas to give low, base and high)
| Assumption | Low | Base | High |
|------------|-----|------|------|
| Share of dispatch misses linked to a courier change that dispatch-aware picking would fix | | | |
| Share of the order's idle warehouse hours that picking at the right time would remove | | | |

### What will be produced
A note with the headline range, results by case, floor and ceiling, what moves the answer and the evidence. One query request to engineering for the 36 fields, then scripts that calculate every figure.

### To approve
Reply "ok" to start, or say what to change.

## Queries to run
Not yet.

## Scripts and outputs
Not yet.

## Definitions and filters
Pending.

## Caveats and confidence
Pending. Feasibility of the 36 fields is unconfirmed with engineering.

## Next check
Pending.
