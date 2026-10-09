---
name: loop
description: The shared engine. Six phases from brief to saved note. Every job uses it.
---

# Loop

Phases are fixed. Checks are in `review.md`. Job differences are in `jobs.md`.

## 1. Route
Done in `route.md`. Output: job, tier, defaults used, context loaded.

## 2. Brief (Tier 2 only)
Build from the intake: objective, questions (each independently answerable), definitions used (name them from `metrics.md`), tables, expected output columns and grain, the decision this feeds, defaults used. Create the note with `./scripts/new-file.sh <project> insights <project>-<topic> md` using `templates/note.md`, status `brief`.
**Gate A only if a blocking assumption was made:** show the brief, wait for approval. Otherwise show it as the note header and continue.

## 3. Build
1. **Reuse first.** A fresh CSV in `raw-data/` that covers the request, or a query in `context/queries/INDEX.md`. If a CSV covers it, skip to phase 4 step 2.
2. **Pre-flight (hard stop).** Every table, column and metric used must exist in `context/data/` and `context/metrics.md`. If not, stop and run `update-context`.
3. **Write SQL (owner: this step).** Apply `rules.md` section 1 exclusions. Filter early, avoid join fan-out, `tmmumpsdb.` prefix, `snake_case`. **Pull wide:** lowest useful grain with every segment column (courier, warehouse, pincode, date, state flags) so cuts happen offline in Python. Header on each query: purpose, grain, tables, definitions used, exclusions, expected shape. Timeout risk: Low (up to 2 joins, up to 30 days), Medium, High (5+ joins or 90+ days). Split High by date range, then write a merge script that checks row counts. Save with `new-file.sh <project> queries-dump <project>-<topic>-query sql`.
4. **Probe.** One combined probe query: row count, distinct key count, and one total that reconciles to a known figure.
5. **Check 1** (`review.md`), then give Tejas **one handoff pack**: all queries, the probe, and the exact filename to save each CSV as in `raw-data/`. Set status `awaiting-data` and fill `awaiting:`.

## 4. Run
1. Tejas runs the pack once. Detect the files by name in `raw-data/`; do not wait to be told. If he pastes an error, a timeout or an odd result: diagnose, fix, re-present from phase 3. Record any new quirk in `rules.md` through `update-context`.
2. **Check 2:** `python3 scripts/validate-csv.py <file> --key ... --require ... --date-col ... --probe ...`. FAIL returns to phase 3 or to Tejas with the failing check.

## 5. Answer
1. **All figures come from code.** Write a script (`new-file.sh <project> scripts aggregate-<topic> py`) that reads the CSV, applies cuts and writes to `outputs/`. Never read numbers off a CSV by eye. Add a test when logic is non-trivial.
2. Write the note from `templates/note.md`: answer first, decision implication, evidence tables with full numbers, definitions used, defaults used, caveats, next check.
3. **Check 3** (`review.md`).

## 6. Save
1. Set `status: saved`, `signed_off: false`. Commit and push now: `scripts/commit-and-push.sh "<msg>" <paths>`. State the message and paths. Never stage `raw-data/` or `outputs/` (gitignored).
2. Tier 2 notes also go to Tejas as an Artifact; Tier 0 and 1 short answers stay in chat with source and as-of.
3. **Context block:** list proposed context changes in one block. Additive items (a new validated query, a new gotcha row, a finding with window and as-of) apply automatically with the diff shown. A change to an existing definition or rule waits for approval. Procedure in `update-context.md`.
4. Tejas reads when he can; his sign-off sets `signed_off: true` and is the gate for adding to `findings.md`.

## Rules
- No aggregations in SQL; aggregation belongs in the script.
- Never name versioned files by hand; `new-file.sh` does it.
- Raw data and outputs are local-only: say so whenever a committed doc names them.
