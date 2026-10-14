---
title: PBA instrumentation schema details
source: "Claude Docs: PBA Instrumentation Q&A (https://claude.ai/code/artifact/cf00e9be-06c6-4c1f-bc4c-cf4c17157fb8, tab 60ef7b50-6571), rev 92"
captured: 2026-10-14
systems: allocation, eta
verticals: courier-forward, hyperlocal-forward
---

# PBA Instrumentation Q&A

Oct 14, 2026 · @Tejas Bhalerao

Where to find each PBA allocation value in the instrumentation logs, worked on one captured order: **57051205**, prepaid, warehouse 34 to pincode 814146, 13 Oct 2026. Field meanings come from the two field dictionaries (updated from prod on 14 Oct 2026).

**Source files and their tables**

| File | Table |
| --- | --- |
| `eta-instrumentation.json` | `logistics_instrumentation` |
| `pba-allocation-from-getpromiseeta.json` | `logistics_instrumentation` |
| `allocation-audit-rows.json` | `logistics_allocation_audit` |
| `hard-allocation-instrumentation.json` | `logistics_instrumentation` |
| `pba-allocation-from-hard-allocation.json` | `logistics_instrumentation` |
| `partner-allocation-instrumentation.json` | `partner_allocation_instrumentation` |
| `pba-cache-refresh-instrumentation.json` | `logistics_instrumentation` |

**Table of contents**

- [Q1. Was PBA the decider?](#q1-was-an-orders-allocation-decided-by-pba)
- [Q2. Order status at allocation](#q2-what-status-was-the-order-in-when-allocation-ran)
- [Q3. Warehouse and delivery pincode](#q3-how-do-i-identify-the-warehouse-and-pincode-for-an-order)
- [Q4. Projected warehouse processing time](#q4-how-do-i-find-the-projected-warehouse-processing-time-for-an-order)
- [Q5. Courier selected by each strategy](#q5-how-do-i-identify-the-courier-selected-by-each-allocation-strategy-irrespective-of-whether-the-order-actually-went-through-that-strategy)
- [Q6. Promised dispatch time](#q6-how-do-i-find-the-promised-dispatch-time-for-all-couriers-across-all-allocation-strategies-at-the-soft-and-hard-stages)
- [Q7. Promised delivery date](#q7-how-do-i-find-the-promised-delivery-date-for-all-couriers-across-all-allocation-strategies-at-the-soft-and-hard-stages)
- [Q8. Was the PBA cache used?](#q8-how-do-i-identify-whether-the-pba-cache-was-used-when-the-allocation-strategy-was-pba)
- [Q9. How old was the cache?](#q9-how-do-i-identify-how-old-the-cache-was-when-the-allocation-strategy-was-pba)
- [Q10. Is it express?](#q10-how-do-i-identify-whether-is_express-is-true-for-the-pba-allocation-strategy)
- [Q11. Is it cold chain?](#q11-how-do-i-identify-whether-is_cold_chain-is-true-for-the-pba-allocation-strategy)
- [Q12. Pickup buffer applied](#q12-how-do-i-identify-the-pickup-buffer-applied-to-the-couriers-across-allocation-strategies)
- [Q13. Drop buffer applied](#q13-how-do-i-identify-the-drop-buffer-applied-to-the-couriers-across-allocation-strategies)
- [Q14. Actual timestamps](#q14-how-do-i-identify-the-timestamps-of-actuals-box-verified-pickup-time-and-delivery-attempt-time)

## How to read this document

- Each question has a **soft** part (the ETA shown to the customer, many per order) and a **hard** part (the real courier booking after doctor confirmation, one per order).
- Every sub-question has four parts: **Primary** (the one field to trust), **Secondary** (fields that back it up), **Notes** (traps and context), **Open Items** (what is still unknown).
- Paths are shortened. `evaluation.` means `payload.evaluation.`, and `request.` or `response.` mean `payload.request.` or `payload.response.`.
- **\[Inferred\]** means worked out, not read from a field. **\[Unverified\]** means not yet seen in data.
- "This order" gives the value found for 57051205.

## Quick answers

| # | Question | Where to look (primary) | This order |
| --- | --- | --- | --- |
| Q1 | Did PBA decide? | `eta-instrumentation.json` or `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.results.selected_candidate_type` | Legacy decided, at both stages |
| Q2 | Order status at allocation | Hard: `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `request.headers_sent_to_lms.reference_status` | `DOCTOR_CONFIRMED` |
| Q3 | Warehouse and pincode | `eta-instrumentation.json` or `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.facts.warehouse_id`, `delivery_pincode` | 34 and 814146 |
| Q4 | Warehouse processing time | `eta-instrumentation.json` or `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.facts.projected_wh_processing_time` | Soft 14 Oct 06:12; hard 13 Oct 22:59 |
| Q5 | Courier each strategy picks | `eta-instrumentation.json` or `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → candidate entry with `rank: 1`. New formulas: `partner-allocation-instrumentation.json` (`partner_allocation_instrumentation`) → shadow row | Legacy 185, PBA 185, new formulas 286 |
| Q6 | Dispatch time | Soft: `eta-instrumentation.json` (`logistics_instrumentation`). Hard: `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluated_candidates[].dispatch_time` | 185: 14 Oct 17:00 |
| Q7 | Delivery date | Soft: `eta-instrumentation.json` (`logistics_instrumentation`). Hard: `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluated_candidates[].delivery_time` | 185: 16 Oct 17:00 (soft) |
| Q8 | PBA cache used? | Soft: `eta-instrumentation.json` (`logistics_instrumentation`) → `candidates[PBA].source`. Hard: `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `cache.allocation_source` | Soft cache; hard live call |
| Q9 | Cache age | `eta-instrumentation.json` (`logistics_instrumentation`) → `cache_row.cache_age_minutes` | 412 minutes (soft only) |
| Q10 | Express | Soft: `eta-instrumentation.json` (`logistics_instrumentation`) → `is_express`. Hard: `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `service_type`. Order: `eta-instrumentation.json` or `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.facts.is_express_eligible` | Order yes; 225 and 286 express; winner no |
| Q11 | Cold chain | `eta-instrumentation.json` or `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.facts.is_cold_chain` (this order's hard file does not have it, see Q11.2) | `false` |
| Q12 | Pickup buffer | Soft: `eta-instrumentation.json` (`logistics_instrumentation`). Hard: `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `buffer_adjusted_candidates[].pickup_buffer_in_minutes` | 0 |
| Q13 | Drop buffer | Soft: `eta-instrumentation.json` (`logistics_instrumentation`). Hard: `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `buffer_adjusted_candidates[].drop_buffer_in_minutes` | 0 (one shadow row shows 1,440) |
| Q14 | Actual timestamps | Not in the data | Not available |

## Key terms

- **Soft allocation**: the ETA calculation for the customer, run on every ETA request. The record is `ETA_INSTRUMENTATION`.
- **Hard allocation**: the actual courier assignment after doctor confirmation. The record is `HARD_ALLOCATION_INSTRUMENTATION`.
- **PBA**: Performance-Based Allocation. It picks couriers using measured performance. *Rollout* is the share of orders where PBA is allowed to decide. Outside rollout PBA runs only in the background.
- **Legacy**: the current TAT-adherence strategy. It decided this order.
- **New formulas**: `COMPUTE_EARLY_TO_BREACH` and `COMPUTE_EARLY_TO_ONTIME`, tested at N = 10, 15 and 20. They appear only in shadow rows.
- **Shadow rows**: a background log of what each strategy would pick. Table `partner_allocation_instrumentation`.
- **TAT**: promised transit time, in minutes unless stated.

## Q1. Was an order's allocation decided by PBA?

### Q1.1 Soft allocation (customer ETA)

#### Primary Place to Look

- `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.results.selected_candidate_type`
  - `COURIER_PBA` means PBA decided. `COURIER_LEGACY_TAT_ADHERENCE` or `COURIER_DDB_TAT_ADHERENCE` means it did not.
  - This order: `COURIER_LEGACY_TAT_ADHERENCE`

#### Secondary Place to Look

- `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_PBA].decision`
  - `USED` = PBA decided. `REJECTED_OUTSIDE_ROLLOUT` = PBA ran only in the background (this order). `REJECTED_NO_DATA` = PBA had nothing usable.
- `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.configurations.pba_rollout` → `percent`, `in_rollout`
  - This order: `0`, `"FALSE"`

#### Notes That Apply

- PBA runs on every order, so a PBA entry existing proves nothing. Only `selected_candidate_type` tells you who decided.
- `in_rollout` is text (`"TRUE"` / `"FALSE"`), not true/false. A true/false filter will miss it.
- An order is in rollout when its order id modulo 100 is below `percent`. This order had `percent` 0, so it was never eligible. The prod sample in the dictionaries was at 5%.
- The `eta-instrumentation.json` record is written once per customer ETA request, so one order has several. This order has 13.

#### Open Items

- [ ] Which of the 13 soft requests counts as "the" soft allocation. Only one full `eta-instrumentation.json` record (`620b8ac3`, the order summary view) was captured. Needs engineering to define the rule.
- [ ] Whether an in-rollout order can still lose to legacy on the TAT ratio (threshold 4). \[Unverified\]

### Q1.2 Hard allocation (after doctor confirmation)

#### Primary Place to Look

- `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.results.selected_candidate_type`
  - `COURIER_PBA` means PBA decided. `COURIER_LEGACY_TAT_ADHERENCE`, `COURIER_DDB_TAT_ADHERENCE`, `SDD` or `NONE` means it did not.
  - This order: `COURIER_LEGACY_TAT_ADHERENCE`

#### Secondary Place to Look

- `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_PBA].decision`
  - `NORMAL` = PBA's partner was booked. `OUTSIDE_ROLLOUT` = PBA ran in the background only (this order). `NOT_CALLED` = PBA was skipped.
- `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.configurations.pba_rollout` → `mode`, `percent`, `in_rollout`
  - This order: `SHADOW`, `0`, `"FALSE"` (`LIVE_ROLLOUT` when in rollout)

#### Notes That Apply

- Same trap as Q1.1: PBA is called on every courier order, so check `selected_candidate_type`.
- The in-rollout `decision` is `NORMAL`. I earlier wrote `INSIDE_ROLLOUT`, which does not exist.
- Soft and hard have different `request_id`s. Join them on `order_id`.
- About half of hard records are SDD (same-day) orders. They show `in_rollout` = `"NOT_EVALUATED"` and skip most fields in this document.

#### Open Items

- [ ] When `decision` is `NOT_CALLED` (the dictionary lists the value, not the case).

## Q2. What status was the order in when allocation ran?

### Q2.1 Hard allocation: is the status doctor confirmation or something else?

#### Primary Place to Look

- `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `request.headers_sent_to_lms.reference_status`
  - `DOCTOR_CONFIRMED` is doctor confirmation. Other values seen in prod: `READY_TO_DISPATCH`, `PROCESSING`, `ORDER_CONFIRMED`, `ORDER_CANCELED`.
  - This order: `DOCTOR_CONFIRMED`

#### Secondary Place to Look

- `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.legacy_logic.order_state_at_entry` → `reference_status`, `order_status_id` (this order: `DOCTOR_CONFIRMED`, `317`)
- `pba-allocation-from-hard-allocation.json` (`logistics_instrumentation`) → `request.headers.reference_status` (`DOCTOR_CONFIRMED`)
- `partner-allocation-instrumentation.json` (`partner_allocation_instrumentation`) → `order_status` label (`DR ORDER CONFIRMED` for rows written at hard allocation)

#### Notes That Apply

- The same status shows as a code (`DOCTOR_CONFIRMED`), a number (`317`) and a label (`DR ORDER CONFIRMED`), depending on the record.
- This field exists only on courier orders. SDD records do not have it.
- Allocation did not change the status on this order (`order_state_at_exit.order_status_changed` = `NONE`).

#### Open Items

- [ ] That `317` always means `DOCTOR_CONFIRMED`. \[Inferred: they appear together here.\]
- [ ] What `49` means in the soft audit row (`allocation-audit-rows.json`), field `order_status`.

## Q3. How do I identify the warehouse and pincode for an order?

### Q3.1 Warehouse

#### Primary Place to Look

- `eta-instrumentation.json` (`logistics_instrumentation`) or `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.facts.warehouse_id`
  - This order: `34` (soft and hard)

#### Secondary Place to Look

- Request: soft `request.warehouseId`, hard `request.warehouse_id`
- `allocation-audit-rows.json` (`logistics_allocation_audit`) → `allocation_metadata.warehouse_id`; `partner-allocation-instrumentation.json` (`partner_allocation_instrumentation`) → `warehouse_id`; `pba-allocation-from-getpromiseeta.json` (`logistics_instrumentation`) or `pba-allocation-from-hard-allocation.json` (`logistics_instrumentation`) → `evaluation.warehouse.warehouse_id`
- Soft `evaluation.facts.warehouse.warehouse_type` (`MFC` here) and hard `is_ankw` (`true` here)

#### Notes That Apply

- Some fields hold `34` as a number, others `"34"` as text. Convert before comparing.
- Cache keys also contain the warehouse (`PBA_CACHE#WH#34#...`).

#### Open Items

- [ ] Whether the warehouse can differ between soft and hard for one order (same here).

### Q3.2 Delivery pincode

#### Primary Place to Look

- `eta-instrumentation.json` (`logistics_instrumentation`) or `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.facts.delivery_pincode`
  - This order: `"814146"`

#### Secondary Place to Look

- Request: soft `request.deliveryPincode`, hard `request.delivery_pincode`
- `allocation-audit-rows.json` (`logistics_allocation_audit`) → `allocation_metadata.pincode`; `partner-allocation-instrumentation.json` (`partner_allocation_instrumentation`) → `pincode`; `pba-allocation-from-getpromiseeta.json` (`logistics_instrumentation`) or `pba-allocation-from-hard-allocation.json` (`logistics_instrumentation`) → `request.deliveryPincode`

#### Notes That Apply

- Use `delivery_pincode`, not `pickup_pincode`. The latter is the warehouse's own pincode (`834010` here).
- A "lane" is warehouse plus pincode. Each record writes the lane key in its own format (audit: `34#814146#185`; cache: `PBA_CACHE#WH#34#PIN#814146#...`).
- The cache refresh file `pba-cache-refresh-instrumentation.json` shows pincode `496227`. That is a different lane and not this order.

#### Open Items

- [ ] Whether the pincode can change between soft and hard (for example after an address edit).

## Q4. How do I find the projected warehouse processing time for an order?

### Q4.1 Soft allocation (what the ETA was built on)

#### Primary Place to Look

- `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.facts.projected_wh_processing_time`
  - This order: 14 Oct 06:12

#### Secondary Place to Look

- `eta-instrumentation.json` (`logistics_instrumentation`) → `request.warehouseProcessingTime`
- `pba-allocation-from-getpromiseeta.json` (`logistics_instrumentation`) → `request.projectedWarehouseProcessingTime`
- `allocation-audit-rows.json` (`logistics_allocation_audit`) → `allocation_metadata.projected_warehouse_processing_time`

#### Notes That Apply

- Processing time is when the warehouse is expected to finish the order (06:12). It is not the dispatch time (courier pickup, 17:00 here).
- The field has a different name in each record, but the same value here.

#### Open Items

- [ ] Where the caller gets this time from.
- [ ] Whether all 13 soft requests carry the same time. Only one full `eta-instrumentation.json` record was captured.

### Q4.2 Hard allocation (after doctor confirmation)

#### Primary Place to Look

- `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.facts.projected_wh_processing_time`
  - This order: 13 Oct 22:59

#### Secondary Place to Look

- `pba-allocation-from-hard-allocation.json` (`logistics_instrumentation`) → `request.projectedWarehouseProcessingTime` (same value)

#### Notes That Apply

- Hard (13 Oct 22:59) is about 7 hours earlier than soft (14 Oct 06:12). Do not assume they match.
- The pickup slot for courier 185 is 14 Oct 17:00 at both stages, despite the different times.
- The dictionary says the `hard-allocation-instrumentation.json` record does not store how this time was worked out.

#### Open Items

- [ ] Why hard projects processing 7 hours earlier than soft.

## Q5. How do I identify the courier selected by each allocation strategy, irrespective of whether the order actually went through that strategy?

*"Selected" means the courier the strategy would pick, even if it did not win. The actual winner is in Q1.*

### Q5.1 Soft allocation (customer ETA)

#### Primary Place to Look

| Strategy | Where to look | This order |
| --- | --- | --- |
| Legacy | `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_LEGACY_TAT_ADHERENCE].buffer_adjusted_candidates[]`, the entry with `rank: 1` → `delivery_partner_id` | 185 |
| PBA | `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_PBA].buffer_adjusted_candidates[]`, the entry with `rank: 1` | 185 |
| New formulas | Shadow row → `selected_courier_partner` (the row ending `#VAR#COMPUTE_EARLY_TO_BREACH#N#10` etc.) | 286 |
| DDB, SDD | Same as legacy when evaluated | Not evaluated |

#### Secondary Place to Look

- `pba-allocation-from-getpromiseeta.json` (`logistics_instrumentation`) → `response.deliveryPartners[]` lists the five eligible couriers, but with no rank.
- `partner-allocation-instrumentation.json` (`partner_allocation_instrumentation`) → `couriers[].rank_in_allocation` (1 = pick) and `tat_adherence_score` (lower is better).
- `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.results.pba_and_internal_same_partner` (`true` here).

#### Notes That Apply

- On this order legacy and PBA pick 185. All six new-formula variants pick 286.
- `pba_and_internal_same_partner` only compares PBA with the winner, not with the new formulas. The dictionary also lists a known defect in it.
- On a non-winning PBA entry, `selected` is `false`. Rank 1 is still its pick.
- Shadow rows (`partner-allocation-instrumentation.json`) have no PBA variant. PBA's pick is only in the `eta-instrumentation.json` record.

#### Open Items

- [ ] Whether each strategy picks the same courier across all 13 soft requests. Needs your go-ahead to compare the 105 shadow rows (`partner-allocation-instrumentation.json`).

### Q5.2 Hard allocation (after doctor confirmation)

#### Primary Place to Look

| Strategy | Where to look | This order |
| --- | --- | --- |
| Legacy | `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_LEGACY_TAT_ADHERENCE].buffer_adjusted_candidates[]`, the entry with `rank: 1` | 185 |
| PBA | `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_PBA].evaluated_candidates[]`, the first entry with `excluded: false` | 185 |
| New formulas | `partner-allocation-instrumentation.json` (`partner_allocation_instrumentation`) for the hard request (client `third_party_service`) → `selected_courier_partner` | 286 |
| DDB, Clickpost fallback, SDD | Not evaluated (`evaluated: false`) | None |

#### Secondary Place to Look

- `partner-allocation-instrumentation.json` (`partner_allocation_instrumentation`) `#VAR#LEGACY_HARD` → `selected_courier_partner` (`185`, matches the hard-allocation record)
- `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.results.delivery_partner_id` (`185`, the winner)

#### Notes That Apply

- PBA's hard pick is a rule, not a ranking: it takes the first courier LMS returned that is not excluded (`FIRST_MAPPED_PARTNER`).
- Legacy and PBA agree again; the new formulas again pick 286.
- Per the dictionary, Clickpost fallback runs only when TAT adherence found no courier, and DDB only on allow-listed lanes.

#### Open Items

- [ ] Whether PBA's pick can differ between soft and hard when the order is in rollout. \[Unverified\]

## Q6. How do I find the promised dispatch time for all couriers, across all allocation strategies, at the soft and hard stages?

*Dispatch means the courier's pickup slot. Everything below is 14 Oct for this order.*

### Q6.1 Soft allocation (customer ETA)

#### Primary Place to Look

- `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_PBA]` or `[COURIER_LEGACY_TAT_ADHERENCE]` → `evaluated_candidates[]` → `dispatch_time`
- New formulas and SDD have no dispatch time.

This order:

| Courier | PBA | Legacy |
| --- | --- | --- |
| 185 XpressBees | 17:00 | 17:00 |
| 286 XpressBees Express | 17:00 | 17:00 |
| 685 Shiprocket | 17:15 | 17:15 |
| 195 Delhivery | 17:30 | 17:30 |
| 225 Delhivery Express | 17:30 | 17:30 |
| 246, 247 | Not eligible | Dropped as not serviceable, no time |

#### Secondary Place to Look

- `pba-allocation-from-getpromiseeta.json` (`logistics_instrumentation`) → `response.deliveryPartners[].projectedDispatchTime`
- Winner only: `evaluation.results.dispatch_time` (17:00, courier 185)
- `allocation-audit-rows.json` (`logistics_allocation_audit`) → `projected_dispatch_time` (UTC)

#### Notes That Apply

- Ignore legacy's `schedule_time`. It is not a clock time (`17:50` means 17:30). Use `dispatch_time`.
- PBA and legacy agree for every courier on this order. That may not hold for other orders.
- If a pickup buffer applies, the buffer-adjusted time can differ (none here).
- New formulas choose the courier only. Their shadow rows (`partner-allocation-instrumentation.json`) have no date.

#### Open Items

- [ ] Whether PBA and legacy always agree on dispatch time.
- [ ] Which of the 13 soft requests is the promise (see Q1.1).

### Q6.2 Hard allocation (after doctor confirmation)

#### Primary Place to Look

- `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_PBA].evaluated_candidates[]` → `dispatch_time`
- Legacy: **not recorded**. The dictionary confirms legacy dispatch time is never written at the hard stage.

This order:

| Courier | PBA | Legacy |
| --- | --- | --- |
| 185 XpressBees | 17:00 | Not recorded |
| 286 XpressBees Express | 17:00 | Not recorded |
| 685 Shiprocket | 17:15 | Not recorded |
| 195 Delhivery | 17:30 | Not recorded |
| 225 Delhivery Express | 17:30 | Not recorded |

#### Secondary Place to Look

- `pba-allocation-from-hard-allocation.json` (`logistics_instrumentation`) → `response.deliveryPartners[].projectedDispatchTime`, `evaluation.pickup_slots[]`
- Winner, only when PBA was booked: `evaluation.results.dispatch_time`

#### Notes That Apply

- The hard PBA times equal the soft ones.
- Legacy's likely hard-stage dispatch is the same 17:00 slot for 185. \[Inferred: a schedule-penalty flag points to the next slot.\]

#### Open Items

- [ ] Where legacy's hard-stage dispatch time can be found, if anywhere.

## Q7. How do I find the promised delivery date for all couriers, across all allocation strategies, at the soft and hard stages?

### Q7.1 Soft allocation (customer ETA)

#### Primary Place to Look

- `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_PBA]` or `[COURIER_LEGACY_TAT_ADHERENCE]` → `evaluated_candidates[]` → `delivery_time` (with `delivery_tat_in_minutes`)
- New formulas and SDD have no delivery date.

This order:

| Courier | PBA | Legacy |
| --- | --- | --- |
| 185 XpressBees | 16 Oct 17:00 | 16 Oct 17:00 |
| 286 XpressBees Express | 17 Oct 17:00 | 17 Oct 17:00 |
| 225 Delhivery Express | 17 Oct 17:30 | 17 Oct 17:30 |
| 195 Delhivery | 17 Oct 17:30 | 18 Oct 17:30 |
| 685 Shiprocket | 18 Oct 20:56 | 19 Oct 17:15 |
| 246, 247 | Not eligible | No date (dropped) |

#### Secondary Place to Look

- Winner only: `response.estimatedDeliveryTime` and `evaluation.results.delivery_time` (16 Oct 17:00, what the customer saw)
- `pba-allocation-from-getpromiseeta.json` (`logistics_instrumentation`) → `response.deliveryPartners[].tatInMinutes` (a TAT, no date)

#### Notes That Apply

- Delivery date looks like dispatch time plus TAT (185: 14 Oct 17:00 + 2,880 min = 16 Oct 17:00). \[Inferred: checked on two couriers.\]
- PBA and legacy differ for 195 and 685.
- New-formula shadow rows (`partner-allocation-instrumentation.json`) give a TAT in days, not a date. They choose a courier and do not make a promise.

#### Open Items

- [ ] Confirm delivery date always equals dispatch plus TAT.
- [ ] Which of the 13 soft requests is the promise (see Q1.1).

### Q7.2 Hard allocation (after doctor confirmation)

#### Primary Place to Look

- `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_PBA].evaluated_candidates[]` → `delivery_time` (with `delivery_tat_in_minutes`)
- Legacy: **no date recorded**. Only `final_tat_days` is kept.

This order:

| Courier | PBA | Legacy (days only) |
| --- | --- | --- |
| 185 XpressBees | 17 Oct 17:00 | 2 |
| 286 XpressBees Express | 18 Oct 17:00 | 3 |
| 225 Delhivery Express | 18 Oct 17:30 | 3 |
| 195 Delhivery | 18 Oct 17:30 | 4 |
| 685 Shiprocket | 19 Oct 23:49 | 5 |
| 246, 247 | None | 6 |

#### Secondary Place to Look

- Winner: `evaluation.results.delivery_tat_in_minutes` (`2880` = 2 days). A winner date (`results.delivery_time`) is written only when PBA was booked.
- `pba-allocation-from-hard-allocation.json` (`logistics_instrumentation`) → `response.deliveryPartners[].tatInMinutes`

#### Notes That Apply

- PBA's hard dates are later than its soft dates for every courier: one day later for 185, 195, 225 and 286, and 1,613 minutes later for 685.
- The customer was promised 16 Oct (legacy won). PBA would have said 17 Oct.
- Legacy days match the soft legacy TAT for each courier (2 days = 2,880 min).

#### Open Items

- [ ] Why PBA's hard TAT is longer than its soft TAT. Hard uses a live call and soft uses a cache, but the cause is unconfirmed.
- [ ] Whether the customer-facing date is recomputed at the hard stage.

## Q8. How do I identify whether the PBA cache was used when the allocation strategy was PBA?

*PBA did not decide this order, so the values below show what PBA did in the background.*

### Q8.1 Soft allocation (customer ETA)

#### Primary Place to Look

- `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_PBA].source`
  - `PBA_CACHE` = cache was read. `NONE` = the cache had no rows.
  - This order: `PBA_CACHE`

#### Secondary Place to Look

- Per courier: `evaluated_candidates[].cache_row.cache_lookup` (`FRESH` here; other values `MISSING`, `LEGACY`)
- `pba-allocation-from-getpromiseeta.json` (`logistics_instrumentation`) → `response.allocationSource` (`ALLOCATION_SOURCE_PBA_CACHE`) and `evaluation.attempts[].cache.read` (`true`)

#### Notes That Apply

- Each courier has two cache rows, one for before and one for after the pickup cutoff. This order used the "before" row.
- The cache read took 3 ms.
- The soft request also wrote fresh "after" rows back to the cache. \[Inferred from timestamps.\]

#### Open Items

- [ ] Whether all 13 soft requests used the cache.

### Q8.2 Hard allocation (after doctor confirmation)

#### Primary Place to Look

- `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_PBA].cache.allocation_source`
  - `PBA_API` = live call to PBA, cache not read. This order: `PBA_API`.

#### Secondary Place to Look

- `pba-allocation-from-hard-allocation.json` (`logistics_instrumentation`) → `response.allocationSource` (`ALLOCATION_SOURCE_PBA_API`) and `evaluation.attempts[].cache.read` (`false`)
- `pba-allocation-from-hard-allocation.json` (`logistics_instrumentation`) → `attempts[].cache_writes[]` (live answer written back)

#### Notes That Apply

- Per the dictionary, hard allocation always calls PBA live and never reads the cache.
- The live call took 191 ms, against 3 ms for the soft cache read.
- The same courier shows a different TAT at soft and hard (185: 2,880 min soft, 4,320 min hard). A cache read versus a live call may explain it. \[Inferred\]

#### Open Items

- [ ] Whether the hard-stage write-back is what the next soft request reads.

## Q9. How do I identify how old the cache was when the allocation strategy was PBA?

### Q9.1 Soft allocation (customer ETA)

#### Primary Place to Look

- `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_PBA].evaluated_candidates[]` → `cache_row.cache_age_minutes`
  - This order: `412` minutes (about 6 h 52 min), the same for all five eligible couriers

#### Secondary Place to Look

- Same `cache_row` → `last_cached_at` (13 Oct 15:05), `updated_by`, `cutoff_window`
- `evaluation.configurations.pba_cache_refresh_after_hours` (`24`)

#### Notes That Apply

- The age checks out: 15:05 to the request time of 21:57 is 412 minutes.
- 412 minutes is within the 24-hour refresh setting, and the row reads `FRESH`. \[Inferred: that FRESH means "within the limit".\]
- The fresher "after" rows were written at 21:57 by this same request but were not the rows used.

#### Open Items

- [ ] What `cache_lookup` shows for a row older than 24 hours. The dictionary lists only `FRESH`, `MISSING` and `LEGACY`. \[Unverified\]

### Q9.2 Hard allocation (after doctor confirmation)

#### Primary Place to Look

- No cache age at hard. The hard stage calls PBA live (`cache.allocation_source` = `PBA_API`, see Q8.2).

#### Secondary Place to Look

- `pba-allocation-from-hard-allocation.json` (`logistics_instrumentation`) → `attempts[].cache_writes[]` (rows written back with a fresh time)

#### Notes That Apply

- Per the dictionary, hard never reads the cache, so no age is expected.

#### Open Items

- [ ] Whether this holds on every hard path, including SDD.

## Q10. How do I identify whether `is_express` is TRUE for the PBA allocation strategy?

*"Express" has three meanings: the order can go express, a courier is an express courier, and the selected courier is express.*

### Q10.1 Soft allocation (customer ETA)

#### Primary Place to Look

- Courier is express: `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_PBA].evaluated_candidates[]` → `is_express`
  - This order: `true` for 225 and 286; `false` for 185, 195 and 685
- Order can go express: `evaluation.facts.is_express_eligible` (`true`), with `express_eligible_reason` (`OK`; other values `LIQUID_OVER_THRESHOLD`, `NO_EXPRESS_LANE`)

#### Secondary Place to Look

- Same courier entry → `service_type` (`EXPRESS` / `SURFACE`)
- Selected courier: `evaluation.results.is_express` (`false`)
- `pba-allocation-from-getpromiseeta.json` (`logistics_instrumentation`) → `evaluation.key_facts.express_eligible` (`true`)

#### Notes That Apply

- On this order: order is eligible (`true`), two of five couriers are express, and the selected courier (185) is not.
- The cache key's `EXP#TRUE` part matches order eligibility. \[Inferred.\]

#### Open Items

- [ ] What PBA lists when the order is not express-eligible. \[Unverified\]

### Q10.2 Hard allocation (after doctor confirmation)

#### Primary Place to Look

- Courier is express: `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_PBA].evaluated_candidates[]` → `service_type` (`EXPRESS` for 225 and 286; `SURFACE` for 185, 195 and 685). The dictionary confirms `is_express` is not written here.
- Order can go express: `evaluation.facts.is_express_eligible` (`true`), with `express_eligible_reason` (`OK`; other values `LIQUID_OVER_200`, `NO_EXPRESS_LANE`)

#### Secondary Place to Look

- Selected courier: `evaluation.results.is_express` (`false`)
- `pba-allocation-from-hard-allocation.json` (`logistics_instrumentation`) → `evaluation.key_facts.express_eligible` (`true`)

#### Notes That Apply

- Soft says `is_express` and hard says `service_type`; both agree for these five couriers.
- The liquid reason is spelled differently by stage (`LIQUID_OVER_THRESHOLD` soft, `LIQUID_OVER_200` hard). Both mean the 200 limit was exceeded.

#### Open Items

- [ ] The unit of the hard stage's liquid limit (soft uses ml).

## Q11. How do I identify whether `is_cold_chain` is TRUE for the PBA allocation strategy?

### Q11.1 Soft allocation (customer ETA)

#### Primary Place to Look

- `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.facts.is_cold_chain`
  - This order: `false`

#### Secondary Place to Look

- `pba-allocation-from-getpromiseeta.json` (`logistics_instrumentation`) → `evaluation.key_facts.is_cold_chain` (`false`)
- Cache key `...#CC#FALSE#...`

#### Notes That Apply

- `lane_config.cold_chain_enabled` says whether the pincode lane supports cold chain. `is_cold_chain` is about the order. Both are `false` here.
- The request has a per-product `coldChain` flag. How product flags roll up to the order flag is not shown.

#### Open Items

- [ ] Confirm that `CC` in the cache key means cold chain. \[Inferred\]
- [ ] What makes an order cold chain, and where that is decided.

### Q11.2 Hard allocation (after doctor confirmation)

#### Primary Place to Look

- `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.facts.is_cold_chain`. **The dictionary lists it, but **this order's hard-allocation record** does not have it.**
- For this order, use the `pba-allocation-from-hard-allocation.json` (`logistics_instrumentation`) → `evaluation.key_facts.is_cold_chain` = `false`.

#### Secondary Place to Look

- Cache key in the hard attempt (`attempts[].cache_pk`, `...#CC#FALSE#...`)

#### Notes That Apply

- The captured record may predate the dictionary, or the field may be written only sometimes.

#### Open Items

- [ ] Whether `facts.is_cold_chain` is written on every `hard-allocation-instrumentation.json` record.

## Q12. How do I identify the pickup buffer applied to the couriers across allocation strategies?

*A buffer is extra time added to a courier's pickup or delivery promise. No pickup buffer was applied on this order.*

### Q12.1 Soft allocation (customer ETA)

#### Primary Place to Look

- Legacy: `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_LEGACY_TAT_ADHERENCE].buffer_adjusted_candidates[]` → `pickup_buffer_in_minutes` (`0` for all five couriers)
- PBA: `candidates[COURIER_PBA].buffer_applied` (`false`)
- New formulas: `partner-allocation-instrumentation.json` (`partner_allocation_instrumentation`) → `couriers[].pickup_buffer` (`0`)
- What the customer's promise carries: `response.instrumentationDetails.buffer` (empty; written only if a buffer applied)

#### Secondary Place to Look

- Each candidate's `fetched_buffer_configs[]` → `buffer_type: PICKUP`, `applied`, `not_applied_reason`
- `evaluation.configurations.pba_pickup_buffer_enabled` (`false`)

#### Notes That Apply

- Buffers were skipped because the PBA buffer switch is off (`PBA_BUFFER_SWITCH_OFF`), or the legacy config was inactive or outside its schedule (`CONFIG_INACTIVE`, `SCHEDULE_NOT_ACTIVE`).
- A buffer can be negative. In the dictionary's example, -420 minutes moves a dispatch from 20:00 to 13:00. \[From an example, not this order.\]
- The dictionary says PBA never gets a buffer applied.

#### Open Items

- [ ] How `response.instrumentationDetails.buffer` relates to `results.buffer_applied`. In the dictionary's example, one says a buffer applied and the other says none.

### Q12.2 Hard allocation (after doctor confirmation)

#### Primary Place to Look

- Legacy: `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_LEGACY_TAT_ADHERENCE].buffer_adjusted_candidates[]` → `pickup_buffer_in_minutes` (`0` for all seven couriers)
- PBA: the hard PBA candidate has no buffer fields unless the order is in rollout.
- New formulas: `partner-allocation-instrumentation.json` (`partner_allocation_instrumentation`) → `couriers[].pickup_buffer` (`0`)

#### Secondary Place to Look

- Legacy candidate → `buffer_applied` (`false`)

#### Notes That Apply

- The `hard-allocation-instrumentation.json` record does not store which buffer configs were considered, so a skipped buffer has no reason on record.

#### Open Items

- [ ] Whether buffers are ever applied at the hard stage, and where the reason would show.

## Q13. How do I identify the drop buffer applied to the couriers across allocation strategies?

### Q13.1 Soft allocation (customer ETA)

#### Primary Place to Look

- Legacy: `eta-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_LEGACY_TAT_ADHERENCE].buffer_adjusted_candidates[]` → `drop_buffer_in_minutes` (`0` for all five couriers)
- PBA: `candidates[COURIER_PBA].buffer_applied` (`false`)
- New formulas and legacy shadow rows: `partner-allocation-instrumentation.json` (`partner_allocation_instrumentation`) → `couriers[].drop_buffer`
- What the customer's promise carries: `response.instrumentationDetails.buffer` (empty)

#### Secondary Place to Look

- Each candidate's `fetched_buffer_configs[]` → `buffer_type: DROP`, `applied`, `not_applied_reason`
- `evaluation.configurations.pba_drop_buffer_enabled` (`false`)
- `partner-allocation-instrumentation.json` (`partner_allocation_instrumentation`): `tat_adherence_score` against `tat_adherence_score_with_buffer`

#### Notes That Apply

- The `eta-instrumentation.json` record shows no drop buffer. **But **one shadow row (`partner-allocation-instrumentation.json`) does**.** For soft request `121e822f` (the first of the 13), the `LEGACY` row has `drop_buffer: 1440` for courier 286, raising its score by exactly 1,440. Courier 185 stayed first. The other 12 requests show 0.
- So the buffer can differ between requests of the same order. Why it appeared once is not shown.
- This was found by scanning the shadow rows (`partner-allocation-instrumentation.json`) for non-zero buffers, which was a lookup, not a comparison across variants.

#### Open Items

- [ ] Why request `121e822f` applied a drop buffer to 286 and the others did not.
- [ ] What `drop_buffer_reset` shows when it is `true`. \[Unverified\]

### Q13.2 Hard allocation (after doctor confirmation)

#### Primary Place to Look

- Legacy: `hard-allocation-instrumentation.json` (`logistics_instrumentation`) → `evaluation.candidates[COURIER_LEGACY_TAT_ADHERENCE].buffer_adjusted_candidates[]` → `drop_buffer_in_minutes` (`0` for all seven couriers)
- PBA: no buffer fields unless in rollout.
- New formulas and `LEGACY_HARD`: `partner-allocation-instrumentation.json` (`partner_allocation_instrumentation`) → `couriers[].drop_buffer` (`0`)

#### Secondary Place to Look

- Legacy candidate → `buffer_applied` (`false`)

#### Notes That Apply

- Same limits as Q12.2.

#### Open Items

- [ ] Whether the hard stage ever applies a drop buffer.

## Q14. How do I identify the timestamps of actuals: box verified, pickup time, and delivery attempt time?

*These files are allocation-time records, taken before the order was packed or shipped. None of the three timestamps is in them. The dictionaries list no actuals either.*

### Q14.1 Box verified

#### Primary Place to Look

- **Not in the captured data.**

#### Secondary Place to Look

- None.

#### Notes That Apply

- The capture ends when allocation finishes, which is before box verification. \[Inferred from timing.\]

#### Open Items

- [ ] Which system or table holds the box verification timestamp.

### Q14.2 Pickup time (actual)

#### Primary Place to Look

- **Not in the captured data.**

#### Secondary Place to Look

- The planned pickup is there: `evaluated_candidates[].dispatch_time` (see Q6).

#### Notes That Apply

- Do not read the planned `dispatch_time` as an actual pickup. It is the promise made at allocation.

#### Open Items

- [ ] Which system or table holds the actual pickup timestamp.

### Q14.3 Delivery attempt time

#### Primary Place to Look

- **Not in the captured data.**

#### Secondary Place to Look

- The promised delivery is there: `evaluated_candidates[].delivery_time` (see Q7).

#### Notes That Apply

- The `attempts` field in the PBA records is about cache lookups, not delivery attempts.

#### Open Items

- [ ] Which system or table holds delivery attempt timestamps (courier status updates are a possibility). \[Unverified\]
