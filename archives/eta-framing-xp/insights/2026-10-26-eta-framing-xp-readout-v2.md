---
project: eta-framing-xp
job: measure
status: saved
awaiting: []
assumptions: [counts taken from Mixpanel dashboard 11538578 (data from 2026-09-19, end date not stated), fulfilment guardrail not checked]
signed_off: true
as_of: 2026-10-26
---

# Did relative-days ETA framing (ETA-F1) lift Summary to Order Placed conversion, and should it scale?

**My reading of the flow:** Test users see "Delivery in X-Y days" on Order Summary, control sees absolute dates; Mixpanel records order_summary_viewed then app_order_placed by variant. Rests on the PRD and the ETA Framing XP dashboard only.

**Assumptions and rules applied:** counts read from the dashboard, no new queries; fulfilment guardrail (M3) not checked.

## Answer
**Do not scale up. Stop the test and keep absolute dates.** (S1 output)
- M1: test 63.41% vs control 63.76%; difference -0.35pp, 95% range -1.05 to +0.35pp, p = 0.33. The PRD's +1pp is outside the range.
- M2: bounce 36.59% test vs 36.24% control.
- M4: sample (36,353 test, 35,809 control) matches the ~36,300 per arm needed for 1pp; detectable lift 1.01pp, so the answer for 1pp is conclusive. Group-size check on unique Summary users (37,204 test vs 36,659 control): p = 0.045, borderline; confirm the Firebase split with engineering.
- Cuts: new users -0.09pp (p 0.886, too few to read); returning users -0.53pp (p 0.214).
- Next: turn ETA-F1 off; pull fulfilment rate by variant; if working on ETA further, try range width or ETA timing rather than framing.
Published summary: https://claude.ai/artifact/Rczh4Nhm9uAkgVqiVAp55j

## Approved brief
Approved by Tejas 2026-10-26: grain one row per variant per day; columns date, variant, user_type, summary_users, order_users (not used: the dashboard gives period totals, not daily rows).
- M1 Summary to Order Placed conversion, test vs control, overall; cuts: new vs returning (pre/post ramp not possible from the dashboard).
- M2 Summary bounce rate.
- M3 Fulfilment rate: not run.
- M4 Group-size check, lift with 95% interval, sample vs 1pp MDE.

## Queries to run
None. Counts were read from Mixpanel dashboard "ETA Framing XP" (reports 92913475, 92913492, 92913512, 93208927) and saved to `raw-data/dashboard-funnels.csv` (local only).

## Scripts and outputs
| ID | Purpose | Serves | Latest file | Reads | Writes | Test | Run with |
|----|---------|--------|-------------|-------|--------|------|----------|
| S1 | Conversion, bounce, difference with 95% range, p-value, group-size check | M1, M2, M4 | `archives/eta-framing-xp/scripts/2026-10-26-aggregate-eta-f1-significance-v1.py` | `raw-data/dashboard-funnels.csv` | `outputs/eta-f1-significance.csv` | none needed | `python3 archives/eta-framing-xp/scripts/2026-10-26-aggregate-eta-f1-significance-v1.py` |

## Definitions and filters
Conversion = users placing an order / users landing on Summary (PRD). Z-test on two proportions, 95% range unpooled, 80% power. Dashboard window: from 19 Sep (launch mid-day 18 Sep), 5% per arm from 21 Sep.

## Caveats and confidence
Dashboard end date not stated. New and returning counts do not sum to the overall count (separate cohorts per card). Two cards would not load and were not used. Ramp effect not separated. Group split borderline (p 0.045).

## Next check
Fulfilment rate by variant (needs Redshift variant mapping). Confirm Firebase split.

## Should we raise exposure to get significance?
No, not unless a smaller lift is worth having.
- More users narrow the range around the true effect; they do not push a null result to significance. Our best guess is -0.35pp, so there is no hidden gain to find.
- The test was sized for 1pp and had enough users (S1). The range tops out at +0.35pp, so 1pp is very unlikely, and more users cannot revive it.
- The one fair reason to extend: a lift of 0.3 to 0.5pp would still be worth shipping at current order volume. Detecting 0.5pp needs about 4x the users; 0.35pp about 8x. That is a new test with a target and stop date set up front.
- Do not keep running until the result crosses 95%: stopping at the first crossing gives false wins, and more customers sit on a variant that looks neutral to slightly worse.
- Sample sizes above follow from sample size scaling with 1 / (lift)^2, from S1's 1pp figure; not separately calculated.
