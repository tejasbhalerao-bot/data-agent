---
title: Validated query index
type: other
systems: [allocation, tracking, eta]
verticals: [all]
source: project queries-dump folders, migrated 2026-10-09
updated: 2026-10-09
---

# Validated query index

`build-sql` reuses these before writing fresh SQL. Until a query is reused outside its project, the SQL stays in its project's `queries-dump/` (canonical path below). When a query is reused by a second project, **move** it into this folder with the standard header (purpose, grain, tables, definitions, exclusions, validated-on) and update the row.

"Validated" means it produced results used in a project insight. Items marked **unconfirmed** have open assumptions.

| Query | Purpose and grain | Tables | Status | Path |
|---|---|---|---|---|
| pba-adherence-base-extract v3 | One row per order, HARD allocation, internal vs PBA partner, TATs, pickup and delivery attempt, warehouse and allocation time. Use v3 going forward | allocation audit, order_tat_details, m_system_value_master | Validated (PBA story 2026-06-25) | `archives/pba-integration/queries-dump/2026-05-25-pba-adherence-base-extract-v3.sql` |
| pba-allocation-with-pref-array v2 | One row per order, HARD allocation, preference array pivoted wide (dp1 to dp6: name, EDD, pricing, AVERAGE_TAT, total score, partner id) | allocation audit, rails api audit, logistics_delivery_partner, m_system_value_master | Validated | `archives/pba-integration/queries-dump/2026-05-25-pba-allocation-with-pref-array-v2.sql` |
| pba-allocation-output v1 | One row per order, SOFT and HARD side by side with actual and promised delivery dates | allocation audit, order_tat_details, delivery_date_tracker, m_system_value_master | Validated | `archives/pba-integration/queries-dump/2026-05-25-pba-allocation-output-v1.sql` |
| pba-diff-courier-internal-rank v2 | One row per order, different-courier cohort, Internal courier's rank and EDD in the PBA array | allocation audit, rails api audit, logistics_delivery_partner, order_tat_details, m_system_value_master | Validated | `archives/pba-integration/queries-dump/2026-05-25-pba-diff-courier-internal-rank-v2.sql` |
| pba-lane-extract v1 | One row per order: warehouse_id and drop pincode, joined in Python | allocation audit | Validated | `archives/pba-integration/queries-dump/2026-05-25-pba-lane-extract-v1.sql` |
| early-delivery-base-extract v1 | One row per order digitised in May 2026: status milestones pivoted, promises, state at placement, actuals, state at shipping | order_status, m_system_value_master, delivery_date_tracker, order_tat_details, package_details_tracking, order_wh_mfc_mapping | **Unconfirmed** (`rules.md` G2) | `archives/early-delivery-analysis/queries-dump/2026-06-16-early-delivery-base-extract-v1.sql` |

The July and August 2026 promise-vs-actual exports (`all-orders-july-2026.csv`, `all-orders-august-2026.xlsx`) were Metabase exports whose SQL is not saved in the repo. Save it here the next time that extract is re-run.

Earlier PBA base queries (`base-query-1`, `base-query-2`, base-extract v1/v2, allocation-with-pref-array v1, diff-courier v1) are superseded and stay in the project for history.
