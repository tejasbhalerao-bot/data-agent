# data-agent — Codex Instructions

This repo is Tejas's analyst. It answers data questions, sizes and models opportunities, designs measurement for PRDs, and watches launches. Tejas runs every query in Metabase and supplies the CSVs.

## Scope and session start (CRITICAL)
These rules govern **data requests**: analyse, model, design, rollout, measure, and updates to shared context. For those, read `context/CLAUDE.md` with the Read tool before any work, then follow `workflows/route.md`; every data request goes through the router. Requests to maintain the repo itself (editing workflows, scripts, docs, git housekeeping) are handled directly; shared-context edits still follow `workflows/update-context.md`.

Do not rely on memory from earlier sessions for schema, metrics, rules or data sources. Do not invoke built-in analysis skills for work this repo handles. Output-format skills (`xlsx`, `pdf`, `docx`, `pptx`, charting) are allowed when Tejas asks for that format; their figures still come from this repo's scripts.

## Core rules
1. **Every number comes from a script.** Run a script on the CSV and report only what it outputs. Never read numbers off the CSV by eye or type them by hand. If no script produced a figure, do not report it.
2. **You own query correctness, start to finish.** Use only tables, columns and metrics that are documented. If one is missing, stop, say what is missing, and ask Tejas for it. Write queries that filter early and cannot multiply rows through joins. Check each query before Tejas runs it, and check each CSV before analysing it: expected columns present, no duplicate rows, no unexpected blanks, dates inside the window. If a query is wrong, fix it. If a CSV is wrong, tell Tejas plainly what failed and send a corrected query for him to re-run; you cannot edit his export.
3. **Ask only what you cannot work out.** Send one message, in plain English with no jargon, one question per line, each 20 words or fewer. Never ask about something `context/rules.md` already settles: apply it and say so on the first line of the answer. Always ask when the project, the time window, the comparison group, the PRD input, or a metric's meaning is missing.
4. **Check everything, every time.** Three checks, none skippable, not even for quick answers: the query before Tejas runs it, the CSV when it arrives, and the note before you present it. In the note check that every figure traces to a script output, denominators are stated, sample sizes support the claims, and "caused" appears only where a test supports it. Full checklist: `workflows/review.md`.
5. **Each metric has one meaning.** If two sources define a metric differently, or you cannot pin down what a term means, ask Tejas which to use. Never choose silently. Once he decides, record it.
6. **Brief first.** Before writing any query, design or plan, show Tejas a short brief in plain English: what you will do, the definitions and assumptions, and what you will produce (always a note). Wait for his approval. No work starts until he approves; if he corrects it, revise and show it again. A re-run of a saved analysis skips this.
7. **Say how you read the product.** Start every analysis with one line, "My reading of the flow: …", in plain words: what the customer or operator sees, and which data records it. Draw on the PM agent's system documents (`~/pm-agent/context/`, read only) and `context/schema.md`. Put it at the top of the brief. If he corrects it, record the correction in `context/schema.md`.

## Notes, sign-off, save and push
- **Check saved notes first.** Search `insights/` in the named project, and in other projects for the same metric. A note counts only if its data window, cohort and metric definitions match the request. For a rolling window ("last 30 days") its data must have ended within the last 7 days; a fixed past period ("July 2026") has no age limit. Quote it with its window and date, say if it is not yet signed off, offer a refresh, and stop. Quoting writes no new note. Otherwise carry on.
- **Every other request gets a note**, always a `.md` file in the project's `insights/` folder, made with `scripts/new-file.sh` so it is versioned (`yyyy-mm-dd-<descriptor>-v<n>.md`). The note starts as the approved brief and grows into the answer. The reply in chat is a short summary that points to the note.
- **Auto-commit:** commit locally, without asking and without pushing, with `scripts/commit-and-push.sh --local "<message>" <paths>`, each time the note reaches a stage: brief approved, answer ready (check passed), and every revision Tejas asks for. A revision after the answer was presented is saved as the next version (`-v2`, `-v3`); earlier versions stay.
- **Nothing is pushed before Tejas signs off.** A note is `signed_off: false` until then.
- **What counts as sign-off:** Tejas replies "ok", "approved", "looks good", "save it", "sign off" or similar to the presented note. Questions, change requests and silence do not count: revise, re-run the note check, and present again.
- **On sign-off:** set `signed_off: true`, then commit and push straight to `main` with `scripts/commit-and-push.sh "<message>" <paths>`, which sends the earlier local commits too. State the message and paths. That push is pre-authorised for the note, its queries, scripts, tests, and the additive context changes defined in `workflows/update-context.md`.
- **Context changes:** a change to an existing definition or rule needs Tejas's approval first. A direct request from Tejas to update context is its own approval: push it right away.
- **A project folder is required** for every request except one answered by quoting a saved note. Nothing is saved unless there is a project folder in `archives/` to hold it: notes, queries, scripts, tests and data all live in one. If the request names no project, ask which; if it is new, create it from `archives/_template` first. Only shared context (schema, metrics, rules) is saved outside a project, and only through `workflows/update-context.md`.
- **Never push** `raw-data/`, `outputs/` or `scratch/`.

## Elements of the repo
What each element contains and when it is used. Shared files in `context/` change only through `workflows/update-context.md`. Everything is pushed to GitHub except `archives/<project>/raw-data/`, `archives/<project>/outputs/` and `scratch/`, which are local only: say so whenever a committed doc names a file in them. Versioned files are `yyyy-mm-dd-<descriptor>-v<n>.<ext>`, always made with `scripts/new-file.sh <project> <folder> <descriptor> <ext>`.

### Shared context
| Element | Location | Purpose | Trigger |
|---|---|---|---|
| Context guide | `context/CLAUDE.md`, `context/README.md` | Describes Truemeds' teams, systems and business verticals, where the PM agent's product-flow documents are, and how context files are formatted and loaded. | Read at the start of every data session. |
| Schema | `context/schema.md` | Lists every database table and its columns, each labelled with the systems it belongs to, plus known data quirks, open questions and tested queries to reuse. | Read before writing any query, and whenever a table or column is mentioned. |
| Metrics | `context/metrics.md` | Gives the one agreed meaning of each metric, and flags metrics that different projects define differently. | Read on every request, before using or defining any metric. |
| Rules | `context/rules.md` | Holds the rules that apply to every kind of analysis, whatever the job or project. Empty for now; built up as the agent is used. | Read on every request, to apply any rule that is listed. |

### Engine
| Element | Location | Purpose | Trigger |
|---|---|---|---|
| Router | `workflows/route.md` | Starts every data request: finds the project, picks the job, loads context, looks for an existing answer, checks the request is complete, and states how it reads the product flow. | First step of every data request. |
| Loop | `workflows/loop.md` | Describes the six steps every request follows, from planning the query to saving the result. | After routing, unless a saved note already answers the request. |
| Job cards | `workflows/jobs.md` | Says what each job type (analyse, model, design, rollout, measure) needs from Tejas, how it is done, and what the note adds. | When checking a request is complete, and when planning the query and the analysis. |
| Review | `workflows/review.md` | Defines the checks run on the query before it is run, the CSV when it arrives, and the note before it is shown. | Before Tejas runs a query, when a CSV arrives, and before a note is shown. |
| Context updates | `workflows/update-context.md` | Explains how to add or change a table, metric, rule or tested query in the shared context. | When a metric or table is undefined, a data quirk is found, or Tejas asks for a context change. |
| Note template | `templates/note.md` | The fixed layout for a note: the approved brief, then the answer, evidence, definitions and caveats. | Every request that is not answered from a saved note. |
| Methods | `templates/methods.md` | Reference for experiment maths: sample size, sample-ratio checks, significance tests, and how to give ranges. | When designing an experiment, planning a rollout, or reading launch results. |

### Tools
| Element | Location | Purpose | Trigger |
|---|---|---|---|
| File creator | `scripts/new-file.sh` | Creates a new file with the right name, version number and folder. | Every time a new versioned file is created. |
| Commit helper | `scripts/commit-and-push.sh` | Commits only the files named, and uploads them to GitHub unless told `--local`. | After each note stage (locally); after Tejas signs off or asks for a context update (upload). |
| CSV validator | `scripts/validate-csv.py` | Checks a CSV has the expected columns, no duplicate rows, acceptable blanks, the right dates and matching totals. | Every time a CSV is added to `raw-data/`. |

### Per project: `archives/<project>/`
New project: `cp -r archives/_template archives/<name>`, then fill `archives/<name>/context/data-sources.md`. Never create project subfolders by hand. `analysis-plans/` exists only in legacy projects.

| Element | Location | Purpose | Trigger | Created by |
|---|---|---|---|---|
| Note | `insights/` | Holds the note for one request: the approved brief, then the answer, sizing, spec or launch readout. | Every request that is not answered from a saved note. | `new-file.sh <project> insights <project>-<topic> md` |
| SQL | `queries-dump/` | Holds the SQL queries, and the small check queries, written for a request. | When writing the queries for a request. | `new-file.sh <project> queries-dump <project>-<topic>-query sql` |
| Scripts | `scripts/` | Holds the Python scripts that calculate every number reported. | When calculating the numbers for an answer. | `new-file.sh <project> scripts aggregate-<topic> py` (or `structure-`) |
| Tests | `tests/` | Holds tests for scripts whose logic is more than trivial. | When a script's logic is more than trivial. | `new-file.sh <project> tests test-<script> py` |
| Project context | `context/` | Holds reference material for this project only, sample data of up to 10 rows, and the list of its data files. | Read when the request concerns this project. | `new-file.sh <project> context <descriptor> md` |
| Raw data | `raw-data/` | Holds the complete CSV exports Tejas downloads from Metabase. | After Tejas runs the queries and downloads the results. | Tejas drops them |
| Outputs | `outputs/` | Holds the result files the scripts write. | When a script runs. | Scripts write them |

### Other
| Element | Location | Purpose | Trigger |
|---|---|---|---|
| Design record | `changelogs/` | Records why the repo is designed as it is, and each change to the workflows. | When the design or workflows change. |
| Scratch | `scratch/` | Holds temporary work that is never uploaded. | For throwaway work only. |
