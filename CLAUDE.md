# data-agent — Claude Instructions

## File Creation Rules (CRITICAL)

Never create files directly in project folders using Write or Edit tools.
Always use `./workflows/scripts/new-file.sh` to create versioned files.
Exception: `workflows/skills/` and `changelogs/` — Write tool allowed directly (non-data files).

---

## New Project Setup (CRITICAL)

When starting a project with no existing folder in `archives/`:

1. Run: `cp -r archives/_template archives/<project-name>`
2. Edit `archives/<project-name>/context/data-sources.md` with known sources
3. Then proceed — never create project subfolders manually

---

## File Routing Table (CRITICAL)

Where every file goes. No exceptions.

| You are creating... | Destination | Tool |
|---|---|---|
| Analysis plan doc | `archives/[project]/analysis-plans/` | `new-file.sh` |
| SQL query written or exported from Metabase | `archives/[project]/queries-dump/` | `new-file.sh` |
| Python/shell script that structures or aggregates data | `archives/[project]/scripts/` | `new-file.sh` |
| Test file for a script | `archives/[project]/tests/` | `new-file.sh` |
| Findings doc with interpreted results | `archives/[project]/insights/` | `new-file.sh` |
| Schema ref, sample CSV (≤10 rows), config snapshot, query reference doc, pricing doc | `archives/[project]/context/` | `new-file.sh` |
| `data-sources.md` manifest | `archives/[project]/context/data-sources.md` | Edit existing |
| Full CSV export from Metabase (real data) | `archives/[project]/raw-data/` | Drop manually — gitignored, bypass `new-file.sh` |
| CSV produced by running a script | `archives/[project]/outputs/` | Script writes here — gitignored |
| Validated reusable SQL (confirmed correct in Metabase) | `context/reference-queries/` | `new-file.sh` with project `_context` |
| Redshift schema update | `context/schema.md` | Edit existing |
| Skill SOP (how Claude does a class of work) | `workflows/skills/` | Write tool directly |
| Session changelog / skill amendment | `changelogs/` | Write tool directly |
| Throwaway / ad-hoc work | `scratch/` | Write directly, never commit |

### Hard rules

- `raw-data/` and `outputs/` are gitignored — never reference their filenames in committed docs without noting they are local-only
- `context/` (global) = cross-project knowledge. `archives/[project]/context/` = project-specific knowledge. Never mix.
- Sample data (≤10 rows) → `archives/[project]/context/`. Full exports → `archives/[project]/raw-data/`.
- `queries-dump/` = SQL only. `scripts/` = Python/shell only. Never mix.

### `new-file.sh` descriptor conventions

| Folder | `<descriptor>` convention |
|---|---|
| `analysis-plans` | `<project>-analysis-plan` |
| `queries-dump` | `<project>-<topic>-query` |
| `scripts` | `structure-<topic>` or `aggregate-<topic>` |
| `insights` | `<project>-insights` |
| `tests` | `test-<script-descriptor>` |
| `context` | `<descriptive-name>` (e.g. `courier-pricing-snapshot`) |

### Examples

```bash
./workflows/scripts/new-file.sh pba analysis-plans pba-analysis-plan md
./workflows/scripts/new-file.sh pba scripts structure-raw-shipments py
./workflows/scripts/new-file.sh pba scripts aggregate-courier-performance py
./workflows/scripts/new-file.sh pba insights pba-insights md
./workflows/scripts/new-file.sh pba context courier-pricing-snapshot md
./workflows/scripts/new-file.sh _context reference-queries allocation-audit-base sql
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

## Context Loading Rules (CRITICAL)

At the start of every session, before any analysis, query, schema design, or script planning:

1. Read all files in `context/` (global schema docs, data dictionary, domain SOPs)
2. If a project folder is active or mentioned — read all files in `archives/[project]/context/`

Do not proceed with any work until both context layers are loaded. Never rely on memory from prior sessions for schema, pricing, cutoffs, or data-source structure — always read the files.

---

## Schema Discovery Rules (CRITICAL)

Before writing any SQL query or data script:

1. Read `context/schema.md`
2. Check every table referenced against the documented tables list
3. If any table is **not documented** — stop all work and invoke `workflows/skills/schema-discovery.md`
4. Do not proceed until discovery is complete, approved by Tejas, and pushed to GitHub

Never infer schema from memory, prior sessions, or column name guesses.

---

## Schema Update Rules (CRITICAL)

After every Metabase session, before ending the conversation:

1. Check if any new tables, columns, joins, or data behaviour was discovered
2. If yes — update `context/schema.md`:
   - Add new table section if table not yet documented
   - Add new columns to existing table if missing
   - Add row to **Discovered Quirks & Gotchas** table if behaviour was unexpected
3. If a query proved reusable (fast-fetch pattern, validated join) — save it to `context/reference-queries/` using `new-file.sh`:
   ```bash
   ./workflows/scripts/new-file.sh _context reference-queries <query-descriptor> sql
   ```
   > Note: reference-queries uses `_context` as the project name since it lives outside archives.

Schema updates are not optional. Every Metabase run that reveals something new must update the doc.

---

## Git Rules

- Push: scripts, analysis plans, query dumps, insights, context docs
- Never push: raw-data CSVs, outputs, scratch work (gitignored)
- Raw data location always documented in `archives/[project]/context/data-sources.md`
