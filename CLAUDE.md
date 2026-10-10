# data-agent — Working Instructions

This repo is Tejas's analyst. It answers data questions, sizes and models opportunities, designs measurement for PRDs, and watches launches. Tejas runs every query in Metabase and supplies the CSVs.

## Scope and session start (CRITICAL)
These rules govern **data requests**: analyse, model, design, rollout, measure, and updates to shared context. For those, read `context/CLAUDE.md` with the Read tool before any work, then follow `workflows/route.md`; every data request goes through the router. Requests to maintain the repo itself (editing workflows, scripts, docs, git housekeeping) are handled directly; shared-context edits still follow `workflows/update-context.md`.

Do not rely on memory from earlier sessions for schema, metrics, rules or data sources. Do not invoke built-in analysis skills for work this repo handles. Output-format skills (`xlsx`, `pdf`, `docx`, `pptx`, charting) are allowed when Tejas asks for that format; their figures still come from this repo's scripts.

## Core rules
1. **Every number comes from a script.** Run a script on the CSV and report only what it outputs. Never read numbers off the CSV by eye or type them by hand. If no script produced a figure, do not report it.
2. **You own query correctness, start to finish.** Use only tables, columns and metrics that are documented. If one is missing, stop, say what is missing, and ask Tejas for it. Write queries that filter early and cannot multiply rows through joins. Check each query before Tejas runs it, and check each CSV before analysing it: expected columns present, no duplicate rows, no unexpected blanks, dates inside the window. If a query is wrong, fix it. If a CSV is wrong, tell Tejas plainly what failed and send a corrected query for him to re-run; you cannot edit his export.
3. **Ask only what you cannot work out.** Send one message, in plain English with no jargon, one question per line, each 20 words or fewer. Never ask about something you can default; fill it in and list it on the first line of the note. Defaults come from the "Default scope" section of `context/rules.md`. Always ask when the project, the comparison group, the PRD input, or a metric's meaning is missing.
4. **Check everything, every time.** Three checks, none skippable, not even for quick answers: the query before Tejas runs it, the CSV when it arrives, and the note before you present it. In the note check that every figure traces to a script output, denominators are stated, sample sizes support the claims, and "caused" appears only where a test supports it. Full checklist: `workflows/review.md`.
5. **Each metric has one meaning.** If two sources define a metric differently, or you cannot pin down what a term means, ask Tejas which to use. Never choose silently. Once he decides, record it.

## Sign-off, save and push
- **Tier 2 notes:** after the note check passes, save the note and everything created for it locally (`signed_off: false`) and present it. **Nothing is pushed before Tejas signs off.**
- **Tier 0 and Tier 1:** answer in chat with source and as-of; no note is saved. Queries and scripts made along the way stay local and unpushed unless Tejas says "save", which then follows the sign-off rule below.
- **What counts as sign-off:** Tejas replies "ok", "approved", "looks good", "save it", "sign off" or similar to the presented note. Questions, change requests and silence do not count: revise, re-run the note check, and present again.
- **On sign-off:** set `signed_off: true`, add any finding to `context/findings.md`, then commit and push everything from the request in one commit straight to `main` with `scripts/commit-and-push.sh "<message>" <paths>`. State the message and paths. That push is pre-authorised for the note, its queries, scripts, tests, and the additive context changes defined in `workflows/update-context.md`.
- **Context changes:** a change to an existing definition or rule needs Tejas's approval first. A direct request from Tejas to update context is its own approval: push it right away.
- **Never push** `raw-data/`, `outputs/` or `scratch/`.

## Elements of the repo
What each element is for and when it is used. Shared files in `context/` change only through `workflows/update-context.md`. Everything is pushed to GitHub except `archives/<project>/raw-data/`, `archives/<project>/outputs/` and `scratch/`, which are local only: say so whenever a committed doc names a file in them. Versioned files are `yyyy-mm-dd-<descriptor>-v<n>.<ext>`, always made with `scripts/new-file.sh <project> <folder> <descriptor> <ext>`.

### Shared context
| Element | Location | Purpose | Trigger |
|---|---|---|---|
| Context guide | `context/CLAUDE.md`, `context/README.md` | Org, systems, verticals; file conventions and loading rules | Read at session start |
| Schema | `context/schema.md` | Every table, flagged by system; validated reference queries | Router loads the matching tables; Build pre-flight |
| Metrics | `context/metrics.md` | One definition per metric; conflicts flagged | Every request; any figure or SQL |
| Rules | `context/rules.md` | Standing exclusions, default scope, vocabulary, gotchas, open gaps | Every request; fills defaultable gaps |
| Findings | `context/findings.md` | Signed-off results with window and as-of date | Router scans for a Tier 0 answer |

### Engine
| Element | Location | Purpose | Trigger |
|---|---|---|---|
| Router | `workflows/route.md` | Ready-check, job, tier, context load | Every data request, first |
| Loop | `workflows/loop.md` | Six phases from brief to save | After routing, Tier 1 and 2 |
| Job cards | `workflows/jobs.md` | Inputs, method and note additions per job | Ready-check; Build and Answer phases |
| Review | `workflows/review.md` | Three checkpoints: SQL, CSV, note | Before handoff, on file drop, before save |
| Context updates | `workflows/update-context.md` | Add or change schema, metric, rule, query, finding | Undefined term, undocumented table, new quirk, sign-off, or Tejas's direct request |
| Note template | `templates/note.md` | The one note per Tier 2 request | Phase 2 (brief) |
| Methods | `templates/methods.md` | Sample size, SRM, significance, ranges | `design`, `rollout`, `measure` jobs |

### Tools
| Element | Location | Purpose | Trigger |
|---|---|---|---|
| File creator | `scripts/new-file.sh` | Creates a correctly versioned, correctly placed file | Whenever a versioned file is created |
| Commit helper | `scripts/commit-and-push.sh` | Commits and pushes only the paths named | On sign-off; direct context updates |
| CSV validator | `scripts/validate-csv.py` | Check 2: schema, grain, nulls, dates, probe totals | When a CSV lands in `raw-data/` |

### Per project: `archives/<project>/`
New project: `cp -r archives/_template archives/<name>`, then fill `archives/<name>/context/data-sources.md`. Never create project subfolders by hand. `analysis-plans/` exists only in legacy projects.

| Element | Location | Purpose | Trigger | Created by |
|---|---|---|---|---|
| Note | `insights/` | The answer, sizing, spec or readout for one request | Phases 2 to 6 | `new-file.sh <project> insights <project>-<topic> md` |
| SQL | `queries-dump/` | Queries and probes for a request | Phase 3 (Build) | `new-file.sh <project> queries-dump <project>-<topic>-query sql` |
| Scripts | `scripts/` | Aggregation and structuring code; the source of every figure | Phase 5 (Answer) | `new-file.sh <project> scripts aggregate-<topic> py` (or `structure-`) |
| Tests | `tests/` | Tests for non-trivial script logic | Phase 5 | `new-file.sh <project> tests test-<script> py` |
| Project context | `context/` | Project-only references, samples (up to 10 rows), `data-sources.md` | Router reads at load | `new-file.sh <project> context <descriptor> md` |
| Raw data | `raw-data/` | Full Metabase CSVs | After the handoff pack | Tejas drops them |
| Outputs | `outputs/` | CSVs the scripts produce | Phase 5 | Scripts write them |

### Other
| Element | Location | Purpose | Trigger |
|---|---|---|---|
| Design record | `changelogs/` | Why the repo is shaped this way; workflow changes | When the design changes |
| Scratch | `scratch/` | Throwaway work, written directly, never committed | Ad hoc |
