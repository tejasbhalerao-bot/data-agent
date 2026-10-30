---
title: PBA CR dashboard field mapping
source: agreed with Tejas, metric by metric, from 2026-10-18
applies to: every raw dump from the Q1 base query, e.g. fahad-raw-dump-3
status: complete, all four sections mapped (2026-10-18). Section 4 metrics 2–4 were mapped on the same rules without a separate review, at Tejas's request
---

# PBA CR dashboard field mapping

Which raw-dump fields compute each dashboard number, and exactly how. Numbering follows the wireframe (https://claude.ai/artifact/XX9QtrxQWPMfiofjq2TjX7). Every metric is read with the rules in this first part; a metric never overrides them.

## Sign-off on query v2.1 (Tejas, 2026-10-30)

| Section | Signed off | On hold |
|---|---|---|
| 1. Funnel | Metrics 1–6 | None |
| 2. Promise | Sub-section 1, metrics 1–10. The buffer open point on metrics 4 and 8 is closed. | Sub-section 2 (hard), metrics 11–13 |
| 3. Courier Allocation Mix | Metrics 1–2 | None |
| 4. Adherence | Sub-section 1 (soft), metrics 1–2, all lanes and lane adjusted | Sub-section 2 (hard), metrics 3–4 |

## Rules for every metric

### Scope
- **No date filter for now.** A metric covers every row of the dump, or of the combined dumps.
- **PBA promise rule (Tejas, 2026-10-26):** PBA always gives a dispatch-to-delivery time; its soft delivery = dispatch + PBA TAT. The dashboard window is chosen so this always holds (after the 19 Oct 7:16 PM IST flip of `PBA_DELIVERY_FROM_PROCESSING_ENABLED`). WH to Delivery metrics stay: they capture the dead time between warehouse processing and dispatch, so a longer gap can raise the customer ETA even when logistics TAT falls.
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
- **Exception: orders with a blank `SDD_ENABLED`** are left out of every metric and base, and their count is reported with each refresh (Tejas, 2026-10-26). The 20 Oct export had 21, with IDs like `TM17GHFNHH0TV01`.

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
- **Hard PBA base** (Section 2 Sub-section 2 and other hard metrics): orders where `SDD_ENABLED = 'false'` and `HARD_SELECTED_CANDIDATE_TYPE = 'COURIER_PBA'`, i.e. the courier booking was made by PBA (Tejas, 2026-10-18).
- **Hard Internal base:** orders where `SDD_ENABLED = 'false'` and `HARD_SELECTED_CANDIDATE_TYPE` is `'COURIER_LEGACY_TAT_ADHERENCE'` or `'COURIER_DDB_TAT_ADHERENCE'`.
- Orders with `HARD_SELECTED_CANDIDATE_TYPE = 'SDD'`, `'NONE'` or empty are in neither hard base. A filled `PBA_HARD_PROJECTED_*` time does not put an order in the Hard PBA base: PBA is evaluated at hard even when it does not make the booking.

### Lanes (lane-adjusted metrics)
- **Lane** = `WH_ID` + `PINCODE`, compared as text (`WH_ID` is 1–2 digits, `PINCODE` 6 digits).
- **Common lane set** = lanes that have at least one order in the PBA base **and** at least one order in the Internal base.
- **Lane-adjusted metrics** keep only orders whose lane is in the common lane set, on both the PBA side and the Internal side. PBA orders on lanes with no internally allocated order are dropped, and so are internal orders on lanes with no PBA order (Tejas, 2026-10-18).
- **Hard lane-adjusted metrics use the same common lane set**, built from the soft PBA base and soft Internal base. Only the orders counted change: Hard PBA base and Hard Internal base orders whose lane is in that set (Tejas, 2026-10-18).

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

### 7. Internal Allocated Orders: Dispatch to Delivery Promise

| Item | Mapping |
|---|---|
| Definition | For the Internal base, the promised days from courier pickup (dispatch) to delivery, using internal's own partner |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `INTERNAL_PROJECTED_DISPATCH_TIME`, `INTERNAL_PROJECTED_DELIVERY_TIME` |
| Numerator | Per order: promise days = date(`INTERNAL_PROJECTED_DELIVERY_TIME`) − date(`INTERNAL_PROJECTED_DISPATCH_TIME`). Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 |
| Denominator | Count of `ORDER_ID` in the Internal base where `INTERNAL_PROJECTED_DISPATCH_TIME` and `INTERNAL_PROJECTED_DELIVERY_TIME` are both not blank |
| Calculation | Avg, p25, p50, p75, p90 and cumulative % as defined in the rules at the top |

### 8. Internal Allocated Orders: PBA Selected Partner Dispatch to Delivery Promise

| Item | Mapping |
|---|---|
| Definition | For the Internal base, the promised days from courier pickup (dispatch) to delivery that PBA's partner would have given, measured from PBA's own dispatch time |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `PBA_PROJECTED_DISPATCH_TIME`, `PBA_PROJECTED_DELIVERY_TIME` |
| Numerator | Per order: promise days = date(`PBA_PROJECTED_DELIVERY_TIME`) − date(`PBA_PROJECTED_DISPATCH_TIME`). Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 |
| Denominator | Count of `ORDER_ID` in the Internal base where `PBA_PROJECTED_DISPATCH_TIME` and `PBA_PROJECTED_DELIVERY_TIME` are both not blank |
| Calculation | Avg, p25, p50, p75, p90 and cumulative % as defined in the rules at the top |

### 9. Lane Adjusted: WH to Delivery Promise Comparison - PBA vs Internal

| Item | PBA | Internal |
|---|---|---|
| Definition | For PBA-base orders on the common lane set, the promised days from warehouse processing to delivery, using PBA's partner | For Internal-base orders on the common lane set, the promised days from warehouse processing to delivery, using internal's own partner |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `WH_ID`, `PINCODE`, `PROMISED_WAREHOUSE_PROCESSING_TIME`, `PBA_PROJECTED_DELIVERY_TIME` | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `WH_ID`, `PINCODE`, `PROMISED_WAREHOUSE_PROCESSING_TIME`, `INTERNAL_PROJECTED_DELIVERY_TIME` |
| Numerator | Per order: promise days = date(`PBA_PROJECTED_DELIVERY_TIME`) − date(`PROMISED_WAREHOUSE_PROCESSING_TIME`). Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 | Per order: promise days = date(`INTERNAL_PROJECTED_DELIVERY_TIME`) − date(`PROMISED_WAREHOUSE_PROCESSING_TIME`). Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 |
| Denominator | Count of `ORDER_ID` in the PBA base whose lane is in the common lane set, where `PROMISED_WAREHOUSE_PROCESSING_TIME` and `PBA_PROJECTED_DELIVERY_TIME` are both not blank | Count of `ORDER_ID` in the Internal base whose lane is in the common lane set, where `PROMISED_WAREHOUSE_PROCESSING_TIME` and `INTERNAL_PROJECTED_DELIVERY_TIME` are both not blank |
| Calculation | Avg, p25, p50, p75, p90 and cumulative % as defined in the rules at the top | Same |

### 10. Lane Adjusted: Dispatch to Delivery Promise Comparison - PBA vs Internal

| Item | PBA | Internal |
|---|---|---|
| Definition | For PBA-base orders on the common lane set, the promised days from courier pickup (dispatch) to delivery, using PBA's partner | For Internal-base orders on the common lane set, the promised days from courier pickup (dispatch) to delivery, using internal's own partner |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `WH_ID`, `PINCODE`, `PBA_PROJECTED_DISPATCH_TIME`, `PBA_PROJECTED_DELIVERY_TIME` | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `WH_ID`, `PINCODE`, `INTERNAL_PROJECTED_DISPATCH_TIME`, `INTERNAL_PROJECTED_DELIVERY_TIME` |
| Numerator | Per order: promise days = date(`PBA_PROJECTED_DELIVERY_TIME`) − date(`PBA_PROJECTED_DISPATCH_TIME`). Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 | Per order: promise days = date(`INTERNAL_PROJECTED_DELIVERY_TIME`) − date(`INTERNAL_PROJECTED_DISPATCH_TIME`). Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 |
| Denominator | Count of `ORDER_ID` in the PBA base whose lane is in the common lane set, where `PBA_PROJECTED_DISPATCH_TIME` and `PBA_PROJECTED_DELIVERY_TIME` are both not blank | Count of `ORDER_ID` in the Internal base whose lane is in the common lane set, where `INTERNAL_PROJECTED_DISPATCH_TIME` and `INTERNAL_PROJECTED_DELIVERY_TIME` are both not blank |
| Calculation | Avg, p25, p50, p75, p90 and cumulative % as defined in the rules at the top | Same |

### Sub-section 2: Hard Promise

Hard metrics use the Hard PBA base and Hard Internal base, and the same promise-days rules as the soft metrics.

### 11. PBA Allocated Orders: Dispatch to Delivery Promise (hard)

| Item | Mapping |
|---|---|
| Definition | For the Hard PBA base, the promised days from courier pickup (dispatch) to delivery that PBA gave when the courier was booked |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `HARD_SELECTED_CANDIDATE_TYPE`, `PBA_HARD_PROJECTED_DISPATCH_TIME`, `PBA_HARD_PROJECTED_DELIVERY_TIME` |
| Numerator | Per order: promise days = date(`PBA_HARD_PROJECTED_DELIVERY_TIME`) − date(`PBA_HARD_PROJECTED_DISPATCH_TIME`). Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 |
| Denominator | Count of `ORDER_ID` in the Hard PBA base where `PBA_HARD_PROJECTED_DISPATCH_TIME` and `PBA_HARD_PROJECTED_DELIVERY_TIME` are both not blank |
| Calculation | Avg, p25, p50, p75, p90 and cumulative % as defined in the rules at the top |

### 12. Internal Allocated Orders: Dispatch to Delivery Promise (hard)

| Item | Mapping |
|---|---|
| Definition | For the Hard Internal base, the promised days from courier pickup (dispatch) to delivery for internal's selected partner when the courier was booked, taken from its TAT because the internal hard record keeps no dispatch or delivery time (Option B, Tejas, 2026-10-18) |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `HARD_SELECTED_CANDIDATE_TYPE`, `INTERNAL_HARD_PARTNER_TAT_IN_DAYS` |
| Numerator | Per order: promise days = `INTERNAL_HARD_PARTNER_TAT_IN_DAYS` (commas removed, read as a number) rounded up to the next whole day; a whole number stays as it is (0.83 → 1, 3.0 → 3, 0 → 0). A negative TAT is left out and reported as a data error. Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 |
| Denominator | Count of `ORDER_ID` in the Hard Internal base where `INTERNAL_HARD_PARTNER_TAT_IN_DAYS` is not blank |
| Calculation | Avg, p25, p50, p75, p90 and cumulative % as defined in the rules at the top. Not on the same basis as metric 11: these are TAT days rounded up, not calendar-date differences |

### 13. Lane Adjusted: Dispatch to Delivery Promise Comparison - PBA vs Internal (hard)

| Item | PBA | Internal |
|---|---|---|
| Definition | For Hard PBA base orders on the common lane set, the promised days from courier pickup (dispatch) to delivery that PBA gave when the courier was booked | For Hard Internal base orders on the common lane set, the promised days from courier pickup (dispatch) to delivery for internal's selected partner, taken from its TAT |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE` (for the common lane set), `HARD_SELECTED_CANDIDATE_TYPE`, `WH_ID`, `PINCODE`, `PBA_HARD_PROJECTED_DISPATCH_TIME`, `PBA_HARD_PROJECTED_DELIVERY_TIME` | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE` (for the common lane set), `HARD_SELECTED_CANDIDATE_TYPE`, `WH_ID`, `PINCODE`, `INTERNAL_HARD_PARTNER_TAT_IN_DAYS` |
| Numerator | Per order: promise days = date(`PBA_HARD_PROJECTED_DELIVERY_TIME`) − date(`PBA_HARD_PROJECTED_DISPATCH_TIME`). Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 | Per order: promise days = `INTERNAL_HARD_PARTNER_TAT_IN_DAYS` rounded up to the next whole day, as in metric 12. Cumulative columns: count of orders with promise days ≤ 0, ≤ 1, ≤ 2, ≤ 3 |
| Denominator | Count of `ORDER_ID` in the Hard PBA base whose lane is in the common lane set (the soft one), where `PBA_HARD_PROJECTED_DISPATCH_TIME` and `PBA_HARD_PROJECTED_DELIVERY_TIME` are both not blank | Count of `ORDER_ID` in the Hard Internal base whose lane is in the common lane set (the soft one), where `INTERNAL_HARD_PARTNER_TAT_IN_DAYS` is not blank |
| Calculation | Avg, p25, p50, p75, p90 and cumulative % as defined in the rules at the top | Same |

## Section 3: Courier Allocation Mix

Each column is the courier mix of its own base: PBA % is the share of the PBA base by courier partner, Internal % the share of the Internal base. Partners are shown by partner ID as it appears in the dump, read as text (Tejas, 2026-10-18).

For every table in this section:
- **Delta (pp)** = PBA % − Internal %, shown to 2 decimals (Tejas, 2026-10-18). Positive means PBA uses that partner more. PBA % and Internal % are shown to 1 decimal.
- **Rows:** every partner ID that appears on either side; a partner with no orders on one side shows 0.0% there. Sorted by PBA % + Internal %, highest first. The "All couriers" row is 100% on each side.

### 1. PBA Allocated Partner vs Internal Allocated Partner

**Soft Allocation**

| Item | PBA % | Internal % |
|---|---|---|
| Definition | Share of PBA base orders whose customer promise used each courier partner | Share of Internal base orders whose customer promise used each courier partner |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `SOFT_SERVED_PARTNER` | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `SOFT_SERVED_PARTNER` |
| Numerator | Per partner: count of `ORDER_ID` in the PBA base with that `SOFT_SERVED_PARTNER` | Per partner: count of `ORDER_ID` in the Internal base with that `SOFT_SERVED_PARTNER` |
| Denominator | Count of `ORDER_ID` in the PBA base where `SOFT_SERVED_PARTNER` is not blank | Count of `ORDER_ID` in the Internal base where `SOFT_SERVED_PARTNER` is not blank |
| Calculation | Numerator ÷ Denominator × 100; Delta as above | Same |

**Hard Allocation**

| Item | PBA % | Internal % |
|---|---|---|
| Definition | Share of Hard PBA base orders booked with each courier partner | Share of Hard Internal base orders booked with each courier partner |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `HARD_SELECTED_CANDIDATE_TYPE`, `HARD_BOOKED_PARTNER` | `ORDER_ID`, `SDD_ENABLED`, `HARD_SELECTED_CANDIDATE_TYPE`, `HARD_BOOKED_PARTNER` |
| Numerator | Per partner: count of `ORDER_ID` in the Hard PBA base with that `HARD_BOOKED_PARTNER` | Per partner: count of `ORDER_ID` in the Hard Internal base with that `HARD_BOOKED_PARTNER` |
| Denominator | Count of `ORDER_ID` in the Hard PBA base where `HARD_BOOKED_PARTNER` is not blank | Count of `ORDER_ID` in the Hard Internal base where `HARD_BOOKED_PARTNER` is not blank |
| Calculation | Numerator ÷ Denominator × 100; Delta as above | Same |

### 2. Lane Adjusted Comparison

Metric 1 restricted to the common lane set (the soft one, for both halves). The "[n] lanes" in the header = number of lanes in the common lane set.

**Soft Allocation**

| Item | PBA % | Internal % |
|---|---|---|
| Definition | Share of PBA base orders on the common lane set whose customer promise used each courier partner | Share of Internal base orders on the common lane set whose customer promise used each courier partner |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `WH_ID`, `PINCODE`, `SOFT_SERVED_PARTNER` | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `WH_ID`, `PINCODE`, `SOFT_SERVED_PARTNER` |
| Numerator | Per partner: count of `ORDER_ID` in the PBA base whose lane is in the common lane set, with that `SOFT_SERVED_PARTNER` | Per partner: count of `ORDER_ID` in the Internal base whose lane is in the common lane set, with that `SOFT_SERVED_PARTNER` |
| Denominator | Count of `ORDER_ID` in the PBA base whose lane is in the common lane set, where `SOFT_SERVED_PARTNER` is not blank | Count of `ORDER_ID` in the Internal base whose lane is in the common lane set, where `SOFT_SERVED_PARTNER` is not blank |
| Calculation | Numerator ÷ Denominator × 100; Delta (pp) to 2 decimals, rows as in metric 1 | Same |

**Hard Allocation**

| Item | PBA % | Internal % |
|---|---|---|
| Definition | Share of Hard PBA base orders on the common lane set booked with each courier partner | Share of Hard Internal base orders on the common lane set booked with each courier partner |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE` (for the common lane set), `HARD_SELECTED_CANDIDATE_TYPE`, `WH_ID`, `PINCODE`, `HARD_BOOKED_PARTNER` | Same as PBA |
| Numerator | Per partner: count of `ORDER_ID` in the Hard PBA base whose lane is in the common lane set, with that `HARD_BOOKED_PARTNER` | Per partner: count of `ORDER_ID` in the Hard Internal base whose lane is in the common lane set, with that `HARD_BOOKED_PARTNER` |
| Denominator | Count of `ORDER_ID` in the Hard PBA base whose lane is in the common lane set, where `HARD_BOOKED_PARTNER` is not blank | Count of `ORDER_ID` in the Hard Internal base whose lane is in the common lane set, where `HARD_BOOKED_PARTNER` is not blank |
| Calculation | Numerator ÷ Denominator × 100; Delta (pp) to 2 decimals, rows as in metric 1 | Same |

## Section 4: Adherence

Each measure is shown as one breach distribution table: PBA vs Internal, all lanes and lane adjusted (Tejas, 2026-10-18). The Early / On-Time / Late cards were removed and the courier-wise view moves to the deep-dive dashboard.

For every measure in this section:
- **Actual** = the first delivery attempt (`DELIVERY_ATTEMPT_TIME`).
- **Promised days** and **actual days** are calendar-date differences, as in the promise-days rules at the top.
- **Days late** = actual days − promised days. Columns: **Early** < 0; **On time** = 0; **1 d late** = 1; **2 d late** = 2; **3+ d late** ≥ 3.
- **Not yet attempted** = `DELIVERY_ATTEMPT_TIME` is blank. It is its own column; each row sums to 100%.
- **Data errors** (left out of the denominator and reported): an attempted order whose actual start timestamp is blank, or whose actual days are negative.

### Sub-section 1: Soft Promise Adherence

### 1. WH to Delivery

| Item | PBA | Internal |
|---|---|---|
| Definition | For the PBA base, how the actual days from box verified to first attempt compare with the promised WH-to-delivery days | Same, for the Internal base |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `WH_ID`, `PINCODE`, `PROMISED_WAREHOUSE_PROCESSING_TIME`, `PBA_PROJECTED_DELIVERY_TIME`, `BOX_VERIFIED_TS`, `DELIVERY_ATTEMPT_TIME` | Same, with `INTERNAL_PROJECTED_DELIVERY_TIME` in place of `PBA_PROJECTED_DELIVERY_TIME` |
| Numerator | Per order: promised days = date(`PBA_PROJECTED_DELIVERY_TIME`) − date(`PROMISED_WAREHOUSE_PROCESSING_TIME`); actual days = date(`DELIVERY_ATTEMPT_TIME`) − date(`BOX_VERIFIED_TS`); days late = actual − promised. Count of orders in each column: Early, On time, 1 d late, 2 d late, 3+ d late, Not yet attempted | Same, with `INTERNAL_PROJECTED_DELIVERY_TIME` |
| Denominator | PBA base orders where `PROMISED_WAREHOUSE_PROCESSING_TIME` and `PBA_PROJECTED_DELIVERY_TIME` are both not blank, less data errors (attempted orders plus not yet attempted) | Same, with `INTERNAL_PROJECTED_DELIVERY_TIME` |
| Calculation | Numerator ÷ Denominator × 100, to 1 decimal; each row sums to 100%. Lane adjusted: the same on the common lane set | Same |

### 2. Dispatch to Delivery

| Item | PBA | Internal |
|---|---|---|
| Definition | For the PBA base, how the actual days from courier pickup to first attempt compare with the promised dispatch-to-delivery days | Same, for the Internal base |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `SOFT_SERVED_CANDIDATE_TYPE`, `WH_ID`, `PINCODE`, `PBA_PROJECTED_DISPATCH_TIME`, `PBA_PROJECTED_DELIVERY_TIME`, `PICKUP_TIME`, `DELIVERY_ATTEMPT_TIME` | Same, with `INTERNAL_PROJECTED_DISPATCH_TIME` and `INTERNAL_PROJECTED_DELIVERY_TIME` in place of the PBA columns |
| Numerator | Per order: promised days = date(`PBA_PROJECTED_DELIVERY_TIME`) − date(`PBA_PROJECTED_DISPATCH_TIME`) (as Section 2 metric 5); actual days = date(`DELIVERY_ATTEMPT_TIME`) − date(`PICKUP_TIME`); days late = actual − promised. Count of orders in each column: Early, On time, 1 d late, 2 d late, 3+ d late, Not yet attempted | Same, with the internal columns (promise as Section 2 metric 7) |
| Denominator | PBA base orders where `PBA_PROJECTED_DISPATCH_TIME` and `PBA_PROJECTED_DELIVERY_TIME` are both not blank, less data errors (attempted with blank `PICKUP_TIME`, or negative actual days) | Same, with the internal columns |
| Calculation | Numerator ÷ Denominator × 100, to 1 decimal; each row sums to 100%. Lane adjusted: the same on the common lane set | Same |

### Sub-section 2: Hard Promise Adherence

Uses the Hard PBA base and Hard Internal base. Lane adjusted uses the common lane set (the soft one), as for every hard lane-adjusted metric.

### 3. WH to Delivery

| Item | PBA | Internal |
|---|---|---|
| Definition | For the Hard PBA base, how the actual days from box verified to first attempt compare with the WH-to-delivery days PBA promised when the courier was booked | Not measurable: the internal hard record keeps no dispatch or delivery time, and its TAT runs from dispatch, so there is no WH-to-delivery promise (wireframe callout) |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `HARD_SELECTED_CANDIDATE_TYPE`, `SOFT_SERVED_CANDIDATE_TYPE` (for the common lane set), `WH_ID`, `PINCODE`, `HARD_WH_PROCESSING_TIME`, `PBA_HARD_PROJECTED_DELIVERY_TIME`, `BOX_VERIFIED_TS`, `DELIVERY_ATTEMPT_TIME` | None |
| Numerator | Per order: promised days = date(`PBA_HARD_PROJECTED_DELIVERY_TIME`) − date(`HARD_WH_PROCESSING_TIME`); actual days = date(`DELIVERY_ATTEMPT_TIME`) − date(`BOX_VERIFIED_TS`); days late = actual − promised. Count of orders in each column: Early, On time, 1 d late, 2 d late, 3+ d late, Not yet attempted | None |
| Denominator | Hard PBA base orders where `HARD_WH_PROCESSING_TIME` and `PBA_HARD_PROJECTED_DELIVERY_TIME` are both not blank, less data errors (attempted with blank `BOX_VERIFIED_TS`, or negative actual days) | None |
| Calculation | Numerator ÷ Denominator × 100, to 1 decimal; each row sums to 100%. Lane adjusted: the same on the common lane set | Every cell shows "n/a", all lanes and lane adjusted |

### 4. Dispatch to Delivery

| Item | PBA | Internal |
|---|---|---|
| Definition | For the Hard PBA base, how the actual days from courier pickup to first attempt compare with the dispatch-to-delivery days PBA promised when the courier was booked | For the Hard Internal base, how the actual days from courier pickup to first attempt compare with internal's selected partner TAT at booking, rounded up (Option B, as Section 2 metric 12) |
| Fields | `ORDER_ID`, `SDD_ENABLED`, `HARD_SELECTED_CANDIDATE_TYPE`, `SOFT_SERVED_CANDIDATE_TYPE` (for the common lane set), `WH_ID`, `PINCODE`, `PBA_HARD_PROJECTED_DISPATCH_TIME`, `PBA_HARD_PROJECTED_DELIVERY_TIME`, `PICKUP_TIME`, `DELIVERY_ATTEMPT_TIME` | `ORDER_ID`, `SDD_ENABLED`, `HARD_SELECTED_CANDIDATE_TYPE`, `SOFT_SERVED_CANDIDATE_TYPE` (for the common lane set), `WH_ID`, `PINCODE`, `INTERNAL_HARD_PARTNER_TAT_IN_DAYS`, `PICKUP_TIME`, `DELIVERY_ATTEMPT_TIME` |
| Numerator | Per order: promised days = date(`PBA_HARD_PROJECTED_DELIVERY_TIME`) − date(`PBA_HARD_PROJECTED_DISPATCH_TIME`) (as Section 2 metric 11); actual days = date(`DELIVERY_ATTEMPT_TIME`) − date(`PICKUP_TIME`); days late = actual − promised. Count of orders in each column: Early, On time, 1 d late, 2 d late, 3+ d late, Not yet attempted | Per order: promised days = `INTERNAL_HARD_PARTNER_TAT_IN_DAYS` rounded up to the next whole day (as Section 2 metric 12); actual days and days late as for PBA. Same columns |
| Denominator | Hard PBA base orders where `PBA_HARD_PROJECTED_DISPATCH_TIME` and `PBA_HARD_PROJECTED_DELIVERY_TIME` are both not blank, less data errors (attempted with blank `PICKUP_TIME`, or negative actual days) | Hard Internal base orders where `INTERNAL_HARD_PARTNER_TAT_IN_DAYS` is not blank, less data errors (same as PBA; a negative TAT is also a data error) |
| Calculation | Numerator ÷ Denominator × 100, to 1 decimal; each row sums to 100%. Lane adjusted: the same on the common lane set | Same. Not on the same basis as PBA: the promise is TAT days rounded up, not a calendar-date difference |
