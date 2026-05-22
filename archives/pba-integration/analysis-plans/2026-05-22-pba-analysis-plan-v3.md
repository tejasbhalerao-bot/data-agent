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

> **Segment all questions by same-courier vs different-courier cohort.** When PBA ≠ Internal courier, actual delivery runs on PBA courier — Internal adherence is a counterfactual on a courier that never fulfilled. Prioritise same-courier findings.

**1.1** Top-line: logistics + overall promise adherence, PBA vs Internal. Split: Early / On-Time / Late / Not Delivered.

**1.2** Per courier: full Early/OT/Late/ND distribution under PBA vs Internal. Which courier drives the gap?

**1.3** At pincode × warehouse × courier: % where PBA outperforms / same / Internal outperforms. Top 10 worst combinations for Internal outperforms.

**1.4** Where Internal outperforms: is PBA promise faster or slower than Internal for those lanes?

**1.5** Recompute adherence at delivery level (final delivery date vs promise), not attempt level. Does gap narrow or persist? Attribute delta to journey leg: first-mile / transit / last-mile.

---

## 2. Promise Distribution — PBA vs Internal

**2.1** Distribution in days (1d / 2d / 3d / 4d+), PBA vs Internal. Is PBA skewing faster across the board or in specific lanes?

**2.2** Average promise TAT per courier, PBA vs Internal. Which courier sees largest compression?

**2.3** At warehouse × pincode × courier: % lower / same / higher promise under PBA. Cross-reference with 1.3.

**2.4** Where PBA promise is higher (slower) than Internal: is adherence ≥ 80%?

**2.5** Same-courier cohort only. Compare:
- Actual TAT vs PBA promised TAT
- Actual TAT vs Internal promised TAT

Which regime is better calibrated to actual delivery speed?

---

## 3. Courier Allocation Mix

**3.1** Allocation % per courier, PBA vs Internal. Which gained / lost share? Is shift lane-specific or uniform?

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
