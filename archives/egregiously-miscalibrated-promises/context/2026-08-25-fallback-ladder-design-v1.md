# Fallback Ladder Design — Promise Accuracy

> Context document. Sources: shared conversation (claude.ai/share/48e1bd94-b66a-45b5-b9f0-f6cc75355f67),
> fallback-design.html (Downloads/Allocation Logic Changes/Fallback/), and simulation results
> (Google Sheets: 1Btw2QXC_uqpqJ8hq7qs5YU2eU9NqD_PwWFQlMAVbE1w).
> Last updated: 2026-08-25

---

## Overview

The fallback ladder is a replacement for the existing courier allocation + promise system, which is
a padding engine rather than a prediction engine. The current system iterates late-days until ≥80%
adherence is met, producing promises at the 80th percentile — structurally guaranteeing ~20% lateness
and ~33% early delivery. The fallback ladder replaces this with an on-time%-maximising selection
over a learned option table, with a hard late cap and a configurable day price.

The design has two phases: a **nightly job** (Steps 1–7) and an **order-time engine** (Steps 8–14).

---

## The 14-Step System

### Phase 1 — Nightly, per warehouse × pincode × courier

**Step 1 — Collect orders.**
Pull the last 7 days of delivered orders for this warehouse × pincode × courier.
If fewer than 30 orders, widen via the fallback ladder (see Geography section below).

**Step 2 — Compute true speed.**
`true_speed = delivery_attempt_date − pickup_date − buffer_applied`
Strips padding from historical actuals before learning. Buffer is re-added at scoring time (Step 9).

**Step 3 — Tally days.**
Count orders landing on day 1, day 2, day 3, etc.

**Step 4 — Build the option table.**
For every candidate promise day, compute:
- Early% — orders arriving before that day
- On-Time% — orders arriving exactly on that day
- Late% — orders arriving after that day

**Step 5 — Delete unsafe rows.**
Remove any promise day where Late% > 20%.

**Step 6 — Pick the best surviving row.**
`score = On-Time% − (15 × promise_days)`
Keep the row with the highest score. The "15" is the **day price** dial — one extra promised day
must buy more than 15 on-time points to be worth it.

**Step 7 — Save.**
Store for this lane: `promise_days`, `on_time_pct`, `late_pct`.

---

### Phase 2 — Order time, per incoming order

**Step 8 — Compute dispatch lag per courier.**
Has this courier's pickup slot already passed today? If yes → 1 extra day; if no → 0 extra days.

**Step 9 — Build the shortlist.**
For every courier serving this pincode:
`total_days = dispatch_lag + stored_promise_days + buffer (rain / holiday / etc.)`
Pull stored `on_time_pct` from the nightly table.

**Step 10 — Score each courier.**
`score = on_time_pct − (15 × total_days)`

**Step 11 — Highest score wins.**
Ties broken randomly — keeps orders flowing to both couriers so their tables stay fresh.

**Step 12 — Fallback if no courier is available.**
Pick whichever has the lowest `late_pct`. Flag the lane for review.

**Step 13 — Lock it in.**
Commit courier + date together. Do not re-pick at shipping unless order contents change,
dispatch slips, or no courier can hit date D. Reselection must re-run Steps 9–11 and update
the customer's date — it is not a silent background swap.

**Step 14 — Log everything.**
Record all couriers considered, their scores, the winner, and what actually happened.
This is the training data for tuning the day price dial.

---

## The Two Dials

| Dial | Starting value | What it controls |
|------|---------------|-----------------|
| Late cap | 20% | Hard floor on promise safety — no row with Late% > this survives Step 5 |
| Day price | 15 on-time points | How much on-time% a longer promise must buy to be preferred over a shorter one |

The TAT/Adherence formula currently in production secretly sets day price at ~42pp on 1–2 day lanes,
~28pp on 3-day lanes, ~17pp on 5-day lanes — with no one having chosen those numbers. The new
system makes it a single explicit dial.

---

## Time Fallback Rules

**Use multiples of 7 only: 7 → 14 → 21 → 28 days.**
Delivery speed has strong day-of-week structure. A 10- or 20-day window over-weights whichever
weekdays appear more often. Multiples of 7 hold weekday composition constant.

**Stop when the sample floor is cleared, not at a fixed count.**
If two couriers are 40 points apart, 6 orders is enough to act. Widening further only adds stale data.

**Cap at 28 days.** Beyond that you cross month boundaries, season changes, and courier network reshuffles.

**One-off calibration check:** compute answers at 7d and 28d on lanes that already have thick data.
If results are systematically different, performance drifts within a month — cap at 14d.

---

## Geography Fallback Rules

**Always exhaust time before touching geography.**
Widening time keeps the physical route identical (same lane, same delivery hub, same last-mile rider).
Widening geography changes the route itself.

**The warehouse never drops from the key.** It's half the route. Falling back to "this pincode
across all warehouses" would mix a 50km journey with a 1,200km one.

**Ordered ladder:**

| Rung | Level | Notes |
|------|-------|-------|
| 1 | Warehouse × pincode | The real lane |
| 2 | Warehouse × pincode cluster | Best fallback — same route, same delivery hub |
| 3 | Warehouse × distance band + zone tier | Distance drives transit days, not admin names |
| 4 | Warehouse × city | Fine for small cities; breaks badly for Mumbai / Bengaluru |
| 5 | Warehouse (all destinations) | Courier's general performance from this origin — blunt but honest |
| — | State | **Skip.** Maharashtra holds Mumbai and Gadchiroli. Averaging is meaningless. |
| — | Country | **Skip.** |

**When borrowing from a higher rung, borrow the gap, not the absolute.**
Don't take the city's transit time and apply it directly to pincode X (which may be far from the centre).
Do take that Courier A runs 15pp more concentrated than Courier B — that relative signal survives
geography widening far better than absolute speed does.

---

## T1 vs T2 — The Two Implementations Tested

Two implementations of the geographic fallback were simulated across June (discovery) and validated
against real July orders. The simulation used adherence% as the metric (matching the existing TAT
system) and a sample floor of 20 orders per cell.

**T1 — Geocoded radius bands**
Geography levels: own pincode (0km), 10km, 20km, 30km, 40km radius from the lane's pincode.
Uses `pgeocode` for real coordinates — no shared-prefix or admin-boundary proxies.
Confirmed finding: 5km added in the original design contributed zero real pincodes for the two
worked lanes; expanded to 10/20/30/40km bands for the platform run.

**T2 — Admin-boundary cascade**
Geography levels: own pincode → pincode prefix → city → district.
Same time windows (7/14/21/28d) and sample floor.

### Platform simulation results (44,907+ lanes, June → July)

**Top-level summary (resolved orders, adherence, deviation):**

| Technique | Floor | Resolved | Never resolved | Exp. Adherence | Act. Adherence | Deviation |
|-----------|-------|----------|---------------|----------------|----------------|-----------|
| T1 | 10 | 489,679 | 1.96% | 92.63% | 86.71% | −5.92pp |
| T1 | 15 | 485,327 | 2.83% | 92.29% | 87.09% | −5.21pp |
| T1 | 20 | 481,061 | 3.68% | 92.05% | 87.27% | −4.78pp |
| T2 | 10 | 492,741 | 1.34% | 91.74% | 86.76% | −4.98pp |
| T2 | 15 | 489,896 | 1.91% | 91.45% | 87.09% | −4.36pp |
| T2 | 20 | 486,959 | 2.50% | 91.25% | 87.24% | −4.02pp |

**Baseline (existing system):** 57,438 orders defaulted (11.5%), expected adherence 93.9%,
actual adherence **84.02%**, deviation **−9.87pp**.

Both T1 and T2 dramatically improve on baseline. T2 wins on all metrics at every floor:
smaller deviation, more orders resolved, and better-calibrated expectations (lower exp. adherence
means it promises less conservatively).

### Volume breakdown — where orders resolve

**T1 (floor 10):** 40.6% resolve at own pincode / 7d alone. 10km adds 12.3%, 20km adds 2.8%.
Wider bands (30km, 40km) add <1% each but carry large deviations (−10.8pp and −9.6pp at 7d).

**T2 (floor 10):** 40.6% resolve at own pincode / 7d (identical to T1's own-pincode). The prefix
rung alone adds 24.9% at 7d — by far the dominant fallback contributor. City and district contribute
<0.1% combined.

### Why T2 outperforms T1 despite the design favouring distance

The conversation that designed this system explicitly placed distance band above city as a fallback
rung, on the argument that distance is what actually drives transit time. In practice T1's 20–40km
bands pull in lanes that are geographically close but route through different hubs and behave
differently — deviation balloons to −10pp+ at those rungs. The prefix cluster in T2 is
unexpectedly homogeneous: orders within the same pincode prefix turn out to share similar
transit characteristics, making prefix a good enough proxy without the instability of wider km
bands.

### Cell-level deviation pattern (T1)

| Geography | 7d deviation | 14d deviation | 21d deviation | 28d deviation |
|-----------|-------------|--------------|--------------|--------------|
| 0km (own) | −6.09pp | −5.22pp | −4.70pp | −4.53pp |
| 10km | −7.01pp | −5.30pp | −4.71pp | −3.87pp |
| 20km | −9.46pp | −5.31pp | −4.69pp | −5.06pp |
| 30km | −12.05pp | −6.52pp | −6.39pp | −5.17pp |
| 40km | −13.78pp | −10.01pp | −4.62pp | −5.97pp |

Wider geography → larger deviation. 7d/0km is the anchor; everything else degrades as the
fallback pool becomes less homogeneous.

---

## Promise Day Distribution Shift

Comparing the new configs against the existing baseline (promise day = 0 means same-day):

| Promise day | Baseline | T1/floor20 | T2/floor20 | Delta T2 vs baseline |
|------------|---------|-----------|-----------|---------------------|
| 1 | 16.63% | 15.91% | 15.45% | −1.18pp |
| 2 | 35.78% | 36.47% | 36.03% | +0.25pp |
| 3 | 33.72% | 29.14% | 29.96% | −3.76pp |
| 4 | 8.44% | 11.70% | 11.93% | +3.49pp |
| 5+ | ~5.4% | ~6.3% | ~6.6% | +~1.2pp |

The new system shifts volume out of day-3 promises (over-promised in baseline) and redistributes
to days 2 and 4 — tighter calibration. Day-3 is the baseline's biggest bucket and it shrinks by
~4pp under both techniques.

---

## Key Design Decisions (settled)

- **On-time% replaces adherence** in the selection score. Adherence (early + on-time) lets a
  courier score high by being early, which is a miss not a success. Using on-time% only removes
  that distortion.
- **Time before geography, always.** Time widening is cheap (same route, older data). Geography
  widening is expensive (different lane, different characteristics).
- **State and country rungs: explicitly rejected.**
- **Promise freezes once shown to the customer.** Subsequent re-runs ask "which courier can hit
  date D?" not "what's the best date now?". Silent reselection at shipping breaks the promise
  contract.
- **Warehouse never drops from the key.**
- **Multiples of 7 for time windows** — weekday bias otherwise.
- **No minimum margin to beat a narrower cell** at this stage (promise accuracy calibration only).
  To revisit once fallback feeds something customer-facing.

---

## Open Questions

1. **What to do when all 12+ cells are exhausted** and still no floor is cleared. Original design:
   pick on cost/serviceability, promise from pooled data. Not yet confirmed for this specific build.
2. **Validate accuracy against the triggering pincode only, or the full geography zone** the
   history was pooled from? Worked example 2 (Bluedart, pincode 454665) tested only the triggering
   pincode.
3. **Whether one platform-wide sequence is right**, or whether it should split by lane density /
   region. Both worked examples were rural; the pattern may differ for dense urban lanes.
4. **Day price reintroduction for courier allocation.** Section 09 of the fallback-design.html
   showed Group 2 (courier changes, promise also changes) is a net −1.6pp and is 2× larger than
   Group 1 (courier changes only, +4.2pp). Day price is needed before allocation goes further.
5. **Whether the recency score** (1 − 0.05 × rung_position) is the right penalty for deep
   fallback in courier allocation scoring.
6. **No-margin winning rule** explicitly flagged to revisit the moment this feeds anything
   customer-facing.

---

## Courier Allocation Simulation (Section 09 of fallback-design.html)

Run after promise accuracy: instead of assuming the historically-assigned courier, every courier
active in a lane's warehouse competes through the same ladder. Lane = warehouse × pincode (courier
is now an output, not part of the key).

**Selection rule:** `adjusted_ratio = (TAT ÷ Adherence) ÷ recency_score`
where `recency_score = 1 − 0.05 × (rung_position − 1)`.
Tie-break: higher early% first, then Delhivery → XpressBees → Bluedart.

**Platform results (T1/T2 at floor 20):**

| Config | Existing Adherence | New Adherence | Lift |
|--------|--------------------|---------------|------|
| T1 / floor 20 | 92.05% | 92.13% | +0.08pp |
| T2 / floor 20 | 91.25% | 91.42% | +0.16pp |

**Group-level breakdown (T1, floor 20):**

| Group | Orders | Existing Adherence | New Adherence | Lift |
|-------|--------|-------------------|---------------|------|
| 1 — courier changes, promise same | 51,908 | 89.7% | 93.9% | **+4.2pp** |
| 2 — courier changes, promise also changes | 114,604 | 91.9% | 90.3% | **−1.6pp** |
| 3 — nothing changes | 314,549 | 92.6% | 92.6% | 0.0pp |

Group 2 is 2× larger than Group 1 and is net negative, cancelling the clean +4.2pp gain.
This is the exact failure mode day price exists to prevent. **Day price must come back in
before allocation goes further.**
