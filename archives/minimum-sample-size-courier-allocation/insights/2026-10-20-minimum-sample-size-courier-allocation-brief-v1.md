---
project: minimum-sample-size-courier-allocation
job: model
status: saved
awaiting: []
assumptions: []
signed_off: false
as_of: 2026-10-20
---

# Brief: minimum sample size in courier allocation

This document holds everything except the results: what we set out to do, how, with which rules and data, how it was checked, and what to watch for. The results are in `2026-10-20-minimum-sample-size-courier-allocation-results-v1.md`, with the metrics defined in its glossary. It replaces the combined note `2026-10-20-minimum-sample-size-courier-allocation-v1.md`, which is kept for history.

## 1. The question

If a lane (warehouse × pincode × courier) must have at least x orders in its window before its TAT and adherence are trusted, how much would adherence change, and what would it cost in the customer's promise? Tested for x = 10, 15 and 20 against today.

## 2. What the simulation does

My reading of the flow: a customer places an order and Strategy 1 picks a courier from each courier's TAT and adherence, built from recent deliveries on its lane. That sets the promise. At invoice it picks the shipping courier again. The first delivery attempt then shows whether the promise held.

For every order in scope:

1. Run the allocation at the order placed date and again at the invoice date.
2. Take the courier allocated at each stage and its promise. The customer's promise is the order placed one.
3. Report adherence only for orders where the courier allocated at invoice is the courier that really shipped the order (matched orders).
4. Report today's adherence on those same orders: the real promise against the real delivery.
5. Report the promise, and its comparison with today's, on those same orders.

Orders where the simulation would allocate a different courier are not compared, because the delivery speed in the data belongs to the courier that really shipped them. The courier allocation mix is reported on all orders, because it describes allocation and not adherence.

## 3. Scope

- **Decision dates:** orders placed 29 Jul to 24 Sep 2026 (the results). 29 Jul is the first date with a full 28-day history. October is never used, because the Clickpost-based allocation (Strategy 2) went live in October. Figures for 29 Jul to 30 Sep are in the output files.
- **Orders:** shipped by 185, 195, 225, 246, 247 or 286, with an order-placed row, invoiced within the window, and with a promised warehouse processing time.
- **Funnel:** 1,492,971 shipment rows for the six couriers; 1,443,611 have an order-placed row; 993,021 were placed 29 Jul to 30 Sep; 992,386 of those were invoiced by 30 Sep; 991,569 have a promised warehouse time. Placed up to 24 Sep: 941,213 orders, of which 940,480 have at least one candidate courier (the denominator of the results).
- **Why 24 Sep:** the shipment files stop at 30 Sep, so an order delivered in October has no outcome. The share of order-placed rows found in the shipment files is 99.0% on average for 29 Jul to 31 Aug and drops below 97% from 25 Sep (`outputs/sim-v2-matchrate.csv`).
- **Today's rule** is not replayed for the results. It is taken from the data.

## 4. Rules used

These follow the Strategy 1 document (`performance-based-speed-calculation-and-allocation.md`) and the steps you vetted on the 9-order example. The full text is in `context/2026-10-20-process-flow-v5.md` and `context/2026-10-20-simulation-scope-v7.md`.

- **History window:** orders with a first delivery attempt in the N days before the decision date (7, 14, 21, 28), counted on warehouse × courier × (pincode | micro-cluster | macro-cluster | state). Micro-cluster: same state, district and division in the GOI directory, with one value per pincode chosen by majority of post offices. Macro-cluster: same first three digits.
- **Ladder:** pincode over 7, 14, 21, 28 days; then micro-cluster; then macro-cluster; then state. Stop at the first step with at least x orders. If none, use the widest pool (state, 28 days) when it has orders; use the ops config and `TAT Adherence Master` only when it has none.
- **Lane TAT:** the 85th percentile of actual days (pickup date to first delivery attempt date), linear interpolation, rounded up.
- **Adherence of a lane:** the running share of orders from the earliest bucket upward, until it first reaches 85%, over nine delay-day buckets (early 4+ to late 4+). Delay days are actual days minus each order's own promise.
- **Candidates:** the six couriers that serve the pincode (serviceability files), have ops config for the warehouse, and have a `TAT Adherence Master` row.
- **Score:** lane TAT ÷ adherence + schedule adjustment. Lowest score wins. Ties go to 195, then 185, 225, 246, 286, 247.
- **Schedule adjustment:** +1 when the time of day of the promised warehouse processing time (at order placed) or of the invoice time (at invoice) is after the courier's cutoff for the warehouse. No cutoff means no adjustment.
- **Buffers:** drop buffer and pickup buffer are 0.
- **Ops config and adherence master** are today's snapshot, used for July to September decisions. A lane with no ops config row gets 3 days.
- **Warehouse 19** is treated as warehouse 40 for config, adherence master and cutoffs. Its orders and history stay its own.
- **A promise** is the lane TAT of the courier allocated at order placed. An order is on time when actual days are at most its promise.

## 5. Data used

All files are exports supplied by you; none of their queries is saved in the repo. They are local only (`raw-data/`), listed in `context/data-sources.md`.

| Data | Files | What it holds |
|---|---|---|
| Shipments | `orders-2026-07` to `-09` | 2,201,315 orders with a first delivery attempt in the month: warehouse, pincode, courier, pickup, attempt, real promise |
| Order placed | `op-2026-07` to `-09` | 1,506,765 orders: digitised, invoice-create and promised-warehouse timestamps |
| Ops config | `ops-speed-config-wh20` to `wh40` (19 files) | Delivery days per warehouse × pincode × courier |
| Adherence master | `tat-adherence-master.csv` | Fallback adherence per warehouse × courier |
| Cutoffs | `courier-partner-schedules.csv` | Cutoff time per warehouse × courier |
| Serviceability | `serviceability-185` to `-286` | Pincodes each courier serves |
| Geography | `goi-pincode-directory.csv` | District, division and state per post office |

## 6. How it was checked

- **Input files:** every CSV was run through the repo's validator. The only failures are known repeated rows (lanes listed twice with identical values) in the config files of warehouses 20, 22, 37, 38, 40 and in the adherence master for warehouse 40; the script drops them.
- **Unit tests:** 9 tests on the buckets, the percentile and adherence arithmetic (against a plain-list reference), the ladder stops, the tie-break, the schedule adjustment and the classes.
- **The 9-order example:** the full simulation reproduces the example you vetted, with 0 mismatches across 36 order × rule rows.
- **Replay of today's rule against reality:** the replay picks the courier that really shipped on 63.9% of orders and the real promise on 61.4%. This is why the results use reality as today. Where it differs: the shipper scores higher than the winner on 33.0% of orders, loses a tie on 2.5%, and is not a candidate on 0.6%. On lanes with 20 or more orders the real promise is shorter than the 85th percentile of the last 7 days at every percentile tried (best match 81%); on lanes with no recent order it is on average 1.4 days shorter than the ops config snapshot. The cause is not yet known.

## 7. What to keep in mind

- **The orders whose courier changes** (56% to 59%) are not compared; how the new courier would have delivered is unknown.
- **Late September** is left out of the results because outcomes after 30 Sep are not in the data.
- **Today's courier at order placed** is not in the data (only the shipping courier is), so the order-placed mix is measured against the replay.
- **Lanes without cutoffs** get no schedule adjustment: warehouse 30 for 195, 225 and 286 (not confirmed) and warehouse 27.
- **Still open:** the two zero adherence pairs (warehouse 23 × 286, warehouse 35 × 246), the 15-day promise spike, the default of 3 days for a missing config row, the cause of the missing order-placed rows (excluded), and the percentile method (linear interpolation; the document does not name one).
- **Sample size:** every headline figure is over hundreds of thousands of orders. "Caused" is not claimed: the simulation shows what the rule would have chosen on past orders, not how customers or couriers respond.

## 8. Scripts and outputs

All outputs are local only (`outputs/`, never pushed). Run order: S0, S1, then the rest.

| ID | What it does | File (in `scripts/`) | Writes |
|---|---|---|---|
| S0 | One state, district, division and macro-cluster per pincode | `2026-10-20-structure-goi-pincode-map-v1.py` | `goi-pincode-map.csv` |
| S1 | The full simulation: allocation at order placed and at invoice under today's rule and x = 10, 15, 20 | `2026-10-20-aggregate-simulation-v2.py` | `sim-v2-orders.csv`, `sim-v2-summary.csv`, `sim-v2-matchrate.csv` |
| S4 | Data-used shares grouped by geography | `2026-10-20-aggregate-note-derived-figures-v1.py` | `note-derived-figures-v1.csv` |
| S5 | Today (real) next to the replay and x; invoice mix against the real mix | `2026-10-20-aggregate-today-real-baseline-v2.py` | `today-real-baseline-v2.csv` |
| S10 | Results on matched orders, with courier, warehouse and common-set cuts | `2026-10-20-aggregate-results-matched-orders-v1.py` | `results-matched-orders-v1.csv` |
| S2, S6, S8, S9 | Checks on how well the replay matches reality | `aggregate-replay-diagnostics-v2`, `aggregate-replay-mismatch-v1`, `aggregate-promise-gap-thin-lanes-v1`, `aggregate-percentile-variants-v1` | `replay-diagnostics-v2.csv`, `replay-mismatch-v1.csv`, `promise-gap-thin-lanes-v1.csv`, `percentile-variants-v1.csv` |
| S3, S7 | Earlier like-for-like comparisons (S10 supersedes them for the results) | `aggregate-like-for-like-v2`, `aggregate-like-for-like-real-v2` | `like-for-like-v2.csv`, `like-for-like-real-v2.csv` |

Tests (in `tests/`): `2026-10-20-test-aggregate-simulation-v2.py` (unit tests) and `2026-10-20-test-simulation-matches-example-v2.py` (reproduces the 9-order example). The 9-order example scripts (steps 1 to 8, in `scripts/`) are the worked example you vetted.

Run command for the simulation: `python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-simulation-v2.py` (about two minutes).

## 9. What would improve it

- Orders placed 25 to 30 Sep that were delivered in October, to extend the window to 30 Sep.
- The courier allocated at order placed (soft allocation) per order, so the order-placed mix can be read against reality.
- An explanation of the replay gap (how the real rule differs), so today's rule can be replayed faithfully.

## 10. Approval

The original brief was approved on 2026-10-20 ("the brief seems okay now"). This version restates it with the simplified metrics you asked for the same day (adherence and promise on matched orders only, today taken from reality). Not yet approved in this form.
