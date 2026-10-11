---
title: Calculation methods
type: other
systems: [all]
verticals: [all]
source: standard methods; Truemeds-specific defaults marked
updated: 2026-10-12
---

# Calculation methods

Reference for the formulas and checks a job in `workflows/jobs.md` calls for. State every setting used in the note. Settings that are Tejas's to give are marked.

## Sample size for an experiment
| Setting | Value | Set by |
|---------|-------|--------|
| Baseline rate `p` | Observed from the data | Data |
| Smallest change worth detecting `delta` (absolute) | | Tejas |
| Confidence and power | 95% (`z_a = 1.96`) and 80% (`z_b = 0.84`) unless Tejas says otherwise | Tejas |

- **Proportion metric:** `n per group = 2 * (z_a + z_b)^2 * p(1-p) / delta^2`.
- **Average metric:** `n per group = 2 * (z_a + z_b)^2 * sigma^2 / delta^2`, where `sigma` is the standard deviation.
- **Not randomised per user** (for example per order): multiply `n` by `1 + (m - 1) * icc`, where `m` is orders per user and `icc` is how alike one user's orders are.
- **Report** `n` per group, the total, and the days needed at the current daily eligible volume. Round up to full weeks.
- **Very small cells** (for example SDD cells with single or double digits): say they cannot be analysed. Do not test them.

## Experiment plan checklist
Hypothesis with direction; main metric; one to three safety metrics with limits; smallest change worth detecting; sample size and duration; who is eligible and what is excluded; the assignment unit; the split, with a holdout (a group left unchanged); and the ship / iterate / kill rules, written before launch.

## Check that group sizes match the plan (SRM)
Run a chi-square test of the actual group counts against the planned split. If `p < 0.001`, the assignment is broken: stop and fix it before reading any result.

## Reading a result
- Show the difference with its 95% interval, not only a p-value. For two proportions, use a two-proportion z-test.
- Do not stop early because a result looks significant. Read it at the planned sample size.
- Splits by segment are exploratory unless planned in advance. Label them "directional", or correct for the number of comparisons.
- Report the safety metrics even when the main metric wins.

## Comparisons without randomisation (before and after, shadow mode)
Name what else could explain the result: a change in the mix of segments, seasonality, other launches at the same time. Prefer comparing the same lane or cohort (as in the PBA same-courier comparison). Say "associated with", not "caused".

## Ranges for sizing
Give low, base and high, and name the assumption that moves each. Separate a **floor** (provably addressable, seen in the data) from a **ceiling** (the whole addressable pool). Example: reallocation uplift of 2.04pp floor and 6.20pp ceiling (note #62 in `archives/egregiously-miscalibrated-promises/insights/`).

## Checks before any figure is shown
- The row count matches the extract.
- The population is the intended denominator.
- Percentages of a whole add to 100.
- A headline comparison is re-checked within the largest segment, in case the overall result hides the opposite trend.
