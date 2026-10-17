---
title: PBA CR dashboard structure (Tejas's sample)
source: Tejas, in chat, 2026-10-16 to 2026-10-18
status: work in progress; Tejas will continue it later
---

# PBA CR dashboard structure

Tejas's sample, with his later changes. The wireframe is at https://claude.ai/artifact/XX9QtrxQWPMfiofjq2TjX7. Base data: `fahad-raw-dump-3`. Metrics are numbered in the order they appear on the wireframe, starting at 1 in each section.

## Section 1: Funnel

Metrics covered below.

**Order Funnel**
1. Total Non-SDD Orders
2. % of non-SDD orders allocated through PBA
3. % of non-SDD orders failed to allocate through PBA even though decision was in-rollout

**PBA Orders Funnel vs Internal Orders Funnel** (each shown for PBA and for Internal)

4. % of orders placed
5. % of orders picked up
6. % of orders with delivery attempt

## Section 2: Promise

Metrics covered below.

Two sub-sections: Sub-section 1: Soft Promise (metrics 1–10) and Sub-section 2: Hard Promise (metrics 11–13). Every metric shows Averages, p25, p50, p75, p90 and the cumulative % of orders.

### Sub-section 1: Soft Promise

WH to Delivery Promise
1. PBA Allocated Orders: WH to Delivery Promise
2. PBA Allocated Orders: Internal Selected Partner WH to Delivery Promise
3. Internal Allocated Orders: WH to Delivery Promise
4. Internal Allocated Orders: PBA Selected Partner WH to Delivery Promise

Dispatch to Delivery Promise

5. PBA Allocated Orders: Dispatch to Delivery Promise
6. PBA Allocated Orders: Internal Selected Partner Dispatch to Delivery Promise
7. Internal Allocated Orders: Dispatch to Delivery Promise
8. Internal Allocated Orders: PBA Selected Partner Dispatch to Delivery Promise

**Lane Adjusted Promise Comparison**

9. WH to Delivery Promise Comparison - PBA vs Internal
10. Dispatch to Delivery Promise Comparison - PBA vs Internal

### Sub-section 2: Hard Promise

The same measures as soft metrics 5, 7 and 10, taken at hard allocation.

Dispatch to Delivery Promise

11. PBA Allocated Orders: Dispatch to Delivery Promise (as 5)
12. Internal Allocated Orders: Dispatch to Delivery Promise (as 7)

**Lane Adjusted Promise Comparison**

13. Dispatch to Delivery Promise Comparison - PBA vs Internal (as 10)

The hard lane-adjusted WH to Delivery comparison (as 9) was removed on 2026-10-18.

**Cumulative % of orders (Tejas, 2026-10-18):** for every metric above, also show the cumulative % of orders by promise days: 0 days, ≤1, ≤2, ≤3, 4+ (4+ = 100%). Example: 0 days 10%, 1 day 25%, 2 days 60%, 3 days 80%, 4+ days 100%.

**What Lane Adjusted Promise Comparison means (Tejas, 2026-10-18):** select only those lanes (warehouse × pincode) from internal-allocated orders that are present in PBA-allocated orders. For example, if PBA orders have WH 20 × Pincode 400079 allocated orders, that lane falls under Lane Adjusted Comparison. If WH 20 × Pincode 400079 has no orders allocated through PBA, it is kept out of Lane Adjusted Promise Comparison.

## Section 3: Courier Allocation Mix

Two sub-sections. Each shows, against every courier partner: Internal %, PBA %, Delta (pp). Each sub-section is split in two halves: Soft Allocation and Hard Allocation.

1. PBA Allocated Partner vs Internal Allocated Partner
2. Lane Adjusted Comparison (same lane definition as Section 2)

## Changes (2026-10-18)
- Section 1: "Total Orders" dropped; the Order Funnel starts at Total Non-SDD Orders. The PBA and Internal funnels are shown side by side as metrics 4–6.
- Section 2: metrics added for internal-allocated orders with the PBA-selected partner, and for the lane-adjusted comparison; cumulative % of orders added to every metric.
- Renumbered to match the wireframe. Section 2, original number → new number: 1→1, 5→2, 2→3, 7→4, 3→5, 6→6, 4→7, 8→8, 9→9, 10→10.

## Further sections

Not given yet.
