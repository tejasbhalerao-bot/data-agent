---
project: minimum-sample-size-courier-allocation
job: model
status: saved
awaiting: []
assumptions: []
signed_off: false
as_of: 2026-10-20
---

# What a minimum sample size of 10, 15 or 20 orders does to adherence and promise

How the simulation works, the rules, the data and the checks are in the companion document: `2026-10-20-minimum-sample-size-courier-allocation-brief-v1.md`. The metrics are defined in the glossary at the end of this document.

## Answer

Where the courier does not change, requiring 20 orders on a lane before its TAT and adherence count raises adherence from 83.1% to 85.5% (+2.4 points) and lengthens the average promise from 2.18 to 2.26 days (+0.08 days). x = 10 and x = 15 give +2.0 and +2.2 points for +0.07 days.

Only 41% to 44% of orders can be compared this way. For the other 56% to 59% the new rule would allocate a different courier from the one that really shipped, and no adherence is reported.

Orders placed 29 Jul to 24 Sep 2026: 940,480 orders. Every table below is on these orders.

## 1. Adherence and promise on matched orders (M1, M2, M3)

A matched order is one where the courier the rule allocates at invoice is the courier that really shipped it. "Today" is reality: the real promise against the real delivery, on the same orders.

| | x = 10 | x = 15 | x = 20 |
|---|---|---|---|
| Matched orders | 414,585 | 395,433 | 383,706 |
| M3: share of orders matched | 44.1% | 42.1% | 40.8% |
| **M1: adherence, today** | 83.11% | 83.13% | 83.12% |
| **M1: adherence, under x** | 85.07% | 85.29% | 85.51% |
| M1: change | +1.96 pts | +2.17 pts | +2.40 pts |
| **M2: average promise, today** | 2.186 days | 2.180 days | 2.178 days |
| **M2: average promise, under x** | 2.256 days | 2.253 days | 2.262 days |
| M2: change | +0.070 days | +0.073 days | +0.084 days |
| M2: orders with a longer promise than today | 18.9% | 19.9% | 21.0% |
| M2: orders with a shorter promise than today | 11.1% | 11.6% | 11.7% |
| M2: orders with the same promise as today | 70.0% | 68.5% | 67.3% |

Source: `outputs/results-matched-orders-v1.csv`, "complete dates", group "all" (script S10).

**The same comparison on one common set of orders.** Each x has its own matched orders, and the sets differ slightly. On the 313,116 orders (33.3%) that match under all three values of x:

| | Today | x = 10 | x = 15 | x = 20 |
|---|---|---|---|---|
| M1: adherence | 83.31% | 85.51% | 85.59% | 85.80% |
| M2: average promise (days) | 2.102 | 2.178 | 2.180 | 2.192 |

Source: `results-matched-orders-v1.csv`, group "common set".

## 2. By courier that shipped the order, x = 20 (M1, M2, M3)

| Courier | Orders | Matched | M3: matched | M1: today | M1: x = 20 | Change | M2: today | M2: x = 20 | Change |
|---|---|---|---|---|---|---|---|---|---|
| 195 | 310,405 | 120,304 | 38.8% | 82.96% | 85.24% | +2.29 | 2.546 | 2.627 | +0.081 |
| 185 | 180,892 | 84,768 | 46.9% | 86.03% | 87.06% | +1.03 | 1.820 | 1.857 | +0.038 |
| 225 | 129,767 | 41,530 | 32.0% | 79.16% | 82.59% | +3.42 | 2.735 | 2.855 | +0.120 |
| 246 | 151,587 | 60,532 | 39.9% | 82.98% | 85.80% | +2.82 | 1.809 | 1.895 | +0.086 |
| 247 | 107,144 | 51,384 | 48.0% | 81.86% | 85.86% | +3.99 | 1.998 | 2.143 | +0.145 |
| 286 | 60,685 | 25,188 | 41.5% | 83.43% | 85.04% | +1.61 | 1.960 | 2.027 | +0.067 |

Adherence improves for every courier. The gain is largest for 247 and 225, and so is the lengthening of the promise. By-warehouse and x = 10, 15 figures are in `results-matched-orders-v1.csv`.

## 3. Courier allocation mix (M4)

**At invoice, against the courier that really shipped (% of orders).** All 940,480 orders.

| Courier | Today (real) | x = 10 | x = 15 | x = 20 | Change x = 10 | Change x = 15 | Change x = 20 |
|---|---|---|---|---|---|---|---|
| 195 | 33.00 | 21.74 | 20.91 | 20.50 | -11.26 | -12.09 | -12.51 |
| 185 | 19.23 | 20.08 | 19.70 | 19.81 | +0.84 | +0.47 | +0.58 |
| 225 | 13.80 | 14.82 | 14.77 | 14.72 | +1.02 | +0.97 | +0.93 |
| 246 | 16.12 | 14.66 | 14.84 | 14.91 | -1.46 | -1.28 | -1.21 |
| 286 | 6.45 | 13.05 | 13.42 | 13.08 | +6.60 | +6.97 | +6.63 |
| 247 | 11.39 | 15.64 | 16.35 | 16.98 | +4.25 | +4.96 | +5.58 |

Source: `outputs/today-real-baseline-v2.csv` (script S5).

**At order placed (% of 941,213 orders).** Today's real courier at order placed is not in our data, so "today" here is the replay of today's rule.

| Courier | Today (replay) | x = 10 | x = 15 | x = 20 | Change x = 10 | Change x = 15 | Change x = 20 |
|---|---|---|---|---|---|---|---|
| 195 | 29.06 | 21.47 | 20.60 | 20.18 | -7.59 | -8.46 | -8.88 |
| 185 | 18.07 | 19.87 | 19.47 | 19.58 | +1.80 | +1.41 | +1.51 |
| 225 | 15.03 | 14.65 | 14.65 | 14.62 | -0.38 | -0.38 | -0.41 |
| 246 | 15.96 | 15.08 | 15.32 | 15.34 | -0.88 | -0.64 | -0.62 |
| 286 | 8.14 | 12.81 | 13.15 | 12.79 | +4.67 | +5.00 | +4.65 |
| 247 | 13.65 | 16.04 | 16.72 | 17.41 | +2.38 | +3.07 | +3.76 |

Source: `outputs/sim-v2-summary.csv` (script S1).

## 4. Where the TAT and adherence data comes from (M5)

Share of courier evaluations at order placed resolved at each source, per value of x. Under today's rule, 29.4% resolve on the pincode's own orders in the last 7 days and 70.6% fall back to the ops config (replay).

| Data used | x = 10 | x = 15 | x = 20 |
|---|---|---|---|
| Pincode, 7 days | 12.15% | 8.85% | 6.80% |
| Pincode, 14 to 28 days | 14.47% | 13.73% | 12.80% |
| Micro-cluster, any window | 48.52% | 48.45% | 47.85% |
| Macro-cluster, any window | 9.39% | 10.75% | 11.99% |
| State, any window | 9.36% | 11.56% | 13.43% |
| Widest pool, below x | 1.16% | 1.69% | 2.16% |
| Ops config | 4.95% | 4.96% | 4.97% |

Source: `outputs/note-derived-figures-v1.csv` (script S4, from S1).

## What the results say

- **A larger sample raises adherence where the courier stays the same.** Every x gains about 2 points. The three values are close: x = 20 gains 0.4 points more than x = 10, and its promise is 0.014 days longer.
- **The gain has a price in promise.** About 19% to 21% of matched orders get a longer promise than today and about 11% to 12% a shorter one.
- **Courier mix moves a lot.** At x = 20, 195 would carry 12.5 points fewer orders at invoice than today, while 286 gains 6.6 and 247 gains 5.6.
- **We cannot judge the orders whose courier changes** (56% to 59%). The simulation does not know how the new courier would have delivered.
- **How reliable are the levels?** The replay of today's rule does not match reality order for order (see the brief), so the comparison above deliberately uses reality as "today" on the same orders.

## Appendix: glossary

**Terms**
- **x:** the minimum number of orders a lane must have in its window before its TAT and adherence count. The values tested are 10, 15 and 20.
- **Today:** what really happened. The courier that shipped the order, the real promise (`PROMISE_TAT`) and the real delivery.
- **Promise:** the logistics promise in days, as the customer sees it at order placed. In the simulation it is the lane TAT of the courier allocated at order placed.
- **On time (adherent):** an order whose actual days from pickup to first delivery attempt are less than or equal to its promise.
- **Order placed stage / invoice stage:** the two moments a courier is allocated. The customer's promise comes from order placed; the shipping courier is chosen at invoice.
- **Matched order:** an order where the courier the simulation allocates at invoice is the courier that really shipped it. Adherence is reported only for these.
- **Lane:** warehouse × pincode × courier.
- **Data used (rung):** the set of past orders a lane's TAT and adherence come from. The ladder tries the pincode over 7, 14, 21 and 28 days, then the micro-cluster (same state, district and division), then the macro-cluster (same first three digits of the pincode), then the state, and stops at the first step with at least x orders. If none reaches x it uses the widest pool that has orders, and only then the ops config.
- **Lane TAT:** the 85th percentile of actual days on the lane's orders, rounded up to whole days.

**Metrics**
- **M1, adherence:** the share of matched orders that are on time. Under x it uses the simulated promise; for today it uses the real promise, on the same orders.
- **M2, promise:** the average promise in days on matched orders, under x and for today on the same orders, with the share of orders whose promise is longer, shorter or the same as today's.
- **M3, share of orders matched:** matched orders as a share of all orders in scope. The remainder are orders where the simulation would allocate a different courier, which are not compared.
- **M4, courier allocation mix:** the share of orders going to each courier, at order placed and at invoice, shown as the change in percentage points between today and each x.
- **M5, data used:** the share of courier evaluations that resolve at each source of data (rung above), per value of x.
