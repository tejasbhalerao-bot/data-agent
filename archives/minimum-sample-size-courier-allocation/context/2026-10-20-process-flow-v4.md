# Process flow for the simulation (v4)

Tejas's whiteboard "Min. Sample Size" (tldraw: https://www.tldraw.com/f/7AoBdIazP04lLoavSenq-), read on 2026-10-20. The board has no connector arrows; the order of steps comes from its layout and its "If yes" and "If no" boxes. This v4 replaces v1 to v3: v2 put the widest-data step back in; v3 defined the two adherence calculations and the promise date; v4 settles the schedule adjustment, the tie-break, the buffers and the lane key. It sits on top of `2026-10-20-simulation-scope-v6.md`. Where the two differ, this file wins.

## 1. Order flow: two allocations per order
- **At order placed.** Resolve the order placed date. Fetch the adherence and the Final TAT as calculated on that date. Keep only serviceable couriers. Allocate with the TAT/Adherence logic. Save that courier's TAT as the order's promise.
- **At invoice.** Same steps on the invoice date. The courier chosen is the shipping courier. Save its TAT as the shipping courier's promise.
- **Dates (confirmed by Tejas):** order placed date = the digitised timestamp (`DIGITISED_TS`); invoice date = the invoice-create timestamp (`INVOICE_CREATE_TS`), both from the order-placed files.
- **Orders without an order-placed row are excluded** (confirmed by Tejas). The order-placed files match about 66% of the shipment orders.

## 2. Adherence: two calculations, both measured against the promise at the order placed date
- **The promise used is always the one at the order placed date** (confirmed by Tejas 2026-10-20): it is what the customer experiences, and the system is modelled to maximise that. It is not the invoice-date promise.
- **A, courier unchanged** (board section 2). The order keeps the courier that actually shipped it. Its promise is that courier's projected lane TAT under the rule (today's rule, or a value of x), as of the order placed date. Classify delay days = actual days - promise as Early, On-Time or Late. Adherence = early + on time. This tests how accurate each courier's speed projection is with the sample rule in mind, and can be calculated for every order. Under today's rule it equals the real promise (`PROMISE_TAT`).
- **B, courier changed** (board section 3). Simulates how the system's world changes. If the courier the new rule would pick as shipping courier is the courier that actually shipped, classify as in A. If it is a different courier, the order is excluded and no adherence is reported for it. The share of excluded orders is reported with every result.

## 3. Allocation score, run at order placed and again at invoice
- Score = Buffer Adjusted Lane TAT / adherence (as a fraction) + schedule time adjustment + pickup buffer + drop buffer; the lowest score wins.
- **Schedule time adjustment (Tejas, 2026-10-20):**
  - at order placed: +1 if the promised warehouse processing time is after the courier's cutoff for the warehouse (`courier-partner-schedules.csv`); otherwise 0. I read "promised warehouse processing" as `DIGITISED_WH_PROMISE` and compare its time of day with the cutoff.
  - at invoice: +1 if the invoice-create time is after the cutoff; otherwise 0.
- **Tie-break priority (Tejas):** 195 > 185 > 225 > 246 > 286 > 247.
- **Pickup buffer = 0**, the same as the drop buffer.
- The promise is the winner's lane TAT.
- Lane TAT = 85th percentile of actual days, rounded up; adherence = running share of delay-day buckets until it first reaches 85% (scope v7).
- **Lane key (Tejas):** warehouse x pincode x courier identifies the orders with a delivery attempt in the 7-day window. The same applies to warehouse x micro-cluster x courier, warehouse x macro-cluster x courier and warehouse x state x courier, and to every window.
- **Ops config and `TAT Adherence Master` are today's snapshot, used for July to September decisions** (Tejas confirmed this is fine).
- **Adherence B uses the promise the customer saw in the simulated world**, which is the lane TAT of the courier chosen at the order placed stage, even when the shipping courier chosen at invoice is a different one. (My reading of the board; pending Tejas's confirmation.) Adherence A uses the shipping courier's own projected lane TAT at the order placed date.

## 4. Which data to use for each lane (warehouse x courier)
Stop at the first step where the order count is at least x:
1. Pincode: 7, 14, 21, 28 days.
2. Micro-cluster: 7, 14, 21, 28 days.
3. Macro-cluster: 7, 14, 21, 28 days.
4. State: 7, 14, 21, 28 days.
5. If no step reaches x, but the widest pool (state, 28 days) has more than 0 orders, **use that pool** even though it is below x (confirmed by Tejas 2026-10-20; it was missing from the whiteboard).
6. Only if that pool has 0 orders, use the ops config and `TAT Adherence Master`.
Windows count orders with a delivery attempt in the window, ending the day before the decision date.

## 5. Calculation of TAT and adherence for a lane
Fetch each order at the chosen step, then calculate TAT and adherence as laid out in `performance-based-speed-calculation-and-allocation.md`.

## Note
The whiteboard omitted the widest-data step; Tejas confirmed it belongs in the flow, as in his earlier written flow.
