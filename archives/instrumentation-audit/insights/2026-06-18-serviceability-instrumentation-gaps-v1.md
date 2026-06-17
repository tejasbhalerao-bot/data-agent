# Serviceability — Instrumentation Gap Catalog (v1)

**System #1 of the cross-system instrumentation audit.** Applies the six-lens framework in `context/2026-06-18-instrumentation-gap-framework-v1.md` to the Serviceability system described in `context/2026-06-18-serviceability-system-description-v1.md`.

**Method:** derived first-principles from the system doc. Every "Current state" below is a **hypothesis** to confirm in a later live audit (Mixpanel taxonomy + `delivery_date_tracker` / allocation instrumentation in Redshift). Nothing here should be built before that grounding pass.

---

## The headline

Serviceability is a **gatekeeper**. Today's instrumentation (`delivery_date_tracker.metadata.instrumentation_details`) is **order-time and backend-promise-focused** — it records the serviceability decision **only for orders that made it through the gate**. The entire product story lives on the *other* side of the gate and is currently dark:

1. **The pre-order decision moment** — serviceability is resolved for every browsing session, but only captured when an order is placed. We can't see the decision *mix* across all demand.
2. **The rejected population** — non-serviceable customers are silently shown the Mumbai catalog and blocked at checkout. They generate **no instrumentation at all**. This is turned-away demand we cannot size.

None of this is an engineering problem. The serviceability API is up and fast while we quietly turn demand away — the exact "green dashboard, bleeding business" failure the framework is built to catch.

---

## Proposed events (none confirmed to exist today)

| Event | Fires when | Key properties | Grain |
|---|---|---|---|
| **`serviceability_resolved`** | Serviceability is resolved for a (session, user, pincode) — Cart and Summary | `pincode, city, page (cart\|summary\|checkout), is_serviceable, wh_eligible_fc_id, wh_eligible_mfc_id, wh_selected_id, wh_selected_type (FC\|MFC), selection_reason (mfc_has_inv \| mfc_no_inv→fc \| both_no_inv→fc), construct (hyperlocal\|courier), hyperlocal_courier_id, is_cold_chain_required, is_cold_chain_deliverable, priority_used` | 1 per resolution |
| **`serviceability_blocked`** | Customer blocked from placing an order (non-serviceable pincode) | `pincode, city, cart_item_count, cart_gmv, has_cold_chain_item, block_point (browse\|cart\|summary\|place_order), browsed_mumbai_catalog, session_depth, prior_block_count_for_user` | 1 per block |
| **`serviceability_changed`** | Address edit flips serviceability / warehouse / construct | `pincode_from, pincode_to, was_serviceable, now_serviceable, wh_type_from, wh_type_to, construct_from, construct_to` | 1 per change |
| **`hyperlocal_no_fallback`** | Priority-1 hyperlocal courier can't serve/accept and no fallback exists | `pincode, wh_id, courier_id, failure_stage` | 1 per failure |
| **`serviceability_config_snapshot`** | Daily snapshot / on config update | `courier_id, source (auto_fetch\|manual_upload), updated_at, serviceable_pincode_count, pincodes_added, pincodes_removed` | 1 per courier per day |

These five events power every metric below.

---

## Lens 1 — Decisions

The system makes three decisions per session, but we only see them post-order today.

| ID | Metric | Decision it drives | Required instrumentation | Current state | Pri | Must NOT be confused with |
|---|---|---|---|---|---|---|
| A1 | **Serviceable rate** (overall / by pincode / by city) | Where are we turning demand away → expansion targets | `serviceability_resolved` aggregated by pincode | **Missing** (no pre-order event) | P1 | Serviceability-API success rate |
| A2 | **Construct mix** (hyperlocal vs courier) **at decision time** | Hyperlocal expansion + experience/CX planning | `serviceability_resolved.construct` | **Partial** — `is_sdd` exists at order-time only, non-converters missing | P1 | Hyperlocal-API call volume |
| A3 | **Warehouse-type selection mix** (MFC vs FC) | MFC utilization / network strategy | `serviceability_resolved.wh_selected_type` | **Partial** — `is_mfc` at order-time only | P1 | MFC service instance count |
| A4 | **MFC eligibility → selection conversion** | MFC inventory health from a *demand-loss* lens | `serviceability_resolved` with both `wh_eligible_mfc_id` and `selection_reason` | **Missing** | P1 | MFC inventory-service uptime |

---

## Lens 2 — Outcomes (decision → conversion join)

| ID | Metric | Decision it drives | Required instrumentation | Current state | Pri | Must NOT be confused with |
|---|---|---|---|---|---|---|
| B1 | **Serviceable → order conversion** by construct / warehouse-type | Is hyperlocal / MFC actually winning conversion? | `serviceability_resolved` carrying a session/order join key into the order funnel | **Partial** — order-time decision exists, non-converters absent | P2 | Order-create API success rate |
| B2 | **Promise-at-decision-moment → order**, by promised speed | Does a faster promise convert better, before order? | `serviceability_resolved` joined to displayed promise + order outcome | **Partial** | P2 | Promise-engine response time |

---

## Lens 3 — Rejections / Demand Leakage  ← biggest gap

Non-serviceable customers are blocked silently. This whole population is dark.

| ID | Metric | Decision it drives | Required instrumentation | Current state | Pri | Must NOT be confused with |
|---|---|---|---|---|---|---|
| C1 | **Blocked sessions / blocked unique users** | Size of turned-away demand | `serviceability_blocked` | **Missing** | **P0** | 4xx/5xx error count |
| C2 | **Blocked GMV** (cart value of blocked attempts) | Lost-revenue sizing → expansion business case | `serviceability_blocked.cart_gmv` | **Missing** | **P0** | Failed-checkout error rate |
| C3 | **Top blocked pincodes (ranked)** | **The expansion prioritization list** — most actionable output | `serviceability_blocked` aggregated by pincode | **Missing** | **P0** | — (no eng equivalent) |
| C4 | **Cold-chain-specific block rate** | Distinct lever: cold-chain infra vs general coverage | `serviceability_blocked.has_cold_chain_item` + `is_cold_chain_deliverable` | **Missing** | P2 | Cold-chain sensor/IoT alerts |
| C5 | **Repeat-blocked users** | High-intent unserved demand → notify-me / waitlist | `serviceability_blocked.prior_block_count_for_user` | **Missing** | P2 | — |
| C6 | **Block-point distribution** (browse vs full cart vs checkout) | Severity of wasted customer effort; UX of where to surface non-serviceability | `serviceability_blocked.block_point` | **Missing** | P3 | Page-load error rate |

---

## Lens 4 — Fallbacks / Degradations (silent substitution)

| ID | Metric | Decision it drives | Required instrumentation | Current state | Pri | Must NOT be confused with |
|---|---|---|---|---|---|---|
| D1 | **MFC→FC inventory fallback rate** + the promise delta it caused | MFC stocking decisions; sizes the slower-promise cost | `serviceability_resolved.selection_reason` + promise delta | **Partial** — inferable at order-time for placed orders only | P1 | MFC inventory-service errors |
| D2 | **Warehouse priority fallback usage** (priority-1 → priority-2) | Is priority-2 config actually used, or dead config? | `serviceability_resolved.priority_used` | **Missing** | P3 | Warehouse routing errors |
| D3 | **Hyperlocal priority-1 failure with no fallback** | Sizes whether priority-2 hyperlocal logic is worth building (doc flags this gap explicitly) | `hyperlocal_no_fallback` | **Missing** | P3 | Courier-API timeout rate |

---

## Lens 5 — Config / Control State (config-vs-reality drift)

The most under-watched area. Non-Bluedart couriers refresh serviceability **manually**, so config silently drifts from reality.

| ID | Metric | Decision it drives | Required instrumentation | Current state | Pri | Must NOT be confused with |
|---|---|---|---|---|---|---|
| E3 | **Paper-vs-reality rejection rate** — orders to a "serviceable" pincode later rejected by Clickpost/courier at manifest/pickup, split manual vs Bluedart | Direct measure of the manual-refresh risk → prioritize auto-fetch / config hygiene | `serviceability_config_snapshot` reconciled against manifest-rejection reasons | **Missing** (as a product metric) | **P0** | Clickpost API error rate |
| E1 | **Courier serviceability config freshness** (age since last pincode-file update, per courier) | Which couriers run on stale coverage | `serviceability_config_snapshot.updated_at` | **Missing** | P1 | Config-table replication lag |
| E2 | **Coverage drift** (serviceable-pincode count per courier over time) | Are we silently losing/gaining coverage | `serviceability_config_snapshot.serviceable_pincode_count` | **Missing** | P1 | Config-table row count |
| E4 | **Auto-fetch coverage advantage** (Bluedart auto vs manual couriers) | Quantifies value of building auto-fetch for other couriers | E1 + E3 split by `source` | **Missing** | P2 | — |
| E5 | **Config-change audit** (who/when edited masters + serviceability flips caused) | Change accountability + impact of ops edits | Change log on `pincode_warehouse_master` / `sdd_pincode_mapping` + resulting pincode on/off flips | **Missing** | P3 | DB audit log / CDC |

---

## Lens 6 — Experience friction

| ID | Metric | Decision it drives | Required instrumentation | Current state | Pri | Must NOT be confused with |
|---|---|---|---|---|---|---|
| F1 | **Phantom-catalog engagement** — non-serviceable users browsing the Mumbai catalog (sessions, depth, add-to-cart on un-orderable catalog) | Is "show Mumbai catalog" helping discovery or misleading & wasting effort? | `serviceability_blocked.browsed_mumbai_catalog` + session events | **Missing** | P3 | CDN / catalog-load latency |
| F2 | **Serviceability flip on address change** (flip rate + conversion impact) | Address-entry UX; whether to warn the customer | `serviceability_changed` | **Missing** | P2 | Address-service API errors |
| F3 | **Pincode-entry friction** (customer-perceived re-entry / spinner, not eng latency) | Is the serviceability check felt as friction? | Client timing around `serviceability_resolved` | **Missing** | P3 | Serviceability-API p95 latency |

---

## Plug-first roadmap

| Tier | Gaps | Why first |
|---|---|---|
| **P0** | C1, C2, C3 (blocked demand, GMV, top blocked pincodes), E3 (paper-vs-reality rejection) | Pure money/expansion, we're totally blind, clear lever. C3 alone is the expansion roadmap. |
| **P1** | A1–A4 (decision mix), D1 (MFC fallback), E1/E2 (config freshness & drift) | Drive network & hyperlocal strategy; partial blindness today. |
| **P2** | B1/B2 (conversion joins), C4/C5 (cold-chain & repeat-block), E4, F2 | Refine known stories; segment-level depth. |
| **P3** | C6, D2/D3, E5, F1, F3 | Edge cases & low-volume failure modes. |

**Minimum to unblock P0:** ship `serviceability_blocked` (unlocks C1/C2/C3) and `serviceability_config_snapshot` + manifest-rejection reconciliation (unlocks E3). Two events close all four P0 gaps.

---

## Coverage check (vs the framework)

- **Three gatekeeping decisions** — pincode serviceable (A1/C-series), warehouse choice (A3/A4/D1/D2), construct+partner (A2/D3/E-series). ✓
- **Documented silent failure modes** — Mumbai-catalog block (C1–C3, F1), MFC→FC fallback (A4/D1), priority-1-only hyperlocal (D3), manual courier refresh (E1–E4), cold-chain flag (C4). ✓
- Every record carries a "must NOT be confused with" eng-health contrast. ✓

## Next step
Ground this catalog: audit the live Mixpanel event taxonomy and `delivery_date_tracker` / `logistics_allocation_audit` instrumentation to flip each `Missing`/`Partial` to a confirmed status, then scope the P0 events with eng.
