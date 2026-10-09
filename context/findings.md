---
title: Findings (what we already know)
type: other
systems: [allocation, tracking, eta, serviceability]
verticals: [all]
source: project insight docs, migrated 2026-10-09. Each entry names its source file.
updated: 2026-10-09
---

# Findings

Durable results that answer questions without a new pull (Tier 0). Every entry carries its **window** and **as-of** date. Quote them with those; offer a refresh when the metric moves with time. Full tables live in the cited source; this file holds headline numbers only.

Entry format: **ID · topic** · window · as-of · definition used (see `metrics.md`) · result · source.

## Promise accuracy (egregiously miscalibrated promises)

### F1 · Egregious rate, July 2026
- **Window:** orders placed July 2026. **As-of:** 2026-07-30. **Definition:** egregiously miscalibrated order (`metrics.md` section 1).
- 803,997 orders; 628,806 with a delivery attempt (78.2%); **96,424 egregious** = 12.0% of all orders, 15.3% of attempted. Early 67,482 (8.4% of all), late 28,942 (3.6%).
- Later requests (#62) used 628,846 as the attempted base; the 40-order difference is unreconciled.
- Source: `archives/egregiously-miscalibrated-promises/insights/2026-07-30-...-insights-v1.md` #1.

### F2 · Egregious orders by segment, July 2026
| Segment | Orders | Share of egregious | Dominant pattern |
|---|---|---|---|
| Non-SDD Non-Inventory | 29,813 | 30.9% | 87.7% WH early + dispatch early + delivery early |
| Non-SDD Inventory | 57,688 | 59.8% | WH late (78.4%), dispatch on-time (75.3%), delivery early (61%) |
| SDD Non-Inventory | 4,591 | 4.8% | 90.8% WH early + dispatch early + delivery early |
| SDD Inventory | 3,955 | 4.1% | Mode 1 (72%): late WH to late delivery. Mode 2 (23.6%): WH ready but SDD broken |

### F3 · Root causes by segment (July 2026, as of 2026-08-05)
- **Non-Inventory (both SDD and non-SDD):** the warehouse promise budgets procurement time that does not exist. Median invoice-to-WH-promise gap 32.4h (SDD: 34.8h). 96.4% of non-SDD orders have the AWB printed before the WH promise, and the courier picks up the same day as the AWB.
- **Stale transit TAT lookup:** the digitised TAT over-estimates actual transit by 2 days for 44% of Non-SDD Non-Inventory orders; the promise is often corrected at shipping with the same courier.
- **Non-SDD Inventory dispatch:** early-1d is a courier-cutoff effect (51.5% same courier, 36.6% switched courier whose dispatch promise is never recalculated). Late is driven by payment pending (37.7% of late-1d, 68.2% of late-2d; median hold 23 to 27h) and, for late 3d+, HA calls with no SLA (52 to 62%).
- **SDD Inventory:** Mode 2 orders were promised 0-day SDD but the courier takes 2 to 3 days.
- Source: insights #5 to #58.

### F4 · Impact of fixes (simulations, July 2026)
| Fix | Rescued | Scope |
|---|---|---|
| Non-Inventory WH promise (Problem 1) | 26,753 orders; -4.25pp egregious rate | 35.7% of egregious |
| Payment pending, Non-SDD Inventory (Problem 2) | 2,518 to 2,951 orders; -0.40pp | On-time dispatch 75.3% to 79.5%, late 13.5% to 8.1% |
| Transit TAT recalibration (shipping-based) | 31,269 | 54.2% of Non-SDD Inventory, 32.4% of all egregious |
| HA call SLA | 391 | 0.4% of egregious |
| SDD eligibility fix | 670 of 932 | SDD Inventory Mode 2 |
| Egregious rate after Problems 1 and 2 | About 10.65% (from 15.3%) | |
- Roadmap: problems 3 to 5 are not yet built out. Source: insights #59 to #60, `2026-08-05-q2-roadmap-v1.html`.

### F5 · Promise-aware reallocation uplift, July 2026
- Late orders 93,876 (14.93% of 628,846 attempted). Courier-adherent lates (courier hit its own TAT but missed the customer promise): 39,016 = 6.20pp ceiling. Switched to a slower courier: 12,844 = **2.04pp floor**. Same courier, pipeline slipped: 24,422 (3.88pp, upper bound).
- Remaining 54,860 lates are courier-performance failures that reallocation cannot fix.
- Source: insights #62; script `2026-09-07-aggregate-promise-aware-reallocation-impact-v1.py`.

### F6 · Promise lead time and date adherence, August 2026
- 850,115 orders. Average promise lead time **2.96 days**. **43.46%** of all orders were picked up and attempted exactly on the promised date (denominator is all orders). Source: insights #63.

### F7 · Production promise performance (window not stated)
- **As-of:** 2026-08-25. Logistics leg: 23.2% early, 54.8% on-time, 22.0% late. End-to-end ETA: 33.0% early, 51.4% on-time, 15.6% late (84.4% not late against an 80% design floor).
- The 80th-percentile design means about 20% late by construction. Quantisation to whole days, additive buffers and the TAT/Adherence division are the structural causes. Source: `adherence-vs-ontime-pct-v1.md`.

## Early delivery (May 2026 cohort)

### F8 · Warehouse leg, May 2026
- **Window:** digitised on or after 2026-05-08, `wh_processing_mins != 0`. **As-of:** 2026-06-19. **Definition:** early-delivery Axis 1 v2 (`metrics.md`, warehouse leg).
- n = 502,774: Early 66.4%, On-Time 0.8%, Late 32.8%. FC 27% late; MFC 42% late (WH 35, 32, 33, 30 at 50 to 60%).
- Non-inventory at placement: 9% late (90.8% early); in-stock: 38% late.
- 21.3% of orders (106,920) finish more than 4h early; 88% are FC and 71% non-inventory. About 81% of that bucket started non-inventory (procurement padding); about 19% is warehouses working after close.
- Source: `archives/early-delivery-analysis/insights/2026-06-19-early-delivery-insights-v2.md`.

### F9 · Base population, May 2026
- 813,499 rows; 624,288 with `digitised_ts` after 8 May 2026 (76.7%); 522,808 with a delivery attempt (64.3%). View 1 N = 515,465, View 2 N = 515,400 (98.6%). Source: `2026-07-04-base-population-filter-v1.md`.

## PBA vs Internal courier allocation

### F10 · PBA vs Internal, as of 2026-06-25
- **Definition:** adherence (PBA analysis). **Data:** actuals workbook of courier lanes where both operate (window not stated in source).
- Full universe: PBA 37,906 orders, avg promise 2.95d, adherence 74.1%; Internal 363,002 orders, 1.82d, 74.9%. The headline gap is hidden by Internal's 31.5% same-day volume.
- **Same lanes:** PBA 74.2% vs Internal 80.0% (**-5.8pp**); promise 2.95d vs 2.43d.
- Every major courier is worse under PBA: partner 225 -13.6pp (3,405 PBA orders), 246 -10.9pp, 247 -10.8pp, 195 -3.0pp (15,292 orders).
- 152 of 507 comparable lanes (30%) promise relatively longer under PBA; worst warehouses 23, 33, 24, 22, 32. WH 37 is the bright spot.
- Source: `archives/pba-integration/insights/2026-06-25-pba-vs-internal-performance-story-v1.md`.

## Serviceability instrumentation

### F11 · Instrumentation gaps, as of 2026-06-18
- Gap catalog (v1 listed 20 metrics, prioritised P0 to P3; v3 is the plain-language revision) for the Serviceability system; hypotheses until the grounding audit is run (`rules.md` G7).
- Biggest blind spots: customers blocked on non-serviceable pincodes (nothing logged) and MFC-vs-FC / courier choices made before an order exists. `is_sdd_eligible` exists as an event property but its page coverage is unconfirmed (Step 0).
- Source: `archives/instrumentation-audit/insights/2026-06-18-serviceability-instrumentation-gaps-v3.md`.

## Other projects (pointers only, no results yet)

| Project | State | Where |
|---|---|---|
| nano-fulfilment-centres | Site-selection method and map built; no numeric findings recorded | `archives/nano-fulfilment-centres/` |
| eta-at-pre-summary-xp (ETA-E2) | Experiment designed; results in the leadership brief and results sheet (not summarised here) | `archives/eta-at-pre-summary-xp/insights/eta-e2-leadership-brief.html` |
| courier-allocation-revamp | System and shadow-mode design plus data sanity-check plans; no results | `archives/courier-allocation-revamp/` |
| promise-opportunities | Data dictionary only | `archives/promise-opportunities/` |
