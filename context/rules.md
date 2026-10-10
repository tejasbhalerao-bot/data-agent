---
title: Rules, exclusions and gotchas
type: business-rule
systems: [allocation, tracking, serviceability, eta, communications]
verticals: [all]
source: schema.md quirks (2026-05-25); early-delivery-analysis, egregiously-miscalibrated-promises, pba-integration, nano-fulfilment-centres (migrated 2026-10-09)
updated: 2026-10-09
---

# Rules, exclusions and gotchas

The single home for standing filters, default scope, vocabulary and data quirks. Schema lives in `data/`, definitions in `metrics.md`.

## 1. Standing exclusions (apply unless the request says otherwise)

| # | Rule | Applies to |
|---|------|-----------|
| E1 | Exclude `order status` 49 (Incomplete) and 312 (Scrapped) | All order analysis |
| E2 | Filter `warehouse_id >= 17`; lower IDs are decommissioned | `logistics_allocation_audit` |
| E3 | Dedupe `logistics_allocation_audit` on `updated_at DESC` per order per `allocation_type` before any join | Allocation audit |
| E4 | Filter `api_name = 'CLICKPOST_RECOMMEND'` for PBA preference data | `logistics_rails_api_audit` |
| E5 | Exclude orders with a NULL `delivery_attempt_time` from any delivery-leg metric | Promise-vs-actual metrics |
| E6 | Segmented analysis uses `digitised_ts >= 2026-05-08` (see V3) | Anything using `digitised_is_sdd`, `digitised_is_inventory`, `digitised_order_category` |

## 2. Default scope (used by the router when a request omits it)

Mirrors rule 3 in the root `CLAUDE.md` (which also lists the exclusions). Change both together.

| Field | Default |
|-------|---------|
| Window | Last 30 days, ending yesterday |
| Verticals | All verticals of the named systems |
| Comparison | Prior period of equal length |
| Exclusions | E1 and E2 always; E3 to E6 where the tables apply |
| Unit of analysis | One row per `order_id` |

## 3. Vocabulary

| Term | Meaning |
|------|---------|
| Digitised | The order was placed. `digitised_ts` equals order placed. |
| `digitised_*` | Snapshot of the promise engine at order placement; what the customer saw |
| `shipping_*` | Snapshot at shipping (AWB print); may differ from `digitised_*` |
| Hyperlocal | Same-day (SDD) or next-day (NDD) delivery |
| Courier vertical | Everything that is not hyperlocal |
| Vertical mapping | `digitised_is_sdd = true` is Hyperlocal, `false` is Courier. `digitised_is_mfc = true` is MFC, `false` is FC. |
| FC / MFC / NFC / DC | Fulfilment centre (full size, full inventory) / micro (smaller, shallower) / nano (proposed, smaller than MFC) / distribution centre |
| Inventory / non-inventory | Whether stock was held at order placement (`digitised_is_inventory`) |
| Segments | SDD x Inventory gives four: SDD Inventory, SDD Non-Inventory, Non-SDD Inventory, Non-SDD Non-Inventory |
| HA | Health Assistant (a call leg alongside the doctor call) |
| PBA | Performance Based Allocation, run through Clickpost. Courier shadow mode compares it against Internal. |

## 4. Value-handling gotchas

| # | Table or field | Quirk |
|---|----------------|-------|
| V1 | `shipping_delivery_promise` | An integer TAT in **days**, not a timestamp. Compare it with `DATE(digitised_delivery_promise) - DATE(digitised_dispatch_promise)`, never with `digitised_delivery_promise` directly. |
| V2 | Boolean columns | `digitised_is_sdd` and `digitised_is_inventory` are `true`/`false` strings; `shipping_is_sdd` is `1`/`0`; `shipping_is_inventory` is `true`/`false`. Normalise before comparing. |
| V3 | `digitised_*` state | SDD, MFC, inventory and category state are populated only from **2026-05-08**. |
| V4 | `digitised_delivery_partner` | About 4.8% blank in the May base population. Treat blanks as indeterminate in courier-switch checks, not "no switch". |
| V5 | Destination city | `pgeocode` (GeoNames) is not a Truemeds pincode-to-city master. |
| V6 | `wh_processing_mins = 0` | Warehouse 39 had a config defect (about 46k orders in May 2026, 99.97% of all zero-SLA rows). Exclude from warehouse-leg metrics. |
| V7 | `processing_start_ts` | Means the warehouse became eligible, not that processing began. It does not net out closed hours. |
| V8 | Warehouse working hours | Warehouses pack after the declared close (52% outside hours and 42% after close for early in-stock orders, vs 5% normally; May 2026). |
| V9 | Courier pricing | Where an order's price does not match the courier's configured price, it fell to default pricing. Shiprocket and Shadowfax have no configured PBA pricing and are excluded from PBA cost analysis. |

## 5. Table gotchas (from the original schema review)

| # | Table | Quirk |
|---|-------|-------|
| T1 | Order Details | The order is created at add-to-cart; `Created_on` is cart-add time, not checkout |
| T2 | Order Status | Many rows per order. Never aggregate without deduplication |
| T3 | Order TAT Details | Stores only the first delivery attempt even if there were several OFD events |
| T4 | Delivery Date Tracker | Promise data is overwritten until the order is placed; earlier values are unreachable. Use `metadata -> instrumentation_details` for the state at placement |
| T5 | Pincode Delivery TAT | `Delivery Days in Mins` overrides `Delivery Days` when non-NULL |
| T6 | Pincode TAT Adherence Data | The system adds 1 day to Ideal TAT per iteration until adherence reaches 80%, so Final TAT differs from Ideal TAT |
| T7 | Warehouse Details | Confirm active warehouses and FC/MFC classification with Tejas before querying |
| T8 | logistics_allocation_audit | `selected_source = 'INTERNAL'` in shadow mode (PBA is counterfactual). **Open: confirm whether PBA has gone live; update E2/T8 and the allocation schema if so.** |
| T9 | logistics_rails_api_audit | Join to the allocation audit on `reference_number = request_id` (exact match, never timestamps) |
| T10 | logistics_rails_api_audit | The preference array has been seen up to 6 couriers (idx 0 to 5) with no hard cap |
| T11 | Metabase | Hard timeout is 10 minutes per query; split by date range first |

## 6. Open gaps (resolve through `update-context`)

| # | Gap | Where it bites |
|---|-----|----------------|
| G1 | **Conflicting leg definitions.** Doctor leg is exact-timestamp in EMP, but a +/-1 minute band in early-delivery. Warehouse leg is promise vs AWB print (EMP), vs invoice creation against the dispatch promise (early-delivery View 1/2), and promised vs actual window (early-delivery Axis 1 v2). See `metrics.md`. | Any warehouse or doctor figure compared across projects |
| G2 | Early-delivery base extract SQL has three unconfirmed assumptions (status timestamp column, status strings, decode join) and uses `order_wh_mfc_mapping`, which is undocumented | Re-running the extract |
| G3 | `m_city_master`, `m_state_master`, `order_wh_mfc_mapping` undocumented | Cascade and inventory-state analysis |
| G4 | PBA shadow vs live status (T8) | Any PBA analysis |
| G5 | Order Status enum IDs 344 and 39 not confirmed against `M System Value Master` | PBA cohort filters |
| G6 | Communications system has no schema documented | Communications analysis |
| G7 | Instrumentation grounding pass (Mixpanel taxonomy, `instrumentation_details`) not done | `instrumentation-audit` conclusions |
