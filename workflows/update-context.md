---
name: update-context
description: How to add or change a table, a metric or a rule in the shared context. Called by the loop or directly by Tejas.
---

# Update context

## Inputs
| Input | What it is | Who gives it |
|---|---|---|
| Kind of change | A table or column, a metric, or a rule | Found by Claude in the loop (an undefined term, an undocumented table, a new data quirk), or asked for by Tejas |
| Details | The table name, or the metric and its meaning, or the rule, or the query | Tejas, or the sample rows he runs when Claude asks |

## Where each fact lives
| Fact | File |
|---|---|
| Tables, columns, data quirks | `context/schema.md` (a quirk goes beside its table) |
| What a metric means | `context/metrics.md` |
| A rule for every analysis | `context/rules.md` |
| Results | Project notes in `archives/<project>/insights/`, never here |
| Project-only material | `archives/<project>/context/` |

## Approval
| Change | What Claude does |
|--------|------------------|
| A small addition (a new table section, a new quirk) | Applies it locally and shows the difference. It is pushed with the request's commit at sign-off, or straight away if Tejas asked for the change |
| A change to something already written, or a conflict between two definitions | Shows the difference, waits for Tejas's approval, then applies it |

## Transformation logic

**New table or column**
| # | Step | What Claude does | Rule |
|---|------|------------------|------|
| 1 | Confirm | Reads `schema.md` | Continues only if the table is really missing |
| 2 | Ask | Asks Tejas, in one message, to run two queries in Metabase: the columns (`SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'tmmumpsdb' AND table_name = '<t>' ORDER BY ordinal_position`) and 10 sample rows (`SELECT * FROM tmmumpsdb.<t> LIMIT 10`) | |
| 3 | Draft | Writes the section: purpose, who writes it, grain, key date column, columns, join keys, quirks | Never infers a column's meaning from its name alone; uses the sample rows and flags unexpected blanks. Marks unverified join keys |
| 4 | Add | Adds it under Tables in `schema.md` with its `Systems:` flag | Sets `updated:` |

**New metric**
| # | Step | What Claude does | Rule |
|---|------|------------------|------|
| 1 | Write | Adds to `metrics.md` using its entry layout. Triggered when Tejas approves a brief that defines a new metric, or asks for one | The definition is the one Tejas approved |
| 2 | Conflict | If a variant already exists, keeps both and marks the row CONFLICT | Stays CONFLICT until Tejas picks one |

**New rule:** adds it to `rules.md` only if it holds for every kind of analysis. A rule about one table goes beside the table in `schema.md`.

## Outputs
| Output | What it is |
|---|---|
| Updated file | The changed file, with `updated:` set in its front matter |
| Difference shown | Tejas sees what changed |
| Push | With `scripts/commit-and-push.sh`, at the point set out under Approval; say what was pushed |
