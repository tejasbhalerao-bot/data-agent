---
name: route
description: Entry point for all data-agent work. Always runs first. Identifies the project and job, loads context, checks saved notes, checks the request is complete, then hands to the loop.
---

# Route

Always first for data requests, never skipped. Use only the local files in `workflows/`; the skills policy is in the root `CLAUDE.md`.

## 1. Project, systems, verticals
Read from the request: the **project** (a folder in `archives/`; may be none yet), the **systems** it touches (allocation, tracking, serviceability, eta, communications) and the **verticals** (hyperlocal, courier or B2B; forward or reverse). Anything you cannot read is a gap for step 6.

## 2. Unfinished work
If the project has a note with `status: awaiting-data`, offer to continue it: check its `awaiting:` files in `raw-data/`, then go to step 4 of `loop.md`. A chat answer has no note; it resumes through the queries and CSVs already in the project (`loop.md`, step 3, "Reuse first").

## 3. Job
An explicit `Job:` line wins (analyse, model, design, rollout, measure, update-context). Otherwise infer it and say so. Split a request with several objectives into separate requests.

## 4. Load context
- `context/metrics.md` and `context/rules.md`, always.
- `context/schema.md`: Key lookups, plus the tables whose `Systems:` flag matches.
- The project's `context/` folder and its `data-sources.md`.
- The PM agent's product docs for the matching systems, loaded the way it does (rules in `context/CLAUDE.md`).

Then output:
```
[CONTEXT LOADED]
Project: <name>  Systems: <list>  Verticals: <list>
Loaded: <paths>
Product docs: <pm-agent paths, or none>
Gaps: <systems with no docs, loaded files older than 90 days, open questions in schema.md or metrics.md that touch this request>
[/CONTEXT LOADED]
```
A system with no documents, or two documents that disagree: follow `context/CLAUDE.md`. A metric with conflicting definitions in `metrics.md`: ask which to use.

## 5. Saved notes
Search `insights/` in the project, or in every project if none is named, and other projects' notes for the same metric. If a note answers the request, and the data window stated in the note ended within the last 7 days, quote it with its window and date, offer a refresh, and **stop**. A note with no stated data window does not count.

## 6. Is the request complete?
Check it against the job's required inputs in `jobs.md`.
- **Settled by a rule:** `context/rules.md` covers it. Apply it, do not ask, and say so on the first line of the answer.
- **Missing:** the project (see step 7), systems or verticals, the time window, the comparison group, an undefined metric, a cohort definition, a control, PRD input. Send **one** message listing everything missing: plain English, no jargon, one question per line, 20 words or fewer each. Never ask one question at a time. Ask only what `metrics.md`, `schema.md`, `rules.md` and the product docs cannot answer.

## 7. Note or chat, and project
- **Note:** write one only if Tejas asks for it, or the job is `design` or `rollout` (their deliverable is a document). Otherwise the loop runs without a brief and the answer goes in chat.
- **Project:** needed for anything that creates files, which is every new query or script. If none is named, ask which; if it is new, create it from `archives/_template`. Nothing is saved without one.

## 8. Flow reading, then the loop
Write one line, "My reading of the flow: …": what the customer or operator sees, and which tables record it, from the product docs and `schema.md`. Then follow `loop.md`, which passes the line to Tejas with the queries. Job-specific method and output are in `jobs.md`.
