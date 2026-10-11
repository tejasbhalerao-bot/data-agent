# Context conventions

Shared knowledge, organised so each fact has one home. Project-only material stays in `archives/<project>/context/`.

## Format
Every file in `context/` starts with:

```
---
title: <name>
type: schema | metric-definition | business-rule | other
systems: [allocation, tracking]
verticals: [all]
source: <where it came from>
updated: YYYY-MM-DD
---
```

| Field | Rule |
|-------|------|
| `verticals` | `all`, or any of `hyperlocal-forward`, `hyperlocal-reverse`, `courier-forward`, `courier-reverse`, `b2b-forward`, `b2b-reverse` |
| `updated` | The date the content was last confirmed, not merely touched. If two documents disagree, the later date wins |

## How context is loaded
| # | Step | Rule |
|---|------|------|
| 1 | Read the systems and verticals from the request | |
| 2 | Read `schema.md` | The Key lookups, plus the tables whose `Systems:` flag matches a requested system or says `all` |
| 3 | Read `metrics.md` and `rules.md` | Always |
| 4 | Read the PM agent's product documents | `~/pm-agent/context/<system>/`, loaded the way the PM agent does (see `context/CLAUDE.md`). Read only |
| 5 | Look for an existing answer | Search project notes (`archives/*/insights/`) and the "Reference queries" section of `schema.md` before building anything |
| 6 | A system has no documents | Say so once. Do not fill the gap from general knowledge |

## Out-of-date material
- Flag any loaded file older than 90 days.
- Quote a saved note only if its data window and scope match the request. For a rolling window ("last 30 days"), its data must have ended within the last 7 days. Give the note's window and as-of date.
