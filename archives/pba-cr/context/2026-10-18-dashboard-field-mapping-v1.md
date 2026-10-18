---
title: PBA CR dashboard field mapping
source: agreed with Tejas, metric by metric, from 2026-10-18
applies to: every raw dump from the Q1 base query, e.g. fahad-raw-dump-3
status: in progress
---

# PBA CR dashboard field mapping

Which raw-dump fields compute each dashboard number. Numbering follows the wireframe (https://claude.ai/artifact/XX9QtrxQWPMfiofjq2TjX7). No date filter for now: every metric covers all orders in the dump, or in the combined dumps, with each `ORDER_ID` counted once. Promise days are IST calendar-date differences (e.g. promised on the 15th for the 17th = 2 days), never hours ÷ 24.

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

### 4. Orders placed (PBA vs Internal)

| Item | PBA | Internal |
|---|---|---|
| Definition | Non-SDD orders whose customer promise was made by PBA at soft allocation; the 100% base of the PBA funnel | Non-SDD orders whose customer promise was made by internal logic at soft allocation; the 100% base of the Internal funnel |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE` | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE` |
| Numerator | Count of distinct `ORDER_ID` where `SDD_ENABLED = false` and `SOFT_SERVED_CANDIDATE_TYPE = COURIER_PBA` | Count of distinct `ORDER_ID` where `SDD_ENABLED = false` and `SOFT_SERVED_CANDIDATE_TYPE` in (`COURIER_LEGACY_TAT_ADHERENCE`, `COURIER_DDB_TAT_ADHERENCE`) |
| Denominator | Same as the numerator | Same as the numerator |
| Calculation | Count shown as [n]; % = 100% | Count shown as [n]; % = 100% |

### 5. % picked up (PBA vs Internal)

| Item | PBA | Internal |
|---|---|---|
| Definition | Share of PBA-allocated orders that a courier has picked up | Share of internally allocated orders that a courier has picked up |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `PICKUP_TIME` | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `PICKUP_TIME` |
| Numerator | Count of distinct `ORDER_ID` in metric 4's PBA base where `PICKUP_TIME` is not blank | Count of distinct `ORDER_ID` in metric 4's Internal base where `PICKUP_TIME` is not blank |
| Denominator | Metric 4, PBA | Metric 4, Internal |
| Calculation | Numerator ÷ Denominator × 100; card also shows the numerator as [n] orders | Numerator ÷ Denominator × 100; card also shows the numerator as [n] orders |

### 6. % with delivery attempt (PBA vs Internal)

| Item | PBA | Internal |
|---|---|---|
| Definition | Share of PBA-allocated orders with at least one delivery attempt | Share of internally allocated orders with at least one delivery attempt |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `DELIVERY_ATTEMPT_TIME` | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `DELIVERY_ATTEMPT_TIME` |
| Numerator | Count of distinct `ORDER_ID` in metric 4's PBA base where `DELIVERY_ATTEMPT_TIME` is not blank | Count of distinct `ORDER_ID` in metric 4's Internal base where `DELIVERY_ATTEMPT_TIME` is not blank |
| Denominator | Metric 4, PBA | Metric 4, Internal |
| Calculation | Numerator ÷ Denominator × 100; card also shows the numerator as [n] orders | Numerator ÷ Denominator × 100; card also shows the numerator as [n] orders |

## Section 2: Promise

### Sub-section 1: Soft Promise

### 1. PBA Allocated Orders: WH to Delivery Promise

| Item | Mapping |
|---|---|
| Definition | For orders PBA allocated at soft allocation, the promised days from warehouse processing to delivery, using PBA's partner |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `PROMISED_WAREHOUSE_PROCESSING_TIME`, `PBA_PROJECTED_DELIVERY_TIME` |
| Numerator | Per order: promise days = `DATE(PBA_PROJECTED_DELIVERY_TIME)` − `DATE(PROMISED_WAREHOUSE_PROCESSING_TIME)`. Cumulative columns: count of orders with promise days = 0, ≤1, ≤2, ≤3 |
| Denominator | Section 1 metric 4, PBA: count of distinct `ORDER_ID` where `SDD_ENABLED = false` and `SOFT_SERVED_CANDIDATE_TYPE = COURIER_PBA` |
| Calculation | Avg = sum of promise days ÷ Denominator. p25, p50, p75, p90 = percentiles of promise days. Cumulative % at k days = orders with promise days ≤ k ÷ Denominator × 100; 4+ = 100% |

### 2. PBA Allocated Orders: Internal Selected Partner WH to Delivery Promise

| Item | Mapping |
|---|---|
| Definition | For orders PBA allocated at soft allocation, the promised days from warehouse processing to delivery that internal logic's partner would have given |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `PROMISED_WAREHOUSE_PROCESSING_TIME`, `INTERNAL_PROJECTED_DELIVERY_TIME` |
| Numerator | Per order: promise days = `DATE(INTERNAL_PROJECTED_DELIVERY_TIME)` − `DATE(PROMISED_WAREHOUSE_PROCESSING_TIME)`. Cumulative columns: count of orders with promise days = 0, ≤1, ≤2, ≤3 |
| Denominator | Count of distinct `ORDER_ID` where `SDD_ENABLED = false`, `SOFT_SERVED_CANDIDATE_TYPE = COURIER_PBA` and `INTERNAL_PROJECTED_DELIVERY_TIME` is not blank |
| Calculation | Avg = sum of promise days ÷ Denominator. p25, p50, p75, p90 = percentiles of promise days. Cumulative % at k days = orders with promise days ≤ k ÷ Denominator × 100; 4+ = 100% |
