---
name: jobs
description: The five jobs as workflows. For each: inputs, transformation logic (steps and rules), and outputs. Used by route.md (is the request complete?) and loop.md.
---

# Jobs

How to read this: each job lists what goes in (**Inputs**), what Claude does to it (**Transformation logic**: steps and their rules), and what comes out (**Outputs**). Every job runs inside the loop (`loop.md`): brief, then queries, then scripts, then a note.

Before anything is built, the brief's "How it will be calculated" section restates each step for this request: the exact rule or formula, and where the data comes from (an existing CSV, a saved query, a new query, or the script alone). Tejas approves it.

## Rules for every job
- Never choose a value that is Tejas's to choose (windows, assumptions, thresholds, grain, columns). Ask, or propose with a reason and let him decide.
- The brief lists the metrics and cuts (M1…) the job will produce. A job that produces no numbers has no queries or scripts.
- The answer always goes in a note, laid out by the job's template.

## Inputs every job needs
| Input | What it is | Who gives it, and when |
|---|---|---|
| Job | analyse, model, design, rollout or measure | Tejas, in the request; or inferred and stated |
| Project | The folder in `archives/` the work is saved in | Tejas, in the request; asked if missing |
| Scope | What the work covers (set out per job below) | Settled in the brief: Tejas gives what he has, Claude proposes the rest with a reason, Tejas decides |
| Grain and columns | What one row is, and which columns the output has | Settled in the brief: Claude may suggest; Tejas decides |
| Definitions | What each metric means | `metrics.md`, unless Tejas names another in the request |
| Decision it feeds | What he will do with the answer (optional) | Tejas, in the request |

---

## analyse: what happened, where, and why

**Inputs**
| Input | What it is | Who gives it, and when |
|---|---|---|
| Scope | Time window, cohort, comparison | Settled in the brief |
| Cuts | How to split the result (courier, warehouse, pincode, vertical, SDD x inventory, day) | Settled in the brief: Claude suggests; Tejas chooses |

**Transformation logic**
| # | Step | What Claude does | Rule |
|---|------|------------------|------|
| 1 | Baseline | Calculates each metric for the whole scope | Uses only the filters in `schema.md` and the definitions in `metrics.md` |
| 2 | Cuts | Splits the baseline by each cut Tejas chose | Cuts add up to the baseline; every percentage is shown with its count |
| 3 | Other explanations | Checks what else could explain the result: a change in the mix of segments, seasonality, too few orders | Marks any cell with too few orders |
| 4 | Reconcile | Compares the totals with a known total or a second source | States what counts as a match; reports any mismatch |
| 5 | Opposite explanation | Tests the opposite of the result | Reports it even when it is ruled out |

**Outputs**
| Output | What it is |
|---|---|
| Note (`templates/analyse.md`) | Headline; where it concentrates; what it is not; so what; evidence |

---

## model: size it, simulate it, compare options

**Inputs**
| Input | What it is | Who gives it, and when |
|---|---|---|
| Lever | The change, rule or option being sized | Tejas, in the request |
| Assumptions | Each named, with a low, base and high value | Named in the request; low, base and high values settled in the brief, given by Tejas (never picked by Claude) |
| Horizon | How far ahead | Tejas, in the request |
| Alternatives | Options to compare (optional) | Tejas, in the request |
| Scope | Time window, cohort | Settled in the brief |

**Transformation logic**
| # | Step | What Claude does | Rule |
|---|------|------------------|------|
| 1 | Affected population | Picks the orders, customers or lanes the lever touches | Picks them by a rule based on the data |
| 2 | Mechanism | Applies the lever's effect to each one | States what changes for each affected unit |
| 3 | Formula | Calculates the effect from the assumptions | Uses only the values Tejas gave |
| 4 | Cases | Runs the low, base and high cases | Never shows one number alone |
| 5 | What moves the answer | Varies the one or two assumptions that matter most | Shows how much the result changes |
| 6 | Floor and ceiling | Calculates both | Floor: what the data proves is addressable. Ceiling: everything addressable if all assumptions hold |
| 7 | Break-even | Finds the value where the decision flips | States the decision rule |

**Outputs**
| Output | What it is |
|---|---|
| Note (`templates/model.md`) | Headline range; assumption table; results by case; floor and ceiling; what moves the answer; break-even; evidence |

---

## design: decide how to measure before building

**Inputs**
| Input | What it is | Who gives it, and when |
|---|---|---|
| PRD | The text, or its key points | Tejas, in the request |
| Mode | Requirements doc, experiment plan, or both | Tejas, in the request |
| Hypothesis and main metric | Only for an experiment | Tejas, in the request |
| Experiment settings | Smallest change worth detecting; confidence and power (95% and 80% unless he says otherwise); longest duration; planned split | Settled in the brief: Tejas gives them |
| Scope | The PRD, and the systems, events and tables it touches | Settled in the brief |

**Transformation logic**
| # | Step | What Claude does | Rule |
|---|------|------------------|------|
| 1 | Data check | Checks that each needed field exists, is filled and is reliable | Uses `schema.md` and its open questions, the instrumentation note in `context/CLAUDE.md`, the PM agent's product docs and probes. Reports each as Present, Partial or Missing |
| 2 | Define the metrics | Writes the numerator, denominator, exclusions and anchor of each metric | New definitions go into `metrics.md` only after Tejas approves |
| 3 | Events | Lists the events and fields engineering must add | For each: its properties, trigger and owner system |
| 4 | Experiment only: plan | Calculates sample size and duration. Sets the main and safety metrics (ones that must not get worse), the holdout (a group left unchanged), the assignment, a check that group sizes match the plan (SRM), and the ship / iterate / kill thresholds | Formulas are in `templates/methods.md`. The settings are Tejas's: smallest change worth detecting, confidence and power, longest duration, split |

**Outputs**
| Output | What it is |
|---|---|
| Requirements doc (`templates/ard.md`) | Metric definitions; events and fields with status; ER diagram; data gaps; questions for engineering; a block to paste into the PRD |
| Experiment plan (`templates/experiment.md`) | Hypothesis; metrics; who is in it; size and duration; checks; thresholds; a block to paste into the PRD |

If only metrics are needed, they go in the brief's "Metric definitions" section.

---

## rollout: design the go-to-market (GTM) plan

**Inputs**
| Input | What it is | Who gives it, and when |
|---|---|---|
| Rollout plan | Stages, locations, % of traffic or orders, launch settings, intended duration | The PM, in the request; anything missing is asked in the one batched message |
| Success and safety metrics | What must improve, and what must not get worse | Tejas, in the request; confirmed in the brief |
| Thresholds | The limit for each metric, and for each stage gate | Settled in the brief: Claude proposes; Tejas decides |

**Transformation logic**
| # | Step | What Claude does | Rule |
|---|------|------------------|------|
| 1 | Eligible | Defines the eligible orders, customers or lanes per location | Uses the product docs; states the definition |
| 2 | Size | Calculates volume per location per day, and per stage | Uses data; states the window used |
| 3 | Readable | Checks each stage is large enough to read the success and safety metrics | Uses `templates/methods.md` |
| 4 | Gates | Proposes the go, hold and roll-back rule for each stage | Thresholds are tied to `metrics.md`; Tejas decides them |
| 5 | Duration | Proposes the minimum duration per stage | Based on step 3 |
| 6 | Risks | Flags overlaps with other live changes, and locations with thin data | Lists each one |

**Outputs**
| Output | What it is |
|---|---|
| Note (`templates/gtm.md`) | Plan as supplied; sizing; success and safety metrics with thresholds; stage gates; risks; readiness checks; decisions for the PM |

The PM owns the plan. The analyst sizes and challenges it.

---

## measure: watch a launch

**Inputs**
| Input | What it is | Who gives it, and when |
|---|---|---|
| Stage | Before launch, day 1, day 7, other day, or final result (internally: baseline, day1, day7, health, readout) | Tejas, in the request |
| Launch date | When the change went live | Tejas, in the request |
| Metrics | From `metrics.md`, the PRD, or the project's design note | Tejas, in the request |
| Cuts | How to split the results | Settled in the brief: the PM's cuts come in the request; Claude suggests more and says which were added |
| Windows | Baseline and comparison windows (match day of week; leave out known odd days) | Settled in the brief: Claude proposes; Tejas decides |
| Limits | Success and safety limits | The project's rollout note if there is one; otherwise settled in the brief, given by Tejas |
| Earlier notes | For every stage after "before launch": the project's baseline note (metrics, windows, snapshot CSV) | Found by Claude; if none, say so and offer a baseline from historical data, labelled as such |

**Transformation logic, by stage**

Before launch (baseline)
| # | Step | What Claude does | Rule |
|---|------|------------------|------|
| 1 | Data checks | Checks that row counts reconcile, the key is unique, and no days are missing | Stops if any check fails |
| 2 | Freeze the snapshot | Keeps the snapshot CSV | Lists it in the "Queries to run" table; never overwrites it |
| 3 | Test the queries | Runs them on historical or shadow data | |
| 4 | Alert limits | Proposes a limit for each metric | Tejas decides |

Day 1, day 7, other day
| # | Step | What Claude does | Rule |
|---|------|------------------|------|
| 1 | Events | Checks the events are firing | Reports yes or no, with evidence |
| 2 | Safety metrics | Compares them with their limits | |
| 3 | Anything odd | Notes unusual movements | |
| 4 | Early read | Gives the direction | Marked "too early to call" |

Final result (readout)
| # | Step | What Claude does | Rule |
|---|------|------------------|------|
| 1 | Compare | Compares the launch with the baseline or control | States the method (against a control, or before and after), how the 95% interval is calculated, and how outliers are handled |
| 2 | Cuts and side effects | Shows the cuts, and the effect on the safety metrics | |
| 3 | Enough data | Checks the sample was large enough | Says so if it was not |
| 4 | Decision | Ends with ship, iterate or kill | Gives the reason |

Any stage, only if asked
- **Dashboard:** writes the dashboard spec. Dashboard queries may aggregate, because Metabase computes the card. Each is still its own query file, referenced by Q-ID, and any number quoted in a note still comes from a script. Tejas builds it in Metabase from the spec; or a static HTML dashboard can be made from the CSVs with the `data:build-dashboard` skill.
- **Recurring report:** uses the `Re-run:` field (`route.md`, step 3) to run the earlier note's saved script on a new CSV. Does not rebuild.

**Outputs**
| Output | What it is |
|---|---|
| Note (`templates/measure.md`) | The section for the stage: baseline, check, or final result; plus the dashboard spec if asked |

---

## update-context
Not a loop job. Follow `workflows/update-context.md`.
