# Truemeds Data Agent Context

## Who and what
- **Tejas Bhalerao:** the PM. Requester, query executor, and approver. There is no analyst; this repo plays that role.
- **Data team (for follow-ups that need an owner):** Dinesh (Director, Analytics), Ashish (Analyst).
- **Engineering owners of the systems below:** Mangesh and Deepak (VP Engineering), Hasan (Principal Engineer).

## Systems and verticals
Systems: **Allocation**, **Tracking** (actuals), **Serviceability**, **ETA** (also called Promise), **Communications**. Same five as the PM agent (`~/pm-agent`), so names match across repos.
Verticals: Hyperlocal Forward, Hyperlocal Reverse, Courier Forward, Courier Reverse, B2B Forward, B2B Reverse.
3rd-party rails (Clickpost, Locus) have no context file yet. Communications has no schema documented.
Not yet done: the instrumentation grounding pass (checking the Mixpanel event list and `instrumentation_details` against the real data). Until it is done, `instrumentation-audit` conclusions are hypotheses.

## Product context (read only, outside this repo)
How each system works for the customer and the operator is kept by Tejas in the PM agent, in `~/pm-agent/context/<system>/` (folders: `allocation`, `tracking`, `serviceability`, `eta`, `communications`). Load it the way the PM agent does (its rules are in `~/pm-agent/context/README.md`):
- For each system the request touches, read **every** document in that system's folder.
- Keep documents whose `verticals` tag includes a requested vertical or `all`; skip the rest. A document filed in several folders (same `source`) is read once.
- If two documents disagree, the later `updated` date wins. Undated documents rank below dated ones. Flag any document older than 90 days.
- If a system's folder has no usable documents, say so once and ask: pause so Tejas can add them to the PM agent, or proceed with flagged assumptions. Do not fill the gap from general knowledge.
- Read only: never copy, edit or add to these documents. If one disagrees with `schema.md`, say so and ask Tejas which is right.

## What is here
Three files: `schema.md`, `metrics.md`, `rules.md`. Results live in project notes, not here. What each holds and when it is used: root `CLAUDE.md`, "Elements of the repo".

Conventions and loading rules: `context/README.md`.

## Source of data
Redshift (schema `tmmumpsdb`, queried through Metabase, 10-minute timeout), Mixpanel (events), and Google Sheets/Docs for experiment results and PRDs. `schema.md` and each project's `data-sources.md` name their source.

## Entry point
All data work starts at `workflows/route.md`. The skills policy (analysis skills banned, output-format skills allowed) is in the root `CLAUDE.md`.
