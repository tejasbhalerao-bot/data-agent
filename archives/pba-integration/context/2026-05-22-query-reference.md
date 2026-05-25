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
