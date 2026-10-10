# data-agent — Codex Instructions

This repo is Tejas's analyst. It answers data questions, sizes and models opportunities, designs measurement for PRDs, and watches launches. Tejas runs every query in Metabase and supplies the CSVs.

## Session start (CRITICAL)
Read `context/CLAUDE.md` with the Read tool before any work, then follow `workflows/route.md`. Every request goes through the router. Do not rely on memory from earlier sessions for schema, metrics, rules or data sources, and do not invoke built-in analysis skills for work this repo handles (output-format skills such as `xlsx`, `pdf`, `docx`, `pptx` and charting are allowed when Tejas asks for that format; their figures still come from this repo's scripts).

## Where things live
```
context/            shared knowledge: CLAUDE.md, schema.md, metrics.md, rules.md, findings.md
workflows/          route.md, loop.md, jobs.md, review.md, update-context.md
templates/          note.md, methods.md
scripts/            new-file.sh, commit-and-push.sh, validate-csv.py
archives/<project>/ context/ queries-dump/ scripts/ tests/ insights/ raw-data/ outputs/ (analysis-plans/ only in legacy projects)
changelogs/         design records and workflow changes
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

New project: `cp -r archives/_template archives/<name>`, then fill `archives/<name>/context/data-sources.md`. Never create project subfolders by hand. Versioned files are `yyyy-mm-dd-<descriptor>-v<n>.<ext>`, always through `new-file.sh`. `raw-data/` and `outputs/` are local only: say so whenever a committed doc names a file in them.

## Core rules
1. **Figures come from code.** Never read numbers off a CSV by eye; the note's figures come from a script output.
2. **Query correctness has one owner:** the Build phase of `workflows/loop.md` (phase 3). Pre-flight against `context/schema.md` and `context/metrics.md`, review before handoff, validate the CSV after. An undocumented table or metric is a hard stop.
3. **Ask only what context cannot answer.** One batched message of blocking gaps; fill defaultable gaps from `context/rules.md` and list them in the note.
4. **Review always runs** (`workflows/review.md`); it cannot be skipped.
5. **Metrics have one definition.** Conflicting variants are asked, not guessed.

## Save and push
After Check 3 passes, save the note and everything created for it locally (`signed_off: false`) and present it. **Nothing is pushed before Tejas signs off.** On sign-off, set `signed_off: true` and commit and push in one commit straight to `main` with `scripts/commit-and-push.sh "<message>" <paths>`; say the message and paths. That push is pre-authorised for the note, its queries, scripts, tests, and the additive context changes defined in `workflows/update-context.md`. A change to an existing definition or rule needs Tejas's approval first. Sign-off also gates additions to `context/findings.md`. A request from Tejas to update context directly is its own approval: push it right away. Never push `raw-data/`, `outputs/` or `scratch/`.
