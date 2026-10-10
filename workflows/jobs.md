---
name: jobs
description: The five job cards. Each lists required inputs, method and what the note adds. Used by route.md (completeness check) and loop.md.
---

# Jobs

Every job starts with a brief that Tejas approves (`loop.md`, phase 2); the cards below say what each brief and note must cover. The brief lists the metrics and cuts (M1…) that the job will produce; if a job produces no numbers (for example an analytics requirements document), it has no queries or scripts to tie back. Common required inputs for every job: **Job, Project, Decision this feeds** (optional; it shapes the answer, it does not trigger a note), Scope (window, cohort, comparison), Definitions (default: `metrics.md`). The cards add to these.

## analyse (look backward: what happened, where, why)
- **Required:** window, cohort, comparison.
- **Method:** baseline, then segment cuts on the wide pull (courier, warehouse, pincode, vertical, SDD x inventory, day), confounder check (mix shift, seasonality, sample size), reconcile against a known total or second source. Test the counter-hypothesis.
- **Note adds:** where it concentrates; what it is not; what was ruled out.

## model (look forward: size it, simulate it, compare options)
- **Required:** the lever, the assumptions (each named), the horizon, and for a comparison the alternatives.
- **Method:** counterfactual or backtest on historical data. Low / base / high cases, never a point estimate alone. Sensitivity to the one or two assumptions that move the answer most. Name a floor (provably addressable) and a ceiling.
- **Note adds:** assumption table, range, break-even, what would change the conclusion.

## design (decide how to measure before building)
- **Required:** the PRD text or its key points, supplied in the request. Mode: **ard** ("requirements doc": analytics requirements document), **experiment** ("experiment plan"), or both. "Metrics", "data check" and "events to track" are parts of the same note. For an experiment: hypothesis and target metric.
- **Method:** (1) data feasibility: does each field exist, is it populated and reliable (use schema, probes, the open questions in `schema.md` and the instrumentation note in `context/CLAUDE.md`); (2) metric definitions: numerator, denominator, exclusions, anchor, written to `metrics.md` after approval; (3) instrumentation needs for engineering; (4) for an experiment: primary and guardrail metrics, MDE, sample size, duration, holdout, assignment, SRM check, ship / iterate / kill thresholds (`templates/methods.md`).
- **ard mode:** the note is the ARD. Sections: objective and the decision it supports; metric definitions (names from `metrics.md`, new ones flagged); **instrumentation table** (event or field, properties, trigger, owner system, status Present / Partial / Missing from `schema.md` and the instrumentation note in `context/CLAUDE.md`); **ER diagram** of the entities and tables involved (Mermaid `erDiagram`, built from `schema.md` join keys, unverified keys dashed in a caption); data feasibility and gaps; open questions for engineering.
- **Note adds:** a paste-ready block for the PRD (metrics, instrumentation, experiment plan), or the ARD sections above.

## rollout (design the GTM)
- **Required:** the PM's rollout plan as supplied: stages, locations, percentages, launch parameters, intended duration. Anything absent is asked in the one batched message.
- **Method:** size each stage from data (eligible orders, customers or lanes per location per day); check the stage is large enough to read the success and guardrail metrics (`templates/methods.md`); propose stage gates (go / hold / rollback) with thresholds tied to `metrics.md`; propose the minimum duration per stage; flag overlaps with other live changes and locations with thin data.
- **Note adds:** rollout table (stage, locations, %, expected volume, duration, gate metrics and thresholds, rollback trigger) and readiness checks (instrumentation live, baseline frozen). The PM owns the plan; the analyst sizes and challenges it.

## measure (watch a launch)
- **Required:** mode (**baseline** = "before launch", **day1** = "day 1", **day7** = "day 7", **health** = "other day", or **readout** = "final result", the end of the GTM), launch date, control or baseline window, metrics (from `metrics.md` or the PRD), cuts the PM wants. The analyst proposes extra cuts and reports which were added.
- **baseline:** define the baseline and comparison windows (match day-of-week, exclude known anomalies), run the correctness checks (row counts reconcile, key unique, no gaps in days), freeze the snapshot, test the queries on historical or shadow data, propose alert thresholds. Save the snapshot CSV name in the note.
- **day1 / day7 / health:** instrumentation firing, guardrails against thresholds, anomalies, an early directional read with an explicit "too early" caveat.
- **readout:** impact versus baseline or control with confidence intervals, segment cuts, side effects, power check. End with **ship / iterate / kill** and the reason.
- **Dashboard (any mode, on request):** a dashboard spec in the note: cards, the saved query behind each, filters and cuts, refresh cadence and alert thresholds. Tejas builds it in Metabase from the spec; alternatively a static HTML dashboard from the CSVs via the `data:build-dashboard` output skill.
- **Recurring packs:** re-run the saved query and script on a new CSV; do not rebuild.

## update-context
Not a loop job. Follow `workflows/update-context.md`.
