# Data Dictionary — Early Deliveries Raw (8 May – 31 May 2026)

Source file: `Early Deliveries Raw 8th May to 31st May.csv`
Rows: ~624K
Location: local raw-data (gitignored)

---

## Canonical terminology

- **Digitised** = order placed. `digitised_ts` and "order placed" are used interchangeably.
- **`digitised_*` fields** = snapshot of state at the moment the order was placed.
- **`shipping_*` fields** = snapshot of state at the moment of shipping (AWB print / label generation). May deviate from digitised snapshot.

---

## Field Definitions

### Identifiers

| Field | Type | Definition |
|---|---|---|
| `order_id` | string | Unique identifier for the order |

---

### Event Timestamps (actual pipeline events)

| Field | Type | Definition |
|---|---|---|
| `digitised_ts` | timestamp | When the order was placed. Canonical synonym: digitised = order placed. |
| `dr_confirm_ts` | timestamp | When the doctor confirmed the order |
| `invoice_create_ts` | timestamp | When the invoice was generated for the order |
| `processing_start_ts` | timestamp | When the warehouse became eligible to start processing the order. Does NOT mean processing had actually started. |
| `awb_print_ts` | timestamp | When the AWB (courier label) was printed |

---

### Promises computed at digitisation (snapshot at order placed)

| Field | Type | Definition |
|---|---|---|
| `digitised_dr_promise` | timestamp | Timestamp when the doctor promised to call the customer |
| `digitised_wh_promise` | timestamp | Timestamp when the warehouse promised to have processed the order (i.e. AWB print) |
| `digitised_dispatch_promise` | timestamp | Timestamp when logistics promised to have the courier pick up the order |
| `digitised_delivery_promise` | timestamp | Timestamp when logistics promised to deliver the order to the customer |

---

### TATs computed at digitisation (all in minutes unless noted)

| Field | Type | Definition |
|---|---|---|
| `digitised_doctor_tat` | minutes | Time the doctor promised to take to call the customer after order placed |
| `digitised_wh_process_mins` | minutes | Time the warehouse committed to take to pack the order after doctor call — counted within warehouse working hours only (excludes time outside shift) |
| `digitised_dispatch_tat` | minutes | Time the dispatch (courier pickup) was promised to happen after warehouse promised to process the order |
| `digitised_delivery_tat_mins` | minutes | Time the delivery was promised to happen after courier pickup |

---

### Dimensions / flags at digitisation (snapshot at order placed)

| Field | Type | Definition |
|---|---|---|
| `digitised_is_sdd` | boolean | SDD (same-day delivery) serviceability state of the order at time of order placed |
| `digitised_is_inventory` | boolean | Inventory state of the order at time of order placed (true = inventory held, false = sourced/non-inventory) |
| `digitised_wh_id` | integer | Warehouse assigned at time of order placed |
| `digitised_order_category` | enum | Category of the order at time of order placed. Values: AUTO_CONFIRM, DOCTOR_CALL_REQUIRED, HA_CALL_REQUIRED, DOCTOR_AND_HA_CALL_REQUIRED. HA = Health Assistant. |
| `digitised_is_mfc` | boolean | Whether the warehouse assigned at order placed was an MFC (Micro Fulfilment Centre) vs FC (Fulfilment Centre) |
| `digitised_delivery_pincode` | string | Customer's delivery pincode at order placed |
| `digitised_delivery_partner` | integer | Delivery partner (courier) ID allocated at time of order placed |
| `digitised_wh_work_start` | time HH:MM | Time of day when the warehouse assigned at order placed opens for business (processing begins after this time) |
| `digitised_wh_work_end` | time HH:MM | Time of day when the warehouse assigned at order placed closes for business (processing ends before this time) |

---

### Actual event timestamps

| Field | Type | Definition |
|---|---|---|
| `actual_doctor_call_time` | timestamp | When the doctor made the first attempt to call the customer |
| `actual_warehouse_processing` | timestamp | When the warehouse actually finished processing the order |
| `pickup_time` | timestamp | When the courier physically picked up the order from the warehouse |
| `delivery_attempt_time` | timestamp | When the courier made a delivery attempt to the customer. Delivery need not have been successful. |

---

### Shipping snapshot (state at AWB print — may deviate from digitised)

| Field | Type | Definition |
|---|---|---|
| `shipping_pincode` | string | Pincode to which the order was shipped. May deviate from digitised_delivery_pincode. |
| `shipping_delivery_partner` | integer | Delivery partner who actually picked up the order from warehouse. Can differ from digitised_delivery_partner. |
| `shipping_delivery_promise` | integer days | Time in DAYS that the delivery partner assigned at shipping promised to deliver after pickup |
| `shipping_warehouse` | integer | Warehouse that actually shipped the order. Can differ from digitised_wh_id. |
| `shipping_is_sdd` | boolean 0/1 | SDD serviceability state at time of shipping. Can differ from digitised_is_sdd. |
| `shipping_is_inventory` | boolean | Inventory state at time of shipping. Can differ from digitised_is_inventory. |

---

## Key deviation pairs

These fields can diverge between digitisation and shipping — always check both when analysing promise accuracy:

| Digitised | Shipping | What can change |
|---|---|---|
| digitised_delivery_pincode | shipping_pincode | Customer address correction |
| digitised_delivery_partner | shipping_delivery_partner | Courier switch |
| digitised_wh_id | shipping_warehouse | Warehouse reassignment |
| digitised_is_sdd | shipping_is_sdd | SDD eligibility re-evaluated |
| digitised_is_inventory | shipping_is_inventory | Inventory state re-evaluated |
| digitised_delivery_promise | derived from shipping_delivery_promise days | Promise recalculated at shipping |

---

## Working Set Definition

**Filter:** `delivery_attempt_time IS NOT NULL`
**Size:** 522,839 orders (83.7% of 624,304 total)

All analyses in this project operate on this working set unless explicitly stated otherwise. Orders without a delivery attempt are excluded — they stalled before reaching the customer and cannot be evaluated for promise performance.
