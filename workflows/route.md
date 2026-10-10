---
name: route
description: Entry point for all data-agent work. Always runs first. Checks the request is complete, picks the job and tier, loads context, then hands to the loop.
---

# Route

Always first for data requests, never skipped. Use only the local files in `workflows/`; the skills policy is in the root `CLAUDE.md`.

## 1. Resume check
Any note in the project's `insights/` with `status: awaiting-data`? Offer to continue it (go to loop phase 4). Check `awaiting:` against `raw-data/`.

## 2. Job
An explicit `Job:` line wins (analyse, model, design, rollout, measure, update-context). Otherwise infer from the request and say so. Split bundled requests into separate notes, one objective each.

## 3. Ready-check
Check the request against the job's required inputs in `jobs.md`. Classify each gap:

- **Defaultable:** fill from `context/rules.md` section 2 (window, verticals, comparison, exclusions). Do not ask. List every default used on the note's first line.
- **Blocking:** an undefined metric, a cohort definition that changes the answer, a missing control, missing PRD input, or (for Tier 1 and 2 only) no project. Send **one** message listing all blocking gaps, then continue. Never ask one question at a time.

Ask only what context cannot answer: check `metrics.md` and `rules.md` first.

## 4. Load context
Read `context/CLAUDE.md`, `context/metrics.md`, `context/rules.md`, and `context/schema.md` (the tables whose `Systems:` flag matches the request). Read the project's `context/` folder and `data-sources.md`. Then scan the project's saved notes (`archives/<project>/insights/`; other projects' notes for the same metric), the "Reference queries" section of `schema.md` and the project's `raw-data/` listing for an existing answer. Output:

```
[CONTEXT LOADED]
Project: <slug>  Systems: <list>  Verticals: <list>
Loaded: <paths>
Reusable: <saved notes / queries / CSVs on disk, or none>
Gaps: <systems with no docs, open rules.md gaps that touch this request>
[/CONTEXT LOADED]
```

If a named system has no documents, offer once: pause and add them, or proceed with flagged assumptions.
If two documents disagree, the later `updated` date wins; if a metric has conflicting variants in `metrics.md`, ask which to use.

## 5. Tier
| Tier | Test | Path |
|---|---|---|
| 0 Recall | A saved note answers it and the as-of date is acceptable | Answer with source and as-of; offer a refresh |
| 1 Quick | Every term resolves in `metrics.md`, every table is in `data/`, one main query | Loop without a brief |
| 2 Full | Anything else | Full loop |

**Project:** Tier 0 needs none (search all projects' notes). Tier 1 and 2 create files, so they need a project folder in `archives/`: if none is named, ask which; if it is new, create it from `archives/_template`. Nothing is saved without one.

Then follow `workflows/loop.md`. For job-specific intake, method and output, use the card in `workflows/jobs.md`.
