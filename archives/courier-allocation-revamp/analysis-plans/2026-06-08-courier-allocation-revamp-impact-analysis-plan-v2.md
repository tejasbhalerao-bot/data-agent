# Courier Allocation Revamp — Impact Analysis Plan
**Date:** 2026-06-08

---

## Shadow Mode Note

Existing algorithm always executes on 100% of orders. Shadow mode winner is the counterfactual — what the new system *would* have selected and what TAT it *would* have promised. Delivery outcomes during Stage 1A belong entirely to the existing algorithm. Stage 2 is when actual outcomes under the new system become measurable.

Cohort split used throughout:
- **Same-courier cohort:** Shadow Rank 1 = Existing Rank 1. Promise TAT may still differ.
- **Different-courier cohort:** Shadow Rank 1 ≠ Existing Rank 1. Both courier and promise differ.

---

## Pre-Analysis: Data Integrity Gate

Run before any comparison. Polluted instrumentation = wrong deltas.

- % orders with instrumentation rows missing for any of the 6 shadow modes
- % orders where `cascade_level_reached` is null or unexpected value
- % orders where `final_adherence_considered` is null for any courier in recommendation list
- % orders where `selected_courier_partner` is non-null on shadow rows (should always be null)
- Count of orders with mismatched `orders_per_cascade` vs raw delivery counts (from sanity checks)

---

## 1. Adherence Delta — New System vs Existing

> **Measurement:** Adherence = actual delivery date vs Final TAT promised. Run at attempt level first, then recompute at delivery level (final delivery date vs promise). Note whether gap narrows or persists.

**1.1** Top-level adherence, shadow winner vs existing winner. Split: Early / On-Time / Late / Not Delivered. Run per mode (all 6) and for the selected threshold mode only.

**1.2** Same-courier cohort: top-level adherence, Early/OT/Late/ND. Here courier selection is identical — any adherence gap is purely from promise TAT correction, not from switching.

**1.3** Same-courier cohort: is adherence movement explained by promise direction? Where same courier is selected — is shadow promise faster or slower than existing, and which direction correlates with breach?

**1.4** Different-courier cohort: top-level adherence for shadow winner vs existing winner. Use historical delivery actuals for each courier on that lane — not new delivery outcomes (those don't exist yet in Stage 1A).

**1.5** Different-courier cohort: for the existing winner, what TAT did the shadow mode assign it in its ranked list? Compare shadow's TAT for existing winner vs actual delivery time by existing winner. Tests whether the new system's score for a deprioritised courier is calibrated — independent of the selection decision.

**1.6** Apply pre/post cutoff as a dimension on 1.1–1.5 where signal exists. Do not run by default on all steps.

**1.7** Lane-level drill-down (pincode × warehouse × courier): run only where aggregate shows material signal. % where shadow outperforms / same / existing outperforms. Surface top 10 worst lanes where shadow selection would have hurt adherence.

---

## 2. Promise Distribution — New System vs Existing

**2.1** Distribution of Final TAT in days (1d / 2d / 3d / 4d+), shadow vs existing. Is the new system skewing faster or slower across the board, or only on specific lanes?

**2.2** Average Final TAT per courier, shadow vs existing. Which courier sees the largest promise correction? Is compression or extension concentrated in specific couriers?

**2.3** At warehouse × pincode × courier: % lower / same / higher promise under shadow. Cross-reference with 1.7.

**2.4** Same-courier cohort only. Compare:
- Actual TAT vs shadow promised TAT
- Actual TAT vs existing promised TAT

Which regime is better calibrated to actual delivery speed? This is the direct test of whether pooled adherence produces more accurate promises.

**2.5** Where shadow promise is longer (slower) than existing: is that lane's actual delivery performance consistent with the slower promise? I.e., was the existing system being overconfident on that lane?

---

## 3. Adherence Score Correction

**3.1** For the existing winner on each order: score correction = (shadow TAT/adherence score) − (existing TAT/adherence score). Distribution of corrections. What % of existing winners had inflated scores from thin data?

**3.2** Couriers with most systematic inflation across lanes. Which couriers were benefiting most from the 1–2 delivery 100% adherence artefact?

**3.3** Score correction magnitude by cascade level: are pincode corrections smaller than city/state corrections? Validates that pooling is adding information proportionate to the geographic jump made.

**3.4** For the different-courier cohort: what was the score gap between shadow winner and existing winner? Narrow gaps (shadow barely preferred a different courier) vs wide gaps (shadow strongly preferred) — do wide-gap switches produce better outcomes than narrow-gap switches?

---

## 4. Courier Allocation Mix

**4.1** Allocation share per courier, shadow vs existing. Which couriers gain / lose share? Lane-specific or uniform shift?

**4.2** Shadow mix HHI vs existing mix HHI. Is pooling concentrating allocation (toward fewer couriers with robust data) or diversifying it (correcting over-reliance on inflated thin-lane couriers)?

**4.3** Per courier per lane: is shadow assigning materially different TAT vs existing? Systematically under-estimating for couriers it prefers? Over-estimating for couriers it deprioritises?

**4.4** RTO rate per courier, shadow allocation vs existing allocation. Is volume shifting toward couriers with higher RTO rates?

---

## 5. Cascade Logic — Signal Quality

**5.1** Does shadow Rank 1 actually deliver faster than shadow Rank 2 / Rank 3 in historical data? Compute actual TAT by shadow rank position per lane. If Rank 1 does not outperform Rank 2, the ranking signal is noise.

**5.2** Which cascade level is driving the most switches? Break different-courier cohort by `cascade_level_reached`. Switches from pincode corrections (thin data directly fixed) vs city/state cascade (geographic pooling) tell different stories.

**5.3** Thin-lane inflation correction: for combinations where existing adherence was 100% (1–2 deliveries), what did pooling bring the score to? Distribution of pooled adherence for formerly-100% lanes. Is the correction material or trivial?

**5.4** Default fallback (80%) usage: what % of orders used default adherence? For those orders, shadow and existing scores are identical — no switch possible. This cohort is a structural blind spot of the new system.

---

## 6. Lane Distribution Control

**6.1** Baseline adherence of lanes where shadow switches vs lanes where it does not switch. Are switched lanes structurally harder (thinner data, worse historical adherence) than non-switched lanes?

**6.2** Common lanes only (lanes present in both shadow and existing cohort with comparable volume): recompute adherence delta. Does the gap narrow, close, or persist?

**6.3** High-volume low-adherence lanes: are they over-represented in the switched cohort? If yes, shadow is concentrating its intervention on the lanes that matter most — good signal.

---

## 7. Temporal Trend (Stage 2 onward)

**7.1** Week-on-week adherence gap between new system and Stage 1A baseline: widening or narrowing?

**7.2** Average promise TAT under new system: converging toward actual delivery speed or diverging?

**7.3** % Switched Orders with Worse Promise on 3-day rolling window. Rollback trigger fires at > 5%.

---

## Decision Framework

| Finding | Action |
|---|---|
| Gap explained by lane bias (section 6) | Restrict new system to lanes with >= n_threshold data before pooling |
| Promise extension is large but adherence improves | Accept — system is correcting over-confident promises |
| Switches producing worse promise at > 5% | Pause rollout. Review score gap distribution (3.4) — may need higher n_threshold |
| Rank 1 does not outperform Rank 2 in actuals (5.1) | Scoring formula bug or TAT data quality issue — investigate before expanding |
| Thin-lane correction trivial (5.3) | n_threshold too low — candidates for higher threshold in Stage 1B |
| Default fallback (80%) cohort large (5.4) | Courier data coverage problem — flag to ops before production |
| RTO materially higher in shadow-preferred couriers (4.4) | Rollback |
| Week-on-week adherence gap widening (7.1) | Hold scale at current %, investigate root cause |
| Adherence improves, TAT guardrail neutral | Expand rollout |
