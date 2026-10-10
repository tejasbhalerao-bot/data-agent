# Truemeds Data Agent Context

## Who and what
- **Tejas Bhalerao:** the PM. Requester, query executor, and approver. There is no analyst; this repo plays that role.
- **Data team (for follow-ups that need an owner):** Dinesh (Director, Analytics), Ashish (Analyst).
- **Engineering owners of the systems below:** Mangesh and Deepak (VP Engineering), Hasan (Principal Engineer).

## Systems and verticals
Systems: **Allocation**, **Tracking** (actuals), **Serviceability**, **ETA** (also called Promise), **Communications**. Same five as the PM agent (`~/pm-agent`), so names match across repos.
Verticals: Hyperlocal Forward, Hyperlocal Reverse, Courier Forward, Courier Reverse, B2B Forward, B2B Reverse.
3rd-party rails (Clickpost, Locus) have no context file yet. Communications has no schema documented (`rules.md` G6).

## What is here
Three files: `schema.md`, `metrics.md`, `rules.md`. Results live in project notes, not here. What each holds and when it is used: root `CLAUDE.md`, "Elements of the repo".

Conventions and loading rules: `context/README.md`.

## Source of data
Redshift (schema `tmmumpsdb`, queried through Metabase, 10-minute timeout), Mixpanel (events), and Google Sheets/Docs for experiment results and PRDs. `schema.md` and each project's `data-sources.md` name their source.

## Entry point
All data work starts at `workflows/route.md`. The skills policy (analysis skills banned, output-format skills allowed) is in the root `CLAUDE.md`.
