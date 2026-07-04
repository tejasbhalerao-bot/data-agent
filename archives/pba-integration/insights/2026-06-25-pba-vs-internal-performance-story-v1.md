# PBA vs Internal — Delivery Performance Review

**Date:** June 25, 2026
**Audience:** Internal stakeholders
**Data scope:** Full actuals (courier lanes where both PBA and Internal operate)

---

## The Headline

> **PBA adherence (74.1%) looks comparable to Internal (74.9%) on the surface — but that's a misleading comparison. On the same lanes where PBA actually operates, Internal runs at 80%. PBA is 5.8 percentage points behind on an apples-to-apples basis, and is also promising significantly longer delivery windows to get even that number.**

---

## 1. Overall Numbers (Full Universe)

| Metric | PBA | Internal |
|---|---|---|
| Total orders | 37,906 | 3,63,002 |
| Avg promised TAT | **2.95 days** | **1.82 days** |
| Adherence | 74.1% | 74.9% |

At first glance, adherence looks nearly identical. But two things inflate Internal's apparent advantage:
1. Internal includes a massive same-day delivery volume that PBA simply cannot handle.
2. PBA only operates on a subset of courier lanes — a harder set of routes on average.

These two factors need to be stripped out before drawing any conclusions.

---

## 2. The Real Comparison: Same Lanes, Same Partners

When we filter Internal orders to **only the lanes where PBA also operates**, the picture shifts materially:

| Metric | PBA | Internal (same lanes) |
|---|---|---|
| Total orders | 37,900 | 2,13,248 |
| Avg promised TAT | **2.95 days** | **2.43 days** |
| Adherence | **74.2%** | **80.0%** |
| Gap | — | **+5.8pp** |

**On the same set of lanes, Internal outperforms PBA by 5.8pp.** And it does so while promising faster delivery (2.43 days vs 2.95 days). PBA is not just missing more — it's also buying itself slack by promising longer windows and still underperforming.

---

## 3. Why the Overall Numbers Looked Similar: The Same-Day Effect

The full-universe numbers masked the gap because of same-day volume:

| TAT bucket | Internal | PBA |
|---|---|---|
| Same-day (Day 0) | **31.5%** of orders | 0.6% of orders |
| Day 1–3 | 53.2% | 68.8% |
| Day 4+ | 15.2% | **30.6%** |

Internal carries 1,14,435 same-day orders (31.5% of its volume) — a bucket where adherence is naturally high and where PBA is structurally absent. Strip those out and Internal's average TAT drops from 1.82 to ~2.4 days, which is exactly what the lane-level cut shows.

**The second observation is more damaging:** even excluding same-day, PBA has 30.6% of its orders at 4+ day promises vs 22.4% for Internal. PBA is systematically promising longer windows, and still missing more.

---

## 4. Courier Partner Breakdown

Where is the adherence gap coming from?

| Courier Partner | Internal Adherence | PBA Adherence | Gap | PBA Orders |
|---|---|---|---|---|
| 225 | 74.4% | 60.7% | **–13.6pp** | 3,405 |
| 685 | 51.4% | 36.7% | **–14.7pp** | 240 |
| 246 | 85.4% | 74.6% | **–10.9pp** | 5,446 |
| 247 | 86.9% | 76.1% | **–10.8pp** | 4,372 |
| 286 | 82.9% | 75.0% | **–7.9pp** | 1,482 |
| 185 | 85.2% | 79.5% | **–5.7pp** | 7,520 |
| 195 | 77.2% | 74.2% | **–3.0pp** | 15,292 |
| 686 | 85.4% | 88.2% | +2.8pp | 51 |
| 608 | 51.4% | 63.6% | +12.2pp | 11 |
| 287 | 64.2% | 97.3% | +33.1pp | 75 |

**Every major courier partner performs worse for PBA than for Internal.** There is no partner where PBA meaningfully outperforms at scale. The three standouts (686, 608, 287) all have tiny PBA volumes — not representative.

### The worst offenders:

**Partner 225** — 3,405 PBA orders, 60.7% adherence vs 74.4% for Internal. A 13.6pp gap on meaningful volume. PBA is losing roughly 1 in 2.5 orders to late delivery on this partner vs 1 in 4 for Internal.

**Partners 246 and 247** — Together 9,818 PBA orders, both showing ~10-11pp gaps. These are high-volume partners for PBA and both are underperforming at scale.

**Partner 195** — Highest PBA volume at 15,292 orders. Gap is "only" 3pp, but at this volume that translates to roughly 450+ extra failed deliveries attributable to PBA's lower performance.

---

## 5. TAT Distribution: What We're Promising

The TAT promise profile differs significantly between PBA and Internal on shared partners:

| Partner | Internal 4+ day % | PBA 4+ day % | Δ |
|---|---|---|---|
| 195 | 28.5% | 37.6% | +9.1pp |
| 225 | 43.0% | 56.1% | +13.1pp |
| 185 | 14.5% | 21.5% | +7.0pp |

PBA is consistently promising longer TATs than Internal on the same partners — and still missing at a higher rate. This suggests PBA's TAT logic is either not calibrated to actual partner performance, or partner allocations themselves are suboptimal.

---

## 6. Lane-Level Analysis: Where PBA Gets Screwed

To identify specific routes where PBA is most disadvantaged, we compare the **% of orders with 4+ day promises** at the warehouse-pincode level.

**Summary across 507 lanes (PBA ≥ 10 orders):**
- 152 lanes (30%) where PBA is promising relatively longer than Internal
- 38 lanes (7.5%) where PBA 4+ day share exceeds Internal by 20+ percentage points

### Worst warehouses (avg gap: PBA 4+ day % minus Internal 4+ day %):

| Warehouse | Avg PBA 4+ day % | Avg Internal 4+ day % | Avg Gap | Lanes affected |
|---|---|---|---|---|
| WH 23 | 24.7% | 15.2% | **+9.5pp** | 6 of 7 |
| WH 33 | 15.9% | 9.7% | **+6.2pp** | 3 of 10 |
| WH 24 | 8.7% | 2.9% | **+5.7pp** | 15 of 22 |
| WH 22 | 25.6% | 22.0% | **+3.6pp** | 17 of 41 |
| WH 32 | 28.3% | 24.9% | **+3.4pp** | 23 of 43 |

### Top 10 individual lanes where PBA is most disadvantaged:

| Warehouse | Pincode | PBA Orders | PBA 4+ day % | Internal 4+ day % | Gap |
|---|---|---|---|---|---|
| WH 22 | 281121 | 10 | 100% | 0% | **+100pp** |
| WH 22 | 797112 | 15 | 100% | 16.9% | **+83pp** |
| WH 32 | 799277 | 11 | 100% | 18.6% | **+81pp** |
| WH 31 | 193201 | 14 | 100% | 19.8% | **+80pp** |
| WH 22 | 799120 | 11 | 100% | 23.3% | **+77pp** |
| WH 39 | 845106 | 10 | 70% | 2.3% | **+68pp** |
| WH 32 | 788710 | 11 | 100% | 50.0% | **+50pp** |
| WH 19 | 204101 | 10 | 50% | 0% | **+50pp** |
| WH 20 | 321001 | 11 | 63.6% | 16.7% | **+47pp** |
| WH 29 | 274001 | 13 | 46.2% | 7.0% | **+39pp** |

On these lanes, PBA is promising 4-day+ delivery where Internal delivers in 1-2 days. These are not close calls — they represent routes where PBA's TAT logic is fundamentally misconfigured relative to the actual lane capability.

### Where PBA is relatively better:

WH 37, 35, and 31 show Internal performing worse on the 4+ day dimension (Internal 4+ day share is higher than PBA). On WH 37 specifically, Internal's 4+ day share averages 12.6pp higher than PBA's across 75 lanes. This suggests PBA's partner allocation or TAT calibration is better on WH 37 routes — worth understanding why.

---

## 7. Summary: The Core Problems

| Problem | Evidence |
|---|---|
| **PBA is 5.8pp behind Internal on adherence** | Lane-level cut: 74.2% vs 80.0% |
| **PBA promises longer TATs and still misses more** | Avg 2.95 vs 2.43 days on same lanes; 30.6% vs 22.4% at 4+ days |
| **Partner 225 is a structural failure point** | 60.7% adherence, 13.6pp below internal, 3,400+ orders |
| **Partners 246 and 247 are systematic underperformers for PBA** | ~10-11pp gap each, together 9,800+ PBA orders |
| **30% of lanes have disproportionately long PBA promises** | 152 of 507 comparable lanes |
| **WH 22, 23, 24, 32, 33 are the most affected warehouses** | Consistently high positive TAT gap vs internal |

---

## 8. What This Points To

**TAT promise calibration is wrong for PBA.** PBA is using buffers that are systematically overlong — and still not meeting them. The TAT logic for courier (PBA) needs recalibration against actual partner delivery data, not assumed TATs.

**Partner 225 needs immediate review.** At 60.7% adherence, this is the single largest drag on PBA's numbers. Either the partner TAT agreement is wrong, or there is a fulfilment/handoff issue specific to PBA orders.

**Partners 246 and 247 need tighter SLAs for PBA volume.** Both are high-volume, both show ~10pp gaps. The gap could be promise-side (PBA not setting tight enough TATs) or delivery-side (partner treating PBA orders differently).

**Lane-level routing has blind spots.** The worst individual lanes (WH22-281121, WH32-799277 etc.) are cases where PBA promises 4+ days on routes where Internal delivers in 1-2 days. The pincode-to-partner-TAT mapping used by PBA has specific pincodes that are misconfigured.

**WH 37 is a relative bright spot.** PBA outperforms Internal on 4+ day TAT share here — worth understanding what is different about routing or partner allocation on this warehouse to replicate elsewhere.

---

*Source: Actuals PBA vs Internal.xlsx — courier lane actuals*
*Analysis: June 25, 2026*
