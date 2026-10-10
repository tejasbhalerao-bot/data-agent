---
project: <slug>
job: analyse | model | design | rollout | measure
tier: 1 | 2
status: brief | awaiting-data | analysing | review | saved
awaiting: []
defaults_used: []
signed_off: false
as_of: YYYY-MM-DD
---

# <Title: the question, as a question or a claim>

**Defaults used:** <field = value, or "none">

## Answer
<One or two sentences with the number and the window. The decision it supports.>

## So what
<Recommended decision or next action. For measure/readout: ship / iterate / kill. For model: the range and what would change it.>

## Brief  (Tier 2; delete once answered if unchanged)
- **Objective:**
- **Questions:** Q1 ... (each independently answerable)
- **Definitions used:** <metric names from metrics.md, variant if any>
- **Tables / files:**
- **Expected output:** <columns, grain>

## Evidence
<Full tables with counts and percentages. Every figure comes from a script output. Name the script and the output file (local only).>

## Definitions and exclusions
<Exclusions applied (rules.md codes), cohort, window, denominators.>

## Caveats and confidence
<Data-quality flags, sample-size limits, unreconciled differences, what is assumed.>

## Next check
<The one or two follow-ups worth running, if any.>

<!-- Job additions: analyse: where it concentrates / what it is not. model: assumption table, low/base/high, break-even. design: paste-ready PRD block (metrics, instrumentation, experiment plan). measure: mode-specific section; readout ends with the decision. -->
