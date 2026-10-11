---
project: <project folder name>
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

<!-- The note is the frame below. Fill each part from its template:
     - "Answer" and the job's evidence: the job's template (analyse.md, model.md, ard.md, experiment.md, gtm.md or measure.md). Until the answer exists, write "Pending".
     - "Approved brief": brief.md, as approved.
     - "Queries to run": the table below; queries are files made from query.md.
     - "Scripts and outputs": the table below; scripts are files made from script.md. -->

## Answer
<Pending until the numbers are calculated. Then paste the body of the job's template here, from its headline to its evidence.>

## Approved brief
<Paste the brief exactly as approved (templates/brief.md).>

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

## Definitions and filters
<Filters applied, cohort, window, denominators.>

## Caveats and confidence
<Data-quality flags, sample-size limits, unreconciled differences, what is assumed.>

## Next check
<The one or two follow-ups worth running, if any.>
