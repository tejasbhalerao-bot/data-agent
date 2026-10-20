# Simulation scope (v4)

Stated by Tejas on 2026-10-20. Applies to this whole project. Replaces v1 and v2. v3 added the drop buffer assumption and the definition of a time window. v4 adds the courier list. It sits on top of `2026-10-20-allocation-strategies-today-v1.md`.

## Objective
Find the change in adherence, and the promise given up to get it, from running Performance Based Speed Calculation & Allocation (Strategy 1) with a **minimum sample size of orders (x)** before a lane's adherence and TAT count as valid.

## Ground rule
**The simulation is done as if Strategy 3 (Courier Allocation Revamp) never existed.** None of its pooling cascade, shadow variants, tables or results are used. The pooling ladder below is Tejas's own design for this project.

## Baseline
Strategy 1 as it runs today. A lane counts as having history with at least 1 order in the last 7 days.

## Proposed flow: adherence calculation
Warehouse and delivery partner stay fixed at every rung. Only the pincodes pooled and the time window widen.

1. Fetch all orders for the warehouse x pincode x delivery partner in the last 7 days.
2. If fewer than x, try the last 14, 21, then 28 days.
3. If still fewer than x, widen to the **micro-cluster**: pincodes in the same division of the same district (district and division come from the GOI database). Try 7 days first.
4. If still fewer than x, try the micro-cluster over 14, 21, then 28 days.
5. If micro-clusters are exhausted, widen to the **macro-cluster**: pincodes sharing the same first 3 digits. Try 7, 14, 21, then 28 days.
6. **State rung (agreed 2026-10-20):** if still fewer than x, widen to warehouse x state x delivery partner (same 7, 14, 21, 28 day windows), with state taken from the GOI file. The count of orders that reach this rung is measured first. If it is small, this rung is moot.
7. If still fewer than x but more than 0, proceed with the widest data found.
8. If 0, use the ops-configured TAT from the delivery TAT tables, and adherence from `TAT Adherence Master`.
9. Calculate lane TAT and adherence with the method in `performance-based-speed-calculation-and-allocation.md`.
10. The allocation formula (`Buffer Adjusted Lane TAT / Adherence + schedule-time adjustment + pickup buffer + drop buffer`, lowest wins) does not change.

## Rules added 2026-10-20 (v3)
- **No drop buffers.** The simulation assumes drop buffer = 0 on every order. Buffer Adjusted Actual Speed therefore equals Actual Speed (`DATE(delivery_attempt_time) - DATE(pickup_time)`), and Buffer Adjusted Lane TAT equals Lane TAT. The drop buffer column question is closed.
- **What "orders over the last N days" means.** Only orders with a **delivery attempt** in the window are counted, for the warehouse x pincode x delivery partner (or the wider group on later rungs). Example: on 20 Oct, "last 7 days" is delivery attempts from 13 Oct to 19 Oct. The window ends the day before the decision date. The 14, 21 and 28 day windows end on the same day.
- **Decision date.** An order allocated on day D sees only deliveries attempted before D.
- **Earliest usable date.** The order data starts at attempts on 1 July, so the first date with a full 28-day history is 29 July 2026.
- Earlier truncated pull (1,048,575 rows, a spreadsheet-style export cap) was rejected and its local copy deleted. Tejas is re-running it in chunks.

## Rule added 2026-10-20 (v4)
- **Couriers in the simulation: 185, 195, 225, 246, 247, 286 only.** Every other courier is kept out: its orders count in no lane, cluster or window, and it cannot be a candidate winner.
- **Example lane uses courier 195.** It has historically had the lowest drop buffers, so ignoring drop buffers distorts it least.

## Facts confirmed by Tejas
- `TAT Adherence Master` stores data at **warehouse x courier** level. `schema.md` lists a Pincode column, so it is out of date there.
- Tejas will supply the GOI file (pincode, district, division, state).
- Strategy 1's Supposed TAT default is 3 days (later document wins over `schema.md`'s 5 days). Not yet confirmed by Tejas.

## Not decided yet (to be proposed in the brief)
- The values of x to test.
- Window, cohort (including whether orders routed by Strategy 2 are excluded), and exact definitions of adherence and promise.

## Still needed
- The order data re-pulled in chunks (columns: order id, warehouse id, pincode, delivery partner, delivery attempt time, pickup time).
- For the full run: the ops-configured TAT tables and `TAT Adherence Master`, for lanes that reach the last rung and for the baseline.
