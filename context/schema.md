# Truemeds — Schema Reference

> Living document. Updated after every Metabase session where new table/column knowledge is discovered.
> All tables prefixed with `tmmumpsdb.` in Metabase SQL.
> Last updated: 2026-05-22

---

## Key Lookups

### Warehouse ID → Name
Join any table's `Warehouse ID` → `Warehouse Details.ID`
> Always confirm with Tejas: (1) whether a warehouse is still active, (2) whether it is FC or MFC.

### Courier Partner ID → Name
`Delivery Partner` or `Courier Partner ID` in tables = `M Courier Partner Master.SVM ID`
`ANKW Courier Partner Account Code` is the human-readable code.

### Order Status Enum
`Order Status.Order Status ID` → join with `M System Value Master` where `Name = 'Order Status'`
> Orders with status `49` (Incomplete) and `312` (Scrapped) are excluded from all standard analysis.

---

## Tables

### Configuration Tables (ops-uploaded)

---

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

#### Pincode Warehouse Master
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

### System-Written Tables

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

#### Order TAT Details
**Purpose:** Pickup time + delivery attempt timestamps per order. Source of truth for courier selected at invoice generation.
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

---

#### Order Status
**Purpose:** Full status history per order. Multi-row per order.
**Written by:** System on each status transition.
**Note:** Does NOT store one row per order. Stores every status the order passed through.

| Column | Definition |
|--------|------------|
| Order ID | Unique order identifier |
| Order Status ID | Enum ID — join with M System Value Master (Name = 'Order Status') to decode |

---

#### Package Details Tracking
**Purpose:** Warehouse + logistics leg tracking. Source of truth for whether order was SDD.
**Written by:** System when order hits warehouse.

| Column | Definition |
|--------|------------|
| Order ID | Unique order identifier |
| Is SDD | Whether order was dispatched as SDD |
| Payment Type ID | Final payment mode |
| Is Clickpost Edit Order | Whether payment mode was updated before or after dispatch |

---

#### Order Details
**Purpose:** Composite repository of all orders. One row per Order ID.
**Written by:** System on ATC (Add to Cart) — order is created at ATC.

| Column | Definition |
|--------|------------|
| Order ID | Unique order identifier |
| Customer ID | Unique customer identifier |
| Orderstatus | Final recorded order status. Exclude 49 (Incomplete) and 312 (Scrapped) |
| Created_on | Timestamp of order creation (= ATC time) |

---

#### Delivery Date Tracker
**Purpose:** Promise data per order — dispatch date, delivery date, doctor call time, WH processing time.
**Written by:** System. Promise data overwritten until doctor confirms order.
**Source of truth for:** Promise dates, actual doctor call time, actual WH processing time.

| Column | Definition |
|--------|------------|
| Order ID | Unique order identifier |
| Promised Delivery Date | Promised delivery date shown to customer |
| Promised Dispatch Date | Promised dispatch date |
| Promised Doctor Call Time | Promised doctor call time |
| Promised Warehouse Processing | Promised WH processing time |
| Actual Doctor Call Time | Actual time doctor called |
| Actual Warehouse Processing | Actual WH processing time |
| Metadata | Snapshot at order placement time. Assume synced with rest of table. |

> Warning: Promise data gets overwritten until doctor confirms order. Pre-confirmation values unreliable.
> Doctor working hours: 7:30 AM – 11:30 PM.

**Metadata column — key fields:**

| Field | Definition |
|-------|------------|
| `buffer_applied_flag` | Boolean. Whether a buffer was applied to this order's promise |
| `pickup_buffer_in_minutes` | Buffer added to dispatch promise time |
| `drop_buffer_in_minutes` | Buffer added to delivery promise time |

**Source of truth for promise engine inputs/outputs:** Always use `metadata → instrumentation_details` — this is the only field that reflects the exact state at order placement time.

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

### Reference / Master Tables

---

#### Warehouse Details
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
**Purpose:** Single source of truth for all courier partner data.

| Column | Definition |
|--------|------------|
| ANKW Courier Partner Account Code | Human-readable courier code |
| SVM ID | = Delivery Partner / Courier Partner ID used in all other tables |

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

## Discovered Quirks & Gotchas

| # | Table | Quirk |
|---|-------|-------|
| 1 | Order Details | ATC creates order — `Created_on` = cart add time, not checkout |
| 2 | Order Status | Multi-row per order. Never aggregate without deduplication |
| 3 | Order TAT Details | Only 1st delivery attempt stored even if multiple OFD events |
| 4 | Delivery Date Tracker | Promise data overwrites until doctor confirms. Pre-confirmation values unreliable |
| 5 | Pincode Delivery TAT | `Delivery Days in Mins` overrides `Delivery Days` when non-NULL |
| 6 | Pincode TAT Adherence Data | System adds 1 day to Ideal TAT per iteration until ≥80% adherence — Final TAT ≠ Ideal TAT |
| 7 | Warehouse Details | Always verify active warehouses + FC/MFC classification with Tejas before querying |
