---
title: PBA CR dashboard field mapping
source: agreed with Tejas, metric by metric, from 2026-10-18
applies to: every raw dump from the Q1 base query, e.g. fahad-raw-dump-3
status: in progress (Section 1 done; Section 2 metrics 1–4 agreed)
---

# PBA CR dashboard field mapping

Which raw-dump fields compute each dashboard number, and exactly how. Numbering follows the wireframe (https://claude.ai/artifact/XX9QtrxQWPMfiofjq2TjX7). Every metric is read with the rules in this first part; a metric never overrides them.

## Rules for every metric

### Scope
- **No date filter for now.** A metric covers every row of the dump, or of the combined dumps.
- **One row per order.** `ORDER_ID` is unique within a dump.
- **Combining dumps:** stack the dumps and keep one row per `ORDER_ID`. Where an order is in more than one dump, keep the row from the dump extracted last (the highest dump number, e.g. dump 4 over dump 3).

### How values appear in the dump (checked on fahad-raw-dump-3)

| Kind | Columns (examples) | How it appears | How to read it |
|---|---|---|---|
| Flags | `SDD_ENABLED`, `PBA_IN_ROLLOUT`, `HAS_SOFT_RECORD` | Lowercase text `true` or `false`. `PBA_IN_ROLLOUT` is empty when the order has no soft record | Compare as text: `= 'false'` or `= 'true'`. Empty is neither |
| Allocation type | `SOFT_SERVED_CANDIDATE_TYPE` | One of `COURIER_PBA`, `COURIER_LEGACY_TAT_ADHERENCE`, `COURIER_DDB_TAT_ADHERENCE`, `NONE`, or empty (no soft record) | Match exact text against a listed set of values. Never use "not equal to" |
| Timestamps | `ORDER_PLACED_AT`, `PROMISED_WAREHOUSE_PROCESSING_TIME`, `*_PROJECTED_*_TIME`, `PICKUP_TIME`, `DELIVERY_ATTEMPT_TIME`, `BOX_VERIFIED_TS` | Text like `Oct 14, 2026, 4:26 PM`: IST, to the minute, no timezone marker. Empty when missing | Parse with the format `Mon D, YYYY, h:mm AM/PM` as IST. Empty = missing |
| Numbers | `*_TAT_IN_DAYS`, `*_IN_MINUTES`, partner ids | Digits, sometimes with a thousands comma (`2,880`) or decimals (`2.5`) | Remove commas, then read as a number. Empty = missing |
| Order id | `ORDER_ID` | 6–8 digits | Read as text. Never blank |

- **"Not blank"** means the value is a non-empty string after trimming spaces.
- **Any value outside these lists** (a new allocation type, a flag that is not `true`, `false` or empty, a timestamp that does not parse) stops the build and is reported. It is never guessed.

### Promise days (Sections 2 and 4)
- **Promise days** = calendar date of the later timestamp − calendar date of the earlier one, both in IST. Example: 15 Oct 11:30 PM to 17 Oct 8:00 AM = 2 days. Never hours ÷ 24.
- **Which orders count:** an order is in a promise-days metric only if both timestamps the metric names are not blank. Each metric's denominator states this.
- **Negative promise days** (end date before start date) are left out of the metric and reported as a data error.
- **Avg** = sum of promise days ÷ number of orders, shown to 1 decimal.
- **Percentiles** (p25, p50, p75, p90) use nearest rank: the p-th percentile is the smallest whole number of days d such that at least p% of the orders have promise days ≤ d. Every percentile is a whole number of days and agrees with the cumulative columns.
- **Cumulative % of orders:** for k = 0, 1, 2, 3, orders with promise days ≤ k ÷ number of orders × 100. The 4+ column is always 100%.

### Percentages
- % = numerator ÷ denominator × 100, shown to 1 decimal. A denominator of 0 shows "n/a".

### Bases used across sections
- **PBA base:** orders where `SDD_ENABLED = 'false'` and `SOFT_SERVED_CANDIDATE_TYPE = 'COURIER_PBA'`.
- **Internal base:** orders where `SDD_ENABLED = 'false'` and `SOFT_SERVED_CANDIDATE_TYPE` is `'COURIER_LEGACY_TAT_ADHERENCE'` or `'COURIER_DDB_TAT_ADHERENCE'`.
- Orders with `SOFT_SERVED_CANDIDATE_TYPE = 'NONE'` or empty are in neither base.

## Section 1: Funnel

### 1. Total Non-SDD Orders

| Item | Mapping |
|---|---|
| Definition | Number of non-SDD orders in the dump |
| Fields | `ORDER_ID`, `SDD_ENABLED` |
| Numerator | Count of `ORDER_ID` where `SDD_ENABLED = 'false'`. Includes orders with no soft record (fallback promises) |
| Denominator | None (a count) |
| Calculation | Numerator |

### 2. % of non-SDD orders allocated through PBA

| Item | Mapping |
|---|---|
| Definition | Share of non-SDD orders whose customer promise was made by PBA at soft allocation |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE` |
| Numerator | Count of `ORDER_ID` in the PBA base |
| Denominator | Metric 1 |
| Calculation | Numerator ÷ Denominator × 100 |

### 3. % of non-SDD orders failed to allocate through PBA even though decision was in-rollout

| Item | Mapping |
|---|---|
| Definition | Share of non-SDD orders that were in the PBA rollout but whose customer promise was not made by PBA |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `PBA_IN_ROLLOUT`, `SOFT_SERVED_CANDIDATE_TYPE` |
| Numerator | Count of `ORDER_ID` where `SDD_ENABLED = 'false'`, `PBA_IN_ROLLOUT = 'true'` and `SOFT_SERVED_CANDIDATE_TYPE` is `'COURIER_LEGACY_TAT_ADHERENCE'`, `'COURIER_DDB_TAT_ADHERENCE'` or `'NONE'` |
| Denominator | Metric 1 |
| Calculation | Numerator ÷ Denominator × 100 |

### 4. Orders placed (PBA vs Internal)

| Item | PBA | Internal |
|---|---|---|
| Definition | The PBA base: the starting point of the PBA funnel | The Internal base: the starting point of the Internal funnel |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE` | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE` |
| Numerator | Count of `ORDER_ID` in the PBA base | Count of `ORDER_ID` in the Internal base |
| Denominator | Same as the numerator | Same as the numerator |
| Calculation | Count shown as [n]; % = 100% | Count shown as [n]; % = 100% |

### 5. % picked up (PBA vs Internal)

| Item | PBA | Internal |
|---|---|---|
| Definition | Share of the PBA base that a courier has picked up | Share of the Internal base that a courier has picked up |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `PICKUP_TIME` | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `PICKUP_TIME` |
| Numerator | Count of `ORDER_ID` in the PBA base where `PICKUP_TIME` is not blank | Count of `ORDER_ID` in the Internal base where `PICKUP_TIME` is not blank |
| Denominator | Metric 4, PBA (the whole PBA base) | Metric 4, Internal (the whole Internal base) |
| Calculation | Numerator ÷ Denominator × 100; the card also shows the numerator as [n] orders | Numerator ÷ Denominator × 100; the card also shows the numerator as [n] orders |

### 6. % with delivery attempt (PBA vs Internal)

| Item | PBA | Internal |
|---|---|---|
| Definition | Share of the PBA base with at least one delivery attempt | Share of the Internal base with at least one delivery attempt |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `DELIVERY_ATTEMPT_TIME` | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `DELIVERY_ATTEMPT_TIME` |
| Numerator | Count of `ORDER_ID` in the PBA base where `DELIVERY_ATTEMPT_TIME` is not blank | Count of `ORDER_ID` in the Internal base where `DELIVERY_ATTEMPT_TIME` is not blank |
| Denominator | Metric 4, PBA (the whole PBA base, not only picked-up orders) | Metric 4, Internal (the whole Internal base, not only picked-up orders) |
| Calculation | Numerator ÷ Denominator × 100; the card also shows the numerator as [n] orders | Numerator ÷ Denominator × 100; the card also shows the numerator as [n] orders |

## Section 2: Promise

### Sub-section 1: Soft Promise

All metrics below use the promise-days rules at the top: calendar days, nearest-rank percentiles, cumulative columns 0 / ≤1 / ≤2 / ≤3 / 4+.

### 1. PBA Allocated Orders: WH to Delivery Promise

| Item | Mapping |
|---|---|
| Definition | For the PBA base, the promised days from warehouse processing to delivery, using PBA's partner |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `PROMISED_WAREHOUSE_PROCESSING_TIME`, `PBA_PROJECTED_DELIVERY_TIME` |
| Numerator | Per order: promise days = date(`PBA_PROJECTED_DELIVERY_TIME`) − date(`PROMISED_WAREHOUSE_PROCESSING_TIME`). Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 |
| Denominator | Count of `ORDER_ID` in the PBA base where `PROMISED_WAREHOUSE_PROCESSING_TIME` and `PBA_PROJECTED_DELIVERY_TIME` are both not blank |
| Calculation | Avg, p25, p50, p75, p90 and cumulative % as defined in the rules at the top |

### 2. PBA Allocated Orders: Internal Selected Partner WH to Delivery Promise

| Item | Mapping |
|---|---|
| Definition | For the PBA base, the promised days from warehouse processing to delivery that internal logic's partner would have given |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `PROMISED_WAREHOUSE_PROCESSING_TIME`, `INTERNAL_PROJECTED_DELIVERY_TIME` |
| Numerator | Per order: promise days = date(`INTERNAL_PROJECTED_DELIVERY_TIME`) − date(`PROMISED_WAREHOUSE_PROCESSING_TIME`). Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 |
| Denominator | Count of `ORDER_ID` in the PBA base where `PROMISED_WAREHOUSE_PROCESSING_TIME` and `INTERNAL_PROJECTED_DELIVERY_TIME` are both not blank |
| Calculation | Avg, p25, p50, p75, p90 and cumulative % as defined in the rules at the top |

### 3. Internal Allocated Orders: WH to Delivery Promise

| Item | Mapping |
|---|---|
| Definition | For the Internal base, the promised days from warehouse processing to delivery, using internal's own partner |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `PROMISED_WAREHOUSE_PROCESSING_TIME`, `INTERNAL_PROJECTED_DELIVERY_TIME` |
| Numerator | Per order: promise days = date(`INTERNAL_PROJECTED_DELIVERY_TIME`) − date(`PROMISED_WAREHOUSE_PROCESSING_TIME`). Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 |
| Denominator | Count of `ORDER_ID` in the Internal base where `PROMISED_WAREHOUSE_PROCESSING_TIME` and `INTERNAL_PROJECTED_DELIVERY_TIME` are both not blank |
| Calculation | Avg, p25, p50, p75, p90 and cumulative % as defined in the rules at the top |

### 4. Internal Allocated Orders: PBA Selected Partner WH to Delivery Promise

| Item | Mapping |
|---|---|
| Definition | For the Internal base, the promised days from warehouse processing to delivery that PBA's partner would have given |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `PROMISED_WAREHOUSE_PROCESSING_TIME`, `PBA_PROJECTED_DELIVERY_TIME` |
| Numerator | Per order: promise days = date(`PBA_PROJECTED_DELIVERY_TIME`) − date(`PROMISED_WAREHOUSE_PROCESSING_TIME`). Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 |
| Denominator | Count of `ORDER_ID` in the Internal base where `PROMISED_WAREHOUSE_PROCESSING_TIME` and `PBA_PROJECTED_DELIVERY_TIME` are both not blank |
| Calculation | Avg, p25, p50, p75, p90 and cumulative % as defined in the rules at the top |

### 5. PBA Allocated Orders: Dispatch to Delivery Promise

| Item | Mapping |
|---|---|
| Definition | For the PBA base, the promised days from courier pickup (dispatch) to delivery, using PBA's partner |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `PBA_PROJECTED_DISPATCH_TIME`, `PBA_PROJECTED_DELIVERY_TIME` |
| Numerator | Per order: promise days = date(`PBA_PROJECTED_DELIVERY_TIME`) − date(`PBA_PROJECTED_DISPATCH_TIME`). Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 |
| Denominator | Count of `ORDER_ID` in the PBA base where `PBA_PROJECTED_DISPATCH_TIME` and `PBA_PROJECTED_DELIVERY_TIME` are both not blank |
| Calculation | Avg, p25, p50, p75, p90 and cumulative % as defined in the rules at the top |

### 6. PBA Allocated Orders: Internal Selected Partner Dispatch to Delivery Promise

| Item | Mapping |
|---|---|
| Definition | For the PBA base, the promised days from courier pickup (dispatch) to delivery that internal logic's partner would have given, measured from internal's own dispatch time |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `INTERNAL_PROJECTED_DISPATCH_TIME`, `INTERNAL_PROJECTED_DELIVERY_TIME` |
| Numerator | Per order: promise days = date(`INTERNAL_PROJECTED_DELIVERY_TIME`) − date(`INTERNAL_PROJECTED_DISPATCH_TIME`). Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 |
| Denominator | Count of `ORDER_ID` in the PBA base where `INTERNAL_PROJECTED_DISPATCH_TIME` and `INTERNAL_PROJECTED_DELIVERY_TIME` are both not blank |
| Calculation | Avg, p25, p50, p75, p90 and cumulative % as defined in the rules at the top |
