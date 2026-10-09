---
name: jobs
description: The four job cards. Each lists required inputs, method and what the note adds. Used by route.md (ready-check) and loop.md.
---

# Jobs

Common required inputs for every job: **Job, Project, Decision this feeds** (Tier 2 only), Scope (defaultable), Definitions (default: `metrics.md`). The cards add to these.

## analyse (look backward: what happened, where, why)
- **Required:** window and cohort (defaultable), comparison (prior period by default).
- **Method:** baseline, then segment cuts on the wide pull (courier, warehouse, pincode, vertical, SDD x inventory, day), confounder check (mix shift, seasonality, sample size), reconcile against a known total or second source. Test the counter-hypothesis.
- **Note adds:** where it concentrates; what it is not; what was ruled out.

## model (look forward: size it, simulate it, compare options)
- **Required:** the lever, the assumptions (each named), the horizon, and for a comparison the alternatives.
- **Method:** counterfactual or backtest on historical data. Low / base / high cases, never a point estimate alone. Sensitivity to the one or two assumptions that move the answer most. Name a floor (provably addressable) and a ceiling.
- **Note adds:** assumption table, range, break-even, what would change the conclusion.

## design (decide how to measure before building)
- **Required:** the PRD text or its key points, supplied in the request. For an experiment: hypothesis and target metric.
- **Method:** (1) data feasibility: does each field exist, is it populated and reliable (use schema, probes, the instrumentation caveats in `rules.md`); (2) metric definitions: numerator, denominator, exclusions, anchor, written to `metrics.md` after approval; (3) instrumentation needs for engineering; (4) for an experiment: primary and guardrail metrics, MDE, sample size, duration, holdout, assignment, SRM check, ship / iterate / kill thresholds (`templates/methods.md`).
- **Note adds:** a paste-ready block for the PRD (metrics, instrumentation, experiment plan).

## measure (watch a launch)
- **Required:** mode (**baseline**, **health** or **readout**), launch date, control or baseline window, metrics (from `metrics.md` or the PRD).
- **baseline:** freeze the pre-launch snapshot, test the queries on historical or shadow data, propose alert thresholds. Save the snapshot CSV name in the note.
- **health (D1 / D3 / D7):** instrumentation firing, guardrails against thresholds, anomalies, an early directional read with an explicit "too early" caveat.
- **readout:** impact versus baseline or control with confidence intervals, segment cuts, side effects, power check. End with **ship / iterate / kill** and the reason.
- **Recurring packs:** re-run the saved query and script on a new CSV; do not rebuild.

## update-context
Not a loop job. Follow `workflows/update-context.md`.
