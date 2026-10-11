---
name: review
description: The three checks, each with what is checked, the pass condition and what to do on failure. They always run and cannot be skipped.
---

# Review

Three checks run at fixed points. None can be skipped, not even for a quick answer. On a failure, fix it yourself and check again before moving on. Anything still unresolved is flagged at the top of the note.

| Check | When | What is checked |
|---|---|---|
| 1. Query | Before Tejas runs it | Each query file and the "Queries to run" table |
| 2. CSV | When a CSV arrives | Each CSV in `raw-data/` |
| 3. Note | Before the note is presented | The whole note |

## Check 1: the query

| # | What Claude checks | Pass when |
|---|--------------------|-----------|
| 1 | Metrics | Each metric matches `metrics.md`, or the approved brief's "Metric definitions" if it is new. If variants conflict, ask Tejas first |
| 2 | Filters | The filters listed for each table in `schema.md` are applied, plus any rule in `rules.md`. Example: keep only the latest row per order on the allocation audit, before any join |
| 3 | Rows | One row is what the brief says. Joins do not multiply rows: the join keys are unique on the side that must be unique |
| 4 | Join keys | They match the keys in `schema.md`, as exact matches and never by timestamp |
| 5 | Style | The date filter is applied as early as possible; no `SELECT *` on large tables; `tmmumpsdb.` prefix; `snake_case` names |
| 6 | Matches the brief | It pulls only what the brief's "Data from" column plans. The output columns are the grain and columns Tejas gave. No aggregation, except the probe and dashboard queries |
| 7 | Coverage | Every metric and cut (M1…) is served by at least one query. Every query serves at least one. Each cut's column is in the output |
| 8 | Files | One file per query, following `templates/query.md`. The note's "Queries to run" table points to the latest version of each and holds no SQL |
| 9 | Safety | The probe is included, the timeout risk is rated, and a High risk is split |

**On failure:** fix the query and check again. Do not send it to Tejas.

## Check 2: the CSV
Run `scripts/validate-csv.py`.

| What Claude checks | Pass when |
|--------------------|-----------|
| Columns | The required columns are present |
| Rows | The key is unique; the row and distinct counts match the probe |
| Blanks | The share of blanks in each column is within its limit |
| Dates | All dates fall inside the window |

**On failure:**
- Query fault (wrong columns, duplicate rows): fix the query and go back to `loop.md`, phase 3.
- Wrong export (cut short, wrong filters in Metabase): tell Tejas plainly what failed and ask him to re-export.

## Check 3: the note

| # | What Claude checks | Pass when |
|---|--------------------|-----------|
| 1 | Figures | Every figure appears in a script output in `outputs/`, cited by metric ID and script ID (M1, via S1). Nothing is typed by hand |
| 2 | Plan followed | The calculation followed the approved "How it will be calculated" steps. Any change was approved in a revised brief |
| 3 | Template | The answer follows the job's template (named in `jobs.md`). Every section is filled or marked "not applicable" |
| 4 | Coverage | Every metric and cut in the brief has a figure in the Evidence. Every script serves at least one. Nothing is reported that is not in the brief's list |
| 5 | Tables | The "Scripts and outputs" table points to the latest script, test and output of each, gives the exact run command, and the note holds no code |
| 6 | Sums | Denominators are stated and are the intended population. Percentages add up |
| 7 | Sample size | The sample supports each claim. Small cells are marked or dropped |
| 8 | Other explanations | The job's other-explanation checks were done (`jobs.md`, "Transformation logic"). Any headline comparison was re-checked within the largest segment, in case the overall result hides the opposite trend |
| 9 | Claim strength | "Caused" appears only where a test supports it. Otherwise "associated with" |
| 10 | Context | The window and as-of date are stated, assumptions listed, definitions named, and the caveats include the data-quality flags from `schema.md` |
| 11 | Answer first | The first two lines answer the question the note was written for |

**On failure:** fix the note and check again before presenting it.
