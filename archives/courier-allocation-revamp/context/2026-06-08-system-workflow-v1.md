# System Workflow — Courier Allocation Revamp

Source: [PRD — Courier Allocation Revamp](https://docs.google.com/document/d/1HxILz8W8_UxLKXkaaoACFW8WPpAHTxESysn6Rjaq-Bc/edit)
Date: 2026-06-08

---

## Overview

Two independent processes make up this system:

1. **Nightly Adherence Job** — runs once per night, pools adherence scores at the right geographic cascade level, and writes results to a store that the allocation engine reads from.
2. **Order Allocation Engine** — runs at order time, reads from that store, scores couriers, and writes instrumentation. Runs for the live decision *and* for 6 parallel shadow modes simultaneously.

---

## Process 1 — Nightly Adherence Job

Runs at **3:00 AM for FCs**, **3:30 AM for MFCs**.

### Step 1 — Fetch Historical Orders

For every **WH × pincode × courier** combination:
- Pull all deliveries from the last 7 days.
- Count total orders at each geographic level: pincode, city, state, warehouse, courier.

### Step 2 — Determine Cascade Level

Read `n_threshold` from config (one of: 10, 15, 20 — determined after Stage 1B).

Check in order:

| Cascade | Condition to use this level |
|---|---|
| Pincode | Orders for WH × pincode × courier >= n_threshold |
| City | Pincode count < n_threshold AND city count >= n_threshold (WH x city x courier) |
| State | City count < n_threshold AND state count >= n_threshold (WH x state x courier) |
| Warehouse | State count < n_threshold AND WH count >= n_threshold (WH x courier) |
| Courier | WH count < n_threshold AND courier count >= n_threshold (courier level) |
| Default | Courier count < n_threshold → use 80% adherence |

**Prerequisite check:** All pincodes must resolve in `m_city_master` and `m_state_master`. Fallback to be designed if any pincode is unmapped.

### Step 3 — Compute Delivery Distribution

At the resolved cascade level, compute the count (and %) of orders in each bucket:

| Bucket | Definition |
|---|---|
| Early 4+day | Delivered >=4 days before Ideal TAT |
| Early 3day | Delivered exactly 3 days early |
| Early 2day | Delivered exactly 2 days early |
| Early 1day | Delivered exactly 1 day early |
| Orders On-Time | Delivered on Ideal TAT day |
| SLA Breach 1day | Delivered 1 day late |
| SLA Breach 2day | Delivered 2 days late |
| SLA Breach 3day | Delivered 3 days late |
| SLA Breach 4+day | Delivered >=4 days late |

### Step 4 — Apply Promise Buffer Adjustment (Pre-Computation)

Before computing adherence, for every order where a drop buffer was applied:

```
Adjusted Actual TAT = Actual TAT - Drop Buffer
```

Use Adjusted Actual TAT when classifying deliveries into the 9 buckets above.

### Step 5 — Compute Adherence (Both Variants)

Run both computations for every WH × pincode × courier × cascade:

**Computation 1 — `adherence_adjusted_80_perc_plus`**
- Sum buckets starting from Early 4+day, moving right through the table.
- Stop when cumulative % >= 80% (SLA breach buckets included if needed to reach 80%).
- The bucket where 80% is first reached determines Final TAT direction.

**Computation 2 — `base_adherence_percentage`**
- Sum buckets starting from Early 4+day, moving right through On-Time only.
- Stop at Orders On-Time regardless of whether 80% is reached.
- SLA breach buckets are never included.

### Step 6 — Fetch Ideal TAT and Calculate Final TAT / Delay Days

| Field | Source / Formula |
|---|---|
| Ideal TAT | Configured by business team; from `TAT Adherence Data` / `TAT Adherence Data MFC` |
| Supposed TAT flag | Set = true when Ideal TAT unavailable; use default of 5 days |
| Promise TAT | = Ideal TAT |
| Final TAT | Ideal TAT +/- direction determined by the bucket where adherence threshold was reached |
| Delay Days | Final TAT - Ideal TAT (negative = early, positive = late) |

**Final TAT direction logic:**
- Threshold reached inside Early buckets → Final TAT = Ideal TAT - (days early of that bucket)
- Threshold reached at On-Time → Final TAT = Ideal TAT
- Threshold reached inside Breach buckets → Final TAT = Ideal TAT + (breach days of that bucket)

**Guardrail:** Final TAT must never be < 0. Instrument every instance where this guardrail fires.

### Step 7 — Write Results to Store

Per WH × pincode × courier, write **6 rows** (2 computation variants × 3 n_threshold values):

| Shadow Mode | Computation Variant | n_threshold |
|---|---|---|
| Mode 1 | Computation 1 | 10 |
| Mode 2 | Computation 1 | 15 |
| Mode 3 | Computation 1 | 20 |
| Mode 4 | Computation 2 | 10 |
| Mode 5 | Computation 2 | 15 |
| Mode 6 | Computation 2 | 20 |

Each row stores: cascade_level_reached, distribution across all 9 buckets, adherence percentage, Ideal TAT, Final TAT, Delay Days, Supposed TAT flag.

### Job Failure Fallback

- If nightly job does not complete → system uses **previous night's pooled scores**.
- Orders placed inside the job window (before 3:00 AM FC / 3:30 AM MFC) → use previous night's scores.
- Allocation is never blocked pending a nightly run.

---

## Process 2 — Order Allocation Engine

Runs at **order time** for every order at stages: Order Placed, Order Confirmed, Picking, Invoice Generated.

### Step A — PBA Routing Decision

```
If PBA rollout % > 0:
    - Route (PBA rollout %) of orders → PBA allocation engine
    - Route remaining % → existing allocation engine (live decision)
Always (100% of orders):
    - Run existing algorithm (shadow only when PBA = 100%)
    - Run all 6 shadow modes
```

### Step B — Fetch Recommendation List

Call the recommendation API → returns eligible courier partners for this order.

### Step C — Score Each Courier

Repeat for each of the 8 runs (existing + 6 shadow + PBA instrumentation):

**1. Fetch cascade adherence from nightly job store**
- Look up this courier's WH × pincode × courier row for the relevant computation variant and n_threshold.
- Read: cascade_level_reached, adherence %, Ideal TAT, Final TAT, Delay Days, Supposed TAT flag.

**2. Apply schedule time check**
```
If order placed after warehouse cutoff time for this courier:
    schedule_time_flag = 1
Else:
    schedule_time_flag = 0
```

**3. Compute final allocation score**
```
Final score = (Final TAT / Adherence) + schedule_time_flag + Pickup Buffer + Drop Buffer
```

**4. Rank all eligible couriers ascending by Final score**
- Lowest score = highest priority = Rank 1.

### Step D — Courier Selection

- **Live allocation:** Rank 1 courier is selected and committed to the order.
- **Shadow modes:** Rankings computed and logged; no courier switched.

### Step E — Write Instrumentation Row

One row per order per run (up to 8 rows per order per allocation trigger):

| Field | Description |
|---|---|
| order_id | Order identifier |
| warehouse_id | Fulfilling warehouse |
| pincode | Customer delivery pincode |
| city | Resolved from m_city_master |
| state | Resolved from m_state_master |
| order_stage | Order Placed / Confirmed / Picking / Invoice Generated |
| computation_variant | Computation 1 or Computation 2 |
| n_threshold | 10, 15, or 20 |
| recommendation_metadata | Full array from recommendation API |
| cascade_level_reached | pincode / city / state / warehouse / courier / default |
| orders_per_cascade | {pincode: x, city: y, state: z, warehouse: a, courier: b, default: c} |
| adherence_metadata | Per-courier breakdown across all 9 buckets |
| final_adherence_considered | {courier_A: pct, courier_B: pct, ...} |
| ideal_tat | Per courier |
| final_tat | Per courier |
| delay_days | Per courier |
| supposed_tat_flag | Per courier (true if default 5-day TAT used) |
| tat_adherence_score | Per courier (before buffers) |
| schedule_time_flag | Per courier |
| drop_buffer | Per courier |
| pickup_buffer | Per courier |
| tat_adherence_score_with_buffer | Per courier (final score) |
| rank_in_allocation | Per courier |
| selected_courier_partner | Winner courier id (live); null for shadow runs |

---

## Rollout Stages

### Stage 1A — Shadow Experiment (14 nights)

- All 6 shadow modes run on 100% of orders. No live allocation changed.
- Nightly job writes 6 rows per WH × pincode × courier (thresholds 10/15/20 × 2 variants).
- Validation:
  - Pooled scores for lanes >= 20 deliveries match raw scores exactly (zero regression).
  - >= 95% of orders have scores before 45-min job window on >= 12 of 14 nights.
  - Instrumentation write success >= 99.9%.
  - % Active Couriers with Recent National Data baselined.

### Stage 1B — Threshold Selection

- Analyse 14-day shadow data. Compare 3 thresholds on: % Orders Switching Courier, Avg Adherence Score Correction, % Switched Orders with Worse Promise.
- Decision rule: lowest % Switched Orders with Worse Promise wins. Tie within 1pp → prefer lower threshold.
- Exit: selected threshold's Worse Promise % < 5%.

### Stage 2 — Live Rollout (graduated)

5% (2 days) → 25% (3 days) → 50% (3 days) → 100% (7 days).

Rollback if:
- % Switched Orders with Worse Promise > 5% on any 3-day rolling window.
- Net promise degrades by > 0.1h vs Stage 1A baseline.

Exit: all steps complete without rollback firing. Worst Promise % < 3% on any single day. Switching within ±5pp of shadow baseline.

### Stage 3 — Full Production (steady state)

- Shadow instrumentation retired (threshold_variant = NULL).
- Alerts active: nightly job SLA (FC + MFC), % Active Couriers with Recent National Data (< 80% = flag), % Evaluations Falling to Default (> 5% = flag).

---

## Metrics

| Type | Metric |
|---|---|
| Success | Adherence % |
| Guardrail | Logistics TAT |
| Guardrail | Courier Allocation Mix |
