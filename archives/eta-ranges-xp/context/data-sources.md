# Data Sources — [project-name]

## Local data (gitignored; list every CSV so the router can reuse it)

| File | Description | Window | Grain | Produced by | Location |
|------|-------------|--------|-------|-------------|----------|
| example.csv | What it holds | 2026-07-01 to 2026-07-31 | one row per order | `queries-dump/<file>.md` or Metabase export | `raw-data/example.csv` (local only) |

## Documents and external sources

| Source | Description | Location |
|--------|-------------|----------|
| PRD / sheet / Mixpanel | What it holds | link |

## Project-specific rules
Filters, cohorts or quirks that apply only to this project. Shared rules go in `context/rules.md`.

## ETA-E3 sources (2026-10-26)
| File | Description | Window | Grain | Produced by | Location |
|------|-------------|--------|-------|-------------|----------|
| mixpanel-etaranges-dashboard-counts-2026-10-26.csv | Users per variant at each funnel step | 2026-09-19 to 2026-10-26 | one row per report per variant | `queries-dump/2026-10-26-eta-ranges-xp-mixpanel-pull-query-v1.md` | `raw-data/` (local only) |
| PRD ETA-E3 | https://docs.google.com/document/d/1e7xGH5lQyy4Fd_lz4eP3tKfuKks7seSk38kIg-2h4Ms | | | | Google Docs |
| Mixpanel dashboard "ETA Ranges XP" | project 2900163, dashboard 11537748 | | | | Mixpanel |
