---
title: PBA CR source digest
captured: 2026-10-13
systems: allocation, eta, serviceability, tracking
verticals: courier-forward (primary), hyperlocal-forward (SDD branch of the same records)
sources:
  - "[PRD] PBA integration with Clickpost": https://docs.google.com/document/d/1pV4RYHdP2a6yfpOBdDBJPL7RZMBwf9xZYRpGEzI-Jvc
  - "[PRD] PBA CR": https://docs.google.com/document/d/1dRRBcfVkMmbBBNCAzfmEAdHtsxCq4T5DurwQ8_pD8xs
  - "PBA CR Schema Clarifications" (metrics + open questions): https://docs.google.com/document/d/14OPOJnW8gqXtDGXHR4FjyE9Rato-58olAAqeDUgldQY
  - "PBA Instrumentation Records" (engineering artifact): https://claude.ai/artifact/63SppFoRTXRUAdWqomvCE5
  - "24-eta-instrumentation-proposed-record.DRAFT.json" and "26-hard-allocation-instrumentation-proposed-record.DRAFT.json" (engineering, shared 2026-10-13)
---

# PBA CR: source digest

A summary of the five sources Tejas shared on 2026-10-13. This is reference for this project only. Nothing here is a shared metric or rule until it goes through `workflows/update-context.md`.

Figures quoted from the PRD are **as reported in that document**. No script in this repo produced them, so they cannot be cited in a note as this repo's numbers.

---

## 1. Original PRD: PBA integration with Clickpost (Dec 2025 to Mar 2026)

**What PBA is.** PBA is performance-based allocation. Clickpost, the 3PL aggregator, shortlists the couriers that can serve an order and ranks them, either by static rules or dynamically by recent ETA adherence and price. Clickpost judges a courier on:
- actual shipments, in days, over a rolling 30-day window (the window can be changed);
- the pickup pincode × delivery pincode lane;
- the **80th percentile** of delivery TAT, used as that courier's ETA;
- cost, as the tie-break when ETAs are equal.

**Expected benefits.** Better adherence to the ETA promised to customers, and lower cost.

**Where the PBA ETA is used.** The pre-order summary page (the date the customer sees), warehouse allocation (the courier and picker sequence), and order creation with the courier (the final ETA). Internal portals (doctor, pharmacist) and pre-pickup tracking reuse the latest ETA. After pickup, tracking is unchanged.

**Soft allocation** (ETA on Cart and Summary) works from a lane cache first.
- A lane is warehouse_id × drop_pincode × courier × before/after cutoff, plus mode (air or surface). Each lane has a `lane_key`.
- Clickpost is called once a day per lane: before the courier's pickup cutoff for the "before" lane, after it for the "after" lane. A 24-hour lag is accepted.
- The session time decides whether the before-cutoff or after-cutoff TAT is used.
- Only the context from current date − 1 is used. The window is configurable per lane by a QA script, refreshed about every 3–4 weeks.
- The customer is shown the best ETA across couriers.
- Fallback 1 is a live Clickpost call, taking the highest-priority courier with the lowest TAT. Fallback 2 is the existing internal logic.

**Hard allocation** (ETA on Live Order and the Doctor and Pharmacist portals) calls Clickpost live first.
- The system calls Clickpost and takes the top courier from the sorted list.
- Fallback 1 is the cache. The system retries until a courier is allocated (tech owns the retry count), and shows the cache ETA in the meantime.
- Fallback 2 is the existing logic.

**Rollout plan.** 1% production sanity, then a 5% pilot, then 100%.

**Metrics in the PRD.**

| Type | Metric | PRD definition |
|---|---|---|
| Success L1 | SLA adherence % | Delivered early / on-time / late |
| Success L2 | PBA accuracy and efficacy | Whether PBA makes better decisions, and how often. Measured in shadow mode |
| Guardrail | % orders with ETA changes | ETA changed between pre-order and post-order |
| Guardrail | RTO % | RTO initiated |
| Guardrail | Delivery partner assignment % | Partner successfully assigned |
| Guardrail | Delivery promise TAT | TAT used in the promise |
| Guardrail | % PBA returned 0 couriers | No courier found |
| Guardrail | % API call to Clickpost made | Cache failed |
| Guardrail | % existing logic used | Clickpost API failed |

**Shadow mode.** Both PBA and the existing logic run on every order. PBA assigns the courier, and the existing logic's pick is only logged. Data captured: order_id, lane_key, PBA courier, existing-logic courier.

**Post-release readout at 5% (as reported in the PRD; data to about 2 Mar 2026).**
- 37,906 orders in total, of which 1,816 (4.79%) went through PBA.
- PBA's partner differed from internal's on 59.24% of orders. Where they differed, internal's partner usually sat at PBA rank 2 or 3.
- PBA moved volume away from courier 195 and towards 225, 246 and 247.
- Logistics promise adherence: internal 88.02%, PBA 85.05%. Overall promise adherence: internal 77.51%, PBA 71.09%.

The PRD's insights (attempt-based status, `pba_adjusted_status`):
1. Faster PBA promises go with more breaches.
2. Breaches are worse when the hard-allocation TAT is also faster.
3. The courier mix shifts under PBA.
4. The adherence gap persists even when PBA and internal pick the same courier, which points to promise construction rather than courier choice.
5. A soft ≠ hard partner mismatch adds to breaches.

The PRD's planned next steps:
1. Benchmark the same cuts on non-PBA orders.
2. Compare promise acceleration with actual acceleration.
3. Restrict the comparison to common lanes.
4. Measure adherence at delivery level, not attempt level, and attribute the gap to journey legs.

Related earlier work in this repo: `archives/pba-integration/` (queries on `logistics_allocation_audit` and `logistics_rails_api_audit`, plus the note `insights/2026-06-25-pba-vs-internal-performance-story-v1.md`).

---

## 2. The CR: change PBA promise construction (Oct 2026)

**Objective.** Stop PBA from giving customers inaccurate (bloated) ETAs.

**Root cause.**
- Clickpost knows TM's 3PL schedule times, so it returns the allocated courier plus a **cutoff-adjusted logistics TAT**. That TAT already covers the wait from warehouse-ready to pickup.
- Our system treats that TAT as a pure logistics TAT and adds it to the **Promised Dispatch Date**.
- This double-counts the gap between Promised WH Processing time and Promised Dispatch time, so the ETA is inflated.

**New construction.**
- *Soft allocation:*
  - Promised Delivery Date = Promised WH Processing Time + PBA TAT.
  - Promised Dispatch Time comes from the selected courier's **earliest schedule time** in the existing configuration.
- *Hard allocation:*
  - Current Delivery Date = projected WH Processing Time for the current order status + PBA TAT.

**Feature flags.** Two flags, combined with AND:
- FF1 (exists today) controls the PBA rollout to live orders.
- FF2 (new) applies the new construction to PBA orders.

If either flag is off, the old mechanism applies.

**Open comment on the CR (Tejas, 2026-10-07).** "Cache Revisit" and "Cutoff Configs" are still to be addressed.

---

## 3. Tracking plan: "PBA CR Schema Clarifications"

| # | Metric | Definition | Cuts |
|---|---|---|---|
| 1 | Promise comparison | PBA: PBA TAT in days (soft). Internal: internal TAT in days (soft) | Overall; matched (PBA partner = internal partner) and unmatched cohorts. Sub-cuts: PBA cache used, express, cold chain |
| 2 | Dispatch-adjusted promise comparison | PBA: PBA soft TAT in days minus the days from WH promise to dispatch promise. Internal: internal soft TAT, dispatch to delivery | Overall; matched and unmatched |
| 3 | Adherence comparison | Soft promise in days vs actuals in days, for each side | Matched and unmatched |
| 4 | Dispatch-adjusted adherence comparison | PBA: dispatch-adjusted soft promise vs actuals. Internal: internal TAT (dispatch to delivery) vs actuals, in days | Matched and unmatched |
| 5 | Courier allocation mix (soft) | PBA vs internal | — |

Metric 2 is the CR's correction applied backwards: it strips the double-counted WH-to-dispatch wait out of the PBA TAT so the two sides can be compared on the same basis.

The doc's open questions (rollout identification, WH and pincode, cache use and age, cutoff window, each side's promise and dispatch time, buffers, express, cold chain, actuals, courier per side) are each answered field by field in `2026-10-13-tracking-question-field-map-v1.md`.

---

## 4. Engineering instrumentation (artifact + DRAFT JSONs)

**Where the records go.** Everything is written to `logistics_instrumentation`. Records join on `request_id` and `reference_id` (the order id). Actuals are **not** in these records: they come from shipment tracking, joined on the order id.

| Record | Status | Written per |
|---|---|---|
| `PBA_ALLOCATION_INSTRUMENTATION` | Live (MR1) | Each PBA call: cache rows read, per-partner `cache_lookup` (FRESH/STALE/MISSING/LEGACY/LIVE), `cache_age_minutes`, `cutoff_window` (BEFORE/AFTER), refreshes, `allocationSource` (PBA_CACHE/PBA_API) |
| `ETA_INSTRUMENTATION` | Proposed (MR2) | Each GetPromiseETA call (soft allocation; also PDP, cart, summary, reorder, tracker, search via `screenContext`; `eta_context` PRE_OP/POST_OP) |
| `HARD_ALLOCATION_INSTRUMENTATION` | Proposed (MR2) | Each TPS cpRecommendation call (hard allocation; trigger SINGLE_ORDER_API/BULK_API/AWB_RETRY/ERP_AUTO_CONFIRM/PARTNER_DRIFT_CHECK) |

### ETA DRAFT (#24), main blocks
- **`payload.request`:**
  - `context`: actor type, `experimentVariantMap` (for example `JIT_ALLOCATION_EXP_V1`), `segmentMap`, platform, `screenContext`, pincode.
  - `warehouseId`, `deliveryPincode`, `userPaymentMode`, `products[]` (with `coldChain`, `liquid`), `warehouseProcessingTime`, `addressType`.
  - `headers`: `sdd_enabled`, `eta_context`.
- **`payload.response`:**
  - `deliveryPartner`, `estimatedWarehouseDispatchTime`, `estimatedDeliveryTime`.
  - `instrumentationDetails`: `deliveryTatInMinutes` and the `buffer` block.
- **`evaluation.facts`:**
  - `flow` (COURIER/SDD/NONE), `projected_wh_processing_time`.
  - `is_cold_chain`, `is_express_eligible` with its reason.
  - `reference_id_kind`, `warehouse`.
  - `lane_config`, including `courier_cache_state`.
- **`evaluation.configurations`:**
  - `pba_rollout`: `enabled`, `percent`, `bucket_key` (REFERENCE_ID/WH_PINCODE_HASH/FULL_ROLLOUT/ZERO_PERCENT), `bucket_value`, `in_rollout`, `pba_fetch_reason` (ROLLOUT/POSITIVE_REFERENCE_ID/NONE).
  - `pba_to_internal_tat_ratio_threshold` (4.0 in the sample).
  - Pickup and drop buffer switches.
  - `ddb_tat_adherence` allowlist and `serviceability_check` rollout.
- **`evaluation.serviceability_check`:** lane serviceability cache state and partner list.
- **`evaluation.results`:**
  - `outcome`.
  - `selected_candidate_type` (SDD/COURIER_LEGACY_TAT_ADHERENCE/COURIER_DDB_TAT_ADHERENCE/COURIER_PBA/NONE).
  - `pba_and_internal_same_partner`, `delivery_partner_id`, `is_express`.
  - `dispatch_time` with `dispatch_source`, `delivery_tat_in_minutes`, `delivery_time`, `applied_buffers[]`.
- **`evaluation.candidates[]`:** one block per source: COURIER_PBA, COURIER_LEGACY_TAT_ADHERENCE, COURIER_DDB_TAT_ADHERENCE, SDD. Each has:
  - `evaluated` and `not_evaluated_reason`, `selected`.
  - `evaluated_candidates[]`: the per-partner TAT, dispatch and delivery times, and schedule config.
  - `fetched_buffer_configs[]`.
  - `buffer_adjusted_candidates[]`: rank, buffers, post-buffer dispatch and delivery.

  The PBA block also carries:
  - `decision` (USED/REJECTED_OUTSIDE_ROLLOUT/REJECTED_NO_DATA/REJECTED_TAT_TOO_HIGH/NOT_FETCHED) and `decision_detail` (marked "to confirm from code").
  - `source` (PBA_CACHE/PBA_API/NONE).
  - `pba_to_internal_tat_ratio` and `internal_tat_used_for_ratio_in_minutes`.
  - `cache` (partition key, payment-mode fallback, refresh).
  - A per-partner `cache_row`: `cache_lookup`, `cutoff_window`, `tat_in_minutes`, `last_cached_at`, `cache_age_minutes`, `updated_by`.

### HARD DRAFT (#26), main blocks
- **`payload.request`:** `trigger`, `order_id`, `warehouse_id`, `delivery_pincode`, `payment_mode_requested`, `is_edit_order`.
- **`evaluation.facts`:**
  - `projected_wh_processing_time` with `_source` (ACTUAL_WH_SAME_DAY/ACTUAL_WH_CROSS_DAY_NOW/DERIVED_FROM_ACTUAL_DR_CALL/DERIVED_FROM_PROJECTED_DR_CALL).
  - `payment` block, `excluded_delivery_partners[]`.
- **`evaluation.configurations`:**
  - `pba_rollout`: `bucket_key` = ORDER_ID_MOD_100, and `mode` LIVE_ROLLOUT/SHADOW/SHADOW_NO_CALL/OFF.
  - `lms_shadow_enabled`, `ranking_mode`.
- **`evaluation.results`:**
  - `outcome`, `no_partner_cause`.
  - `selected_candidate_type`, which adds COURIER_CLICKPOST_FALLBACK.
  - `pba_and_internal_same_partner`, `cod_conversion`.
  - `events_published[]`: the shadow-queue `selected_source` and `decision_reason`.
- **`evaluation.candidates[]`:** COURIER_PBA (with `lms_calls[]`, `selection_rule`, `buffer_call`), COURIER_LEGACY_TAT_ADHERENCE (MySQL pincode TAT adherence), COURIER_DDB_TAT_ADHERENCE, COURIER_CLICKPOST_FALLBACK, SDD.
- **`evaluation.legacy_logic`:** order state at entry and exit, and `order_writes[]`.

---

## 5. Open questions and inconsistencies found while filing

| # | Issue | Why it matters |
|---|---|---|
| Q1 | **Two layouts for the same records.** The artifact's ETA/HARD dictionary uses `evaluation.rollout.*`, `evaluation.delivery_partner.*`, `evaluation.promises.{pba,internal,matched,allocated}` and `evaluation.times.*`. The DRAFT JSONs use `evaluation.facts`, `configurations`, `results` and `candidates[]`. Neither says it replaces the other. | Every query path depends on which one ships. The DRAFTs have no single `promises.pba` / `promises.internal` block, so each side's promise has to be rebuilt from `candidates[]`. |
| Q2 | **No CR feature flag 2 field** in either DRAFT or in the artifact dictionary. | We cannot tell which orders got the new promise construction, or separate old-construction from new-construction PBA promises. |
| Q3 | **The DRAFT samples build the PBA delivery time from the dispatch time.** ETA sample: dispatch 11:00 + 1,500 min = next day 12:00, not WH processing 09:00 + TAT. HARD sample: dispatch 17:00 + 4,320 min. | That is the pre-CR (double-counting) construction. Either the samples are illustrative or the record does not reflect the CR. Engineering should confirm. |
| Q4 | **Soft and hard rollout buckets use different keys.** Soft uses REFERENCE_ID or WH_PINCODE_HASH; hard uses ORDER_ID_MOD_100. | An order can be in PBA at soft and out at hard. "In rollout" must be defined per stage. |
| Q5 | **Several soft calls per order.** GetPromiseETA fires on PDP, cart, summary, reorder, tracker and search, pre-OP and post-OP; pre-order calls may have no `reference_id` (`reference_id_kind` = ABSENT). | We need a rule for which call is "the soft allocation" of an order (likely the ORDER_SUMMARY, PRE_OP call that carries the order id), and how calls without an order id link to orders. |
| Q6 | **Hard DRAFT lacks cache age and cutoff window.** It has only `cache.allocation_source`. | Hard-side cache questions need the `PBA_ALLOCATION_INSTRUMENTATION` record, joined on `request_id`. |
| Q7 | **`logistics_instrumentation` is not in `context/schema.md`**, and its pk/sk keys suggest a DynamoDB-style store. | We need to know whether it is queryable from Metabase/Redshift and under what table name before any query is written. |
| Q8 | **Box verified (actuals) has no documented table.** Pickup time and first delivery attempt are in `Order TAT Details`; delivery dates are in `Delivery Date Tracker`. | Metric 3/4 actuals need the box-verified source. |
| Q9 | **Minutes vs days.** Instrumentation is in minutes; every metric is in days. | Pick the conversion: `CEILING(min/1440)` as in `pba-integration`, or a calendar-date difference. Propose it in the brief. |
| Q10 | **Typo in the clarifications doc.** In section #2, items 7 and 8 are both "allocated through Internal Logic when tracking PBA promises". | Item 8 presumably means "tracking Internal promises"; confirm. |
| Q11 | **`decision_detail` values are marked "to confirm from code"** in the ETA DRAFT. | The REJECTED_TAT_TOO_HIGH ratio cut-off (4.0 in config) should be confirmed before any rejection-reason cut. |
| Q12 | **A PBA promise for internal's courier exists only if PBA returned that courier.** | For metric 1 on unmatched orders allocated by internal, the PBA promise "of the allocated courier" may be missing. Decide: use PBA's own top pick, or leave it as null. |
