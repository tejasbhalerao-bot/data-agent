---
name: loop
description: The shared engine. Six phases from an approved brief to a saved answer. Every job uses it.
---

# Loop

Phases are fixed. Checks are in `review.md`. Job differences are in `jobs.md`. Rework limit: after two failed rounds on the same problem, stop and tell Tejas what you think is wrong.

## 1. Route
Done in `route.md`. Output: job, rules applied, context loaded, whether a note will be written, and the **flow reading** ("My reading of the flow: …").

## 2. Brief (always; nothing starts without approval)
Before writing any query, design or plan, show Tejas a short brief in plain English and **wait for his approval**. Do no work until he approves. If he corrects it, revise and show it again.
- The flow reading ("My reading of the flow: …").
- The objective, and the questions to answer (each answerable on its own).
- Definitions used (named from `metrics.md`) and tables.
- **Grain and output columns: ask Tejas.** Ask what one row should be and which columns he needs. You may suggest, with reasons, but he decides; never choose them alone, and do not write any query until he has answered.
- What you will produce (queries, a design, a rollout plan, a baseline, a dashboard spec). The result is always a note.
- Assumptions made, and the decision it feeds if he gave one.

When he approves, create the note with `scripts/new-file.sh <project> insights <project>-<topic> md` from `templates/note.md`, put the approved brief in it, set `status: brief`, and commit it locally (`scripts/commit-and-push.sh --local "<message>" <path>`). A re-run skips the approval, because the saved analysis is the spec, but still gets a note.

## 3. Build
1. **Reuse first.** A CSV in `raw-data/` that covers the window, cohort and columns needed, or a validated query in the "Reference queries" section of `context/schema.md`. If a CSV covers it, go to phase 4, step 2.
2. **Pre-flight (hard stop).** Every table, column and metric used must exist in `context/schema.md` and `context/metrics.md`. If not, stop and run `update-context`. If the data cannot answer the request, tell Tejas what cannot be answered and what would be needed.
3. **Write the SQL** (you own its correctness).
   - Apply the filters listed for each table in `schema.md`, and any rule in `rules.md`.
   - Filter early, avoid join fan-out, use the `tmmumpsdb.` prefix and `snake_case` names.
   - Use the grain and columns Tejas gave in the brief. Do not add or drop columns on your own; if a cut later needs a column that is missing, ask him.
   - Rate timeout risk. Low: up to 2 joins and 30 days. Medium: 3 to 4 joins, or 31 to 89 days. High: 5+ joins, or 90+ days. Tell Tejas the rating. For High, propose a split (by date range first) and let him choose; then write a merge script (`scripts/new-file.sh <project> scripts merge-<topic> py`) that joins the chunks and checks the row counts.
   - **One query, one file.** Write each query as its own `.md` file in `queries-dump/`, made with `scripts/new-file.sh <project> queries-dump <project>-<topic>-query md`. The file has a short header (purpose, grain, tables, definitions used, filters, expected shape, timeout rating), then the SQL in a single ```sql code block. Never put SQL in the note.
   - **Versions.** A query changed after Tejas has seen it (for example an error fix) is a new version of its file (`-v2`, `-v3`); earlier versions stay.
4. **Probe.** One combined query, in its own file (`<project>-<topic>-probe-query`): row count, distinct key count, and one total that reconciles to a known figure (from a signed-off note or from Tejas; if none exists, skip the reconciliation and say so).
5. **Check the query** (`review.md`), then add a **"Queries to run"** section to the same note (the one holding the approved brief). It is a table with the columns ID (Q1, Q2…; the probe is Q0), Purpose, Latest file (full path from the repo root, with version), and Save the CSV as (full path in `raw-data/`). The note only references the query files; it never contains SQL. When a query gets a new version, update its row to the latest.
   Set the note's `status: awaiting-data`, fill `awaiting:`, commit the note and the query files locally, and tell Tejas in chat that the queries are ready, with the note's path.

## 4. Run
1. Tejas runs the queries once, opening each file listed in the note's "Queries to run" table. When he next writes, check `raw-data/` for the expected files first; do not ask him to say "done". If he pastes an error, a timeout or an odd result: diagnose, write a new version of the query, update its row in the table, and re-present from phase 3. Record any new quirk beside its table in `schema.md` through `update-context`. If the query was split, run the merge script and check the combined file.
2. **Check the CSV:** `python3 scripts/validate-csv.py <file> --key <grain columns> --require <needed columns> --date-col <date column> --probe rows=<n> --probe distinct=<n>`, with the values from the brief and the probe.
   - **FAIL from a query fault** (wrong columns, duplicate rows): fix the query, back to phase 3.
   - **FAIL from a wrong export** (cut short, wrong filters in Metabase): tell Tejas plainly what failed and ask him to re-export.

## 5. Answer
1. **All figures come from code.** Never read numbers off a CSV by eye.
   - **Re-run:** if the project's earlier note has a script covering the cuts needed, take its latest file and "Run with" command from that note's "Scripts and outputs" table and run it on the new CSV.
   - **Otherwise write one script per calculation** with `scripts/new-file.sh <project> scripts aggregate-<topic> py`. Start the file with a comment block: purpose, the CSV it reads, the files it writes to `outputs/`, and the exact command to run it. It reads the CSV, applies the cuts and writes to `outputs/`.
   - **Versions.** A script changed after its output has been used is a new version (`-v2`, `-v3`), never an edit in place; earlier versions stay.
   - **Tests.** Add one (`scripts/new-file.sh <project> tests test-<script> py`) for any script that classifies, does date arithmetic or joins.
   - **Run it** and add a **"Scripts and outputs"** section to the note: a table with the columns ID (S1, S2…), Purpose, Latest file (full path), Reads (the Q-ID and its CSV), Writes (full path in `outputs/`), Test (full path, or "none needed"), and Run with (the exact command). The note only references the files; it never contains code. Commit the scripts, tests and note locally.
2. **Open with the flow reading** from the approved brief. If Tejas corrected it, record the correction beside the relevant table or system in `schema.md` through `update-context`.
3. **Write the answer into the note** (`templates/note.md`): answer first, decision implication, evidence tables with full numbers, definitions used, assumptions made, caveats, next check. The reply in chat is a short summary (flow reading, the key numbers, the data window) that points to the note file.
4. **Check the answer** (`review.md`).

## 6. Save
Sign-off, save and push rules are in `CLAUDE.md` ("Sign-off, save and push"). In short:
1. Set `status: saved`, `signed_off: false`, and `as_of`; commit the note, queries, scripts and tests locally with `--local` (and again after every revision Tejas asks for; a revision after the answer was presented is saved as the next version). Point Tejas to the note file. Nothing is pushed yet.
2. **Context changes:** list them in one block. Small additions (a new validated query, a new quirk beside its table) are applied locally with the diff shown. A change to an existing definition or rule waits for approval. Procedure in `update-context.md`.
3. **On sign-off** (as `CLAUDE.md` defines it): set `signed_off: true`, then commit and push everything from the request in one commit to `main` with `scripts/commit-and-push.sh`. State the message and paths. Never stage `raw-data/` or `outputs/`. If he asks for changes, revise and check again before presenting.

## Rules
- No aggregations in SQL, except the probe; aggregation belongs in the script.
- Never name versioned files by hand; `new-file.sh` does it.
- Raw data and outputs are local only: say so whenever a committed doc names them.
