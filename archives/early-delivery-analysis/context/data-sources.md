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

- **Outcome metric:** day-level. `offset = date(delivery_attempt_time) − date(digitised_delivery_promise)`; ≤−1 Early, 0 On-Time, ≥+1 Late.
- **Instrumentation cutover:** digitised SDD/MFC/inventory/category state only populated from **8 May 2026**. Segmented analysis restricted to `digitised_ts >= 2026-05-08`.
- **Vertical:** `digitised_is_sdd` → Hyperlocal (true) / Courier (false).
- **WH type:** `digitised_is_mfc` → MFC (true) / FC (false).
- **Doctor-leg band:** exact sign, ±1-min buffer.
