# Courier allocation today: three strategies

Stated by Tejas on 2026-10-20. Sources are the PM agent's system documents in `~/pm-agent/context/allocation/` (read only). Where this file and those documents disagree, this file wins.

## Strategies running today

| # | Strategy | Source document | Share of orders | Status |
|---|---|---|---|---|
| 1 | Performance Based Speed Calculation & Allocation | `performance-based-speed-calculation-and-allocation.md` | ~95% | Live |
| 2 | PBA (Clickpost) | `pba-clickpost.md` | ~5% | Live |
| 3 | Courier Allocation Revamp | `courier-allocation-revamp.md` | 0% | Shadow mode only; no orders exposed |

- The earlier "legacy" TAT/Adherence logic is **no longer active**. "Legacy" and "Legacy_Hard" in the documents are shadow-mode formula variants, not what serves orders.
- The "Final TAT = Ideal TAT + delay offset" definition in the revamp document describes the retired logic. Ignore it.

## How each strategy works

**Strategy 1 (live, ~95%)**
- Scores each serviceable courier at warehouse x pincode x courier level on the last 7 days of deliveries.
- Score: `Buffer Adjusted Lane TAT / Adherence + schedule-time adjustment + pickup buffer + drop buffer`. The lowest score wins.
- Lane TAT = ROUNDUP(percentile of buffer-adjusted actual speed). The percentile is configurable by warehouse, pincode and courier, and the default is 0.8.
- Adherence is the running sum of the nine delay-day buckets (Early 4+ days up to Late 4+ days) until the sum reaches the percentile.
- A lane counts as having history if it has **at least 1 order** in the last 7 days. With none, the system falls back to the ops-configured TAT (default 3 days) and `tat_adherence_master`.
- The job reruns nightly at 3:00 AM for FCs and 3:30 AM for MFCs.

**Strategy 2 (live, ~5%)**
- Clickpost ranks the serviceable couriers, using its own 80th-percentile delivery TAT over a rolling 30-day window and price as the tie-breaker.
- Scoring happens inside Clickpost, so our n-threshold does not apply to it.

**Strategy 3 (shadow)**
- Replaces the 1-order history threshold with a minimum order count n. Below n at a level, it pools upward: pincode, city, state, warehouse, courier, then a default of 80%.
- Six parallel shadow variants: Computation 1 or Computation 2, each at n = 10, 15 and 20.
- The planned choice of n uses shadow data. The rule is the lowest "% switched orders with worse promise". If two variants are within 1pp, prefer the lower n. The winner must be under 5%.

## The problem this project tackles
- Under Strategy 1, one delivery on a lane is enough to set that lane's TAT and adherence. One on-time delivery gives 100% adherence.
- On 1 April 2026, 94.7% of 25,716 data lanes had fewer than 20 deliveries, and the median lane had 2.
- On that day, 56.6% of orders went to a courier whose lane had fewer than 20 recent deliveries.
- Pooling under Strategy 3 is the proposed fix. This project works out the minimum sample size (n) it should use.
- Tejas will describe a further L2 problem later.

## Open items
- Whether every pincode exists in `m_city_master` and `m_state_master` is unverified (the revamp document says so). Check before any pooling query.
- Tejas has not yet said whether Strategy 2 is in scope.
