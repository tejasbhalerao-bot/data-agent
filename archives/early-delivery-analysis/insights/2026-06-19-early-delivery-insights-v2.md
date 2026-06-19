# Early Delivery — Insights v2: Warehouse Leg (Axis 1, ops accuracy)

Builds on v1 (Step 1 + doctor leg). Focus: the warehouse processing leg.

---

## Headline

**Warehouse ops mostly finishes *inside* the promised window (66% early, 33% late) — but the earliness is structural over-promise, concentrated in FC non-inventory orders.** Two distinct levers, cleanly sized.

---

## Method correction (important — earlier numbers were wrong)

First WH metric compared `wh_processing_mins` to `invoice − dr_confirm`. That **broke** for two reasons:
1. **WH 39 config defect:** `wh_processing_mins = 0` for ~46k orders (99.97% of all zero-SLA). Promise collapses to doctor time → "late" by construction. **Excluded.**
2. **Closed hours:** `processing_start_ts ≈ dr_confirm` and does NOT net out non-working hours. Orders confirmed after close show 14h "windows" that are mostly the warehouse being shut. 51% of "late" spanned an overnight close; 55% had `processing_start` outside hours.

**Corrected (Axis 1 v2) metric — working-hours-robust:**
`promised = digitised_wh_promise − digitised_dr_promise` vs `actual = invoice_create − processing_start`.
Early if promised > actual (+1 min buffer). Works because `wh_promise` is itself built as `work_start + wh_processing_mins`, rolled to the next working day — it already encodes the WH's hours/batch logic, so comparing the two wall-clock windows cancels the closed-hours confound.
Scope: digitised ≥ 8 May, `wh_processing_mins ≠ 0`, four timestamps present. Cohort = 502,774.

---

## Axis 1 corrected result

| | n | % |
|---|---:|---:|
| Early | 333,876 | 66.4% |
| On-Time | 4,001 | 0.8% |
| Late | 164,897 | 32.8% |

Breakdowns:
- **FC vs MFC:** FC 27% late, **MFC 42% late.** Genuine slow MFCs: WH 35/32/33/30 at 50–60% late.
- **Inventory @ digitisation:** in-stock 38% late vs **non-inventory only 9% late** (90.8% early) — non-inventory promises are padded (procurement budget reality beats).
- **Working hours do NOT explain warehouse-level variance** (shortest-hours WH 19 mid-pack; longest WH 20 among best).

---

## Deep dive: the "Early >4h" bucket (the most diagnostic slice)

106,920 orders = 21.3% of the WH cohort finish **>4h** inside the promised window.

**Composition (FC dominates):** 88% FC, 8% MFC; 71% non-inventory.

**FC orders within the >4h-early bucket (n=94,181), by inventory change:**

| FC change bucket | % of >4h-early bucket |
|---|---:|
| Non-Inv → Non-Inv | 49.8% |
| Non-Inv → Inv | 30.8% |
| Inv → Inv | 18.8% |
| Inv → Non-Inv | 0.5% |

→ **Started non-inventory = 80.7%; started in-stock = 19.3%.**

### Two causes

1. **Procurement padding (≈81% of the bucket).** Non-inventory promises budget sourcing time that mostly doesn't materialise (a third are in-stock by shipping). Reality beats the pad → >4h early. **The needle-mover for promise tightening.**

2. **Warehouses working after close (≈19% — the in-stock Inv→Inv slice).** In-stock orders can't run 4h early on an honest promise. Validated: early-inventory orders finish **outside working hours 52%** of the time and **after close 42%** — vs 5% for normal inventory orders (8× gap). The system thinks the WH is shut; the floor is still packing. **Config/governance fix, not padding.**

In-stock orders that stay within hours are already roughly honest (Inv→Inv leans slightly *tight* — 35% late).

---

## Open / next

- Axis 2 (customer commitment vs `actual_warehouse_processing`) — pending Tejas's signal.
- Axis 3 (doctor-leg → WH-leg cascade) — pending.
- Eng follow-ups: (a) why WH 39 `wh_processing_mins = 0`; (b) align declared WH hours with reality (after-close working); (c) tighten FC non-inventory procurement padding.

> Scripts in `scripts/` (Axis-1 v2 = `2026-06-18-...-v2.py`; deep-dives = `2026-06-19-...`). Regenerate gitignored `outputs/` by running them against the raw CSV.
