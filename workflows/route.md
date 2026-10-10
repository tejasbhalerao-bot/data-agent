---
name: route
description: Entry point for all data-agent work. Always runs first. Checks the request is complete, picks the job, loads context, checks saved notes, then hands to the loop.
---

# Route

Always first for data requests, never skipped. Use only the local files in `workflows/`; the skills policy is in the root `CLAUDE.md`.

## 1. Resume check
Any note in the project's `insights/` with `status: awaiting-data`? Offer to continue it (go to loop phase 4). Check `awaiting:` against `raw-data/`.

## 2. Job
An explicit `Job:` line wins (analyse, model, design, rollout, measure, update-context). Otherwise infer from the request and say so. Split bundled requests into separate notes, one objective each.

## 3. Ready-check
Check the request against the job's required inputs in `jobs.md`. Classify each gap:

- **Settled by a rule:** `context/rules.md` has a rule that covers it. Apply it, do not ask, and say so on the first line of the answer.
- **Blocking:** everything else that is missing and changes the answer: the time window, the comparison group, an undefined metric, a cohort definition, a missing control, missing PRD input, or no project (unless a saved note answers it). Send **one** message listing all blocking gaps, then continue. Never ask one question at a time.

Ask only what context cannot answer: check `metrics.md`, `schema.md` and `rules.md` first.

## 4. Load context
Read `context/CLAUDE.md`, `context/metrics.md`, `context/rules.md`, and `context/schema.md` (the tables whose `Systems:` flag matches the request). Read the project's `context/` folder and `data-sources.md`. Read the matching system folders of `~/pm-agent/context/` (product flows, read only; see `context/CLAUDE.md`). Then scan the project's saved notes (`archives/<project>/insights/`; other projects' notes for the same metric), the "Reference queries" section of `schema.md` and the project's `raw-data/` listing for an existing answer. Output:

```
[CONTEXT LOADED]
Project: <slug>  Systems: <list>  Verticals: <list>
Loaded: <paths>
Product docs: <pm-agent paths, or none>
Reusable: <saved notes / queries / CSVs on disk, or none>
Gaps: <systems with no docs, loaded files older than 90 days, open questions in `schema.md` or `metrics.md` that touch this request>
[/CONTEXT LOADED]
```

If a named system has no documents, offer once: pause and add them, or proceed with flagged assumptions.
If two documents disagree, the later `updated` date wins; if a metric has conflicting variants in `metrics.md`, ask which to use.

## 5. Saved notes, and whether to write a note
- **Saved-note check:** if a note in `archives/<project>/insights/` (or another project's, for the same metric) answers the request and its data window ended within the last 7 days, quote it with its window and date, offer a refresh, and stop. A stale or partial match is not enough: carry on.
- **Note or chat:** write a note only if Tejas asks for one, or the job is `design` or `rollout` (their deliverable is a document). Otherwise the loop runs without a brief and the answer goes in chat.
- **Project:** needed for anything that creates files, which is every new query or script; not needed when a saved note answers it. If none is named, ask which; if it is new, create it from `archives/_template`. Nothing is saved without one.

Then follow `workflows/loop.md`. For job-specific intake, method and output, use the card in `workflows/jobs.md`.
