# data-agent

Truemeds data analysis workflows, scripts, and insights.

## Structure

```
data-agent/
├── workflows/
│   ├── skills/         # General Claude skills, always invoked at session start
│   └── prompts/        # Reusable prompt templates for analysis steps
├── context/            # Global: schema docs, data dictionary, Truemeds domain SOPs
├── archives/
│   └── [project]/      # One folder per structured analysis project
│       ├── context/        # Project-specific schema refs, sample rows, notes
│       ├── analysis-plans/ # Analysis plan docs
│       ├── queries-dump/   # SQL queries written for this analysis
│       ├── raw-data/       # Sample raw data (gitignored for large files)
│       ├── scripts/        # Data structuring + aggregate scripts
│       ├── tests/          # Script tests
│       ├── outputs/        # Script run results (gitignored for large files)
│       └── insights/       # Final interpreted findings
├── recurring/          # Scheduled/weekly analyses (KPI monitors, recurring reports)
├── changelogs/         # Session-by-session amendments to skills
└── scratch/            # Ad-hoc, anomaly investigations (gitignored)
```

## File Naming

All versioned files: `yyyy-mm-dd-<descriptor>.<ext>`

Examples:
- `2026-05-21-pba-analysis-plan.md`
- `2026-05-21-structure-raw-shipments.py`
- `2026-05-21-aggregate-courier-performance.sql`

## Workflow (Structured Analysis)

1. Create `archives/[project]/`
2. Drop schema ref + sample rows in `archives/[project]/context/`
3. Build analysis plan → `analysis-plans/`
4. Write/dump queries → `queries-dump/`
5. Push sample raw data → `raw-data/`
6. Write structuring script → `scripts/`
7. Write aggregates script → `scripts/`
8. Test both → `tests/`
9. Run scripts, save outputs → `outputs/`
10. Interpret findings → `insights/`
