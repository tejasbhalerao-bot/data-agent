---
title: Allocation schema
type: schema
systems: [allocation, eta]
verticals: [all]
source: former context/schema.md (split into context/data/ on 2026-10-09; see git history); logistics_delivery_partner from pba-integration
updated: 2026-05-25
---

# Allocation schema

> Redshift tables are prefixed `tmmumpsdb.` in Metabase SQL. Column names are `snake_case` in SQL; the display names below are the Metabase UI names. Quirks and standing exclusions live in `../rules.md`, not here.

#### SDD Pincode Mapping
**Purpose:** Selects delivery partner for SDD at pincode × warehouse level.
**Written by:** Ops team upload.

| Column | Definition |
|--------|------------|
| Delivery Partner | Courier partner account code (= M Courier Partner Master) |
| Warehouse ID | Maps to Warehouse Details |
| Pincode | Pincode for config |
| Priority | Determines courier selection for warehouse × pincode in SDD flow |
| Active | Whether this config row is active |

---

#### Same Day Delivery Master
**Purpose:** Selects courier for warehouse × pincode when cold chain = true.
**Written by:** Engineering manual upload.

| Column | Definition |
|--------|------------|
| Courier Partner ID | Maps to M Courier Partner Master |
| Warehouse ID | Maps to Warehouse Details |
| Is Cold Chain | Whether this courier × warehouse is eligible for cold chain |
| Active | Whether this config row is active |

---

#### TAT Adherence Master
**Purpose:** Backup adherence values when no orders found in last 7 days for a lane.
**Written by:** Engineering manual upload.

| Column | Definition |
|--------|------------|
| Delivery Partner | Maps to M Courier Partner Master |
| Warehouse ID | Maps to Warehouse Details |
| Pincode | Pincode for config |
| Adherence Percentage | Default adherence value |
| Active | Whether this config row is active |

---

#### Courier Partner Schedule
**Purpose:** Courier cutoff times at warehouse level for non-SDD flow.
**Written by:** Ops team upload.

| Column | Definition |
|--------|------------|
| Courier Partner ID | Maps to M Courier Partner Master |
| Warehouse ID | Maps to Warehouse Details |
| Active | Whether this config row is active |
| Courier Partner Schedule Time | Cutoff time in HH:MM format |

---

#### SDD Courier Partner Cutoff
**Purpose:** Courier cutoff times at warehouse × pincode level for SDD flow.
**Written by:** Ops team upload.

| Column | Definition |
|--------|------------|
| Pincode | Pincode for config |
| Warehouse ID | Maps to Warehouse Details |
| Courier Partner ID | Maps to M Courier Partner Master |
| Cutoff in HH MM | Cutoff time in HH:MM format |

---

#### Pincode TAT Adherence Data
**Purpose:** Nightly job output — 7-day adherence calculation for FCs.
**Written by:** System nightly job. Logic: https://truemeds.atlassian.net/wiki/x/E4COZ

| Column | Definition |
|--------|------------|
| Delivery Partner | Maps to M Courier Partner Master |
| Warehouse ID | Maps to Warehouse Details |
| Pincode | Pincode for config |
| Ideal TAT | Uploaded value from Pincode Delivery TAT |
| Final TAT | TAT after ≥80% adherence achieved. System adds 1 day to Ideal TAT until ≥80% |
| Supposed TAT | Boolean. True if no Pincode Delivery TAT value exists (defaults to 5 days) |
| Adherence Percentage | Calculated adherence once ≥80% is reached |
| Sla Breach1day | % orders delivered 1 day late. Added first if adherence <80% |
| Sla Breach2day | % orders delivered 2 days late. Added second if still <80% |
| Sla Breach3day | % orders delivered 3 days late. Added third if still <80% |
| Sla Breach4plusday | % orders delivered ≥4 days late. Added last if still <80% |
| Active | Whether this config row is active |

---

#### Pincode TAT Adherence Data MFC
**Purpose:** Same as Pincode TAT Adherence Data but for MFCs.
**Written by:** System nightly job. Same logic doc as above.

| Column | Definition |
|--------|------------|
| Delivery Partner | Maps to M Courier Partner Master |
| Warehouse ID | Maps to Warehouse Details |
| Pincode | Pincode for config |
| Ideal TAT | Uploaded value from Pincode Delivery TAT MFC |
| Final TAT | TAT after ≥80% adherence achieved |
| Supposed TAT | Boolean. True if no config value exists (defaults to 5 days) |
| Adherence Percentage | Calculated adherence once ≥80% reached |
| Sla Breach1day | % orders 1 day late |
| Sla Breach2day | % orders 2 days late |
| Sla Breach3day | % orders 3 days late |
| Sla Breach4plusday | % orders ≥4 days late |
| Active | Whether this config row is active |

---

#### Logistics Allocation Audit
**Purpose:** One record per order per allocation event. Stores both PBA and Internal courier decisions in `allocation_metadata` JSON.
**Written by:** System on each Clickpost allocation call (SOFT at order placement, HARD at dispatch).

| Column | Definition |
|--------|------------|
| order_id | Order identifier |
| request_id | Links this allocation to the Clickpost API call — joins to `logistics_rails_api_audit.reference_number` |
| allocation_type | `SOFT` (order placement) or `HARD` (dispatch) |
| selected_source | `INTERNAL` in shadow mode — PBA is counterfactual only. **Update when PBA goes live.** |
| created_at | When the allocation record was created |
| updated_at | Last update timestamp — used for deduplication |
| allocation_metadata | JSON — see sub-fields below |

**`allocation_metadata` sub-fields:**

| Field | Definition |
|-------|------------|
| `warehouse_id` | int — active warehouses `>= 17` |
| `pincode` | int — drop pincode |
| `projected_dispatch_time` | epoch milliseconds — cast: `timestamp 'epoch' + (val::bigint/1000) * interval '1 second'` |
| `pba_partner_id` | int — PBA-selected courier (`delivery_partner_id`) |
| `pba_tat` | int minutes — `CEILING(x/1440)` for days |
| `internal_partner_id` | int — Internal-selected courier (`delivery_partner_id`) |
| `internal_tat` | int minutes — `CEILING(x/1440)` for days |

**Delivery partner name decode:**
`m_system_value_master` used as `SELECT serial_id AS delivery_partner_id, value AS partner_name` to map `pba_partner_id` / `internal_partner_id` → human-readable name.

---

#### Logistics Rails API Audit
**Purpose:** Raw Clickpost API response logs. One row per API call.
**Written by:** System on every Clickpost API call.

| Column | Definition |
|--------|------------|
| pk | Format: `RECOMMEND#<order_id>` for PBA recommendation calls |
| reference_number | Joins to `logistics_allocation_audit.request_id` — use this for exact matching, not timestamps |
| api_name | API type. Filter on `'CLICKPOST_RECOMMEND'` for PBA preference array data |
| created_at | Timestamp of API call |
| request_payload | JSON — contains `pickup_pincode` |
| response_payload | JSON — contains `preference_array` at path `result[0].preference_array` |

**Per courier in `preference_array` (idx 0 = rank 1):**

| Field | Definition |
|-------|------------|
| `account_code` | Human-readable courier code (= ANKW account code) |
| `cp_id` | Clickpost internal courier ID |
| `courier_name` | Courier display name |
| `priority` | Array position — determines rank |
| `delivery_type` | Surface / Express |
| `scores_computation.scoring_params_actual.EDD` | EDD score (lower = better) |
| `scores_computation.scoring_params_actual.PRICING` | Pricing score (lower = better) |
| `scores_computation.scoring_params_actual.AVERAGE_TAT` | Historical TAT score |
| `scores_computation.total_score` | Overall score |

**Ranking logic:** `EDD ASC → PRICING ASC → AVERAGE_TAT ASC → total_score ASC → priority ASC`

---

#### logistics_delivery_partner
**Purpose:** Maps internal `delivery_partner_id` to Clickpost `cp_id` and `ankw_account_code`.
**Provenance:** Documented from `archives/pba-integration/context/2026-05-22-query-reference.md` and its sample rows. Not re-verified against live data.

| Column | Definition |
|--------|------------|
| pk | Format `DP#<delivery_partner_id>` |
| delivery_partner_id | Internal courier ID; the value used in all other tables |
| account_code / ankw_account_code | Human-readable Clickpost account code; used to match couriers in the preference array |
| is_express | Express vs surface |
| is_active | Whether the partner is active |
| metadata | JSON: `clickpost_partner_id`, `clickpost_partner_name`, `delivery_partner_name` |

#### How courier scoring works (reference)
Summarised from `archives/courier-allocation-revamp/context/2026-06-08-system-workflow-v1.md` (source: Courier Allocation Revamp PRD).
- **Nightly adherence job:** 3:00 AM for FCs, 3:30 AM for MFCs. Pools the last 7 days of deliveries at the first cascade level with at least `n_threshold` orders: pincode, city, state, warehouse, courier, default (80%).
- **Delivery buckets (9):** Early 4+d, Early 3d, 2d, 1d, On-Time, SLA breach 1d, 2d, 3d, 4+d. Drop buffer is subtracted from actual TAT before bucketing.
- **Final TAT:** Ideal TAT shifted by the bucket where the adherence threshold is reached. Must never be below 0.
- **Final allocation score:** `(Final TAT / Adherence) + schedule_time_flag + Pickup Buffer + Drop Buffer`, ranked ascending; rank 1 is selected.
- **Job failure:** the previous night's scores are used; allocation is never blocked.
- **Shadow modes:** 6 parallel runs (2 computation variants x `n_threshold` 10/15/20) log rankings without switching couriers.

