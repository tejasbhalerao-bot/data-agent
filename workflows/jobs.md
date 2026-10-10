---
name: jobs
description: The five job cards. Each lists required inputs, what the brief must cover, the method and what the note adds. Used by route.md (completeness check) and loop.md.
---

# Jobs

Every job starts with a brief that Tejas approves (`loop.md`, phase 2) and ends in a note. The brief lists the metrics and cuts (M1…) the job will produce; a job that produces no numbers (an analytics requirements document, say) has no queries or scripts to tie back. Never choose values Tejas should choose (windows, assumptions, thresholds, grain, columns): ask, or propose and let him decide.

Required for every job: **Job, Project, Scope** (window, cohort, comparison) and **Definitions** (from `metrics.md` unless he names another). **Decision this feeds** is optional; it shapes the answer. Each card adds to these.

## analyse (look backward: what happened, where, why)
- **Required:** window, cohort, comparison.
- **Brief covers:** the metrics and cuts (suggest cuts such as courier, warehouse, pincode, vertical, SDD x inventory, day; Tejas chooses), the baseline and comparison, and the checks below.
- **Method:** baseline, then the cuts Tejas chose. Check what else could explain the result (a change in the mix of segments, seasonality, too few orders). Reconcile against a known total or a second source. Test the opposite explanation.
- **Note adds:** where it concentrates; what it is not; what was ruled out.

## model (look forward: size it, simulate it, compare options)
- **Required:** the lever, the assumptions (each named), the horizon, and for a comparison the alternatives.
- **Brief covers:** the assumption table with a **low, base and high value for each assumption, asked from Tejas** (never picked by you), and the outputs per case as M-IDs.
- **Method:** replay or simulate the change on historical data. Show low, base and high cases, never one number alone. Show how much the answer moves for the one or two assumptions that matter most. Name a floor (provably addressable) and a ceiling.
- **Note adds:** assumption table, range, break-even, what would change the conclusion.

## design (decide how to measure before building)
- **Required:** the PRD text or its key points, supplied in the request. Mode: **ard** ("requirements doc": analytics requirements document), **experiment** ("experiment plan"), or both. "Metrics", "data check" and "events to track" are parts of the same note. For an experiment: hypothesis and target metric.
- **Brief covers:** the mode; the metrics to define; the events and fields to check; for an experiment, the settings Tejas gives (smallest change worth detecting, confidence and power if he wants other than the standard, longest duration allowed, planned split).
- **Method:** (1) data check: does each field exist, is it filled and reliable (use `schema.md`, probes, its open questions, the instrumentation note in `context/CLAUDE.md`, and the PM agent's product docs); (2) metric definitions: numerator, denominator, exclusions, anchor, written to `metrics.md` after approval; (3) events engineering must add; (4) for an experiment: main metric and safety metrics (ones that must not get worse), sample size, duration, holdout (a group left unchanged), assignment, a check that group sizes match the plan (SRM), and ship / iterate / kill thresholds (`templates/methods.md` gives the formulas; the settings are Tejas's).
- **ard mode:** the note is the ARD. Sections: objective and the decision it supports; metric definitions (names from `metrics.md`, new ones flagged); **instrumentation table** (event or field, properties, trigger, owner system, status Present / Partial / Missing from `schema.md` and the instrumentation note); **ER diagram** of the entities and tables involved (Mermaid `erDiagram`, built from `schema.md` join keys, unverified keys named in a caption); data gaps; open questions for engineering.
- **Note adds:** a paste-ready block for the PRD (metrics, instrumentation, experiment plan), or the ARD sections above.

## rollout (design the GTM)
- **Required:** the PM's rollout plan as supplied: stages, locations, percentages, launch parameters, intended duration. Anything absent is asked in the one batched message.
- **Brief covers:** the plan as supplied, the numbers to size per stage (M-IDs), and the success and safety metrics.
- **Method:** size each stage from data (eligible orders, customers or lanes per location per day), using the product docs for what is eligible; check the stage is large enough to read the success and safety metrics (`templates/methods.md`); propose stage gates (go / hold / rollback) with thresholds tied to `metrics.md`; propose the minimum duration per stage; flag overlaps with other live changes and locations with thin data. Tejas decides the thresholds.
- **Note adds:** rollout table (stage, locations, %, expected volume, duration, gate metrics and thresholds, rollback trigger) and readiness checks (instrumentation live, baseline frozen). The PM owns the plan; the analyst sizes and challenges it.

## measure (watch a launch)
- **Required:** the stage (**baseline** = "before launch", **day1** = "day 1", **day7** = "day 7", **health** = "other day", **readout** = "final result", the end of the GTM), launch date, control or comparison period, metrics (from `metrics.md`, the PRD, or the project's design note), cuts the PM wants. Suggest extra cuts and say which were added.
- **Earlier notes this job uses:** for every stage after baseline, the project's baseline note (its metrics, windows and snapshot CSV). If none exists, say so and offer a baseline built from historical data, labelled as such. Success and safety limits come from the project's rollout note if there is one; otherwise ask.
- **Brief covers:** the stage, the windows (**proposed by you, decided by Tejas**: match day of week, leave out known odd days), the metrics and cuts (M-IDs), the limits, and which earlier notes are used.
- **baseline:** run the data checks (row counts reconcile, key unique, no missing days), freeze the snapshot (list its CSV in the "Queries to run" table and never overwrite it), test the queries on historical or shadow data, propose alert limits.
- **day1 / day7 / health:** are events firing, safety metrics against limits, anything odd, and an early read marked "too early to call".
- **readout:** impact versus baseline or control with confidence intervals, cuts, side effects, and whether the sample was large enough. End with **ship / iterate / kill** and the reason.
- **Dashboard (any stage, on request):** a dashboard spec in the note: one row per card with the query file behind it (by Q-ID), filters and cuts, refresh cadence and alert limits. Dashboard queries may aggregate, because Metabase computes the card; each is still its own query file, and any number quoted in a note still comes from a script. Tejas builds it in Metabase from the spec; alternatively a static HTML dashboard from the CSVs via the `data:build-dashboard` output skill.
- **Recurring packs:** use the `Re-run:` field (`route.md`, step 3) to run the earlier note's saved script on a new CSV; do not rebuild.

## update-context
Not a loop job. Follow `workflows/update-context.md`.
