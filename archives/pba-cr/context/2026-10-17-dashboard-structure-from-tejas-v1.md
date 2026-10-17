---
title: PBA CR dashboard structure (Tejas's sample)
source: Tejas, in chat, 2026-10-16
status: work in progress; Tejas will continue it later
---

# PBA CR dashboard structure

Tejas's sample, as given. It replaces both earlier wireframe drafts (artifact https://claude.ai/artifact/XX9QtrxQWPMfiofjq2TjX7), which he rejected. Base data: `fahad-raw-dump-3`.

## Section 1: Funnel

Metrics covered below.

**Order Funnel**
1. Total Orders
2. Total Non-SDD Orders
3. % of non-SDD orders allocated through PBA
4. % of non-SDD orders failed to allocate through PBA even though decision was in-rollout

**PBA Orders Funnel**
1. % of PBA orders placed
2. % of PBA orders picked up
3. % of PBA orders with delivery attempt

**Internal Orders Funnel**
1. % of Internal orders placed
2. % of Internal orders picked up
3. % of Internal orders with delivery attempt

## Section 2: Promise

Metrics covered below.

**Soft Promise Comparison** (Averages, p25, p50, p75, p90)
1. PBA Allocated Orders: WH to Delivery Promise
2. Internal Allocated Orders: WH to Delivery Promise
3. PBA Allocated Orders: Dispatch to Delivery Promise
4. Internal Allocated Orders: Dispatch to Delivery Promise
5. PBA Allocated Orders: Internal Selected Partner WH to Delivery Promise
6. PBA Allocated Orders: Internal Selected Partner Dispatch to Delivery Promise
7. Internal Allocated Orders: PBA Selected Partner WH to Delivery Promise
8. Internal Allocated Orders: PBA Selected Partner Dispatch to Delivery Promise
9. Lane Adjusted Promise Comparison: WH to Delivery Promise Comparison - PBA vs Internal
10. Lane Adjusted Promise Comparison: Dispatch to Delivery Promise Comparison - PBA vs Internal

**Cumulative % of orders (Tejas, 2026-10-18):** for every metric above, also show the cumulative % of orders by promise days: 0 days, ≤1, ≤2, ≤3, 4+ (4+ = 100%). Example: 0 days 10%, 1 day 25%, 2 days 60%, 3 days 80%, 4+ days 100%.

**What Lane Adjusted Promise Comparison means (Tejas, 2026-10-18):** select only those lanes (warehouse × pincode) from internal-allocated orders that are present in PBA-allocated orders. For example, if PBA orders have WH 20 × Pincode 400079 allocated orders, that lane falls under Lane Adjusted Comparison. If WH 20 × Pincode 400079 has no orders allocated through PBA, it is kept out of Lane Adjusted Promise Comparison.

## Changes since the first version (2026-10-18)
- Section 1: "Total Orders" dropped; the Order Funnel starts at Total Non-SDD Orders.
- Section 2: metrics 7–10 and the lane-adjusted definition added.

## Further sections

Not given yet.
