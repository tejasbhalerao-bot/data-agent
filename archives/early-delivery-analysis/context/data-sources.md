# Data Sources — early-delivery-analysis

## Raw data (gitignored — local only)

| File | Description | Location |
|------|-------------|----------|
| `early-delivery-raw-may-2026.csv` | Base extract, one row per order, May 2026 cohort. 813,499 rows × 29 cols. Provided by Tejas (Metabase export "Early Delivery Raw 1 May.csv"). | `archives/early-delivery-analysis/raw-data/` (local only — 260 MB, exceeds GitHub limits) |

> Raw CSV is gitignored (`archives/*/raw-data/*.csv`) and not pushed. Re-obtain from the
> Metabase extract or re-run the query in `queries-dump/`.

## Query

| File | Description |
|------|-------------|
| `queries-dump/2026-06-16-early-delivery-base-extract-v1.sql` | Source SQL for the base extract (pivots order_status N→1, 1:1 joins). |

## Derived inputs

| Input | Source | Notes |
|-------|--------|-------|
| Destination city | `pgeocode` (GeoNames India, offline) | `city = county_name` from `digitised_delivery_pincode`. NOT a Truemeds canonical pincode→city master. |

## Outputs (gitignored — local only)

Script outputs land in `archives/early-delivery-analysis/outputs/*.csv` (gitignored). Regenerate by
running the scripts in `scripts/` against the raw CSV.

## Key scope decisions (locked)

- **View 1 / View 2 cascade (MANDATORY definitions for Doctor/Warehouse/Dispatch/Delivery leg classification):** full rules, cuts, and final N in [`2026-07-04-view1-view2-cascade-definitions-v1.md`](2026-07-04-view1-view2-cascade-definitions-v1.md). Script: `scripts/2026-07-04-aggregate-view-cascade-v1.py`.
- **Base population (MANDATORY, applies to every script/query in this project):** `digitised_ts > 8 May 2026` AND `delivery_attempt_time` not null → 522,808 of 813,499 rows (64.3%). Full detail in [`2026-07-04-base-population-filter-v1.md`](2026-07-04-base-population-filter-v1.md). Reusable filter: `scripts/2026-07-04-structure-base-population-filter-v1.py` → `outputs/base-population.csv`. Every new script/query must read from this filtered set, not the raw file directly.
- **Outcome metric:** day-level. `offset = date(delivery_attempt_time) − date(digitised_delivery_promise)`; ≤−1 Early, 0 On-Time, ≥+1 Late.
- **Instrumentation cutover:** digitised SDD/MFC/inventory/category state only populated from **8 May 2026**. Segmented analysis restricted to `digitised_ts >= 2026-05-08`.
- **Vertical:** `digitised_is_sdd` → Hyperlocal (true) / Courier (false).
- **WH type:** `digitised_is_mfc` → MFC (true) / FC (false).
- **Doctor-leg band:** exact sign, ±1-min buffer.

## Discovered quirks & gotchas

- **`shipping_delivery_promise` is an integer TAT in days** (the delivery TAT promised by the courier selected at shipping time), NOT an absolute timestamp — unlike `digitised_delivery_promise`, which is a timestamp. The comparable digitised-side quantity is a derived TAT: `date(digitised_delivery_promise) − date(digitised_dispatch_promise)`, not `digitised_delivery_promise` itself. Do not compare these two columns directly.
- **`digitised_is_sdd`/`digitised_is_inventory` use `true`/`false` strings; `shipping_is_sdd` uses `1`/`0`; `shipping_is_inventory` uses `true`/`false`.** Normalize before comparing digitised vs shipping boolean state (`{"true":True,"1":True,"false":False,"0":False}`).
- **`digitised_delivery_partner` has ~4.8% blanks** in the base population; `shipping_delivery_partner` is essentially always populated. Treat blank-digitised-partner orders as indeterminate for any courier-switch check, not as "no switch."
