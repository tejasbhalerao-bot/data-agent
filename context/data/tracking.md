---
title: Tracking and order schema
type: schema
systems: [tracking]
verticals: [all]
source: former context/schema.md (split into context/data/ on 2026-10-09; see git history)
updated: 2026-05-25
---

# Tracking and order schema

> Redshift tables are prefixed `tmmumpsdb.` in Metabase SQL. Column names are `snake_case` in SQL; the display names below are the Metabase UI names. Quirks and standing exclusions live in `../rules.md`, not here.

#### Order TAT Details
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
**Purpose:** Full status history per order. Multi-row per order.
**Written by:** System on each status transition.
**Note:** Does NOT store one row per order. Stores every status the order passed through.

| Column | Definition |
|--------|------------|
| Order ID | Unique order identifier |
| Order Status ID | Enum ID — join with M System Value Master (Name = 'Order Status') to decode |

---

#### Package Details Tracking
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
Provenance: `pba-integration` query reference and `early-delivery` base extract. Not yet confirmed against `M System Value Master`.

| Value | Meaning |
|-------|---------|
| 344 | PBA-eligible placed order |
| 39 | Order created timestamp |
| 49 | Incomplete (excluded) |
| 312 | Scrapped (excluded) |
| `Order Digitised`, `Doctor Confirmed`, `Invoice Generated` | Status names used to pivot milestone timestamps; the status timestamp column is assumed `created_at` |

