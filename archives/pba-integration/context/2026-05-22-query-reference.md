# PBA Query Reference
**Date:** 2026-05-22

All Redshift tables prefixed with `tmmumpsdb.`

> **Always read `context/schema.md` (global schema reference) before writing any query. Table definitions, column meanings, join keys, and quirks live there.**

---

## Tables

| Table | Purpose |
|---|---|
| `logistics_allocation_audit` | One record per order per allocation type (SOFT/HARD). Stores both PBA and internal courier decisions + TATs in `allocation_metadata` JSON |
| `logistics_rails_api_audit` | Raw Clickpost API response logs. PK = `#order_id`. Contains full `preference_array` — every courier Clickpost considered + scoring params |
| `logistics_delivery_partner` | Maps internal `delivery_partner_id` ↔ Clickpost `cp_id` + `ankw_account_code`. PK = `#delivery_partner_id` |
| `order_status` | Order lifecycle events. `order_status_id = 344` = PBA-eligible placed order. `order_status_id = 39` = order created timestamp |
| `order_tat_details` | `pickup_time`, `delivery_attempt_time` per order |
| `delivery_date_tracker` | `actual_delivery_date`, `promised_delivery_date` (surface), `promised_air_delivery_date` (express) |
| `m_system_value_master` | General system enum/lookup table. Decodes various IDs across system (e.g. `Order Status ID` where `Name = 'Order Status'`). Used in Query 1 to decode `delivery_partner_id → partner_name` to determine express vs surface promise column. |

---

## Key Field Notes

**`allocation_metadata` fields (from `logistics_allocation_audit`):**
- `pba_partner_id`, `pba_tat` — PBA-selected courier + TAT in minutes (CEILING(x/1440) for days)
- `internal_partner_id`, `internal_tat` — Internal-selected courier + TAT in minutes
- `warehouse_id`, `pincode`, `projected_dispatch_time` (epoch ms)

**Shadow mode:**
- `selected_source = 'INTERNAL'` — internal courier always executes. PBA is counterfactual.
- `warehouse_id >= 17` — active warehouses only (older shut down, not a PBA filter)

**Preference array path:**
`response_payload → result[0] → preference_array`

**Per courier in preference array:**
`cp_id`, `account_code`, `courier_name`, `priority`, `delivery_type`
Scoring: `scores_computation.scoring_params_actual.EDD / PRICING / AVERAGE_TAT`, `scores_computation.total_score`

**Promised delivery date:**
Use `promised_air_delivery_date` if courier is express-type (`partner_name ILIKE '%express%'`), else `promised_delivery_date`. Promise is constructed from courier TAT at order creation time.

---

## Allocation Ranking Logic (Clickpost)

`EDD ASC → PRICING ASC → AVERAGE_TAT ASC → TOTAL_SCORE ASC → PRIORITY ASC`

---

## Courier Pricing Scope

Shiprocket and Shadowfax have no configured pricing in the Clickpost PBA setup.
Their `cost_per_shipment` columns will be null in output.
They are NOT excluded from preference array analysis — all couriers are included.

---

## Query Nomenclature Rules

- **Name by content, not plan section number.** Plan section numbers shift; query purpose doesn't.
- **Format:** `pba-<what-it-does>-v<n>.sql` — e.g. `pba-adherence-base-extract-v1.sql`
- **Versioning:** bump `v<n>` when query logic changes. Never overwrite an existing version.
- **Mapping query → plan question** lives in the Analysis Queries table below — that is the single source of truth. Do not encode plan question numbers in filenames.

---

## Base Queries

| File | Purpose |
|---|---|
| `queries-dump/2026-05-25-pba-allocation-with-pref-array-v1.sql` | One row per order. HARD allocation only. PBA + Internal partner IDs, TATs, preference array pivoted wide (dp1–dp6: name, EDD, pricing, total_score). Joins `logistics_rails_api_audit` on `request_id = reference_number` — exact match, no timestamp approximation. |
| `queries-dump/2026-05-25-pba-allocation-output-v1.sql` | One row per order. SOFT + HARD side-by-side. PBA + Internal partner IDs, TATs, actual delivery date, promised delivery date. `order_tat_details` joined LEFT (preserves orders without pickup data). |

**Query 1 date filter:** `2026-05-22 19:00:00` (adjust for production run)
**Query 1 preference array:** up to 6 couriers (idx 0–5 → dp1–dp6)
**Query 2 date filter:** `2026-05-10 00:00:00`
**Query 2 notes:** No `order_status` join. Warehouse filter (`>= 17`) applied in `allocation` CTE, not in `cte`.

---

## Analysis Queries

Mapping of analysis queries to plan questions. Add every new query here.

| File | Plan Questions | Output | Notes |
|---|---|---|---|
| `queries-dump/2026-05-25-pba-adherence-base-extract-v1.sql` | 1.1, 1.2, 1.3, 1.4 | 1 row per order. `hard_pba_tat_days`, `hard_internal_tat_days`, `pickup_time`, `delivery_attempt_time`, partner IDs + names | Adherence = TAT vs `CEIL((delivery_attempt_time - pickup_time) in days)`. Aggregations in script, not in query. |
| `scripts/2026-05-25-aggregate-1-1-adherence-top-level-v1.py` | 1.1 | 6-row summary. Buckets: Early / On-Time / Late / Not Picked Up / Not Delivered / Excluded. PBA + Internal counts + pct. | — |
| `scripts/2026-05-25-aggregate-courier-adherence-v1.py` | 1.2 | Two CSVs — PBA and Internal. courier_name × adherence_bucket with pct_within_courier + pct_of_total. | Excluded bucket logged, not in output tables. |
| `scripts/2026-05-25-aggregate-same-courier-adherence-v1.py` | 1.3 | 5-row summary. Same-courier cohort only (pba_partner_id == internal_partner_id). PBA + Internal counts + pct. Cohort size printed to console. | — |
| `scripts/2026-05-25-aggregate-same-courier-courier-adherence-v1.py` | 1.4 | courier_name × adherence_bucket. PBA + Internal counts + pct_within_courier + pct_of_total. Same-courier cohort only. | — |
| `scripts/2026-05-25-aggregate-promise-direction-adherence-v1.py` | 1.5 | promise_direction × adherence_bucket. PBA + Internal pct_within_direction. Same-courier cohort only. Direction distribution printed to console. | promise_direction = PBA_FASTER / SAME / INTERNAL_FASTER |
| `queries-dump/2026-05-25-pba-diff-courier-internal-rank-v1.sql` | 1.6 | 1 row per order. Different-courier cohort only. Internal courier's rank + EDD score in PBA's preference array. Joined via request_id = reference_number + ankw_account_code match. | Internal courier absent from array → NULL rank + EDD. |
| `scripts/2026-05-25-aggregate-diff-courier-pba-calibration-v1.py` | 1.6 | Calibration buckets: ACCURATE / PBA_OVERESTIMATED / PBA_UNDERESTIMATED / NOT_IN_PREF_ARRAY / Not Picked Up / Not Delivered. Rank distribution printed to console. | Reads pba-diff-courier-internal-rank CSV. |
| `scripts/2026-05-25-aggregate-promise-distribution-v1.py` | 2.1 | 8-row summary. tat_bucket (1d–7d / 7d+) × pba_orders + pba_pct + internal_orders + internal_pct. | Reads adherence base extract. Null TAT logged to console. |
| `queries-dump/2026-05-25-pba-adherence-base-extract-v2.sql` | 1.1–1.6, 1.7 | Same as v1 + `allocation_created_at`. Required for pre/post cohort filtering. | Use this going forward. v1 preserved for reference. |
| `queries-dump/2026-05-25-pba-diff-courier-internal-rank-v2.sql` | 1.6, 1.7 | Same as v1 + `allocation_created_at`. Required for pre/post cohort filtering in 1.6 script. | Use this going forward. v1 preserved for reference. |
| `scripts/2026-05-25-aggregate-1-1-adherence-top-level-v2.py` | 1.1, 1.7 | Same as v1. Adds `--cohort PRE\|POST\|ALL` + `--cutoff-date`. Output suffix `_PRE`/`_POST` when filtered. | — |
| `scripts/2026-05-25-aggregate-courier-adherence-v2.py` | 1.2, 1.7 | Same as v1. Adds cohort filtering. Two CSVs (PBA + Internal) with optional suffix. | — |
| `scripts/2026-05-25-aggregate-same-courier-adherence-v2.py` | 1.3, 1.7 | Same as v1. Adds cohort filtering. | — |
| `scripts/2026-05-25-aggregate-same-courier-courier-adherence-v2.py` | 1.4, 1.7 | Same as v1. Adds cohort filtering. | — |
| `scripts/2026-05-25-aggregate-promise-direction-adherence-v2.py` | 1.5, 1.7 | Same as v1. Adds cohort filtering. | — |
| `scripts/2026-05-25-aggregate-diff-courier-pba-calibration-v2.py` | 1.6, 1.7 | Same as v1. Adds cohort filtering. Reads v2 diff-courier-internal-rank CSV. | — |
| `scripts/2026-05-25-aggregate-1-7-pre-post-cutoff-adherence-v1.py` | 1.7 | Calendar date split only (PRE/POST by `--cutoff-date`). Superseded by v2 for time-of-day cutoff analysis. | Kept for calendar-date splits if needed. |
| `queries-dump/2026-05-25-pba-adherence-base-extract-v3.sql` | 1.7 | Same as v2 + `warehouse_id`. Required for 1.7 v2 time-of-day cutoff classification. | Use this for 1.7 v2. v2 scripts (1.1–1.6) work with v2 or v3. |
| `scripts/2026-05-25-aggregate-1-7-pre-post-cutoff-adherence-v2.py` | 1.7 | Per-courier × regime (INTERNAL/PBA) × PRE/POST × adherence_bucket. Reads warehouse-id-mapping.csv + cutoff-times.csv for time-of-day classification. | Requires v3 base extract. Check "Unmatched partner names" on first run. |
| `context/warehouse-id-mapping.csv` | 1.7 | warehouse_id → alias → city_label. Maps to Row Labels in cutoff-times.csv. | Faridabad (21) has no city_label — orders excluded from PRE/POST. |
| `queries-dump/2026-05-25-pba-lane-extract-v1.sql` | 1.8 | 1 row per order. warehouse_id + drop_pincode. Joined to base extract in script on order_id. | Same HARD/INTERNAL/warehouse>=17 filters as base extract. |
| `scripts/2026-05-25-aggregate-1-8-lane-drill-down-v1.py` | 1.8 | warehouse_id × drop_pincode × courier_name. order_count + pba/internal adherence_pct + late_pct + comparison. Sorted by order_count DESC. Top 10 worst by pba_late_pct printed to console. | Same-courier cohort only. Reads base extract + lane extract. |
| `scripts/2026-05-25-aggregate-avg-tat-per-courier-v1.py` | 2.2 | courier_name × pba_order_count + pba_avg_tat_days + internal_order_count + internal_avg_tat_days + tat_compression. Sorted by tat_compression DESC. | Reads adherence base extract. No new query needed. |
| `scripts/2026-05-25-aggregate-lane-promise-direction-v1.py` | 2.3 | warehouse_id × drop_pincode × courier_name × order_count + pba_lower/same/higher counts + pcts. Sorted by order_count DESC. | Same-courier cohort only. Reads base extract + lane extract. Cross-reference with 1.8 for combined signal. |
| `scripts/2026-05-25-aggregate-pba-higher-adherence-v1.py` | 2.4 | adherence_bucket × pba_orders + pba_pct + internal_orders + internal_pct. Cohort: orders where pba_tat > internal_tat. 80% adherence threshold check printed to console. | Reads adherence base extract. Tests whether PBA's conservative buffers translate into better adherence. |
| `scripts/2026-05-25-aggregate-tat-calibration-v1.py` | 2.5 | regime (PBA/INTERNAL) × calibration_bucket (ACCURATE/OVERESTIMATED/UNDERESTIMATED/Not Picked Up/Not Delivered) × order_count + pct_of_cohort. Mean signed error (actual − promised) per regime printed to console. | Same-courier cohort only. Reads adherence base extract. Positive MSE = promise too optimistic; negative = too conservative. |
| `scripts/2026-05-25-aggregate-courier-allocation-share-v1.py` | 3.1 | courier_name × pba_order_count + pba_share_pct + internal_order_count + internal_share_pct + share_delta. Sorted by share_delta DESC. Top 5 gainers + losers printed to console. | Reads adherence base extract. No new query. |
| `scripts/2026-05-25-aggregate-cost-comparison-v1.py` | 3.2 | regime × courier_name × order_count + price_per_shipment + total_cost + share_pct. Prices from context/2026-05-22-courier-pricing-snapshot.md. Cost delta (PBA − Internal) per order printed to console. | No RTO/redelivery adjustment. Unmapped couriers (Shiprocket, Shadowfax, others) excluded from totals. Reads adherence base extract. |
| `scripts/2026-05-25-aggregate-courier-lane-tat-delta-v1.py` | 3.3 | courier_name × warehouse_id × drop_pincode × order_count + pba_avg_tat + internal_avg_tat + tat_delta + direction. Sorted by tat_delta ASC. Order-weighted courier-level mean delta + aggression flag (< −0.5d) printed to console. | Same-courier cohort only. Reads base extract + lane extract. No new query. |
