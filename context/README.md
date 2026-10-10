# Context conventions

Shared knowledge, organised so each fact has one home. Project-only material stays in `archives/<project>/context/`.

## Front matter
Every file in `context/` starts with:

```
---
title: <name>
type: schema | metric-definition | business-rule | past-prd | other
systems: [allocation, tracking]
verticals: [all]
source: <where it came from>
updated: YYYY-MM-DD
---
```

- `verticals`: `all`, or any of `hyperlocal-forward`, `hyperlocal-reverse`, `courier-forward`, `courier-reverse`, `b2b-forward`, `b2b-reverse`.
- `updated`: the date the content was last confirmed, not merely touched. When two documents disagree, the later `updated` wins.

## Loading
1. Identify systems and verticals in the request.
2. Read `schema.md` (Key lookups, plus the tables whose `Systems:` flag includes a requested system or `all`), and `metrics.md` and `rules.md` always.
3. Scan project notes (`archives/*/insights/`) and the "Reference queries" section of `schema.md` for reuse before building anything.
4. Also load the matching system folders of `~/pm-agent/context/` the way the PM agent does: every document per system, filtered by vertical (product flows; read only, see `context/CLAUDE.md`).
5. A system with no documents is surfaced once; do not fill the gap from general knowledge.

## Staleness
Flag any loaded file older than 90 days. Notes are time-bound: quote one only if its data window ended within the last 7 days, and give its window and as-of date.
