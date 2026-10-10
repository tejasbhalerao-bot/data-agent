---
name: loop
description: The shared engine. Six phases from brief to saved note. Every job uses it.
---

# Loop

Phases are fixed. Checks are in `review.md`. Job differences are in `jobs.md`. Rework limit: after two failed rounds on the same problem, stop and tell Tejas what you think is wrong.

## 1. Route
Done in `route.md`. Output: job, rules applied, context loaded, whether a note will be written, and the **flow reading** ("My reading of the flow: …").

## 2. Brief (only when a note will be written)
Build from the request: objective, questions (each answerable on its own), definitions used (named from `metrics.md`), tables, expected output columns and grain, the decision it feeds, assumptions made. Create the note with `scripts/new-file.sh <project> insights <project>-<topic> md` from `templates/note.md`, `status: brief`.
Show the brief and wait for approval only if Tejas told you to assume something that was missing. Otherwise show it as the note header and continue.

## 3. Build
1. **Reuse first.** A CSV in `raw-data/` that covers the window, cohort and columns needed, or a validated query in the "Reference queries" section of `context/schema.md`. If a CSV covers it, go to phase 4, step 2.
2. **Pre-flight (hard stop).** Every table, column and metric used must exist in `context/schema.md` and `context/metrics.md`. If not, stop and run `update-context`. If the data cannot answer the request, tell Tejas what cannot be answered and what would be needed.
3. **Write the SQL** (you own its correctness).
   - Apply the filters listed for each table in `schema.md`, and any rule in `rules.md`.
   - Filter early, avoid join fan-out, use the `tmmumpsdb.` prefix and `snake_case` names.
   - **Pull wide:** one row per order (or the smallest unit the request needs), with every column a later cut might use (courier, warehouse, pincode, date, state flags), so cuts happen in the script.
   - Put a header on each query: purpose, grain, tables, definitions used, filters, expected shape.
   - Rate timeout risk. Low: up to 2 joins and 30 days. Medium: 3 to 4 joins, or 31 to 89 days. High: 5+ joins, or 90+ days. Split High queries by date range, and write a merge script (`scripts/new-file.sh <project> scripts merge-<topic> py`) that joins the chunks and checks the row counts.
   - Save with `scripts/new-file.sh <project> queries-dump <project>-<topic>-query sql`.
4. **Probe.** One combined query: row count, distinct key count, and one total that reconciles to a known figure (from a signed-off note or from Tejas; if none exists, skip the reconciliation and say so).
5. **Check the query** (`review.md`), then give Tejas **one handoff pack** that opens with the flow reading, so he can correct it before running anything: all queries, the probe, and the exact filename to save each CSV as in `raw-data/`. For a note, set `status: awaiting-data` and fill `awaiting:`. A chat answer has no note to mark.

## 4. Run
1. Tejas runs the pack once. When he next writes, check `raw-data/` for the expected files first; do not ask him to say "done". If he pastes an error, a timeout or an odd result: diagnose, fix, and re-present from phase 3. Record any new quirk beside its table in `schema.md` through `update-context`. If the query was split, run the merge script and check the combined file.
2. **Check the CSV:** `python3 scripts/validate-csv.py <file> --key <grain columns> --require <needed columns> --date-col <date column> --probe rows=<n> --probe distinct=<n>`, with the values from the brief and the probe.
   - **FAIL from a query fault** (wrong columns, duplicate rows): fix the query, back to phase 3.
   - **FAIL from a wrong export** (cut short, wrong filters in Metabase): tell Tejas plainly what failed and ask him to re-export.

## 5. Answer
1. **All figures come from code.** If a saved script covers the cuts needed (a re-run), run it on the new CSV. Otherwise write one (`scripts/new-file.sh <project> scripts aggregate-<topic> py`) that reads the CSV, applies the cuts and writes to `outputs/`. Never read numbers off a CSV by eye. Add a test for any script that classifies, does date arithmetic or joins.
2. **Open with the flow reading.** If Tejas corrected it, record the correction beside the relevant table or system in `schema.md` through `update-context`.
3. **Note:** write it from `templates/note.md`: answer first, decision implication, evidence tables with full numbers, definitions used, assumptions made, caveats, next check.
   **Chat answer:** the flow reading, the assumptions and rules applied, the answer with its numbers, the source (script and data window), and one line of caveats.
4. **Check the answer** (`review.md`).

## 6. Save
Sign-off, save and push rules are in `CLAUDE.md` ("Sign-off, save and push"). In short:
1. **Note:** set `status: saved`, `signed_off: false`, and `as_of`; save the note, queries, scripts and tests locally; point Tejas to the note file. Nothing is pushed yet. **Chat answer:** no note; anything created stays local unless Tejas says "save".
2. **Context changes:** list them in one block. Small additions (a new validated query, a new quirk beside its table) are applied locally with the diff shown. A change to an existing definition or rule waits for approval. Procedure in `update-context.md`.
3. **On sign-off** (as `CLAUDE.md` defines it): set `signed_off: true`, then commit and push everything from the request in one commit to `main` with `scripts/commit-and-push.sh`. State the message and paths. Never stage `raw-data/` or `outputs/`. If he asks for changes, revise and check again before presenting.

## Rules
- No aggregations in SQL, except the probe; aggregation belongs in the script.
- Never name versioned files by hand; `new-file.sh` does it.
- Raw data and outputs are local only: say so whenever a committed doc names them.
