---
title: Serviceability schema
type: schema
systems: [serviceability]
verticals: [all]
source: former context/schema.md (split into context/data/ on 2026-10-09; see git history)
updated: 2026-05-25
---

# Serviceability schema

> Redshift tables are prefixed `tmmumpsdb.` in Metabase SQL. Column names are `snake_case` in SQL; the display names below are the Metabase UI names. Quirks and standing exclusions live in `../rules.md`, not here.

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

#### How serviceability works (reference)
Summarised from `archives/instrumentation-audit/context/2026-06-18-serviceability-system-description-v1.md`.
- Three decisions: which pincode is serviceable, which warehouse serves it (by `Priority`), which courier serves the pair.
- **Cart page** uses the FC catalog (`Pincode Warehouse Master`). **Summary page** checks inventory at the priority-1 warehouse in both the FC and MFC tables: both stocked selects MFC; otherwise FC (FCs are assumed stocked via JIT).
- **Non-serviceable pincode:** the customer sees the Mumbai FC catalog but cannot place an order.
- **Construct:** `Is SDD = true` selects Hyperlocal, otherwise Courier. Hyperlocal considers only Ithink, Shipsy and Shiprocket, chosen from `SDD Pincode Mapping`; only priority 1 is ever used. Courier selection happens in Clickpost.
- Clickpost pincode serviceability is updated by CSV upload. Bluedart alone is auto-synced.

