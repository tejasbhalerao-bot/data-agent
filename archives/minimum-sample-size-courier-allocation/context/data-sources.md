# Data Sources — Minimum Sample Size in Courier Allocation

## Local data (gitignored; list every CSV so the router can reuse it)

| File | Description | Window | Grain | Produced by | Location |
|------|-------------|--------|-------|-------------|----------|
| goi-pincode-directory.csv | GOI All India Pincode Directory, Sept 2026: district, division, state per post office | Sept 2026 snapshot | one row per post office (165,627 rows, 19,586 pincodes) | Tejas, from Google Sheets export | `raw-data/goi-pincode-directory.csv` (local only) |

## Documents and external sources

| Source | Description | Location |
|--------|-------------|----------|
| PM agent docs (read only) | The three allocation strategies' PRDs | `~/pm-agent/context/allocation/` |
| Project context | How allocation works today, as stated by Tejas | `context/2026-10-20-allocation-strategies-today-v1.md` |

## Project-specific rules
Filters, cohorts or quirks that apply only to this project. Shared rules go in `context/rules.md`.
