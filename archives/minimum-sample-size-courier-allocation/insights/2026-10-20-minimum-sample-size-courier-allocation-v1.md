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

**Assumptions and rules applied:** the rules are in the project context: `context/2026-10-20-process-flow-v4.md` and `context/2026-10-20-simulation-scope-v7.md`.

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
- M1: Adherence A, courier unchanged. Share of orders early or on time against the shipping courier's projected TAT at the order placed date. By rule. Cuts: courier, warehouse, rung reached.
- M2: Adherence B, courier changed. Share early or on time among orders where the rule's invoice winner is the shipping courier, against the promise at the order placed date. By rule. Cuts: courier, warehouse.
- M3: Orders excluded from B. Share of orders whose courier would change. By rule.
- M4: Customer promise. Average simulated promise at order placed against today's rule, plus the share of orders with a longer, shorter or equal promise. By rule.
- M5: Courier allocation mix. Share of orders by invoice-stage winner against the courier that actually shipped. By rule.
- M6: Rung reached. Share of courier evaluations resolved at each rung, the widest-data step, and the ops config. By x. This is the volume view for choosing x.
- M7: Replay match. Share of orders where today's rule picks the courier that actually shipped. This checks the replay.

### Grain and output columns (Tejas to decide)
- Suggestion for the main file: one row per order x rule, with order ID, warehouse, pincode, shipping courier, placed and invoice times, rule, placed-stage winner and promise, invoice-stage winner, the shipping courier's projected TAT, and the A and B results.
- A second summary file would have one row per rule x cut.

### How it will be calculated
Each step follows the process flow in `context/2026-10-20-process-flow-v4.md`.

| Step | What | Serves | Data from |
|---|---|---|---|
| 1 | Pick orders in scope, with placed, invoice and promised-warehouse times | all | existing CSVs, in the script |
| 2 | For each order, stage and courier: walk the ladder, then calculate lane TAT and adherence at 85% | M1 to M6 | existing CSVs, in the script |
| 3 | Score each courier with the schedule adjustment, apply the tie-break, and pick winners at placed and invoice | M2 to M5 | script |
| 4 | Classify each order for A and B against the order placed promise | M1 to M3 | script |
| 5 | Roll up by rule and cut, and check the replay | all | script |

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
