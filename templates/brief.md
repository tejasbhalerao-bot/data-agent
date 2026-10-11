# Brief: <title>

Shown to Tejas in plain English before any work starts. Nothing is built until he approves. Once approved it is pasted into the note under "Approved brief".

**My reading of the flow:** <one line: what the customer or operator sees, and which tables record it. Say if it rests on schema.md alone.>

## Objective
<One sentence: what this will answer or produce.>

## Questions
<Each answerable on its own.>

## Scope
<As agreed. Use what Tejas gave; propose the rest with a one-line reason, and he decides.>
- analyse, model, measure: time window, cohort, comparison.
- design: the PRD, and the systems, events and tables it touches.
- rollout: stages, locations, launch settings.

## Metrics and cuts
Every query and script must serve at least one line. Nothing outside this list is built.
- M1: <metric from metrics.md, variant stated> by <cut, or "overall">
- M2: …

## Metric definitions (only for new or changed metrics)
| Metric | Numerator | Denominator | Exclusions | Anchor (the event or date it is measured from) |
|--------|-----------|-------------|------------|------|
| <name> | | | | |

## Tables used
<From schema.md.>

## Grain and output columns (asked from Tejas)
- One row is: <Tejas's answer. You may suggest, with reasons; he decides.>
- Columns: <Tejas's answer.>

## How it will be calculated
Plain steps, in order. Name each decision that changes the answer, so Tejas can correct it before anything is built. `workflows/jobs.md` lists what each job's steps must cover.
| Step | What it calculates | Rule or formula | Serves | Data from |
|------|--------------------|-----------------|--------|-----------|
| 1 | | | M1 | existing CSV, saved query, new query, or the script alone |

## Job-specific
- model: assumption table. One row per assumption, with a low, base and high value that Tejas gives.
- design: the mode (requirements doc, experiment plan, or both); for an experiment, the settings Tejas gives.
- rollout: the plan as supplied, and the numbers to size per stage.
- measure: the stage; the windows (proposed by you, decided by Tejas); the success and safety limits; the earlier notes used.

## What will be produced
<Queries, a design, a rollout plan, a baseline, a dashboard spec. The result is always a note.>

## Assumptions made
<List, or "none". Add the decision it feeds if Tejas gave one.>

## To approve
Reply "ok" to start, or say what to change.
