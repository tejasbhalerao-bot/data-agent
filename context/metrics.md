---
title: Metric dictionary
type: metric-definition
systems: [all]
verticals: [all]
source: none yet
updated: 2026-10-12
---

# Metric dictionary

The one agreed meaning of each metric. Empty for now. It is filled project by project: a metric is added when Tejas approves its definition in a brief, or asks for it directly (`workflows/update-context.md`). Earlier definitions from past projects are still in those projects' own `context/` folders.

If another project defines the same metric differently, keep both and mark the row CONFLICT until Tejas picks one.

## Entry layout
| Field | What to write |
|-------|---------------|
| Metric | The name |
| Meaning | One sentence |
| Formula | Using named columns, for example `DATE(delivery_attempt_time) - DATE(digitised_delivery_promise)` |
| Unit | Days, minutes, %, count |
| Exclusions | Which orders are left out, and why |
| Caveats | Edge cases and data quirks |
| Source | The project and note it was agreed in |

## Metrics
None yet.
