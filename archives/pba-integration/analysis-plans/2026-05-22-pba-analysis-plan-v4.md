# PBA Integration — Post-Release Analysis Plan
**Date:** 2026-05-22

---

## Pre-Analysis: Data Integrity Gate

Run before any comparison. Polluted cohort = wrong deltas.

- % PBA-eligible orders fell back to API cache
- % fell back to existing logic (Clickpost API failure)
- % Clickpost calls returned 0 couriers
- Count of orders with ineligible / invalid courier partner values

---

## 1. Adherence Delta — PBA vs Internal

> **Shadow mode note:** Internal courier always executes. PBA courier is the counterfactual. Adherence for both regimes is measured against actual delivery by Internal courier — but against different promises (PBA promise vs Internal promise).

> **Measurement:** Run all steps at attempt level first, then recompute at delivery level (final delivery date vs promise). Note whether gap narrows or persists.

**1.1** Top-level adherence, PBA vs Internal. Split: Early / On-Time / Late / Not Delivered.

**1.2** Courier-level adherence, PBA vs Internal. Full Early/OT/Late/ND distribution per courier. Which courier drives the gap?

**1.3** Same-courier cohort (PBA courier = Internal courier): top-level adherence, Early/OT/Late/ND.

**1.4** Same-courier cohort: courier-level adherence, Early/OT/Late/ND.

**1.5** Same-courier cohort: is adherence movement explained by promise direction? Where same courier is selected — is PBA promise faster or slower than Internal, and which direction correlates with breach?

**1.6** Different-courier cohort (PBA courier ≠ Internal courier): for the Internal courier, what TAT did PBA assign it in its ranked list? Compare PBA's TAT for Internal courier vs actual delivery time by Internal courier. Tests whether PBA's promise calibration for deprioritised couriers is accurate — independent of selection decision.

**1.7** Apply pre/post cutoff as a dimension on steps 1.1–1.6 where signal exists. Do not run by default on all steps.

**1.8** Lane-level drill-down (pincode × warehouse × courier): run only on steps where aggregate shows material signal. % where PBA outperforms / same / Internal outperforms. Surface top 10 worst lanes.

---

## 2. Promise Distribution — PBA vs Internal

**2.1** Distribution in days (1d / 2d / 3d / 4d+), PBA vs Internal. Skewing faster across the board or in specific lanes?

**2.2** Average promise TAT per courier, PBA vs Internal. Which courier sees largest compression?

**2.3** At warehouse × pincode × courier: % lower / same / higher promise under PBA. Cross-reference with 1.8.

**2.4** Where PBA promise is higher (slower) than Internal: is adherence ≥ 80%?

**2.5** Same-courier cohort only. Compare:
- Actual TAT vs PBA promised TAT
- Actual TAT vs Internal promised TAT

Which regime is better calibrated to actual delivery speed?

---

## 3. Courier Allocation Mix

**3.1** Allocation % per courier, PBA vs Internal. Which gained / lost share? Lane-specific or uniform?

**3.2** Per-shipment cost, PBA vs Internal. Adjust for redeliveries + RTOs. Does cost advantage survive?

**3.3** Per courier per lane: is PBA assigning materially different TAT vs Internal? Systematically under-estimating for couriers it prefers? Over-estimating for couriers it deprioritises?

**3.4** RTO rate per courier, PBA vs Internal. Concentrated in couriers PBA shifted volume toward?

---

## 4. Courier Selection — Correctness & Signal Quality

**4.0 Logic correctness (run first)**
- Is rank 1 always the lowest-TAT courier for that lane?
- When TAT is tied, is pricing the tie-breaker — or something else?
- When both TAT and pricing are tied: what happens, how often?
- Are there cases where allocated courier ≠ expected top-rank courier?

**4.1** Does rank 1 actually deliver faster than rank 2 / 3 in observed data? Compute actual TAT by PBA rank position per lane.

**4.2** Pricing tie-breaker: how often used? When used, does selected courier outperform alternative on adherence?

**4.3** Soft vs Hard consistency: how often does courier differ across stages? Mismatch rate PBA vs non-PBA. Which is the promise source when they differ?

**4.4** Soft ≠ Hard: concentrated near cutoff time? Before/after cutoff designation in cache matching customer session correctly?

---

## 5. Lane Distribution Control

**5.1** Baseline adherence of PBA lanes in non-PBA orders. Structurally harder than average?

**5.2** Common lanes only: recompute adherence delta. Gap narrow / close / persist?

**5.3** High-volume, low-adherence lanes over-represented in PBA?

---

## 6. Temporal Trend

**6.1** Week-on-week adherence gap: widening or narrowing?

**6.2** Average PBA promise TAT: converging toward Internal or diverging?

---

## Decision Framework

| Finding | Action |
|---|---|
| Gap explained by lane bias | Restrict PBA to high-adherence lanes |
| Optimistic promise construction | Apply TAT buffer before committing promise |
| Courier mix driving gap | Cap couriers where PBA accuracy below threshold |
| Soft ≠ Hard mismatch structural | Pin courier from soft through to hard allocation |
| Logic correctness failure (4.0) | Bug fix before any further analysis |
| PBA improving week-on-week | Hold scale, wait for stabilisation |
| Gap persists after all controls | Escalate to Clickpost — reconfigure window / percentile / sample size |
| RTO materially higher | Rollback |
