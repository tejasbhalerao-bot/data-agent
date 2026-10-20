# Process flow for the simulation (v2)

Tejas's whiteboard "Min. Sample Size" (tldraw: https://www.tldraw.com/f/7AoBdIazP04lLoavSenq-), read on 2026-10-20. The board has no connector arrows; the order of steps comes from its layout and its "If yes" and "If no" boxes. This v2 replaces v1: the widest-data step is back in. It sits on top of `2026-10-20-simulation-scope-v6.md`. Where the two differ, this file wins.

## 1. Order flow: two allocations per order
- **At order placed.** Resolve the order placed date. Fetch the adherence and the Final TAT as calculated on that date. Keep only serviceable couriers. Allocate with the TAT/Adherence logic. Save that courier's TAT as the order's promise.
- **At invoice.** Same steps on the invoice date. The courier chosen is the shipping courier. Save its TAT as the shipping courier's promise.
- **Dates (confirmed by Tejas):** order placed date = the digitised timestamp (`DIGITISED_TS`); invoice date = the invoice-create timestamp (`INVOICE_CREATE_TS`), both from the order-placed files.
- **Orders without an order-placed row are excluded** (confirmed by Tejas). The order-placed files match about 66% of the shipment orders.

## 2. Baseline adherence (courier allocation unchanged)
Promise given in days at order placed. Actual days from pickup to first delivery attempt. Classify early, on time or late. Adherence = early + on time.

## 3. Simulated adherence (courier allocation changed)
- Check whether the simulated shipping courier is the same as the courier that actually shipped the order.
- **Same:** classify the order against the simulated promise, using the real delivery time. Adherence = early + on time.
- **Different:** halt for that order. No adherence is reported, because the real and simulated shipping couriers differ.
- So the simulated adherence covers only orders whose shipping courier did not change. The share of orders dropped this way is reported next to every result.

## 4. Which data to use for each lane (warehouse x courier)
Stop at the first step where the order count is at least x:
1. Pincode: 7, 14, 21, 28 days.
2. Micro-cluster: 7, 14, 21, 28 days.
3. Macro-cluster: 7, 14, 21, 28 days.
4. State: 7, 14, 21, 28 days.
5. If no step reaches x, but the widest pool (state, 28 days) has more than 0 orders, **use that pool** even though it is below x (confirmed by Tejas 2026-10-20; it was missing from the whiteboard).
6. Only if that pool has 0 orders, use the ops config and `TAT Adherence Master`.
Windows count orders with a delivery attempt in the window, ending the day before the decision date.

## 5. Calculation
Fetch each order at the chosen step, then calculate TAT and adherence as laid out in `performance-based-speed-calculation-and-allocation.md`.

## Note
The whiteboard omitted the widest-data step; Tejas confirmed it belongs in the flow, as in his earlier written flow.
