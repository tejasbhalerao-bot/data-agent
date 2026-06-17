# Early Delivery — Insights (v1, in progress)

**Data:** `early-delivery-raw-may-2026.csv` (813,499 orders, May 2026). Day-level outcome:
`offset = date(delivery_attempt_time) − date(digitised_delivery_promise)`; ≤−1 Early, 0 On-Time, ≥+1 Late.
Segmented analysis restricted to `digitised_ts ≥ 8 May 2026` (instrumentation go-live).

---

## Verdict so far

**Early delivery is a systemic promise-over-padding problem, not a localised one. ~1 in 3 delivered
courier orders arrives ≥1 full day early (≈2× the late rate), and that earliness is uniform across
origin warehouse, courier partner, and destination city, and stable week-over-week. The doctor leg
does not cause it — the doctor leg moves in minutes; the earliness is built in days, downstream
(warehouse / dispatch / courier).**

---

## 1. Top-level outcome (Step 1)

Delivered, post-May-8 cohort = 522,708.

| Segment | n | Early | On-Time | Late |
|---|---:|---:|---:|---:|
| All delivered | 522,708 | 33.0% | 51.4% | 15.6% |
| Hyperlocal | 165,660 | 21.9% | 70.9% | 7.2% |
| Courier | 350,069 | 37.7% | 42.7% | 19.6% |
| Courier × FC | 174,231 | 43.6% | 37.7% | 18.7% |
| Courier × MFC | 175,838 | 31.8% | 47.7% | 20.5% |
| Hyperlocal × MFC | 39,215 | 13.1% | 80.7% | 6.3% |

- **Courier is the early-heavy, bimodal vertical** (high early *and* high late, lowest on-time) — padding exists but is mis-placed.
- **Hyperlocal × MFC is already tight** (81% on-time) — no headroom.

## 2. Earliness is systemic, not localised

- **Warehouse:** 21 courier warehouses; top-5 FCs = 57.6% of all early, but it tracks volume. WHs 22/38/20 (FC) run ~50% early (worst). MFC tighter.
- **Courier partner:** flat early rates (33–41%) across the big carriers; top-2 partners own 50% of early by *volume*, not rate. → earliness is a lane property, not a carrier property.
- **Destination city** (pgeocode/GeoNames district): 618 cities; top-25 = 17.8% of volume ≈ 19.8% of early. No geographic concentration.
- **Week-over-week:** top cities sit at ~40–52% early every full week (W19–W22), mild upward drift through May. Recurring, not a blip.

Triangulated conclusion: not a *who/where* problem → it's *how the promise is constructed*. Lever = promise engine / TAT config, not allocation or geography.

## 3. Doctor leg is a non-contributor (Step 2a)

Cohort: call + confirm present, post-May-8 = 576,797. Band ±1 min.

- **Doctors call early but only by a fixed buffer:** 52.5% of calls land in the *Early 10–30 min* bucket (median −13 min). DOCTOR_AND_HA: 78.9% in that bucket. The promise is stamped ~15 min ahead of the call — a quarter-hour buffer, not a day.
- **Customer wait is the only real spread, and it runs late:** confirmation median −1 min, mean +27 min (long right tail). ~22% of confirmations late; DOCTOR_AND_HA worst (33% late, two-call exposure).
- **Minutes vs days:** the doctor leg's whole range (±15 min buffer + a sub-hour-to-hours customer-wait tail) is sub-day. It cannot create day-level earliness; downstream legs must even be *absorbing* its late tail (orders confirmed hours late still arrive a day early).

## Data-quality flags

| Flag | Count | Note |
|---|---|---|
| Pre-May-8 = no digitised state | 159,676 | instrumentation go-live 8 May; segment-blind, excluded |
| `digitised_order_category` blank | 171,982 (27.5% post-May-8) | raw value = `''`. These are **instant-confirm** orders (promise = call = confirm, same minute, median 0). Not a real category — field gap. |
| Duplicate `order_id` | 15 | contradicts 1-row/order; deduped keep-first |
| Blank `digitised_delivery_partner` | 18,617 courier | 50.8% early (off-pattern) |
| Not-delivered | 131,014 | `delivery_attempt_time` null; out of delivered scope |

## Open threads / next

- **WH leg** (next): does it absorb the doctor late-tail, and where does the first *day* of earliness appear?
- Then dispatch + courier legs → full absorber/propagator map.
- Phase 2 (scoped by cascade): promise-tightening sizing on the systemic over-padding.

> Scripts in `scripts/`; regenerate `outputs/*.csv` (gitignored) by running them against the raw CSV.
