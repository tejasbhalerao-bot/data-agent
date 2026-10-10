---
name: route
description: Entry point for all data-agent work. Always runs first. Identifies the project and job, loads context, checks saved notes, checks the request is complete, then hands to the loop.
---

# Route

Always first for data requests, never skipped. Use only the local files in `workflows/`; the skills policy is in the root `CLAUDE.md`.

**Not a data request?** (a question about the repo, edits to workflows or docs, git housekeeping) Stop here and handle it directly, as `CLAUDE.md` says.
**Follow-up in the same session?** Do not reload what is already loaded. Load only the systems, verticals or project not yet loaded.

## 1. Project, systems, verticals
Read from the request: the **project** (a folder in `archives/`; may be none yet), the **systems** it touches (allocation, tracking, serviceability, eta, communications) and the **verticals** (hyperlocal, courier or B2B; forward or reverse). Anything you cannot read is a gap for step 6. Steps 4 and 5 need the systems: if you could not read them, skip to step 6, ask for everything missing in one message, then continue from step 4.

## 2. Unfinished work
If the project has notes with `status: awaiting-data`, list them (name, and which `awaiting:` files are not yet in `raw-data/`) and ask which to continue. If all files are there, go to step 4 of `loop.md`; if some are missing, say which and stop.

## 3. Job
- An explicit `Job:` line wins (analyse, model, design, rollout, measure, update-context). Otherwise infer it and say so. If two jobs fit equally, ask once.
- **update-context:** stop here and follow `update-context.md`.
- **Re-run:** if the request has a `Re-run:` field, check the new CSV (`loop.md`, phase 4, step 2), then run the named saved script on it (`loop.md`, phase 5), and skip steps 5 and 6 below.
- **Several objectives:** split into separate requests. Tell Tejas the split and the order (dependencies first), keep the list of pending requests, work on one at a time, and when each finishes say "done; next is <request>".

## 4. Load context
- `context/metrics.md` and `context/rules.md`, always.
- `context/schema.md`: Key lookups, plus the tables whose `Systems:` flag matches.
- The project's `context/` folder and its `data-sources.md`.
- The PM agent's product docs for the matching systems, loaded the way it does (rules in `context/CLAUDE.md`).

Then show:
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
Search `insights/` in the project (every project if none is named) and other projects' notes for the same metric. A new project has no notes yet, so only other projects' notes are searched; if none answer, carry on. A note counts only if all of these hold:
- It states its data window, and its metric definitions, cohort and window match the request.
- For a rolling window ("last 30 days"), its data ended within the last 7 days. A fixed past period ("July 2026") has no age limit.

Quote a matching note with its window and date, say if it is not yet signed off, offer a refresh, and **stop**. If Tejas accepts the refresh, continue from step 6 and ignore the note.

## 6. Is the request complete?
Check it against the job's required inputs in `jobs.md`.
- **Settled by a rule:** `context/rules.md` covers it. Apply it, do not ask, and say so on the first line of the answer.
- **Missing:** the project, systems or verticals, the time window, the comparison group, an undefined metric, a cohort definition, a control, PRD input, or anything else that would change the answer. Send **one** message listing everything missing: plain English, no jargon, one question per line, 20 words or fewer each. Never ask one question at a time. Ask only what `metrics.md`, `schema.md`, `rules.md` and the product docs cannot answer. If Tejas answers only part, ask again for the rest only.
- **Project:** needed for every request except one answered by quoting a saved note. If none is named, ask which, listing the folders in `archives/`. If it is new, use a lowercase name with hyphens, run `cp -r archives/_template archives/<name>`, and fill its `context/data-sources.md`. Nothing is saved without a project.

## 7. The note
Every request that is not answered by quoting a saved note gets a note: a `.md` file in the project's `insights/` folder. It starts as the approved brief, grows into the answer, and is committed locally at each stage (rules in `CLAUDE.md`). The loop starts with a brief that Tejas approves.

## 8. Flow reading, then the loop
Write one line, "My reading of the flow: …": what the customer or operator sees, and which tables record it, from the product docs and `schema.md`. If there are no product docs for the systems, say the reading rests on `schema.md` alone. Then follow `loop.md`, which puts the line at the top of the brief for Tejas to approve. Job-specific method and output are in `jobs.md`.
