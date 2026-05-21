# data-agent — Claude Instructions

## File Creation Rules (CRITICAL)

Never create files directly in project folders using Write or Edit tools.
Always use `./workflows/scripts/new-file.sh` to create versioned files.

### Detect project from context

- If a project folder is mentioned or already active (e.g. `archives/pba/`), use that as `<project>`.
- If no project exists yet, run `cp -r archives/_template archives/<project-name>` first, then use `new-file.sh`.

### Folder → descriptor mapping

| What you're creating | `<folder>` arg | `<descriptor>` convention |
|---|---|---|
| Analysis plan doc | `analysis-plans` | `<project>-analysis-plan` |
| SQL query dump | `queries-dump` | `<project>-<topic>-query` |
| Data structuring script | `scripts` | `structure-<data-topic>` |
| Aggregates script | `scripts` | `aggregate-<topic>` |
| Insight / findings doc | `insights` | `<project>-insights` |
| Test file | `tests` | `test-<script-descriptor>` |

### Examples

```bash
./workflows/scripts/new-file.sh pba analysis-plans pba-analysis-plan md
./workflows/scripts/new-file.sh pba scripts structure-raw-shipments py
./workflows/scripts/new-file.sh pba scripts aggregate-courier-performance py
./workflows/scripts/new-file.sh pba insights pba-insights md
```

After `new-file.sh` creates the file, use Edit tool to write content into it.

---

## Repo Structure

```
data-agent/
├── workflows/
│   ├── skills/         # General Claude skills, always load at session start
│   ├── prompts/        # Reusable prompt templates
│   └── scripts/        # Helper scripts (new-file.sh etc.)
├── context/            # Global: schema docs, data dictionary, domain SOPs
├── archives/
│   └── [project]/      # One folder per analysis project
│       ├── context/    # data-sources.md + schema refs
│       ├── analysis-plans/
│       ├── queries-dump/
│       ├── raw-data/   # gitignored
│       ├── scripts/
│       ├── tests/
│       ├── outputs/    # gitignored
│       └── insights/
├── recurring/          # Scheduled / weekly analyses
├── changelogs/         # Skill amendments per session
└── scratch/            # Fully gitignored — ad-hoc work only
```

## File Naming Convention

`yyyy-mm-dd-<descriptor>-v<n>.<ext>`

Versioning is managed automatically by `new-file.sh`. Never manually name versioned files.

## Git Rules

- Push: scripts, analysis plans, query dumps, insights, context docs
- Never push: raw-data CSVs, outputs, scratch work (gitignored)
- Raw data location always documented in `archives/[project]/context/data-sources.md`
