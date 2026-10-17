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

## Further sections

Not given yet.
