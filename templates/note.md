---
project: <slug>
job: analyse | model | design | rollout | measure
status: brief | awaiting-data | saved
awaiting: []
assumptions: []
signed_off: false
as_of: YYYY-MM-DD
---

# <Title: the question, as a question or a claim>

**My reading of the flow:** <one line: what the customer or operator sees, and which tables record it>

**Assumptions and rules applied:** <field = value, or "none">

## Answer
<One or two sentences with the number and the window. The decision it supports.>

## So what
<Recommended decision or next action. For measure/readout: ship / iterate / kill. For model: the range and what would change it.>

## Approved brief
- **Objective:**
- **Questions:** <each answerable on its own>
- **Metrics and cuts:**
  - M1: <metric from metrics.md, variant if any> by <cut, or "overall">
  - M2: …
- **Tables / files:**
- **Expected output:** <columns, grain>

## Queries to run
<Added when the queries are ready. Never paste SQL here: each query is its own file. Update a row when a query gets a new version, so it always points to the latest.>

| ID | Purpose | Serves | Latest file | Save the CSV as |
|----|---------|--------|-------------|-----------------|
| Q1 | <what it pulls, in a few words> | M1, M2 | `archives/<project>/queries-dump/<file>-v<n>.md` | `archives/<project>/raw-data/<name>.csv` |
| Q0 | Probe: row count, distinct keys, a reconciling total | none | `archives/<project>/queries-dump/<file>-v<n>.md` | `archives/<project>/raw-data/<name>.csv` |

## Scripts and outputs
<Added when the numbers are calculated. Never paste code here: each script is its own file. Update a row when a script gets a new version. Outputs are local only.>

| ID | Purpose | Serves | Latest file | Reads | Writes | Test | Run with |
|----|---------|--------|-------------|-------|--------|------|----------|
| S1 | <what it calculates, in a few words> | M1, M2 | `archives/<project>/scripts/<file>-v<n>.py` | Q1's CSV | `archives/<project>/outputs/<name>.csv` | `archives/<project>/tests/<file>-v<n>.py`, or "none needed" | `python3 archives/<project>/scripts/<file>-v<n>.py` |

## Evidence
<Full tables with counts and percentages. Every figure comes from a script output. Cite each table by metric ID, script ID and output file, for example "M1, via S1, outputs/<name>.csv" (local only). Every M in the brief has a table here.>

## Definitions and exclusions
<Filters applied, cohort, window, denominators.>

## Caveats and confidence
<Data-quality flags, sample-size limits, unreconciled differences, what is assumed.>

## Next check
<The one or two follow-ups worth running, if any.>

<!-- Job additions: analyse: where it concentrates / what it is not. model: assumption table, low/base/high, break-even. design: paste-ready PRD block (metrics, instrumentation, experiment plan). measure: mode-specific section; readout ends with the decision. -->
