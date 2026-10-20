---
project: minimum-sample-size-courier-allocation
job: model
status: brief
awaiting: []
assumptions: []
signed_off: false
as_of: 2026-10-20
---

# What happens to adherence, and to the customer's promise, if a lane needs at least x orders before its TAT and adherence count?

**My reading of the flow:** A customer places an order and Strategy 1 picks a courier from each courier's TAT and adherence, built from recent deliveries on its warehouse x pincode lane. That sets the promise. At invoice it picks the shipping courier again. The first delivery attempt then shows whether the promise held. The data comes from the shipment files (pickup, attempt, promise), the order-placed files (placed and invoice times), the ops config, `TAT Adherence Master`, the courier cutoffs, and the serviceability and GOI files.

**Assumptions and rules applied:** the rules are in the project context: `context/2026-10-20-process-flow-v5.md` and `context/2026-10-20-simulation-scope-v7.md`.

## Answer
Pending. The brief below is waiting for Tejas's approval.

## Brief (awaiting approval)

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

### Grain and output columns (Tejas to decide)
- Suggestion for the main file: one row per order x rule, with order ID, warehouse, pincode, shipping courier, placed and invoice times, rule, placed-stage winner and promise, invoice-stage winner, the shipping courier's projected TAT, and the M1 and M2 results.
- A second summary file would have one row per rule x cut.

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

### To approve
Reply "ok" to start, or say what to change.

## Queries to run
Not applicable: no new query is needed.

## Scripts and outputs
Not yet written.

## Definitions and filters
Pending approval of the brief.

## Caveats and confidence
Pending.

## Next check
Pending.
