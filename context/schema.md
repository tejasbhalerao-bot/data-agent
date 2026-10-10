---
title: Schema
type: schema
systems: [allocation, tracking, serviceability, eta]
verticals: [all]
source: former context/schema.md (2026-05-25) plus additions from the early-delivery, egregiously-miscalibrated-promises, promise-opportunities, pba-integration, courier-allocation-revamp and instrumentation-audit projects. Merged into one file 2026-10-10.
updated: 2026-05-25
---

# Schema

One file for every table. Each table carries a `Systems:` flag (allocation, tracking, serviceability, eta, communications, or all); filter on it to load only the relevant tables. Communications has no tables documented yet.

> Redshift tables are prefixed `tmmumpsdb.` in Metabase SQL. Column names are `snake_case` in SQL; the display names below are the Metabase UI names. Data quirks and required filters are listed with the table they affect. Items marked "Provenance" were added from project docs and not re-verified against live data.

## Key lookups

- **Warehouse ID to name:** join any table's `Warehouse ID` to `Warehouse Details.ID`. Confirm with Tejas whether a warehouse is active and whether it is an FC or an MFC.
- **Courier Partner ID to name:** `Delivery Partner` or `Courier Partner ID` in any table equals `M Courier Partner Master.SVM ID`; `ANKW Courier Partner Account Code` is the readable code.
- **Order status:** `Order Status.Order Status ID` joins `M System Value Master` where `Name = 'Order Status'`.

---

## Tables

#### Pincode Warehouse Master
**Systems:** serviceability
**Purpose:** FC serviceability — SDD, cold chain, overall; priority warehouse per pincode.
**Written by:** Ops team upload.

| Column | Definition |
|--------|------------|
| Pincode | Pincode for config |
| Warehouse ID | Maps to Warehouse Details |
| Is SDD | Whether this pincode × warehouse serves SDD |
| Is Cold Chain Deliverable | Whether cold chain orders are serviceable |
| Is Serviceable | Overall Truemeds serviceability |
| Priority | Priority warehouse for this pincode |
| Active | Whether this config row is active |

---

#### Pincode Microfc Master
**Systems:** serviceability
**Purpose:** MFC serviceability — same structure as Pincode Warehouse Master but for MFCs.
**Written by:** Ops team upload.

| Column | Definition |
|--------|------------|
| Pincode | Pincode for config |
| Warehouse ID | Maps to Warehouse Details |
| Is SDD | Whether this pincode × warehouse serves SDD |
| Is Cold Chain Deliverable | Whether cold chain orders are serviceable |
| Is Serviceable | Overall Truemeds serviceability |
| Priority | Priority warehouse for this pincode |
| Active | Whether this config row is active |

---

#### SDD Pincode Mapping
**Systems:** serviceability, allocation
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
**Systems:** allocation
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
**Systems:** allocation, eta
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
**Systems:** allocation, eta
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
**Systems:** allocation, eta
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
**Systems:** allocation, eta
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
**Systems:** allocation, eta
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
**Systems:** allocation
**Purpose:** One record per order per allocation event. Stores both PBA and Internal courier decisions in `allocation_metadata` JSON.
**Written by:** System on each Clickpost allocation call (SOFT at order placement, HARD at dispatch).

| Column | Definition |
|--------|------------|
| order_id | Order identifier |
| request_id | Links this allocation to the Clickpost API call — joins to `logistics_rails_api_audit.reference_number` |
| allocation_type | `SOFT` (order placement) or `HARD` (dispatch) |
| selected_source | `INTERNAL` in shadow mode — PBA is counterfactual only. **Update when PBA goes live.** |
| created_at | When the allocation record was created |
| updated_at | Last update timestamp — used for deduplication. An order can have several rows per `allocation_type`; keep the latest by `updated_at` before any join |
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
**Systems:** allocation
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

**Per courier in `preference_array` (idx 0 = rank 1; up to 6 couriers seen, no fixed limit):**

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
**Systems:** allocation
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

---

#### Pincode Delivery TAT
**Systems:** eta, allocation
**Purpose:** Logistics TAT from dispatch to delivery for FCs.
**Written by:** Ops team upload.

| Column | Definition |
|--------|------------|
| Delivery Partner | Maps to M Courier Partner Master |
| Warehouse ID | Maps to Warehouse Details |
| Pincode | Pincode for config |
| Delivery Days | TAT in days for warehouse × pincode × courier |
| Delivery Days in Mins | TAT in minutes. If non-NULL, system uses this over Delivery Days |
| Active | Whether this config row is active |

---

#### Pincode Delivery TAT MFC
**Systems:** eta, allocation
**Purpose:** Logistics TAT from dispatch to delivery for MFCs. Same structure as Pincode Delivery TAT.
**Written by:** Ops team upload.

| Column | Definition |
|--------|------------|
| Delivery Partner | Maps to M Courier Partner Master |
| Warehouse ID | Maps to Warehouse Details |
| Pincode | Pincode for config |
| Delivery Days | TAT in days |
| Delivery Days in Mins | TAT in minutes. If non-NULL, overrides Delivery Days |
| Active | Whether this config row is active |

---

#### Delivery Date Tracker
**Systems:** eta, tracking
**Purpose:** Promise data per order — dispatch date, delivery date, doctor call time, WH processing time.
**Written by:** System. Promise data overwritten until order placed.
**Source of truth for:** Promise dates, actual doctor call time, actual WH processing time.

| Column | Definition |
|--------|------------|
| Order ID | Unique order identifier |
| Promised Delivery Date | Promised delivery date shown to customer. **Always use this for analysis.** |
| Promised Air Delivery Date | Promised delivery date for express/air couriers. Populated when courier is air-enabled. |
| Actual Delivery Date | Date order was actually delivered |
| Promised Dispatch Date | Promised dispatch date |
| Promised Doctor Call Time | Promised doctor call time |
| Promised Warehouse Processing | Promised WH processing time |
| Actual Doctor Call Time | Actual time doctor called |
| Actual Warehouse Processing | Actual WH processing time |
| Metadata | Snapshot at order placement time. Assume synced with rest of table. |

> Warning: Promise data gets overwritten until order placement. Pre-order placed values unreachable.
> Doctor working hours: 8:00 AM – 11:00 PM.

**Metadata column — key fields:**

| Field | Definition |
|-------|------------|
| `buffer_applied_flag` | Boolean. Whether a buffer was applied to this order's promise |
| `pickup_buffer_in_minutes` | Buffer added to dispatch promise time |
| `drop_buffer_in_minutes` | Buffer added to delivery promise time |

**Source of truth for promise engine inputs/outputs:** Always use `metadata → instrumentation_details` — this is the only field that reflects the exact state at order placement time. Essentially, your pincode, warehouse, inventory state, sdd state. These are the primary inputs which control every other input to promise getting constructed. Things may change from at time of order placed to at time of shipping. 

`instrumentation_details` contains three sub-objects:

| Sub-object | Key fields |
|------------|------------|
| `doctor_attributes` | `promised_doctor_call_time`, `doctor_call_required`, `cass_flow_enabled`, `doctor_working_hours` |
| `warehouse_attributes` | `promised_warehouse_time`, `wh_processing_type`, `wh_processing_mins`, `warehouse_id`, `is_mfc`, `is_sdd`, `is_inventory`, `warehouse_work_start`, `warehouse_work_end` |
| `logistics_attributes` | `promised_dispatch_time`, `promised_delivery_time`, `delivery_tat_mins`, `delivery_partner_id`, `is_air`, `air_delivery_enabled`, `payment_type`, `input_pincode`, `resolved_pincode` |

<details>
<summary>Sample metadata JSON</summary>

```json
{
  "pb_audit_update_promise_time": true,
  "buffer_applied_flag": false,
  "pickup_buffer_in_minutes": 0,
  "drop_buffer_in_minutes": 0,
  "instrumentation_details": {
    "doctor_attributes": {
      "promised_doctor_call_time": "2026-05-22T08:48:47.985",
      "default_doctor_call_minutes_config": 60,
      "doctor_call_required": true,
      "cass_flow_enabled": true,
      "order_category": null,
      "doctor_working_hours": { "work_start": "08:00", "work_end": "22:00" }
    },
    "warehouse_attributes": {
      "promised_warehouse_time": "2026-05-23T14:30",
      "wh_processing_type": "NON_SDD_NON_INVENTORY",
      "wh_processing_mins": 810,
      "warehouse_id": 30,
      "is_mfc": true,
      "is_inventory": false,
      "is_sdd": false,
      "warehouse_work_start": "10:00",
      "warehouse_work_end": "19:00",
      "input_pincode": "766105"
    },
    "logistics_attributes": {
      "warehouse_id": 30,
      "input_pincode": "766105",
      "resolved_pincode": "766105",
      "is_sdd": false,
      "is_mfc": true,
      "is_inventory": false,
      "promised_wh_processing_time": "2026-05-23T14:30",
      "payment_type": "PREPAID",
      "promised_dispatch_time": "2026-05-23T18:00",
      "delivery_tat_mins": 2880,
      "air_delivery_tat_mins": 2880,
      "is_air": true,
      "promised_delivery_time": "2026-05-25T18:00",
      "promised_air_delivery_time": "2026-05-25T18:00",
      "delivery_partner_id": 225,
      "air_delivery_enabled": true
    },
    "stamped_ts": "2026-05-22T00:04:48.312"
  }
}
```
</details>

---

#### WH Processing Time
**Systems:** eta
**Purpose:** WH processing time per bucket (SDD × Inventory).

| Column | Definition |
|--------|------------|
| Wh ID | Maps to Warehouse Details |
| Type | Processing bucket. Values: `SDD_Inventory`, `SDD_Non_Inventory`, `Non_SDD_Inventory`, `Non_SDD_Non_Inventory` |
| Active | Whether active |
| Processing Time in Mins | WH processing time in minutes for this bucket |

---

#### WH Weekoff Schedule
**Systems:** eta
**Purpose:** Stores when JIT cycles are closed per warehouse.

| Column | Definition |
|--------|------------|
| Wh ID | Maps to Warehouse Details |
| Active | Whether active |
| Weekoff Day | Day when JIT cycles close |

---

#### Derived extract: order promise vs actuals (wide, one row per order)
**Systems:** eta, tracking
**Purpose:** The base extract used by `early-delivery-analysis`, `egregiously-miscalibrated-promises` and `promise-opportunities`. Exported from Metabase as CSV.
**Provenance:** Column meanings from `archives/egregiously-miscalibrated-promises/context/data-sources.md` and `archives/promise-opportunities/context/2026-07-10-early-deliveries-data-dictionary-v1.md`. Source SQL: `archives/early-delivery-analysis/queries-dump/2026-06-16-early-delivery-base-extract-v1.sql` (see `rules.md` open gaps).

| Group | Columns |
|-------|---------|
| Lifecycle timestamps | `order_id`, `digitised_ts` (= order placed), `dr_confirm_ts`, `invoice_create_ts`, `processing_start_ts` (warehouse became eligible to start; not that processing started), `awb_sticker_printed_ts` (alias `awb_print_ts`) |
| Promises at placement (`digitised_*`) | `digitised_dr_promise`, `digitised_wh_promise`, `digitised_dispatch_promise`, `digitised_delivery_promise` (timestamps); `digitised_doctor_tat`, `digitised_wh_process_mins` (within working hours only), `digitised_dispatch_tat`, `digitised_delivery_tat_mins` (minutes) |
| State at placement | `digitised_is_sdd`, `digitised_is_inventory`, `digitised_is_mfc`, `digitised_wh_id`, `digitised_order_category` (AUTO_CONFIRM, DOCTOR_CALL_REQUIRED, HA_CALL_REQUIRED, DOCTOR_AND_HA_CALL_REQUIRED), `digitised_delivery_pincode`, `digitised_delivery_partner` |
| Working hours | `doctor_work_start/end`, `warehouse_work_start/end` (`digitised_wh_work_start/end` in the older export), `wh_processing_type` |
| Payment | `initial_payment_type`, `final_payment_code`, `final_payment_type`, `payment_pending_ts`, `payment_completed_ts` |
| Actuals | `actual_doctor_call_time` (first call attempt), `actual_warehouse_processing`, `pickup_time`, `delivery_attempt_time` (first attempt, need not succeed), `actual_delivery_date` |
| State at shipping (`shipping_*`) | `shipping_pincode`, `shipping_delivery_partner`, `shipping_delivery_promise` (integer **days**), `shipping_warehouse`, `shipping_is_sdd`, `shipping_is_inventory` |

**Quirks of this extract:**
- `shipping_delivery_promise` is a number of **days**, not a timestamp. Compare it with `DATE(digitised_delivery_promise) - DATE(digitised_dispatch_promise)`, never with `digitised_delivery_promise` directly.
- Boolean columns use different formats: `digitised_is_sdd` and `digitised_is_inventory` are `true`/`false` text, `shipping_is_sdd` is `1`/`0`, `shipping_is_inventory` is `true`/`false`. Convert before comparing.
- `digitised_*` SDD, MFC, inventory and category fields are filled only from **2026-05-08**. Use `digitised_ts >= 2026-05-08` for any analysis that splits by them.

Pairs that can diverge between placement and shipping (check both when assessing promise accuracy): pincode, delivery partner, warehouse, `is_sdd`, `is_inventory`, delivery promise.

---

#### Order TAT Details
**Systems:** tracking
**Purpose:** Pickup time + delivery attempt timestamps per order. Source of truth for courier selected at invoice generation, warehouse shipping, promise TAT of the courier selected. 
**Written by:** System, on order pickup by courier.
**Note:** Stores only 1st delivery attempt timestamp even if multiple OFD attempts exist.

| Column | Definition |
|--------|------------|
| Delivery Partner | Courier selected at invoice generation |
| Warehouse ID | Maps to Warehouse Details |
| Pincode | Delivery pincode |
| Order ID | Unique order identifier |
| Pickup Time | Timestamp when courier marked order as picked up |
| Delivery Attempt Time | Timestamp of 1st OFD attempt |
| Promise TAT | Final selected courier's TAT = Ideal TAT from Pincode Delivery TAT config |
| Delay Days | Days added to Promise TAT to reach ≥80% adherence. Customer TAT = Promise TAT + Delay Days |
| Supposed TAT | Boolean. True if no config value existed (defaults to 5 days) |

Note: Shipping courier's promise = Promise TAT + Delay Days

---

#### Order Status
**Systems:** tracking
**Purpose:** Full status history per order. Multi-row per order.
**Written by:** System on each status transition.
**Note:** Does NOT store one row per order. Stores every status the order passed through.

| Column | Definition |
|--------|------------|
| Order ID | Unique order identifier |
| Order Status ID | Enum ID — join with M System Value Master (Name = 'Order Status') to decode |

---

#### Package Details Tracking
**Systems:** tracking
**Purpose:** Warehouse + logistics leg tracking. Source of truth for whether order was SDD at the time of shipping.
**Written by:** System when order hits warehouse.

| Column | Definition |
|--------|------------|
| Order ID | Unique order identifier |
| Is SDD | Whether order was dispatched as SDD |
| Payment Type ID | Final payment mode |
| Is Clickpost Edit Order | Whether payment mode was updated before or after dispatch |

---

#### Order Details
**Systems:** tracking
**Purpose:** Composite repository of all orders. One row per Order ID.
**Written by:** System on ATC (Add to Cart) — order is created at ATC.

| Column | Definition |
|--------|------------|
| Order ID | Unique order identifier |
| Customer ID | Unique customer identifier |
| Orderstatus | Final recorded order status. Exclude 49 (Incomplete) and 312 (Scrapped) |
| Created_on | Timestamp of order creation (= ATC time) |

---

#### Order Status enum values seen in project queries
**Systems:** tracking
Provenance: `pba-integration` query reference and `early-delivery` base extract. Not yet confirmed against `M System Value Master`.

| Value | Meaning |
|-------|---------|
| 344 | PBA-eligible placed order |
| 39 | Order created timestamp |
| 49 | Incomplete (excluded) |
| 312 | Scrapped (excluded) |
| `Order Digitised`, `Doctor Confirmed`, `Invoice Generated` | Status names used to pivot milestone timestamps; the status timestamp column is assumed `created_at` |

---

#### Warehouse Details
**Systems:** all
**Purpose:** Mapping of all warehouses and their status.

| Column | Definition |
|--------|------------|
| ID | Warehouse ID referenced in all other tables |
| Warehouse Name | Human-readable warehouse name |
| Work Start | Warehouse opening time |
| Work End | Warehouse closing time |

> Always confirm with Tejas: (1) which warehouses are active, (2) which are FC vs MFC.

---

#### M Courier Partner Master
**Systems:** all
**Purpose:** Single source of truth for all courier partner data.

| Column | Definition |
|--------|------------|
| ANKW Courier Partner Account Code | Human-readable courier code |
| SVM ID | = Delivery Partner / Courier Partner ID used in all other tables |

---

#### M System Value Master (`m_system_value_master`)
**Systems:** all
**Purpose:** General enum and lookup table. Decodes IDs across the system.
**Provenance:** Usage seen in the former `schema.md` (2026-05-25) and project queries.

| Column | Definition |
|--------|------------|
| serial_id | The enum ID (for example `order_status_id`, `delivery_partner_id`) |
| name | Enum family, for example `'Order Status'` |
| value | Human-readable value, for example a partner name |

---

## How the systems use these tables (reference)

#### How serviceability works (reference)
Summarised from `archives/instrumentation-audit/context/2026-06-18-serviceability-system-description-v1.md`.
- Three decisions: which pincode is serviceable, which warehouse serves it (by `Priority`), which courier serves the pair.
- **Cart page** uses the FC catalog (`Pincode Warehouse Master`). **Summary page** checks inventory at the priority-1 warehouse in both the FC and MFC tables: both stocked selects MFC; otherwise FC (FCs are assumed stocked via JIT).
- **Non-serviceable pincode:** the customer sees the Mumbai FC catalog but cannot place an order.
- **Construct:** `Is SDD = true` selects Hyperlocal, otherwise Courier. Hyperlocal considers only Ithink, Shipsy and Shiprocket, chosen from `SDD Pincode Mapping`; only priority 1 is ever used. Courier selection happens in Clickpost.
- Clickpost pincode serviceability is updated by CSV upload. Bluedart alone is auto-synced.

#### How courier scoring works (reference)
Summarised from `archives/courier-allocation-revamp/context/2026-06-08-system-workflow-v1.md` (source: Courier Allocation Revamp PRD).
- **Nightly adherence job:** 3:00 AM for FCs, 3:30 AM for MFCs. Pools the last 7 days of deliveries at the first cascade level with at least `n_threshold` orders: pincode, city, state, warehouse, courier, default (80%).
- **Delivery buckets (9):** Early 4+d, Early 3d, 2d, 1d, On-Time, SLA breach 1d, 2d, 3d, 4+d. Drop buffer is subtracted from actual TAT before bucketing.
- **Final TAT:** Ideal TAT shifted by the bucket where the adherence threshold is reached. Must never be below 0.
- **Final allocation score:** `(Final TAT / Adherence) + schedule_time_flag + Pickup Buffer + Drop Buffer`, ranked ascending; rank 1 is selected.
- **Job failure:** the previous night's scores are used; allocation is never blocked.
- **Shadow modes:** 6 parallel runs (2 computation variants x `n_threshold` 10/15/20) log rankings without switching couriers.


## Open questions and undocumented tables
- **Undocumented tables:** `m_city_master`, `m_state_master` (city and state of a pincode, used by the nightly adherence cascade) and `order_wh_mfc_mapping` (source of `shipping_is_inventory` in the early-delivery extract). Run `update-context` before relying on them.
- **PBA status:** `selected_source = 'INTERNAL'` means PBA is still in shadow mode. Confirm whether PBA is now live; if so, update the allocation audit section.
- **Order status IDs 344 and 39** (placed PBA-eligible order, order created) are not confirmed against `M System Value Master`.
- **Communications** has no tables documented.

## Reference queries
Validated SQL for these tables, grouped by system. The Build phase reuses these before writing fresh SQL. SQL stays in its project's `queries-dump/` until a second project reuses it, then moves into `context/` with a header (purpose, grain, tables, definitions, exclusions, validated-on) and the entry is updated. "Validated" means it produced results used in a signed-off insight.

### Allocation
| Query | Purpose and grain | Tables | Status | Path |
|---|---|---|---|---|
| pba-adherence-base-extract v3 | One row per order, HARD allocation: internal vs PBA partner, TATs, pickup and delivery attempt, warehouse, allocation time. Use v3 going forward | allocation audit, order_tat_details, m_system_value_master | Validated (PBA story 2026-06-25) | `archives/pba-integration/queries-dump/2026-05-25-pba-adherence-base-extract-v3.sql` |
| pba-allocation-with-pref-array v2 | One row per order, HARD allocation, preference array pivoted wide (dp1 to dp6: name, EDD, pricing, AVERAGE_TAT, total score, partner id) | allocation audit, rails api audit, logistics_delivery_partner, m_system_value_master | Validated | `archives/pba-integration/queries-dump/2026-05-25-pba-allocation-with-pref-array-v2.sql` |
| pba-allocation-output v1 | One row per order, SOFT and HARD side by side with actual and promised delivery dates | allocation audit, order_tat_details, delivery_date_tracker, m_system_value_master | Validated | `archives/pba-integration/queries-dump/2026-05-25-pba-allocation-output-v1.sql` |
| pba-diff-courier-internal-rank v2 | One row per order, different-courier cohort: Internal courier's rank and EDD in the PBA array | allocation audit, rails api audit, logistics_delivery_partner, order_tat_details, m_system_value_master | Validated | `archives/pba-integration/queries-dump/2026-05-25-pba-diff-courier-internal-rank-v2.sql` |
| pba-lane-extract v1 | One row per order: warehouse_id and drop pincode, joined in Python | allocation audit | Validated | `archives/pba-integration/queries-dump/2026-05-25-pba-lane-extract-v1.sql` |

Earlier PBA queries (`base-query-1`, `base-query-2`, base-extract v1/v2, allocation-with-pref-array v1, diff-courier v1) are superseded and stay in the project for history.

### ETA
| Query | Purpose and grain | Tables | Status | Path |
|---|---|---|---|---|
| early-delivery-base-extract v1 | One row per order digitised in May 2026: status milestones pivoted, promises, state at placement, actuals, state at shipping | order_status, m_system_value_master, delivery_date_tracker, order_tat_details, package_details_tracking, order_wh_mfc_mapping | **Unconfirmed** (three assumptions unconfirmed: the status timestamp column, the status names, and the decode join; also uses `order_wh_mfc_mapping`, which is undocumented) | `archives/early-delivery-analysis/queries-dump/2026-06-16-early-delivery-base-extract-v1.sql` |

The July and August 2026 promise-vs-actual exports (`all-orders-july-2026.csv`, `all-orders-august-2026.xlsx`) were Metabase exports whose SQL is not saved in the repo. Save it here the next time that extract is re-run.
