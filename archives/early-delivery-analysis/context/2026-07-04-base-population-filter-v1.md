# Base Population Filter — Early Delivery Analysis

Locked base population for all analysis on `early-delivery-raw-may-2026.csv`. Every script/query in this project must apply both filters before computing metrics.

## Source

`archives/early-delivery-analysis/raw-data/early-delivery-raw-may-2026.csv` (local only, gitignored)

## Rules

1. `digitised_ts` strictly after **8th May 2026** (index all "post-cutoff" logic on this column, not `dr_confirm_ts` or any other timestamp)
2. `delivery_attempt_time` is not null (order must have an actual delivery attempt recorded)

## Result (as of 2026-07-04)

| Stage | Rows | % of total |
|---|---|---|
| Total rows | 813,499 | 100% |
| + digitised_ts > 8 May 2026 | 624,288 | 76.7% |
| + delivery_attempt_time not null | **522,808** | **64.3%** |

## Enforcement

Reusable filter script: `archives/early-delivery-analysis/scripts/2026-07-04-structure-base-population-filter-v1.py`

Run once to produce the locked base population file:

```bash
python3 archives/early-delivery-analysis/scripts/2026-07-04-structure-base-population-filter-v1.py
```

Output: `archives/early-delivery-analysis/outputs/base-population.csv` (gitignored — regenerate from raw-data as needed).

All downstream analysis scripts in this project should read from `outputs/base-population.csv`, not the raw file directly.
