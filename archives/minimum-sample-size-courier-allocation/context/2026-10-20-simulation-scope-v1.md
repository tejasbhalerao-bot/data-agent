# Simulation scope

Stated by Tejas on 2026-10-20. Applies to this whole project. It sits on top of `2026-10-20-allocation-strategies-today-v1.md`.

## Objective
Find the change in adherence, and the promise given up to get it, from running Performance Based Speed Calculation & Allocation (Strategy 1) with a **minimum sample size of orders** before a lane's adherence and TAT count as valid.

## Ground rule
**The simulation is done as if Strategy 3 (Courier Allocation Revamp) never existed.**
- No pooling cascade (pincode, city, state, warehouse, courier). No shadow-mode variants, tables or results.
- The only lever is the minimum number of orders a lane (warehouse x pincode x courier) needs in the 7-day window to count as having history.
- A lane below the minimum is treated like a lane with no history in Strategy 1:
  - TAT is the ops-configured value (`Pincode Delivery TAT` / `Pincode Delivery TAT MFC`), plus any drop buffer.
  - Adherence is the value in `TAT Adherence Master`.

## Baseline
Strategy 1 as it runs today. A lane counts as having history with at least 1 order in the last 7 days.

## Not decided yet (to be proposed in the brief)
- Which minimum values to test.
- Window, cohort (including whether orders routed by Strategy 2 are excluded), and the exact definitions of adherence and promise.

## Data conflict to resolve
- `schema.md` says Supposed TAT defaults to 5 days. The Strategy 1 document (updated 2026-08-22) says 3 days. The later document wins unless Tejas says otherwise.
