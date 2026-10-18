---
title: PBA CR dashboard field mapping
source: agreed with Tejas, metric by metric, from 2026-10-18
applies to: every raw dump from the Q1 base query (`queries-dump/…-promise-adherence-base-query-v2.md`), e.g. fahad-raw-dump-3
status: in progress (Section 1, metric 1 agreed)
---

# PBA CR dashboard field mapping

The reference for building or refreshing the PBA CR dashboard. It records which raw-dump fields compute each number, and how. Section and metric numbers follow the wireframe (https://claude.ai/artifact/XX9QtrxQWPMfiofjq2TjX7) and `2026-10-17-dashboard-structure-from-tejas-v1.md`.

## Rules for every metric
- **Scope:** no date filter for now. A metric covers every order in the dump, or in the combined dumps.
- **Combining dumps:** pool the dumps and count each `ORDER_ID` once. Where an order appears in more than one dump, the newer dump's row wins.
- **Window shown:** every refresh shows the dump name(s), plus the earliest and latest `ORDER_PLACED_AT`.

## Section 1: Funnel

### 1. Total Non-SDD Orders

| Item | Mapping |
|---|---|
| Definition | Number of distinct non-SDD orders in the dump |
| Fields | `ORDER_ID`, `SDD_ENABLED` |
| Calculation | Count distinct `ORDER_ID` where `SDD_ENABLED = false` |
| Included | Orders on a fallback promise with no soft record (`HAS_SOFT_RECORD = false`, `IS_FALLBACK_PROMISE = true`). They are real non-SDD orders, though neither PBA nor internal allocated them |
| Excluded | Rows with blank `SDD_ENABLED`, including non-numeric order ids (e.g. `TM0B0FMMMC24S01`). Counted in the data checks, not dropped silently |
| Agreed | Tejas, 2026-10-18 |
