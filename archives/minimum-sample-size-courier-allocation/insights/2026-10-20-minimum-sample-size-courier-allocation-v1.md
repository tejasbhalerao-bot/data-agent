---
project: minimum-sample-size-courier-allocation
job: model
status: saved
awaiting: []
assumptions: []
signed_off: false
as_of: 2026-10-20
---

# What happens to adherence, and to the customer's promise, if a lane needs at least x orders before its TAT and adherence count?

**My reading of the flow:** A customer places an order and Strategy 1 picks a courier from each courier's TAT and adherence, built from recent deliveries on its warehouse x pincode lane. That sets the promise. At invoice it picks the shipping courier again. The first delivery attempt then shows whether the promise held. The data comes from the shipment files (pickup, attempt, promise), the order-placed files (placed and invoice times), the ops config, `TAT Adherence Master`, the courier cutoffs, and the serviceability and GOI files.

**Assumptions and rules applied:** the rules are in the project context: `context/2026-10-20-process-flow-v5.md` and `context/2026-10-20-simulation-scope-v7.md`.

## Answer

### Headline
Requiring at least 10, 15 or 20 orders before a lane's TAT and adherence count would have raised on-time adherence by about 1.6 to 1.8 points across all orders (M1) and by about 3.4 to 3.9 points on the orders whose courier does not change (M2), at the cost of a 0.09 to 0.10 day longer average promise (M4). Orders placed 29 Jul to 24 Sep 2026, 940,480 orders. (M1, M2, M4 via S1, `sim-v2-summary.csv`.)

The courier would change for 56% to 59% of orders (M3), so M2 describes only the 41% to 44% that stay with the same courier. The three values of x give nearly the same result: x = 20 is best on M1 and M2 and costs the most in promise and courier changes.

### Assumptions
| Assumption | Low | Base | High | Source |
|------------|-----|------|------|--------|
| Minimum sample size x (orders on a lane before its TAT and adherence count) | 10 | 15 | 20 | Tejas |

Everything else is fixed by the process flow and the scope notes: percentile 85%, no drop or pickup buffer, today's ops config and adherence master. Today's rule (x = 1) is the baseline.

### Results by case
Orders placed 29 Jul to 24 Sep (S1, `sim-v2-summary.csv`, "complete dates").

| Metric | Today | x = 10 | x = 15 | x = 20 |
|---|---|---|---|---|
| M1 adherence % (940,480 orders) | 74.46 | 76.16 | 76.04 | 76.26 |
| M1 change vs today (points) | | +1.70 | +1.58 | +1.80 |
| M2 adherence % (orders reported) | 81.65 (601,469) | 85.08 (414,585) | 85.29 (395,433) | 85.51 (383,706) |
| M2 change vs today (points) | | +3.42 | +3.64 | +3.86 |
| M3 orders not reported in M2 % | 36.05 | 55.92 | 57.95 | 59.20 |
| M4 average promise (days) | 2.204 | 2.295 | 2.295 | 2.307 |
| M4 change vs today (days) | | +0.091 | +0.091 | +0.103 |
| M4 share of orders with a longer promise % | 0.00 | 21.65 | 22.32 | 23.42 |
| M4 share with a shorter promise % | 0.00 | 13.66 | 14.31 | 14.29 |
| M4 share with an equal promise % | 100.00 | 64.70 | 63.37 | 62.28 |

For reference, real adherence (actual days against the real promise) is 81.01% on 941,213 orders (S1).

### Floor and ceiling
Not applicable: this is a replay of a rule change on past orders, not a sizing from assumptions.

### What moves the answer
- **Moving from today to any x of 10 or more is the large step; the choice among 10, 15 and 20 is small.** M1 differs by at most 0.22 points between the three, and M2 by 0.44 points. M3 rises 3.3 points and the average promise 0.012 days from x = 10 to x = 20 (S4).
- **Under today's rule, 70.6% of courier evaluations at order placed fall back to the ops config** because the pincode has no order in the last 7 days (M7). At x = 20 that falls to 5.0%, with 2.2% on the widest pool below x; most evaluations resolve in the micro-cluster (47.9% across windows, 25.7% of them over 7 days) or at the pincode (19.6% across windows) (S4).
- **Part of the M2 gain comes with a longer promise.** On the same orders where the courier is unchanged under x = 20, adherence is 85.51% under x's promise against 80.34% under today's promise, and the average promise is 2.262 against 2.088 days (table 6).

### Break-even and what would change the conclusion
Not calculated: there is no agreed value for a day of promise against a point of adherence. If a longer promise costs more conversion than the adherence is worth, the gain reverses; Tejas's earlier rollout limits (promise worse by 0.5 days, adherence worse by 3 points) are well outside these results. A better match between the replay and real promises would change the size of the effect.

### So what
x = 20 gives the largest adherence gain (+1.8 on M1, +3.9 on M2) for about a tenth of a day of promise, and x = 10 and 15 are nearly as good, so the choice among them can rest on operational grounds. The larger consequence is the courier mix: at x = 20, 195 would lose 8.9 points of orders at order placed while 286 gains 4.7 and 247 gains 3.8. That, and the replay gap in Caveats, should be settled before a pilot.

### Evidence
All figures are from S1 (`outputs/sim-v2-summary.csv`, "complete dates") unless stated.

**Table 1. Courier mix at order placed, % of 941,213 orders (M5).**

| Courier | Today | x = 10 | x = 15 | x = 20 | Change x = 10 | Change x = 15 | Change x = 20 | Actually shipped |
|---|---|---|---|---|---|---|---|---|
| 195 | 29.06 | 21.47 | 20.60 | 20.18 | -7.59 | -8.46 | -8.88 | 33.02 |
| 185 | 18.07 | 19.87 | 19.47 | 19.58 | +1.80 | +1.41 | +1.51 | 19.22 |
| 225 | 15.03 | 14.65 | 14.65 | 14.62 | -0.38 | -0.38 | -0.41 | 13.82 |
| 246 | 15.96 | 15.08 | 15.32 | 15.34 | -0.88 | -0.64 | -0.62 | 16.11 |
| 286 | 8.14 | 12.81 | 13.15 | 12.79 | +4.67 | +5.00 | +4.65 | 6.45 |
| 247 | 13.65 | 16.04 | 16.72 | 17.41 | +2.38 | +3.07 | +3.76 | 11.38 |

**Table 2. Courier mix at invoice, change vs today in points (M6).** x = 20: 195 -8.82, 185 +1.67, 225 -0.44, 246 -0.84, 286 +4.91, 247 +3.52. x = 10 and x = 15 are in the summary file.

**Table 3. Where courier evaluations at order placed resolve, % (M7).**

| Data used | Today | x = 10 | x = 15 | x = 20 |
|---|---|---|---|---|
| Pincode, 7 days | 29.43 | 12.15 | 8.85 | 6.80 |
| Pincode, 14 to 28 days | 0 | 14.47 | 13.73 | 12.80 |
| Micro-cluster, any window | 0 | 48.52 | 48.45 | 47.85 |
| Macro-cluster, any window | 0 | 9.39 | 10.75 | 11.99 |
| State, any window | 0 | 9.36 | 11.56 | 13.43 |
| Widest pool below x | 0 | 1.16 | 1.69 | 2.16 |
| Ops config | 70.56 | 4.95 | 4.96 | 4.97 |

(Grouped rows are the sums of the windows in `sim-v2-summary.csv`, computed by S4, `outputs/note-derived-figures-v1.csv`, via S1.)

**Table 4. M1 and M2 by courier that shipped (%).**

| Courier | M1 today | M1 x = 20 | M2 today | M2 x = 20 |
|---|---|---|---|---|
| 195 | 71.6 | 72.1 | 80.6 | 85.2 |
| 185 | 78.6 | 80.0 | 85.3 | 87.1 |
| 225 | 67.0 | 70.0 | 75.0 | 82.6 |
| 246 | 77.9 | 80.1 | 83.8 | 85.8 |
| 286 | 74.5 | 78.8 | 80.8 | 85.0 |
| 247 | 79.7 | 82.8 | 82.8 | 85.9 |

Every courier improves on both metrics. By-warehouse figures are in the summary file.

**Table 5. How closely the replay of today's rule matches reality (S2, `replay-diagnostics-v2.csv`).** Replayed promise equals the real promise: 61.4%. The shipping courier's own projected TAT equals the real promise: 62.8%. The replayed invoice winner is the courier that shipped (M8): 63.9% overall, from 31.9% in warehouse 23 to 74.0% in warehouse 22.

**Table 6. Like-for-like (S3, `like-for-like-v2.csv`).**

| Rule | Orders | Adherence under x's promise | Adherence under today's promise | Average promise, x | Average promise, today |
|---|---|---|---|---|---|
| x = 10, courier unchanged | 414,585 | 85.07 | 80.04 | 2.256 | 2.089 |
| x = 10, courier would change | 525,895 | 69.12 | 70.06 | 2.326 | 2.294 |
| x = 15, courier unchanged | 395,433 | 85.29 | 80.28 | 2.253 | 2.088 |
| x = 15, courier would change | 545,047 | 69.32 | 70.23 | 2.325 | 2.288 |
| x = 20, courier unchanged | 383,706 | 85.51 | 80.34 | 2.262 | 2.088 |
| x = 20, courier would change | 556,774 | 69.88 | 70.40 | 2.338 | 2.284 |

## Approved brief

### Objective
Show the change in adherence, and the change in the customer's promise, when a lane needs at least x orders (x = 10, 15 and 20) before its TAT and adherence count, widening through the ladder when it doesn't.

### Scope
- **Decision dates:** orders placed 29 Jul to 30 Sep 2026. 29 Jul is the first date with a full 28-day history, and October is never used.
- **Orders:** shipped by 185, 195, 225, 246, 247 or 286, with an order-placed row. Orders delivered in October still count. Warehouse 19 uses warehouse 40's config.
- **Comparison:** today's rule (x = 1, replayed) against x = 10, 15 and 20.

### Metrics and cuts
- M1: Adherence. An order is on time when its actual days from pickup to first delivery attempt are within the promise at the order placed date (promise 2 days, actual 2 days: on time). This holds irrespective of the courier chosen at order placed or at invoice. By rule. Cuts: courier, warehouse, rung reached.
- M2: Adherence, reported only when the courier chosen at invoice is the courier that actually shipped the order. Same comparison as M1. The rule does not depend on the courier chosen at order placed. By rule. Cuts: courier, warehouse.
- M3: Orders not reported in M2. Share of orders where the invoice-stage courier differs from the shipping courier. By rule.
- M4: Customer promise. Average promise at order placed against today's rule, plus the share of orders with a longer, shorter or equal promise. By rule.
- M5: Courier allocation mix at order placed. Share of orders by courier chosen at order placed, shown as the change in percentage points between today and each x. By rule. Cut: courier.
- M6: Courier allocation mix at invoice. Share of orders by courier chosen at invoice, shown as the change between today and each x, with the courier that actually shipped alongside. By rule. Cut: courier.
- M7: Rung reached. Share of courier evaluations resolved at each rung, the widest-data step, and the ops config. By x. This is the volume view for choosing x.
- M8: Replay match. Share of orders where today's rule picks the courier that actually shipped. This checks the replay.

### Grain and output columns
- Main file: one row per order x rule, with order ID, warehouse, pincode, shipping courier, placed and invoice times, rule, placed-stage winner and promise, invoice-stage winner, the shipping courier's projected TAT, and the M1 and M2 results.
- A second summary file has one row per rule x cut.

### How it will be calculated
Each step follows the process flow in `context/2026-10-20-process-flow-v5.md`.

| Step | What | Serves | Data from |
|---|---|---|---|
| 1 | Pick orders in scope, with placed, invoice and promised-warehouse times | all | existing CSVs, in the script |
| 2 | For each order, stage and courier: walk the ladder, then calculate lane TAT and adherence at 85% | M1 to M7 | existing CSVs, in the script |
| 3 | Score each courier with the schedule adjustment, apply the tie-break, and pick winners at placed and invoice | M2 to M6 | script |
| 4 | Classify each order against the order placed promise for M1, and for M2 only when the invoice winner shipped it | M1 to M4 | script |
| 5 | Roll up by rule and cut, including the mix deltas, and check the replay | all | script |

### Job-specific
- **Lever:** minimum sample size x. Cases: x = 10, 15 and 20, given by Tejas. Today's rule (x = 1) is the baseline.

### What will be produced
No new query is needed, because all the data is in hand. The output is a script run on the existing CSVs, its tests, and this note.

### Not yet settled
None of these blocks approval, but each affects the numbers: warehouse 30's config and cutoffs, the zero adherence values, the 15-day promise spike, the default TAT when a config row is missing, and the cause of the missing order-placed rows.

### Approval
Approved by Tejas on 2026-10-20 ("the brief seems okay now"), including the suggested grain and columns.

## Queries to run
Not applicable: no new query was needed. All inputs are CSVs Tejas supplied (listed in `context/data-sources.md`); none of their queries is saved in the repo.

## Scripts and outputs
All outputs are local only (`outputs/`, never pushed).

| ID | Purpose | Serves | Latest file | Reads | Writes | Test | Run with |
|----|---------|--------|-------------|-------|--------|------|----------|
| S0 | Gives each pincode one state, district, division and macro-cluster | ladder | `archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-structure-goi-pincode-map-v1.py` | GOI pincode directory | `outputs/goi-pincode-map.csv` | none needed (checked by hand on two pincodes) | `python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-structure-goi-pincode-map-v1.py` |
| S1 | The full simulation: allocation at order placed and at invoice, M1 to M8 | M1 to M8 | `archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-simulation-v2.py` | shipment, order-placed, config, adherence master, cutoff, serviceability files, S0 | `outputs/sim-v2-orders.csv`, `outputs/sim-v2-summary.csv`, `outputs/sim-v2-matchrate.csv` | `archives/minimum-sample-size-courier-allocation/tests/2026-10-20-test-aggregate-simulation-v2.py` (9 unit tests) and `tests/2026-10-20-test-simulation-matches-example-v2.py` (reproduces the 9-order example: 36 order x rule rows, 0 mismatches) | `python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-simulation-v2.py` |
| S2 | How closely the replay of today's rule reproduces reality | M8, caveats | `archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-replay-diagnostics-v2.py` | `sim-v2-orders.csv` | `outputs/replay-diagnostics-v2.csv` | none needed | `python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-replay-diagnostics-v2.py` |
| S3 | Like-for-like check of M2 on the same orders | M1, M2 | `archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-like-for-like-v2.py` | `sim-v2-orders.csv` | `outputs/like-for-like-v2.csv` | none needed | `python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-like-for-like-v2.py` |
| S4 | Sums and spreads the note quotes: M7 grouped by geography, and the spread across x | M1 to M4, M7 | `archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-note-derived-figures-v1.py` | `sim-v2-summary.csv` | `outputs/note-derived-figures-v1.csv` | none needed | `python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-note-derived-figures-v1.py` |

The 9-order example scripts (steps 1 to 8, in `scripts/`) are the worked example Tejas vetted; S1 reproduces them exactly.

## Definitions and filters
- **Window:** orders placed 29 Jul to 24 Sep 2026 (the headline, "complete dates"); the same figures for 29 Jul to 30 Sep ("all dates") are in `sim-v2-summary.csv`. October is never used.
- **Orders in scope:** 1,492,971 shipment rows for the six couriers; 1,443,611 have an order-placed row; 993,021 were placed 29 Jul to 30 Sep; 992,386 were also invoiced in that window; 991,569 have a promised warehouse time. Headline orders (placed to 24 Sep): 941,213; of these 940,480 have at least one candidate courier, which is the denominator of M1, M3 and M4 (S1, `sim-v2-summary.csv`).
- **Rules:** `context/2026-10-20-process-flow-v5.md` and `context/2026-10-20-simulation-scope-v7.md`: 85% percentile, ladder in time-then-geography order, widest-data step, schedule adjustment from the promised warehouse time (order placed) and the invoice time (invoice), tie-break 195 > 185 > 225 > 246 > 286 > 247, no drop or pickup buffer, warehouse 19 as warehouse 40, today's ops config and adherence master.
- **Candidates:** couriers among the six that serve the pincode, have ops config for the warehouse, and have an adherence master row.
- **Orders delivered after 30 Sep are not in the shipment files**, so their outcome is unknown. Placed dates up to 24 Sep keep the order-placed rows found in the shipment files above 97% (99.0% on average for 29 Jul to 31 Aug; `sim-v2-matchrate.csv`).

## Caveats and confidence
- **The replay of today's rule is close but not exact.** The replayed promise equals the real promise on 61.4% of orders, and the replayed invoice winner is the courier that shipped on 63.9% (M8). Real adherence is 81.0%, against 74.5% for M1 under today's replay (S2, S1). Real orders carry drop and pickup buffers and promise buffers that this simulation sets to zero. Trust the change between rules more than the level of any single figure.
- **M2 compares different orders under each rule.** M2 covers the 41% to 44% of orders whose courier would not change under x, against 64% under today's rule. The like-for-like check (table 6) shows how much of the M2 gain comes with a longer promise.
- **Late September is incomplete** (see Definitions), which is why the headline stops at 24 Sep. Tejas said orders delivered in October still count, but the October files are not in the project, so those orders cannot be scored.
- **Lanes without cutoffs get no schedule adjustment**: warehouse 30 for 195, 225 and 286 (not confirmed by Tejas) and warehouse 27.
- **Open data questions from the brief remain**: the two zero adherence pairs, the 15-day promise spike, the default TAT where a config row is missing (3 days used), and the cause of the missing order-placed rows (excluded).
- **Percentile method:** linear interpolation (the document does not name one).
- **Sample size:** every headline figure is over hundreds of thousands of orders. Of the 248 cut cells in `sim-v2-summary.csv` (courier, warehouse and data-used cuts), the smallest holds 485 orders (M1, state over 28 days, x = 15); five cells hold fewer than 1,000, all in the data-used cut, and none holds fewer than 100. Confidence is high in the direction of the changes and moderate in their size, because of the replay gap.
- **"Caused" is not claimed.** The simulation shows what the rule would have chosen on past orders; it does not measure how customers or couriers respond.

## Next check
- Get the orders placed 25 to 30 Sep that were delivered in October, then rerun to extend the window to 30 Sep.
- Explain the replay gap (drop and pickup buffers, promise buffers) before using the levels, for example by adding drop buffers if Tejas can supply them.
- Test whether the courier shifts at x = 20 (195 down 8.9 points, 286 and 247 up 4.7 and 3.8) are acceptable operationally.
