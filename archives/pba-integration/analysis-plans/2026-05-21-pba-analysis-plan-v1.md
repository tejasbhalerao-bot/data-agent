# PBA Integration — Post-Release Analysis Plan
**Initiative:** Performance-Based Allocation (PBA) via Clickpost  
**Pilot scale:** 5% of orders (1,816 PBA orders out of 37,906 total)  
**Date:** 2026-05-21  

---

## Objective

Determine whether PBA should be scaled to 100%, tuned, or rolled back. Adherence is the primary success metric. Cost is secondary. Analysis proceeds from outcome → diagnostic → root cause.

---

## Pre-Analysis: Fallback Funnel Health

Before any comparison is made, audit what fraction of "PBA orders" actually ran on PBA logic vs fallback.

- What % of PBA-eligible orders fell back to API cache?
- What % fell back to existing internal logic (Clickpost API failure)?
- What % of Clickpost API calls returned 0 eligible couriers?

**Why first:** If a material % of the "PBA cohort" ran on fallback logic, every delta computed downstream is understated or polluted. This is a data integrity gate.

---

## Section 1: Adherence Delta — PBA vs Internal

**Core question:** Did PBA improve or worsen promise adherence?

### 1.1 Top-line adherence comparison
- Logistics promise adherence: PBA vs Internal
- Overall promise adherence (customer-facing): PBA vs Internal
- Split by: Early / On-Time / Late / Not Delivered
- Which bucket drives the gap — is PBA losing on late deliveries, or on not-delivered?

### 1.2 Adherence by courier partner
- For each courier, what is adherence under PBA vs Internal allocation?
- Which courier contributes most to the adherence gap?
- Full distribution (Early / On-Time / Late / ND) per courier under each regime

### 1.3 Granular win/loss map
- At **pincode × warehouse × courier** level: what % of combinations outperform under PBA, are equal, or outperform under Internal?
- Surface the top 10 combinations where Internal outperforms PBA most severely — these are the highest-priority lanes to diagnose

### 1.4 Adherence vs promise direction (key diagnostic)
- For combinations where Internal outperforms PBA: is PBA promise faster or slower than Internal promise for those lanes?
- Hypothesis to test: Internal outperforms PBA in lanes where PBA gave a faster (more aggressive) promise

### 1.5 Adherence at delivery level, not attempt level
- Recompute adherence using **final delivery date vs promised delivery date** (not first attempt)
- Compare attempt-level vs delivery-level delta — does the gap narrow or persist?
- Attribute adherence delta to specific journey legs: first-mile, transit, last-mile

---

## Section 2: Promise Distribution — PBA vs Internal

**Core question:** Is PBA constructing promises that are achievable?

### 2.1 Promise distribution at aggregate level
- Distribution of promise TAT in days: what % of orders fall under 1-day, 2-day, 3-day, 4-day+ for PBA vs Internal
- Is PBA skewing toward faster promises across the board, or only in specific lanes?

### 2.2 Promise movement by courier
- For each courier, what is the average promise TAT under PBA vs Internal?
- Which courier sees the largest TAT compression under PBA?
- Is the compression real (courier actually delivers faster) or optimistic?

### 2.3 Granular promise comparison
- At **warehouse × pincode × courier** level: what % of combinations have lower promise under PBA, same, or higher promise?
- Cross-reference with 1.3 — do the lanes where PBA gives faster promises also show worse adherence?

### 2.4 Higher promise → higher adherence? (most important question)
- For lanes where PBA gives a **higher** (slower) promise than Internal: what is adherence?
- Is adherence in those cases at or above the 80% threshold?
- This validates whether PBA's model is directionally correct when it is conservative

### 2.5 Actual delivery speed vs promise speed
- For cases where PBA gave a faster promise than Internal AND breached: did actual delivery also happen faster, just not fast enough?
- Measure: (Actual TAT PBA) vs (Actual TAT Internal) for same lane-courier pairs
- If actual TAT also improved under PBA, the breach reflects calibration gap, not model failure

---

## Section 3: Courier Allocation Mix

**Core question:** Is PBA's courier shift justified by performance, and does it reduce cost?

### 3.1 Mix shift analysis
- Courier allocation % under PBA vs Internal (hard allocation)
- Identify which couriers gained share and which lost share under PBA
- Is the shift driven by specific lanes or uniform across all lanes?

### 3.2 Cost impact of mix shift
- Per-shipment cost for PBA-selected couriers vs Internal-selected couriers
- Net cost delta across the PBA cohort
- **Adjusted cost:** account for adherence-driven redeliveries and RTOs — does the cost advantage survive?

### 3.3 TAT assignment differences by courier
- For each courier, is PBA assigning a materially different TAT than Internal for the same lane?
- Is PBA systematically under-estimating TAT for couriers it prefers (225, 246, 247)?
- Is PBA over-estimating TAT for couriers it de-prioritises (195), causing it to unfairly downrank them?

### 3.4 RTO rate by courier under PBA vs Internal
- Does PBA allocation result in higher RTO rate vs Internal?
- Is RTO concentrated in specific couriers that PBA has shifted volume toward?

---

## Section 4: Courier Selection Algorithm Accuracy

**Core question:** Is Clickpost's ranking signal valid?

### 4.1 Rank vs actual performance validation
- When Clickpost returns a ranked list, does rank-1 courier actually deliver faster than rank-2/3 in our observed shipment data?
- Compute: for each lane, actual delivery TAT by PBA rank position (1, 2, 3, >3)
- If rank-1 is not consistently fastest, the PBA model's ranking signal is weak

### 4.2 Tie-breaker (pricing) accuracy
- How often is pricing used as tie-breaker (2+ couriers with same TAT for a lane)?
- When pricing is used, does the selected courier outperform, match, or underperform the alternative on adherence?

### 4.3 Soft vs Hard allocation consistency (structural)
- How often does the courier selected at soft allocation differ from courier selected at hard allocation?
- When they differ, which is the promise source used for adherence measurement?
- Is the mismatch rate higher for PBA orders than non-PBA orders?
- Hypothesis: stale lane cache at soft allocation + fresh API call at hard allocation produces promise drift

### 4.4 Lane cache freshness
- For lanes where soft ≠ hard: is this concentrated in orders placed near cutoff time?
- Is the before/after cutoff designation in the cache correctly matching the customer's session time?

---

## Section 5: Lane Distribution Control

**Core question:** Is the adherence comparison fair, or are PBA lanes structurally harder?

### 5.1 Baseline adherence of PBA lanes
- For lanes where PBA operated, what is the baseline adherence in non-PBA orders?
- Are PBA lanes harder (lower baseline) than average?

### 5.2 Like-for-like comparison
- Restrict analysis to lanes common across both PBA and non-PBA orders
- Recompute adherence delta on this controlled set
- Does the gap narrow, close, or persist?

### 5.3 Lane coverage concentration
- Are specific high-volume, low-adherence lanes (remote pincodes, low courier count) over-represented in PBA?

---

## Section 6: Temporal Trend

**Core question:** Is PBA improving, stable, or degrading over time?

### 6.1 Week-on-week adherence trend for PBA orders
- Is adherence gap between PBA and Internal widening or narrowing week-on-week?
- Note: first 30 days of PBA trained on pre-PBA data. After 30 days, model trains on its own decisions — look for inflection

### 6.2 Promise calibration trend
- Is the average PBA promise TAT converging toward Internal over time, or diverging?

---

## Decision Framework (Post-Analysis)

Each finding maps to a specific intervention:

| Finding | Intervention |
|---|---|
| Gap explained by lane bias | Restrict PBA to high-adherence lanes only |
| Gap from optimistic promise construction | Apply TAT buffer before committing customer promise |
| Gap from courier mix (195 underweighted) | Cap or blacklist couriers where PBA recommendation accuracy is below threshold |
| Soft ≠ Hard mismatch is structural | Pin courier selection from soft allocation through to hard allocation |
| PBA model improving week-on-week | Hold at 5%, wait for stabilisation before scale-up decision |
| Gap persists after all controls | Escalate to Clickpost — review 30-day window config, 80th percentile calibration, sample size per lane |
| RTO rate materially higher under PBA | Immediate rollback trigger |

**Kill condition:** Define minimum adherence floor and sample size threshold before next review. Current state (-6.42pp overall promise adherence) is below acceptable range — scale-up is blocked until root cause is resolved.
