# data-agent — Codex Instructions

This repo is Tejas's analyst. It answers data questions, sizes and models opportunities, designs measurement for PRDs, and watches launches. Tejas runs every query in Metabase and supplies the CSVs.

## Session start (CRITICAL)
Read `context/CLAUDE.md` with the Read tool before any work, then follow `workflows/route.md`. Every request goes through the router. Do not rely on memory from earlier sessions for schema, metrics, rules or data sources, and do not invoke built-in analysis skills for work this repo handles (output-format skills such as `xlsx`, `pdf`, `docx`, `pptx` and charting are allowed when Tejas asks for that format; their figures still come from this repo's scripts).

## Elements of the repo
Every element, where it sits, what it is for, when it is used, who creates it, and whether it is pushed. "Created by" is the file-routing rule: no exceptions. Versioned files are `yyyy-mm-dd-<descriptor>-v<n>.<ext>`, always made with `scripts/new-file.sh <project> <folder> <descriptor> <ext>`.

### Entry and shared context
| Element | Location | Purpose | Trigger | Created by | Git |
|---|---|---|---|---|---|
| Working rules | `CLAUDE.md` (and `AGENTS.md`, a copy) | Rules, element map, save rule | Read at every session start | Tejas | Pushed |
| Context guide | `context/CLAUDE.md`, `context/README.md` | Org, systems, verticals; file conventions and loading rules | Read first by the router | Tejas | Pushed |
| Schema | `context/schema.md` | Every table, flagged by system; validated reference queries | Router loads the matching tables; Build phase pre-flight | `update-context.md` | Pushed |
| Metrics | `context/metrics.md` | One definition per metric; conflicts flagged | Every request; any figure or SQL | `update-context.md` | Pushed |
| Rules | `context/rules.md` | Standing exclusions, default scope, vocabulary, gotchas, open gaps | Every request; fills defaultable gaps | `update-context.md` | Pushed |
| Findings | `context/findings.md` | Signed-off results with window and as-of date | Router scans for a Tier 0 answer | `update-context.md`, after sign-off | Pushed |

### Engine
| Element | Location | Purpose | Trigger | Created by | Git |
|---|---|---|---|---|---|
| Router | `workflows/route.md` | Ready-check, job, tier, context load | Every request, first | Tejas | Pushed |
| Loop | `workflows/loop.md` | Six phases from brief to save | After routing, every tier above 0 | Tejas | Pushed |
| Job cards | `workflows/jobs.md` | Inputs, method and note additions per job | Ready-check; the Build and Answer phases | Tejas | Pushed |
| Review | `workflows/review.md` | Three checkpoints: SQL, CSV, note | Before handoff, on file drop, before save | Tejas | Pushed |
| Context updates | `workflows/update-context.md` | Add or change schema, metric, rule, query, finding | Undefined term, undocumented table, new quirk, sign-off, or Tejas's direct request | Tejas | Pushed |
| Note template | `templates/note.md` | The one note per request | Phase 2 (brief) | Tejas | Pushed |
| Methods | `templates/methods.md` | Sample size, SRM, significance, ranges | `design`, `rollout` and `measure` jobs | Tejas | Pushed |

### Tools
| Element | Location | Purpose | Trigger | Created by | Git |
|---|---|---|---|---|---|
| File creator | `scripts/new-file.sh` | Creates a correctly versioned, correctly placed file | Whenever a versioned file is created | Tejas | Pushed |
| Commit helper | `scripts/commit-and-push.sh` | Commits and pushes only the paths named | On sign-off; direct context updates | Tejas | Pushed |
| CSV validator | `scripts/validate-csv.py` | Check 2: schema, grain, nulls, dates, probe totals | When a CSV lands in `raw-data/` | Tejas | Pushed |

### Per project: `archives/<project>/`
New project: `cp -r archives/_template archives/<name>`, then fill `archives/<name>/context/data-sources.md`. Never create project subfolders by hand.

| Element | Location | Purpose | Trigger | Created by | Git |
|---|---|---|---|---|---|
| Note | `insights/` | The answer, sizing, spec or readout for one request | Phases 2 to 6 | `new-file.sh <project> insights <project>-<topic> md` | Pushed on sign-off |
| SQL | `queries-dump/` | Queries and probes for a request | Phase 3 (Build) | `new-file.sh <project> queries-dump <project>-<topic>-query sql` | Pushed on sign-off |
| Scripts | `scripts/` | Aggregation and structuring code; the source of every figure | Phase 5 (Answer) | `new-file.sh <project> scripts aggregate-<topic> py` (or `structure-`) | Pushed on sign-off |
| Tests | `tests/` | Tests for non-trivial script logic | Phase 5 | `new-file.sh <project> tests test-<script> py` | Pushed on sign-off |
| Project context | `context/` | Project-only references, samples (up to 10 rows), `data-sources.md` | Router reads at load; new project setup | `new-file.sh <project> context <descriptor> md` | Pushed |
| Raw data | `raw-data/` | Full Metabase CSVs | Tejas drops them after the handoff pack | Tejas | Local only |
| Outputs | `outputs/` | CSVs the scripts produce | Phase 5 | Scripts write them | Local only |

`raw-data/` and `outputs/` are local only: say so whenever a committed doc names a file in them. `analysis-plans/` exists only in legacy projects.

### Other
| Element | Location | Purpose | Trigger | Created by | Git |
|---|---|---|---|---|---|
| Design record | `changelogs/` | Why the repo is shaped this way; workflow changes | When the design changes | Written directly | Pushed |
| Scratch | `scratch/` | Throwaway work | Ad hoc | Written directly | Never |

## Core rules
1. **Figures come from code.** Never read numbers off a CSV by eye; the note's figures come from a script output.
2. **Query correctness has one owner:** the Build phase of `workflows/loop.md` (phase 3). Pre-flight against `context/schema.md` and `context/metrics.md`, review before handoff, validate the CSV after. An undocumented table or metric is a hard stop.
3. **Ask only what context cannot answer.** One batched message of blocking gaps; fill defaultable gaps from `context/rules.md` and list them in the note.
4. **Review always runs** (`workflows/review.md`); it cannot be skipped.
5. **Metrics have one definition.** Conflicting variants are asked, not guessed.

## Save and push
After Check 3 passes, save the note and everything created for it locally (`signed_off: false`) and present it. **Nothing is pushed before Tejas signs off.** On sign-off, set `signed_off: true` and commit and push in one commit straight to `main` with `scripts/commit-and-push.sh "<message>" <paths>`; say the message and paths. That push is pre-authorised for the note, its queries, scripts, tests, and the additive context changes defined in `workflows/update-context.md`. A change to an existing definition or rule needs Tejas's approval first. Sign-off also gates additions to `context/findings.md`. A request from Tejas to update context directly is its own approval: push it right away. Never push `raw-data/`, `outputs/` or `scratch/`.
