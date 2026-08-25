# Sample Floor and Exploration Slice

**Project:** Egregiously Miscalibrated Promises
**Date:** 2026-08-25

---

## Why sample size determines minimum detectable gap

The number of orders needed to reliably detect a gap between two couriers depends on how large that gap is. Smaller gaps require larger samples before the signal clears the noise floor of weekly order volume variation.

### Gap-dependent sample size requirements

| Gap between best and second courier (on-time pp) | Orders needed |
|--------------------------------------------------|---------------|
| 40 points | ~6 |
| 20 points | ~25 |
| 10 points | ~100 |
| 5 points | ~400 |

**Absolute floor:** approximately **25 orders**, regardless of gap size. Below this you cannot even see what the gap is — the estimate of on-time% has too much variance to be meaningful.

---

## Rolling window instability

With 30 orders on a lane, one order = **3.3 percentage points** of on-time%. Normal weekly variation of 2–3 orders produces **7–10 points of score movement**. This is large enough to flip a 2-point gap between couriers every night without any real change in courier performance.

The implication: lanes with fewer than ~100 orders should not be treated as having stable courier rankings. Any gap under 10 points on such a lane is within the noise band.

---

## PRD n_threshold

The PRD currently sets `n_threshold = 10`. This should be raised to **30–50**.

**Reason:** mode estimation requires enough orders to separate adjacent integer delivery-day buckets. With only 10 orders, the mode is often a tie across multiple days, or the most-common bucket is just the only one with more than one observation. A floor of 30–50 gives the mode estimate enough resolution to be meaningful.

---

## Exploration slice

**2–5% of orders per lane are permanently reserved for non-winner couriers.**

This is not a per-experiment allocation — it is a standing reservation that persists indefinitely on every active lane.

**Rationale:** Without the exploration slice, the winning courier accumulates all the order volume and thus all the data. The losing courier's option table goes stale. Future comparisons become unreliable because one courier has a fresh, high-volume estimate and the other has an outdated, low-volume estimate. The exploration slice keeps both tables fresh enough to make comparisons meaningful.

The 2–5% range is a tradeoff: too small and the non-winner's table still goes stale on low-volume lanes; too large and the business is intentionally sending meaningful volume to a courier it believes is worse.

---

## Open questions (unresolved)

1. **Geographic pooling:** Are distributions genuinely concentrated at lane level, or are they being averaged into flatness by geographic pooling? If lanes are pooled across broad geographies (e.g. all of Maharashtra), the mode and on-time% estimates reflect a blended population, not the actual lane behaviour. This could make couriers look more similar than they are.

2. **Transit vs consignee-side lateness:** What share of first-attempt lateness is transit-side (courier fails to deliver within TAT) versus consignee-side (courier arrives but consignee is unavailable)? If consignee-side failure is a large share of late orders, courier selection cannot fix it — the signal is contaminated and the model will incorrectly penalise couriers for lateness they did not cause.
