# data-agent — Claude Instructions

---

## 1. Session Start (CRITICAL)

Before any work in every session:

1. Read all files in `context/` — global schema, data dictionary, domain SOPs
2. If a project is active or mentioned — read all files in `archives/[project]/context/`

Do not proceed until both layers are loaded. Never rely on memory from prior sessions for schema, pricing, cutoffs, or data-source structure.

---

## 2. Skill Routing

Load and follow the listed skill when the request matches. Do not improvise the workflow.

| Tejas wants to... | Invoke |
|---|---|
| Run any analysis — exploratory, post-release, one-time, recurring | `workflows/skills/plan-builder.md` |
| Review / refine an existing plan | `workflows/skills/plan-refiner.md` |
| Map tables and define output schema from an approved plan | `workflows/skills/table-mapper.md` |
| Write SQL queries from an approved data spec | `workflows/skills/query-builder.md` |
| A query timed out in Metabase — split and retry | `workflows/skills/query-builder.md` (re-entry: timed out) |
| Discover or validate a table not in `context/schema.md` | `workflows/skills/schema-discovery.md` |

### Analysis pipeline (invoked in order after plan-builder)

```
plan-builder → plan-refiner → [Tejas approval] → table-mapper → query-builder
→ data-validator → script-builder → output-validator → analysis-runner
→ insights-runner → loop-runner
```

**Chaining rules:**
- `plan-refiner` always runs after `plan-builder` — never hand plan to Tejas directly from plan-builder
- Each skill hands off to the next only when its own completion criteria are met
- Do not skip steps — if a skill is not yet built, stop and flag to Tejas

---

## 3. New Project Setup (CRITICAL)

When a project has no folder in `archives/` yet:

1. Run: `cp -r archives/_template archives/<project-name>`
2. Edit `archives/<project-name>/context/data-sources.md` with known sources
3. Then proceed — never create project subfolders manually

---

## 4. File Routing (CRITICAL)

Where every file goes. No exceptions.

| Creating... | Destination | Tool |
|---|---|---|
| Analysis plan doc | `archives/[project]/analysis-plans/` | `new-file.sh` |
| SQL query written or exported from Metabase | `archives/[project]/queries-dump/` | `new-file.sh` |
| Python/shell script (structure or aggregate) | `archives/[project]/scripts/` | `new-file.sh` |
| Test file for a script | `archives/[project]/tests/` | `new-file.sh` |
| Findings doc with interpreted results | `archives/[project]/insights/` | `new-file.sh` |
| Schema ref, sample CSV (≤10 rows), config/pricing/query ref doc | `archives/[project]/context/` | `new-file.sh` |
| `data-sources.md` manifest | `archives/[project]/context/data-sources.md` | Edit existing |
| Full CSV export from Metabase (real data) | `archives/[project]/raw-data/` | Drop manually — gitignored |
| CSV produced by running a script | `archives/[project]/outputs/` | Script writes here — gitignored |
| Validated reusable SQL (confirmed correct in Metabase) | `context/reference-queries/` | `new-file.sh` project `_context` |
| Redshift schema update | `context/schema.md` | Edit existing |
| Skill SOP | `workflows/skills/` | Write tool directly |
| Session changelog / skill amendment | `changelogs/` | Write tool directly |
| Throwaway / ad-hoc work | `scratch/` | Write directly, never commit |

### Hard rules

- `raw-data/` and `outputs/` are gitignored — never reference their filenames in committed docs without noting they are local-only
- `context/` (global) = cross-project. `archives/[project]/context/` = project-specific. Never mix.
- Sample data (≤10 rows) → `archives/[project]/context/`. Full exports → `archives/[project]/raw-data/`.
- `queries-dump/` = SQL only. `scripts/` = Python/shell only. Never mix.

### File naming

`yyyy-mm-dd-<descriptor>-v<n>.<ext>` — managed by `new-file.sh`. Never name versioned files manually.

### `new-file.sh` descriptor conventions

| Folder | Descriptor pattern |
|---|---|
| `analysis-plans` | `<project>-analysis-plan` |
| `queries-dump` | `<project>-<topic>-query` |
| `scripts` | `structure-<topic>` or `aggregate-<topic>` |
| `insights` | `<project>-insights` |
| `tests` | `test-<script-descriptor>` |
| `context` | `<descriptive-name>` (e.g. `courier-pricing-snapshot`) |

```bash
# Examples
./workflows/scripts/new-file.sh pba analysis-plans pba-analysis-plan md
./workflows/scripts/new-file.sh pba scripts structure-raw-shipments py
./workflows/scripts/new-file.sh pba insights pba-insights md
./workflows/scripts/new-file.sh pba context courier-pricing-snapshot md
./workflows/scripts/new-file.sh _context reference-queries allocation-audit-base sql
```

After `new-file.sh` creates the file, use Edit tool to write content into it.

---

## 5. Schema Rules (CRITICAL)

### Before writing any SQL or script

1. Read `context/schema.md`
2. Check every referenced table against documented tables
3. If any table is missing — stop and invoke `workflows/skills/schema-discovery.md`
4. Do not proceed until discovery is approved by Tejas and pushed to GitHub

Never infer schema from memory, prior sessions, or column name guesses.

### After every Metabase session

Before ending the conversation:

1. Check if any new tables, columns, joins, or data behaviour was discovered
2. If yes — update `context/schema.md`:
   - Add new table section if missing
   - Add new columns to existing table if missing
   - Add row to **Discovered Quirks & Gotchas** if behaviour was unexpected
3. If a query proved reusable — save to `context/reference-queries/`:
   ```bash
   ./workflows/scripts/new-file.sh _context reference-queries <query-descriptor> sql
   ```

Schema updates are not optional. Every Metabase run that reveals something new must update the doc.

---

## 6. Git Rules

- **Push:** scripts, analysis plans, query dumps, insights, context docs, skills, changelogs
- **Never push:** raw-data CSVs, outputs, scratch work (gitignored)
- Raw data location always documented in `archives/[project]/context/data-sources.md`

---

## 7. Repo Structure

```
data-agent/
├── context/                  # Global: schema.md, reference-queries/
├── workflows/
│   ├── skills/               # Analysis SOPs — invoked on demand, not at session start
│   ├── prompts/              # Reusable prompt templates
│   └── scripts/              # new-file.sh and other repo helpers
├── archives/
│   ├── _template/            # Skeleton — copy to create new project
│   └── [project]/
│       ├── context/          # Project schema refs, samples, configs
│       ├── analysis-plans/
│       ├── queries-dump/
│       ├── scripts/
│       ├── tests/
│       ├── raw-data/         # gitignored
│       ├── outputs/          # gitignored
│       └── insights/
├── recurring/                # Scheduled / weekly analyses
├── changelogs/               # Skill amendments per session
└── scratch/                  # Fully gitignored
```
