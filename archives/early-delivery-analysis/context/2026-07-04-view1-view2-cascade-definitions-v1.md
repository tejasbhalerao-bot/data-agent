# View 1 / View 2 Cascade — Locked Definitions

Two lenses on the same Doctor → Warehouse → Dispatch → Delivery cascade. Doctor and Delivery legs differ by view; Warehouse and Dispatch legs are identical in both (intentional — warehouse ops is expected to operate customer-backwards regardless of view).

- **View 1 — customer-experienced.** What the customer actually saw.
- **View 2 — ops-execution.** How operations performed, isolated from customer-facing lag.

## Leg rules

| Leg | View 1 | View 2 | Classification |
|---|---|---|---|
| Doctor | `digitised_dr_promise` vs `dr_confirm_ts` | `digitised_dr_promise` vs `actual_doctor_call_time` | timestamp, ±60s buffer → Early / On-Time / Late |
| Warehouse | `digitised_dispatch_promise` vs `invoice_create_ts` | same as View 1 | matched to the minute (data has no seconds) → less=Early, equal=On-Time, greater=Late. **Deliberately benchmarked against the dispatch promise, not `digitised_wh_promise`** — warehouse should optimize for orders out the door by the promised dispatch time, not just "processed and ready." |
| Dispatch | `digitised_dispatch_promise` vs `pickup_time` | same as View 1 | calendar-date diff → <0 Early, 0 On-Time, >0 Late |
| Delivery | `digitised_delivery_promise` vs `delivery_attempt_time`, calendar-date diff | `promise_duration_days = date(delivery promise) − date(dispatch promise)`; `actual_duration_days = date(delivery attempt) − date(pickup)`; compare the two integers | less=Early, equal=On-Time, greater=Late |

## Cuts (both views)

4-way cross + ALL (uncut), sliced on digitise-time state:
- `digitised_is_sdd` (true/false)
- `digitised_is_inventory` (true/false)

→ 5 cohorts per view: `all`, `sdd-inventory`, `sdd-noninventory`, `nonsdd-inventory`, `nonsdd-noninventory`.

## Population

Base: locked project population (`outputs/base-population.csv` — `digitised_ts > 8 May 2026` + `delivery_attempt_time` not null, 522,793 unique orders after dedup).

Each view drops rows additionally missing any of its required fields (`digitised_dr_promise`, `invoice_create_ts`, `digitised_dispatch_promise`, `pickup_time`, `digitised_delivery_promise`, `delivery_attempt_time`, `digitised_is_sdd`/`is_inventory` populated true/false, + the view's own Doctor-actual column). Final N is reported per view — the two views do **not** necessarily land on the same N.

| View | Final N | % of base population |
|---|---|---|
| View 1 (`dr_confirm_ts` populated) | 515,465 | 98.6% |
| View 2 (`actual_doctor_call_time` populated) | 515,400 | 98.6% |

| Cut | View 1 N | View 2 N |
|---|---|---|
| all | 515,465 | 515,400 |
| sdd-inventory | 133,151 | 133,142 |
| sdd-noninventory | 32,437 | 32,434 |
| nonsdd-inventory | 292,113 | 292,068 |
| nonsdd-noninventory | 57,764 | 57,756 |

## Script

`scripts/2026-07-04-aggregate-view-cascade-v1.py`

## Outputs (gitignored, regenerate by re-running the script)

Per view (view1, view2) × per cut (all, sdd-inventory, sdd-noninventory, nonsdd-inventory, nonsdd-noninventory):

- `outputs/viewN-cascade-<cut>.csv` — 27-row (max) Doctor×Warehouse×Dispatch table with order count and Delivery Early/On-Time/Late % breakdown within each combo.
- `outputs/viewN-orders-<cut>.csv` — every raw column for each order in that cohort + computed `doctor_leg` / `warehouse_leg` / `dispatch_leg` / `delivery_leg` labels. Point directly to these files for order-level follow-up analysis.
