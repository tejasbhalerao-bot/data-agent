# Data Sources — pba-cr

PBA change request: correct how PBA (Clickpost performance-based allocation) builds the customer promise, removing the double-counted wait from WH processing to dispatch, and track PBA against internal logic on the new instrumentation. Project created 2026-10-13. Start with `context/2026-10-13-pba-cr-source-digest-v1.md`.

## Local data (gitignored; list every CSV so the router can reuse it)

| File | Description | Window | Grain | Produced by | Location |
|------|-------------|--------|-------|-------------|----------|
| fahad-raw-dump-1.csv | Q1 v2 base extract, run by engineering (Fahad) on a test window. 20,504 orders, 86 columns. Profile: `outputs/fahad-raw-dump-1-profile.txt` (local only) | Orders placed 14 Oct 2026 16:00–20:59 IST, extracted 15 Oct 20:06 IST (before the CR soft go-live; actuals mostly not yet in) | one row per order | `queries-dump/2026-10-15-pba-cr-promise-adherence-base-query-v2.md` with a test window | `raw-data/fahad-raw-dump-1.csv` (local only) |
| fahad-raw-dump-2.csv | Q1 v2 base extract re-run courier-only (non-SDD), by engineering (Fahad), same test window as dump 1. 12,789 orders, 86 columns. Profile: `outputs/fahad-raw-dump-2-profile.txt` (local only). Supersedes dump 1 for this project's scope | Orders placed 14 Oct 2026 16:00–20:59 IST, extracted 15 Oct 20:17 IST | one row per order | `queries-dump/2026-10-15-pba-cr-promise-adherence-base-query-v2.md` with a test window; SDD orders excluded | `raw-data/fahad-raw-dump-2.csv` (local only) |

## Project context files (committed)

| File | What it holds |
|------|---------------|
| `context/2026-10-13-pba-cr-source-digest-v1.md` | Summary of the original PRD, the CR, the tracking plan and the instrumentation, plus open questions Q1–Q12 |
| `context/2026-10-13-tracking-question-field-map-v1.md` | Each tracking question mapped to the field that answers it, in both the DRAFT and the artifact layouts |
| `context/2026-10-13-eta-instrumentation-draft-record-v1.json` | Engineering's proposed `ETA_INSTRUMENTATION` record (DRAFT #24), unchanged copy |
| `context/2026-10-13-hard-allocation-instrumentation-draft-record-v1.json` | Engineering's proposed `HARD_ALLOCATION_INSTRUMENTATION` record (DRAFT #26), unchanged copy |
| `context/2026-10-13-instrumentation-field-dictionary-v1.csv` | The artifact's field dictionary: 695 field paths across the 3 record types, with definition, values, null-when, renamed-from and live/proposed status |
| `context/2026-10-13-instrumentation-scenarios-v1.md` | The artifact's question guide, plus an index of its 141 scenario records |
| `context/2026-10-14-pba-instrumentation-schema-details-v1.md` | Where to find each PBA value in the instrumentation, soft and hard, worked on order 57051205 (Q1–Q14 with primary and secondary fields, notes, open items). Copied from the Claude Docs "PBA Instrumentation Q&A" tab, rev 92 |
| `context/2026-10-13-instrumentation-scenario-records-eta-hard-v1.json` | The 21 full ETA and HARD scenario records from the artifact (spec examples, not production data) |

## Documents and external sources

| Source | Description | Location |
|--------|-------------|----------|
| [PRD] PBA integration with Clickpost | Original PBA PRD: soft and hard allocation logic, fallbacks, metrics, shadow mode, and the 5% post-release readout | https://docs.google.com/document/d/1pV4RYHdP2a6yfpOBdDBJPL7RZMBwf9xZYRpGEzI-Jvc |
| [PRD] PBA CR | The change request: new soft and hard promise construction, gated by two feature flags | https://docs.google.com/document/d/1dRRBcfVkMmbBBNCAzfmEAdHtsxCq4T5DurwQ8_pD8xs |
| PBA CR Schema Clarifications | Tejas's tracking plan (5 metrics) and the questions about where each field lives | https://docs.google.com/document/d/14OPOJnW8gqXtDGXHR4FjyE9Rato-58olAAqeDUgldQY |
| PBA Instrumentation Records (engineering artifact) | Record types, field dictionary, question guide and scenario records for `logistics_instrumentation` | https://claude.ai/artifact/63SppFoRTXRUAdWqomvCE5 |
| ARD: PBA Integration Setup | Analytics requirements linked from the original PRD (not yet read) | https://docs.google.com/document/d/16b_ATSAihXd6DMoL2FNXiXJOcrU5VLM4jHLJ85jDg2Q |
| Metric Measurement Framework | Linked from the original PRD (not yet read) | https://docs.google.com/document/d/1Cwom3vdvUB5R7G3BQLalO2lca8wvwHEKpvExwMuXG2I |
| PM agent product docs | `~/pm-agent/context/allocation/pba-clickpost.md`, `performance-based-speed-calculation-and-allocation.md`, `adding-promise-buffers.md`, `serviceability-check-at-soft-allocation.md`; `~/pm-agent/context/eta/promise-instrumentation.md`, `multiple-cutoffs-v2.md`, `warehouse-processing-time-revamp.md` (read only; load per `context/CLAUDE.md` when a request comes in) | `~/pm-agent/context/` |
| Prior project | `archives/pba-integration/`: the `logistics_allocation_audit` and `logistics_rails_api_audit` queries, and the 2026-06-25 PBA vs internal note | this repo |

## Project-specific rules
None yet. Candidates to settle in the first brief: which soft call stands for an order (Q5), the minutes-to-days conversion (Q9), and how "in rollout" is defined per stage (Q4). See the source digest.
