# Data Sources — Minimum Sample Size in Courier Allocation

## Local data (gitignored; list every CSV so the router can reuse it)

| File | Description | Window | Grain | Produced by | Location |
|------|-------------|--------|-------|-------------|----------|
| goi-pincode-directory.csv | GOI All India Pincode Directory, Sept 2026: district, division, state per post office | Sept 2026 snapshot | one row per post office (165,627 rows, 19,586 pincodes) | Tejas, from Google Sheets export | `raw-data/goi-pincode-directory.csv` (local only) |
| orders-2026-07.csv | Orders with a delivery attempt in the window: order id, warehouse, pincode, delivery partner, delivery attempt time, pickup time (721,987 rows) | 2026-07-01 to 2026-07-31 (delivery attempt date) | one row per order | Metabase export by Tejas (query not saved in the repo) | `raw-data/orders-2026-07.csv` (local only) |
| orders-2026-08.csv | Orders with a delivery attempt in the window: order id, warehouse, pincode, delivery partner, delivery attempt time, pickup time (724,107 rows) | 2026-08-01 to 2026-08-31 (delivery attempt date) | one row per order | Metabase export by Tejas (query not saved in the repo) | `raw-data/orders-2026-08.csv` (local only) |
| orders-2026-09.csv | Orders with a delivery attempt in the window: order id, warehouse, pincode, delivery partner, delivery attempt time, pickup time (755,221 rows) | 2026-09-01 to 2026-09-30 (delivery attempt date) | one row per order | Metabase export by Tejas (query not saved in the repo) | `raw-data/orders-2026-09.csv` (local only) |
| orders-2026-10.csv | Orders with a delivery attempt in the window: order id, warehouse, pincode, delivery partner, delivery attempt time, pickup time (494,814 rows) | 2026-10-01 to 2026-10-19 (delivery attempt date) | one row per order | Metabase export by Tejas (query not saved in the repo) | `raw-data/orders-2026-10.csv` (local only) |

## Documents and external sources

| Source | Description | Location |
|--------|-------------|----------|
| PM agent docs (read only) | The three allocation strategies' PRDs | `~/pm-agent/context/allocation/` |
| Project context | How allocation works today, as stated by Tejas | `context/2026-10-20-allocation-strategies-today-v1.md` |

## Project-specific rules
Filters, cohorts or quirks that apply only to this project. Shared rules go in `context/rules.md`.
