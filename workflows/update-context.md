---
name: update-context
description: Add or change schema, a metric, a rule, or a validated query. Called by the loop (undefined term, undocumented table, new quirk, promotion) or directly by Tejas.
---

# Update context

One home per fact: schema in `context/schema.md`, definitions in `context/metrics.md`, standard filters, defaults and vocabulary in `context/rules.md`, data quirks beside their table in `context/schema.md`, validated SQL as a "Reference queries" entry in `context/schema.md`. Results live in project notes (`archives/<project>/insights/`), not here. Project-only material stays in `archives/<project>/context/`.

## Approval rule
- **Additive and low-risk** (a new table section, a new gotcha row, a validated query): apply locally and show the diff. It is pushed with the request's commit at sign-off, or right away when Tejas asked for the update directly.
- **Change to an existing definition, rule or schema statement, or a conflict between variants:** show the diff, wait for approval, then apply.

## New table or column (schema discovery)
1. Read `context/schema.md` first; confirm the table is really missing.
2. Ask Tejas to run in Metabase: columns (`SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'tmmumpsdb' AND table_name = '<t>' ORDER BY ordinal_position`) and 10 sample rows (`SELECT * FROM tmmumpsdb.<t> LIMIT 10`), in one pack.
3. Draft the section: purpose, written by, grain, key date column, column table, join keys (mark unverified keys), quirks. Never infer a column's meaning from its name alone; use the sample rows and flag unexpected nulls.
4. Add it under Tables in `context/schema.md` with its `Systems:` flag; set `updated:`. Record any quirk beside its table.

## New metric or definition
Add to `metrics.md`: definition, inputs (named columns), formula, unit, caveats, source. Where it conflicts with an existing variant, keep both and mark the row CONFLICT in `metrics.md` until Tejas picks one.

## New validated query
Add a row to the "Reference queries" section of `context/schema.md`, under its system. When a second project reuses a query, move the file into `context/` with the standard header (purpose, grain, tables, definitions, exclusions, validated-on) and update the row.

## Always
Show what changed. Push with `scripts/commit-and-push.sh` at the point set out above, and say what was pushed. Set `updated:` in the front matter of every file touched.
