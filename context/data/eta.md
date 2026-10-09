---
title: ETA / promise schema
type: schema
systems: [eta, allocation]
verticals: [all]
source: former context/schema.md (split into context/data/ on 2026-10-09; see git history); derived extract from early-delivery and EMP projects
updated: 2026-05-25
---

# ETA / promise schema

> Redshift tables are prefixed `tmmumpsdb.` in Metabase SQL. Column names are `snake_case` in SQL; the display names below are the Metabase UI names. Quirks and standing exclusions live in `../rules.md`, not here.

#### Pincode Delivery TAT
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
**Purpose:** WH processing time per bucket (SDD × Inventory).

| Column | Definition |
|--------|------------|
| Wh ID | Maps to Warehouse Details |
| Type | Processing bucket. Values: `SDD_Inventory`, `SDD_Non_Inventory`, `Non_SDD_Inventory`, `Non_SDD_Non_Inventory` |
| Active | Whether active |
| Processing Time in Mins | WH processing time in minutes for this bucket |

---

#### WH Weekoff Schedule
**Purpose:** Stores when JIT cycles are closed per warehouse.

| Column | Definition |
|--------|------------|
| Wh ID | Maps to Warehouse Details |
| Active | Whether active |
| Weekoff Day | Day when JIT cycles close |

---

#### Derived extract: order promise vs actuals (wide, one row per order)
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

Pairs that can diverge between placement and shipping (check both when assessing promise accuracy): pincode, delivery partner, warehouse, `is_sdd`, `is_inventory`, delivery promise.

