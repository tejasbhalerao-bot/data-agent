---
title: PBA CR dashboard field mapping
source: agreed with Tejas, metric by metric, from 2026-10-18
applies to: every raw dump from the Q1 base query, e.g. fahad-raw-dump-3
status: in progress
---

# PBA CR dashboard field mapping

Which raw-dump fields compute each dashboard number. Numbering follows the wireframe (https://claude.ai/artifact/XX9QtrxQWPMfiofjq2TjX7). No date filter for now: every metric covers all orders in the dump, or in the combined dumps, with each `ORDER_ID` counted once.

## Section 1: Funnel

### 1. Total Non-SDD Orders

| Item | Mapping |
|---|---|
| Definition | Number of distinct non-SDD orders in the dump |
| Fields | `ORDER_ID`, `SDD_ENABLED` |
| Numerator | Count of distinct `ORDER_ID` where `SDD_ENABLED = false` |
| Denominator | None (a count) |
| Calculation | Numerator |

### 2. % of non-SDD orders allocated through PBA

| Item | Mapping |
|---|---|
| Definition | Share of non-SDD orders whose customer promise was made by PBA at soft allocation |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE` |
| Numerator | Count of distinct `ORDER_ID` where `SDD_ENABLED = false` and `SOFT_SERVED_CANDIDATE_TYPE = COURIER_PBA` |
| Denominator | Metric 1: Total Non-SDD Orders |
| Calculation | Numerator ÷ Denominator × 100 |

### 3. % of non-SDD orders failed to allocate through PBA even though decision was in-rollout

| Item | Mapping |
|---|---|
| Definition | Share of non-SDD orders that were in the PBA rollout but did not get PBA's promise |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `PBA_IN_ROLLOUT`, `SOFT_SERVED_CANDIDATE_TYPE` |
| Numerator | Count of distinct `ORDER_ID` where `SDD_ENABLED = false`, `PBA_IN_ROLLOUT = true` and `SOFT_SERVED_CANDIDATE_TYPE ≠ COURIER_PBA` |
| Denominator | Metric 1: Total Non-SDD Orders |
| Calculation | Numerator ÷ Denominator × 100 |
