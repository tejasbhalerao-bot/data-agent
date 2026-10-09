---
name: update-context
description: Add or change schema, a metric, a rule, a validated query or a finding. Called by the loop (undefined term, undocumented table, new quirk, promotion) or directly by Tejas.
---

# Update context

One home per fact: schema in `context/data/<system>.md`, definitions in `context/metrics.md`, filters, vocabulary and quirks in `context/rules.md`, SQL in `context/queries/`, results in `context/findings.md`. Project-only material stays in `archives/<project>/context/`.

## Approval rule
- **Additive and low-risk** (a new table section, a new gotcha row, a validated query, a finding with window and as-of): apply, show the diff, push.
- **Change to an existing definition, rule or schema statement, or a conflict between variants:** show the diff, wait for approval, then apply.

## New table or column (schema discovery)
1. Read the relevant `context/data/*.md` first; confirm the table is really missing.
2. Ask Tejas to run in Metabase: columns (`SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'tmmumpsdb' AND table_name = '<t>' ORDER BY ordinal_position`) and 10 sample rows (`SELECT * FROM tmmumpsdb.<t> LIMIT 10`), in one pack.
3. Draft the section: purpose, written by, grain, key date column, column table, join keys (mark unverified keys), quirks. Never infer a column's meaning from its name alone; use the sample rows and flag unexpected nulls.
4. Put it in the file for the owning system; set `updated:`. Move any quirk to `rules.md`.

## New metric or definition
Add to `metrics.md`: definition, inputs (named columns), formula, unit, caveats, source. Where it conflicts with an existing variant, keep both and log the conflict in `rules.md` section 6 until Tejas picks one.

## New finding
Only from a **signed-off** note. Format: ID, topic, window, as-of, definition used, result, source path. Headlines only; full tables stay in the note.

## New validated query
Add a row to `context/queries/INDEX.md`. When a second project reuses a query, move the file into `context/queries/` with the standard header and update the row.

## Always
Show what changed, commit and push with `scripts/commit-and-push.sh`, and say what was pushed. Set `updated:` in the front matter of every file touched.
