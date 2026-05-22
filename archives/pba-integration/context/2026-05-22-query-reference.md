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

## Base Queries

| File | Purpose |
|---|---|
| `queries-dump/2026-05-22-base-query-1-allocation-output.sql` | One row per order. Soft + Hard side-by-side. PBA + Internal partner IDs, TATs, actual delivery date, promised delivery date |
| `queries-dump/2026-05-22-base-query-2-preference-array.sql` | One row per order per courier in Clickpost preference array. Internal courier rank position, TAT comparison, scoring params |

**Query 1 date filter:** `2026-05-08` (PBA go-live)
**Query 2 date filter:** `2026-02-18` (broader — ranking signal analysis)
**Query 2 coverage note:** Excludes orders where internal courier absent from Clickpost list (`internal_actual_rank IS NOT NULL` filter). `pba_matches_rank1` always NULL in shadow mode.
