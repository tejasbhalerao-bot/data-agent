---
title: Rules and vocabulary
type: business-rule
systems: [allocation, tracking, serviceability, eta, communications]
verticals: [all]
source: schema.md review (2026-05-25); early-delivery-analysis, egregiously-miscalibrated-promises, pba-integration, nano-fulfilment-centres (migrated 2026-10-09; narrowed 2026-10-10)
updated: 2026-10-10
---

# Rules and vocabulary

Applies to every request. Table layouts and data quirks are in `schema.md`; metric definitions are in `metrics.md`.

## 1. Standard filters (apply unless the request says otherwise)

| # | Rule | Applies to |
|---|------|-----------|
| E1 | Exclude orders with status 49 (Incomplete) or 312 (Scrapped) | All order analysis |
| E2 | Keep only `warehouse_id >= 17`; lower IDs are closed warehouses | `logistics_allocation_audit` |
| E3 | Keep only the latest row (`updated_at DESC`) per order per `allocation_type`, before any join | `logistics_allocation_audit` |
| E4 | Keep only `api_name = 'CLICKPOST_RECOMMEND'` for courier-preference data | `logistics_rails_api_audit` |

## 2. Default scope (used when a request leaves it out)

| Field | Default |
|-------|---------|
| Window | Last 30 days, ending yesterday |
| Verticals | All verticals of the named systems |
| Comparison | Previous period of the same length |
| Filters | E1 always; E2 to E4 on the tables they name |
| One row means | One order (`order_id`) |

## 3. Vocabulary

| Term | Meaning |
|------|---------|
| Digitised | The order was placed. `digitised_ts` is the order-placed time. |
| `digitised_*` | The promise engine's state when the order was placed; what the customer saw |
| `shipping_*` | The state when the order shipped (label printed); may differ from `digitised_*` |
| Hyperlocal | Same-day (SDD) or next-day (NDD) delivery |
| Courier vertical | Everything that is not hyperlocal |
| Vertical mapping | `digitised_is_sdd = true` is Hyperlocal, `false` is Courier. `digitised_is_mfc = true` is MFC, `false` is FC. |
| FC / MFC / NFC / DC | Fulfilment centre (full size, full stock) / micro (smaller, less stock) / nano (proposed, smaller than micro) / distribution centre |
| Inventory / non-inventory | Whether stock was held when the order was placed (`digitised_is_inventory`) |
| Segments | SDD x inventory gives four: SDD Inventory, SDD Non-Inventory, Non-SDD Inventory, Non-SDD Non-Inventory |
| HA | Health Assistant (a call step alongside the doctor call) |
| PBA | Performance Based Allocation: a courier-choice method run through Clickpost. In shadow mode it picks a courier, but the Internal method's pick is the one used. |
| Internal | The existing in-house courier-choice method |
| TAT | Turnaround time: time between two events, in minutes or days |
| SLA | The service time promised to the customer or by a courier |
| EDD | Estimated delivery date |
| OFD | Out for delivery |
| AWB | The courier shipping label. "AWB print" is when the label is printed; used as the time packing finished. |
| JIT | Just-in-time buying: full fulfilment centres are assumed stocked this way |
| ATC | Add to cart |
| RTO | Return to origin: a shipment sent back |
