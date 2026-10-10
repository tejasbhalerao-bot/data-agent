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
| File | Holds |
|---|---|
| `schema.md` | Every table, each flagged with its `Systems:`, with provenance, plus validated reference queries. Load the tables whose flag matches the request. |
| `metrics.md` | One definition per metric, variants and conflicts flagged |
| `rules.md` | Standing exclusions, default scope, vocabulary, value gotchas, table gotchas, open gaps |
| `findings.md` | Durable results with window and as-of date |

Conventions and loading rules: `context/README.md`.

## Source of data
Redshift (schema `tmmumpsdb`, queried through Metabase, 10-minute timeout), Mixpanel (events), and Google Sheets/Docs for experiment results and PRDs. `schema.md` and each project's `data-sources.md` name their source.

## Entry point
All work starts at `workflows/route.md`. Do not invoke built-in analysis skills (`data:*`, or `anthropic-skills:*` for analysis, PRD or research) for work this repo handles: they lack the metric dictionary, the rules and the review. Output-format skills (`xlsx`, `pdf`, `docx`, `pptx`, `dataviz`, `data:create-viz`) are allowed when Tejas asks for that format; the figures in them still come from this repo's scripts.
