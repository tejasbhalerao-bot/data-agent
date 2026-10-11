# Design: experiment plan

Goes under "Answer" in the note. Delete the guidance in angle brackets. Settings marked "Tejas" are his to give.

## Headline
<One or two sentences: what is tested, on whom, for how long.>

## Hypothesis
<If we change X for Y, then metric Z moves in direction D by at least E.>

## Metrics
- **Main metric:** <from metrics.md or the metric definitions table.>
- **Safety metrics (must not get worse), with limits:** <each, with its limit (Tejas).>

## Who is in it
- **Eligible:** <the universe and exclusions.>
- **Assignment:** <the unit and how it is randomised.>
- **Split and holdout (a group left unchanged):** <percentages (Tejas).>

## Size and duration
| Setting | Value | Set by |
|---------|-------|--------|
| Smallest change worth detecting | | Tejas |
| Confidence and power | 95% and 80% unless Tejas says otherwise | Tejas |
| Longest duration allowed | | Tejas |
| Sample size per group | | calculated (`methods.md`) |
| Expected duration at current volume | | calculated |

## Checks planned
<A check that group sizes match the plan (SRM); how interactions with other live changes are handled.>

## Ship, iterate or kill
<Thresholds for each outcome, written before launch (Tejas).>

## Paste-ready block for the PRD
<Hypothesis, metrics, split, duration and thresholds, ready to paste.>

## Evidence
<The calculation, cited by script and output file (local only).>
