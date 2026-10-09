---
title: Master and lookup tables
type: schema
systems: [allocation, tracking, eta, serviceability]
verticals: [all]
source: former context/schema.md (split into context/data/ on 2026-10-09; see git history)
updated: 2026-05-25
---

# Master and lookup tables

> Redshift tables are prefixed `tmmumpsdb.` in Metabase SQL. Column names are `snake_case` in SQL; the display names below are the Metabase UI names. Quirks and standing exclusions live in `../rules.md`, not here.

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

#### M System Value Master (`m_system_value_master`)
**Purpose:** General enum and lookup table. Decodes IDs across the system.
**Provenance:** Usage seen in the former `schema.md` (2026-05-25) and project queries.

| Column | Definition |
|--------|------------|
| serial_id | The enum ID (for example `order_status_id`, `delivery_partner_id`) |
| name | Enum family, for example `'Order Status'` |
| value | Human-readable value, for example a partner name |

#### Referenced but not yet documented
`m_city_master`, `m_state_master` (city and state of a pincode, used by the nightly adherence cascade) and `order_wh_mfc_mapping` (source of `shipping_is_inventory` in the early-delivery extract). Run `update-context` before relying on them.

---

## Key lookups

- **Warehouse ID to name:** join any table's `Warehouse ID` to `Warehouse Details.ID`. Confirm with Tejas whether a warehouse is active and whether it is an FC or an MFC.
- **Courier Partner ID to name:** `Delivery Partner` or `Courier Partner ID` in any table equals `M Courier Partner Master.SVM ID`; `ANKW Courier Partner Account Code` is the readable code.
- **Order status:** `Order Status.Order Status ID` joins `M System Value Master` where `Name = 'Order Status'`.

