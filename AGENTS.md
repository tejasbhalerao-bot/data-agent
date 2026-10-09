# data-agent — Codex Instructions

This repo is Tejas's analyst. It answers data questions, sizes and models opportunities, designs measurement for PRDs, and watches launches. Tejas runs every query in Metabase and supplies the CSVs.

## Session start (CRITICAL)
Read `context/CLAUDE.md` with the Read tool before any work, then follow `workflows/route.md`. Every request goes through the router. Do not rely on memory from earlier sessions for schema, metrics, rules or data sources, and do not invoke built-in `data:*` or `anthropic-skills:*` skills for work this repo handles.

## Where things live
```
context/            shared knowledge: CLAUDE.md, data/<system>.md, metrics.md, rules.md, queries/, findings.md
workflows/          route.md, loop.md, jobs.md, review.md, update-context.md
templates/          note.md, methods.md
scripts/            new-file.sh, commit-and-push.sh, validate-csv.py
archives/<project>/ context/ queries-dump/ scripts/ tests/ insights/ raw-data/ outputs/ (analysis-plans/ only in legacy projects)
changelogs/         design records and skill-level changes
scratch/            throwaway work, never committed
```

## File routing (no exceptions)
| Creating | Destination | Tool |
|---|---|---|
| A note (answer, sizing, spec, readout) | `archives/<project>/insights/` | `scripts/new-file.sh <project> insights <project>-<topic> md` |
| SQL | `archives/<project>/queries-dump/` | `new-file.sh <project> queries-dump <project>-<topic>-query sql` |
| Python or shell | `archives/<project>/scripts/` | `new-file.sh <project> scripts aggregate-<topic> py` (or `structure-`) |
| Script test | `archives/<project>/tests/` | `new-file.sh <project> tests test-<script> py` |
| Project-only reference or sample (up to 10 rows) | `archives/<project>/context/` | `new-file.sh` |
| Full CSV from Metabase | `archives/<project>/raw-data/` | Tejas drops it; gitignored |
| CSV a script produces | `archives/<project>/outputs/` | Script writes it; gitignored |
| Shared schema, definition, rule, query, finding | `context/` | `workflows/update-context.md` |
| Anything throwaway | `scratch/` | Write directly |

New project: `cp -r archives/_template archives/<name>`, then fill `context/data-sources.md`. Never create project subfolders by hand. Versioned files are `yyyy-mm-dd-<descriptor>-v<n>.<ext>`, always through `new-file.sh`. `raw-data/` and `outputs/` are local only: say so whenever a committed doc names a file in them.

## Core rules
1. **Figures come from code.** Never read numbers off a CSV by eye; the note's figures come from a script output.
2. **Query correctness has one owner:** loop phase 3 (`build-sql`). Pre-flight against `context/data/` and `context/metrics.md`, review before handoff, validate the CSV after. An undocumented table or metric is a hard stop.
3. **Ask only what context cannot answer.** One batched message of blocking gaps; fill defaultable gaps from `context/rules.md` and list them in the note.
4. **Review always runs** (`workflows/review.md`); it cannot be skipped.
5. **Metrics have one definition.** Conflicting variants are asked, not guessed.

## Save and push
After Check 3 passes, save and push the note immediately with `scripts/commit-and-push.sh "<message>" <paths>`, `signed_off: false`. Say the message and paths. This is pre-authorised for notes, queries, scripts, tests and the additive context changes defined in `workflows/update-context.md`. Changes to an existing definition or rule wait for Tejas's approval. Tejas's sign-off sets `signed_off: true` and gates additions to `context/findings.md`. Never push `raw-data/`, `outputs/` or `scratch/`.
