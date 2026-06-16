# Early Delivery Analysis — Analysis Plan (v1)

**Project:** early-delivery-analysis
**Approach:** Cascade-first (map where deviation is created and absorbed, before leg-specific deep dives)
**Cohort:** Forward orders digitised in May 2026 — Hyperlocal (SDD) + Courier

---

## Objective

Identify why forward orders are delivered earlier than their customer promise by mapping where earliness — and lateness — is **created and absorbed** across an order's legs. This precedes any leg-specific deep dive (courier allocation, TAT config), so that those deep dives are pointed at the leg the data actually implicates.

---

## Outcome definition

- **Baseline (planned):** `promised_delivery_date` — the promise stamped at digitisation and shown to the customer.
- **Actual:** `delivery_attempt_time` — the 1st delivery attempt. The 1st attempt should not land before the promise.
- **Classification:** for the order overall and for each leg, label **Early / On-Time / Late** by comparing the actual handoff to its promised handoff. (On-Time tolerance band fixed at execution time.)

---

## Legs and their boundaries

All legs anchored from `order_digitised_at`.

| Leg | Promised handoff | Actual handoff |
|---|---|---|
| Doctor | `promised_doctor_call_time` | `doctor_confirmed_at` |
| Warehouse | `promised_warehouse_processing` | `actual_warehouse_processing` |
| Dispatch | `promised_dispatch_date` | `pickup_time` |
| Delivery (logistics) | `promised_delivery_date` | `delivery_attempt_time` |

---

## Analysis steps

### 1. Top-level outcome distribution
Early / On-Time / Late distribution of final delivery (`delivery_attempt_time` vs `promised_delivery_date`). Split by **FC vs MFC** and **Hyperlocal vs Courier**. Establishes the size and shape of the problem in each segment.

### 2. Leg-level outcome distribution
For each leg (Doctor, Warehouse, Dispatch, Delivery), the Early / On-Time / Late distribution measured against that leg's own promise. Same FC/MFC × Hyperlocal/Courier splits. Shows where in the journey earliness and lateness originate.

### 3. Doctor-leg cascade
Condition on the doctor leg's outcome:
- Where the doctor leg ended **early** → what is the final order outcome (Early / On-Time / Late)? And of those orders, did the Warehouse leg also end early? Did the Delivery leg also end early?
- Repeat for where the doctor leg ended **late** (order doctor-confirmed late).

Goal: understand which downstream leg **absorbs** (soaks up) or **propagates** (passes on) the doctor leg's deviation.

### 4. Extend the cascade to the remaining legs
Apply the same conditional method anchoring on the Warehouse, Dispatch, and Delivery legs in turn. Output: a complete **absorber-vs-propagator map** across the chain — which leg consistently absorbs upstream deviation, and which passes it through.

---

## Deferred to Phase 2 (scoped by the cascade map above)

- Leg-specific mechanism deep dives: courier allocation strategy, delivery-TAT config strategy, promise padding, placement→shipping state drift.
- Promise-tightening sizing.

Phase 2 targets whichever leg the cascade map identifies as the earliness owner / primary absorber.

---

## Definition of done

- Top-level and per-leg Early / On-Time / Late distributions, split by FC/MFC × Hyperlocal/Courier.
- Cascade matrices for all four legs, with an absorber/propagator verdict per leg.
- Findings doc in `insights/` naming the Phase-2 target leg(s).
