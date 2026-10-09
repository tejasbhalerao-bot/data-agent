---
title: Statistical methods reference
type: other
systems: [all]
verticals: [all]
source: standard methods; Truemeds-specific defaults marked
updated: 2026-10-09
---

# Methods

Use these when a job card calls for them. State every parameter chosen in the note.

## Sample size for a proportion (two-sided A/B)
`n per arm = 2 * (z_a + z_b)^2 * p(1-p) / delta^2` with `p` the baseline rate, `delta` the absolute minimum detectable effect (MDE). Defaults: alpha 0.05 (`z_a = 1.96`), power 0.80 (`z_b = 0.84`). Report n per arm, total, and expected duration at the observed daily eligible volume. For a continuous metric use `n = 2 * (z_a + z_b)^2 * sigma^2 / delta^2`.
- Traffic that is not randomised per user (for example per order) needs the cluster-adjusted n: multiply by `1 + (m - 1) * icc`.
- If the metric is low-volume (for example SDD cells in single or double digits), say it is not analysable rather than test it.

## Experiment design checklist
Hypothesis with direction; primary metric; 1 to 3 guardrails with thresholds; MDE; n and duration (full weeks, covering day-of-week effects); universe and exclusions; assignment unit and hash; traffic split with a holdout; ship / iterate / kill rules written before launch.

## SRM (sample ratio mismatch)
Chi-square test of observed arm counts against the planned split. `p < 0.001` means the assignment is broken: stop and fix before reading any result.

## Reading a result
- Difference with a 95% confidence interval, not only a p-value. Proportions: Wilson or normal approximation with large n; use a two-proportion z-test for two arms.
- Do not peek and stop early on significance; read at the planned n or use a pre-registered sequential rule.
- Multiple segments: treat as exploratory unless pre-specified; correct for many comparisons or label as directional.
- Report the effect on the guardrails even when the primary metric wins.

## Pre/post and shadow comparisons (no randomisation)
State the confounders: mix shift, seasonality, concurrent launches. Prefer same-lane or same-cohort matching (as in the PBA same-courier cohort). Say "associated with", not "caused".

## Ranges and sizing
Give low / base / high, naming the assumption that moves each. Separate a **floor** (provably addressable, observed in the data) from a **ceiling** (all of the addressable pool). Example: reallocation uplift 2.04pp floor, 6.20pp ceiling (F5 in `findings.md`).

## Sanity checks before any figure is published
Row count reconciles to the extract; the population equals the intended denominator; percentages of a partition add to 100; a headline comparison is re-cut by the largest segment (Simpson's paradox).
