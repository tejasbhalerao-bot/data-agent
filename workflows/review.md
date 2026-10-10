---
name: review
description: One reviewer, three checkpoints. Always runs, cannot be skipped. Fix and re-check until no blocking issue.
---

# Review

Run at each checkpoint. Fix issues yourself, re-check, and only then move on. Anything unresolved is flagged at the top of the note.

## Check 1: SQL (before handoff)
- Every metric used matches `metrics.md` (variant named). Conflicting variants: ask first.
- `rules.md` section 1 exclusions applied (E1 to E4 as relevant); dedupe E3 done before any join.
- Grain stated and true: join keys are unique on the side that must be unique; no fan-out.
- Join keys match the documented keys in `context/schema.md` (exact `request_id = reference_number`, not timestamps).
- Date filter sits in the innermost CTE; no `SELECT *` on large tables; `tmmumpsdb.` prefix; `snake_case` names.
- Output columns equal the brief's expected columns. No aggregation in SQL.
- Probe included; timeout risk rated; High is split.

## Check 2: CSV (on file drop)
`scripts/validate-csv.py` passes: required columns present, key unique, null shares within limits, dates inside the window, row and distinct counts match the probe. A FAIL goes back to phase 3 (query fault) or to Tejas (wrong export).

## Check 3: note (before save)
- Every figure in the note appears in a script output in `outputs/`. No hand-typed numbers.
- Denominators are stated and are the intended population; percentages add up.
- Sample size supports the claim; small cells are marked or dropped.
- Segment mix and confounders considered (job card list); a Simpson's-paradox check on any headline comparison.
- Claim strength matches the evidence: "caused" only with a test, otherwise "associated with".
- Window and as-of date stated; defaults listed; definitions named; caveats include data-quality flags from `schema.md`.
- The note answers the decision it was written for in the first two lines.
