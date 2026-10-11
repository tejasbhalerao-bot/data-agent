---
name: jobs
description: The five jobs as workflows. For each: inputs, steps with their rules, and outputs. Used by route.md (is the request complete?) and loop.md.
---

# Jobs

How to read this: each job lists what goes in (**Inputs**), what Claude does (**Steps**), and what comes out (**Outputs**). Every job runs inside the loop (`loop.md`): brief, then queries, then scripts, then a note.

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

**Steps**
1. Calculate the baseline.
2. Split it by the cuts Tejas chose.
3. Check what else could explain the result: a change in the mix of segments, seasonality, too few orders.
4. Check the totals against a known total or a second source.
5. Test the opposite explanation.

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

**Steps**
1. Replay or simulate the change on historical data.
2. Run the low, base and high cases. Never show one number alone.
3. Find the one or two assumptions that move the answer most.
4. Name a floor (what the data proves is addressable) and a ceiling (everything addressable if all assumptions hold).
5. Find the break-even value, where the decision flips.

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

**Steps**
1. **Data check:** does each field exist, is it filled, is it reliable? Use `schema.md`, its open questions, the instrumentation note in `context/CLAUDE.md`, the PM agent's product docs, and probes.
2. **Define the metrics:** numerator, denominator, exclusions, anchor. New definitions go into `metrics.md` only after Tejas approves.
3. **List the events engineering must add.**
4. **Experiment only:** set the main metric and the safety metrics (ones that must not get worse), sample size, duration, holdout (a group left unchanged), assignment, a check that group sizes match the plan (SRM), and the ship / iterate / kill thresholds. `templates/methods.md` gives the formulas; the settings are Tejas's.

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

**Steps**
1. Size each stage from data: eligible orders, customers or lanes per location per day. Use the product docs for what is eligible.
2. Check each stage is large enough to read the success and safety metrics (`templates/methods.md`).
3. Propose the stage gates: go, hold, roll back.
4. Propose the minimum duration per stage.
5. Flag overlaps with other live changes, and locations with thin data.

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

**Steps, by stage**
- **Before launch (baseline):**
  1. Run the data checks: row counts reconcile, key unique, no missing days.
  2. Freeze the snapshot: list its CSV in the "Queries to run" table and never overwrite it.
  3. Test the queries on historical or shadow data.
  4. Propose alert limits.
- **Day 1, day 7, other day:**
  1. Check the events are firing.
  2. Compare the safety metrics with their limits.
  3. Note anything odd.
  4. Give an early read, marked "too early to call".
- **Final result (readout):**
  1. Compare the launch with the baseline or control, with 95% intervals.
  2. Show the cuts, and the side effects on the safety metrics.
  3. Check there was enough data.
  4. End with **ship, iterate or kill**, and the reason.
- **Dashboard (any stage, only if asked):** write the dashboard spec. Dashboard queries may aggregate, because Metabase computes the card. Each is still its own query file, referenced by Q-ID, and any number quoted in a note still comes from a script. Tejas builds it in Metabase from the spec; or a static HTML dashboard can be made from the CSVs with the `data:build-dashboard` skill.
- **Recurring report:** use the `Re-run:` field (`route.md`, step 3) to run the earlier note's saved script on a new CSV. Do not rebuild.

**Outputs**
| Output | What it is |
|---|---|
| Note (`templates/measure.md`) | The section for the stage: baseline, check, or final result; plus the dashboard spec if asked |

---

## update-context
Not a loop job. Follow `workflows/update-context.md`.
