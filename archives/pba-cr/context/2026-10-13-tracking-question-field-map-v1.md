---
title: PBA CR tracking questions mapped to instrumentation fields
captured: 2026-10-13
systems: allocation, eta, tracking
verticals: courier-forward
sources: PBA CR Schema Clarifications (Google Doc 14OPOJnW…); ETA DRAFT #24; HARD DRAFT #26; artifact 63SppFoRTXRUAdWqomvCE5
status: draft. Paths are taken from proposed (MR2) records and are not verified against live data.
---

# Tracking questions → fields

Each question from "PBA CR Schema Clarifications" is listed with the field that answers it in both layouts engineering has shared.

**How to read this:**
- **DRAFT** paths are relative to `payload.` in the 2026-10-13 DRAFT JSONs. `cand[X]` means the `evaluation.candidates[]` element whose `candidate_type = X`.
- **Artifact** paths come from the artifact's question guide and field dictionary.
- Which layout ships is open question Q1 in the source digest.

Candidate types used below: PBA = `COURIER_PBA`; INT = the internal side, which is `COURIER_LEGACY_TAT_ADHERENCE` or `COURIER_DDB_TAT_ADHERENCE`, whichever was evaluated (`COURIER_CLICKPOST_FALLBACK` too on hard).

## For all metrics

| Q | Soft: ETA DRAFT | Hard: HARD DRAFT | Artifact | Gap |
|---|---|---|---|---|
| In PBA rollout? | `evaluation.configurations.pba_rollout.in_rollout` (+ `bucket_key`, `bucket_value`, `percent`, `pba_fetch_reason`); `cand[PBA].decision` = REJECTED_OUTSIDE_ROLLOUT | `evaluation.configurations.pba_rollout.in_rollout` (+ `mode`, `bucket_value`) | `evaluation.rollout.pba.in_rollout`; `evaluation.lms.rollout.in_rollout` | Soft and hard bucket on different keys (Q4). No CR flag-2 field (Q2) |
| WH and pincode | `request.warehouseId`, `request.deliveryPincode`; `evaluation.facts.warehouse_id`, `pickup_pincode`, `delivery_pincode` | `request.warehouse_id`, `request.delivery_pincode`; `evaluation.facts.*` | `evaluation.lane.*` (ETA); `evaluation.warehouse.*` + `evaluation.pincode.*` (HARD) | — |
| Matched / unmatched cohort | `evaluation.results.pba_and_internal_same_partner` | same | `evaluation.promises.matched` | Null when one side was not evaluated |
| Which side allocated | `evaluation.results.selected_candidate_type` | same | `evaluation.promises.allocated` | — |

## Metric 1: promise comparison

| Q | Soft: ETA DRAFT | Hard: HARD DRAFT | Artifact | Gap |
|---|---|---|---|---|
| 1.1–1.4: WH promise → delivery promise, per allocated side × tracked side | WH promise: `evaluation.facts.projected_wh_processing_time`. PBA side: `cand[PBA].buffer_adjusted_candidates[rank=1].delivery_time` (pre-buffer: `evaluated_candidates[].delivery_time`). INT side: same fields under `cand[INT]`. Allocated side: `results.selected_candidate_type` | WH promise: `evaluation.facts.projected_wh_processing_time` (+ `_source`). Sides as for soft | `evaluation.promises.projected_wh_processing_time`, `promises.pba.delivery_time`, `promises.internal.delivery_time` | Present only when that side was `evaluated` (PBA is skipped when not fetched, for example no reference id). Samples build delivery from dispatch, not from WH time (Q3) |
| 1.5–1.6: Cache used (in / outside rollout) | `cand[PBA].source` (PBA_CACHE/PBA_API/NONE); `cand[PBA].evaluated_candidates[].cache_row.cache_lookup`. Outside rollout only if fetched: `pba_rollout.pba_fetch_reason` = POSITIVE_REFERENCE_ID | `cand[PBA].source`, `cand[PBA].cache.allocation_source`. Outside rollout only in shadow (`pba_rollout.mode` = SHADOW) | `PBA_ALLOCATION`: `response.allocationSource`, `evaluation.attempts[].partners[].cache_lookup` (written in or outside rollout whenever there is an order id) | — |
| 1.7–1.8: Cache age | `cand[PBA].evaluated_candidates[].cache_row.cache_age_minutes`, `.last_cached_at` | **Not in DRAFT** | `PBA_ALLOCATION`: `attempts[].partners[].cache_age_minutes`, `attempts[].cache.records[].last_cached_at`; ETA `promises.pba.cache_age_minutes` | Hard needs a join to PBA_ALLOCATION on `request_id` (Q6) |
| 1.9–1.10: Before or after cutoff (cache / live) | `cand[PBA].evaluated_candidates[].cache_row.cutoff_window`; `pickup_slot.final_slot_time` | **Not in DRAFT** | `PBA_ALLOCATION`: `attempts[].partners[].cutoff_window`, `pickup_slots[].final_slot_time`; ETA `promises.pba.cutoff_window` | For live calls (`cache_lookup` = LIVE), confirm `cutoff_window` is filled |
| 1.11: PBA promise of the allocated courier when internal allocated | `cand[PBA].evaluated_candidates[]` where `delivery_partner_id = results.delivery_partner_id` | same, under HARD `cand[PBA]` | `promises.pba.*` ("both sides computed on every call") | Missing if PBA did not return that courier (Q12) |
| 1.12: Internal promise of the allocated courier when PBA allocated | `cand[INT].evaluated_candidates[]` / `buffer_adjusted_candidates[]` where `delivery_partner_id = results.delivery_partner_id` | same | `promises.internal.*` | Same caveat |
| 1.13: Express | `results.is_express`; `cand[*].evaluated_candidates[].is_express`; eligibility `facts.is_express_eligible`, `facts.express_eligible_reason` | `results.is_express`; `results.selected_courier_master.is_express` | `promises.pba.is_express`, `promises.internal.is_express` | — |
| 1.14: Cold chain | `facts.is_cold_chain`; `request.products[].coldChain` | `facts.is_cold_chain` | `evaluation.product.is_cold_chain` / `evaluation.package.is_cold_chain` | Hard evaluates cold chain on SDD only |

## Metric 2: dispatch-adjusted promise (on top of metric 1)

| Q | Soft: ETA DRAFT | Hard: HARD DRAFT | Artifact | Gap |
|---|---|---|---|---|
| 2.1–2.4: Dispatch time per allocated side × tracked side | `cand[X].evaluated_candidates[].dispatch_time` (pre-buffer) and `buffer_adjusted_candidates[].dispatch_time` (post-buffer), with `dispatch_source`; served value: `results.dispatch_time`, `response.estimatedWarehouseDispatchTime` | same under HARD `cand[X]`; `results.dispatch_time` | `promises.pba.dispatch_before_buffer` / `dispatch_time`; `promises.internal.*` | — |
| 2.5–2.8: Pickup / drop buffer applied, and how much, per side | `cand[X].buffer_applied`, `applied_buffers[]`, `fetched_buffer_configs[]` (`applied`, `not_applied_reason`), `buffer_adjusted_candidates[].pickup_buffer_in_minutes` / `drop_buffer_in_minutes` / `pickup_day_rolled` / `drop_buffer_reset`; switches: `configurations.pba_pickup_buffer_enabled`, `pba_drop_buffer_enabled` | `cand[X].buffer_applied`, `buffer_adjusted_candidates[]`, `buffer_call.attempted` / `applied` / `skip_reason` | `promises.pba.pickup_buffer_in_minutes` / `drop_buffer_in_minutes`; same for internal | The doc repeats item 7 as item 8 (Q10) |

## Metrics 3–4: adherence (actuals)

| Q | Source | Gap |
|---|---|---|
| Box verified, pickup time, delivery attempt time | Not in the instrumentation. Artifact: shipment tracking (`logistics_shipment_details` / tracking events) on `reference_id`. In `context/schema.md`: `Order TAT Details` (Pickup Time, first Delivery Attempt Time) and `Delivery Date Tracker` (Actual Delivery Date) | Box verified has no documented table (Q8); `logistics_shipment_details` is not in `schema.md` |

## Metric 5: courier allocation mix (soft)

| Q | Soft: ETA DRAFT | Artifact | Gap |
|---|---|---|---|
| Courier via PBA and via internal | PBA pick: `cand[PBA].buffer_adjusted_candidates[rank=1].delivery_partner_id`. Internal pick: `cand[INT].buffer_adjusted_candidates[rank=1].delivery_partner_id`. Served: `results.delivery_partner_id` | `promises.pba.delivery_partner_id`, `promises.internal.delivery_partner_id`; `delivery_partner.selection.delivery_partner_id` | Choice of one soft call per order (Q5) |

Note: in the DRAFTs, `selected` on `buffer_adjusted_candidates[]` marks each source's own top pick; `selected` on the `candidates[]` element marks the source that was served.
