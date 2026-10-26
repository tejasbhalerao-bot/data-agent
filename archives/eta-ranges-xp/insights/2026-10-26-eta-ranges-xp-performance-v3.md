---
project: eta-ranges-xp
job: measure
status: saved
awaiting: []
assumptions: [primary metric is Placed to Delivered and Summary to Placed is the guardrail (the PRD is mistaken, per Tejas 2026-10-26), dashboard report filters apply the PRD cohort]
signed_off: false
as_of: 2026-10-26
---

# ETA Ranges XP (ETA-E3): did the centred ±1 day range improve Placed → Delivered?

**My reading of the flow:** The customer sees a centred ±1 day ETA range on Order Summary. The aim is a more honest promise, so more placed orders end up delivered. Mixpanel records this through `app_order_placed` and `order_delivered`, split by variant. Summary → Placed is the guardrail that shows whether the new range scares buyers off.

**Assumptions and rules applied:** Primary metric is Placed → Delivered and Summary → Placed is the guardrail. The PRD names it the other way round; Tejas says the PRD is mistaken. v1 of this note used the PRD's framing and is superseded. The overall Placed → Delivered pull (Q2) was dropped: Tejas said the dashboard cards are already built, so M1 uses the new-user and repeat-user cards.

## Answer

**Stage:** final result  **Launch date:** 2026-09-18 (data from 2026-09-19; 5% scale-up 2026-09-21)  **Compared against:** control (variant B). Holdout excluded.  **Earlier notes used:** v1 of this note (superseded)

### Headline
Scale down. The centred range did not improve Placed → Delivered: repeat users are 0.19pp lower than control and the +1pp target is ruled out. New users cannot say either way. The guardrail (Summary → Placed) stays within the -1pp limit on the point estimate, but the 95% range cannot rule out a breach (M1, M2 via S1).

### Final result
| Metric | Control | Test | Difference | 95% interval | Enough data? |
|--------|---------|------|------------|--------------|--------------|
| M1: Placed → Delivered, repeat users | 86.52% (18,078 / 20,895) | 86.32% (18,179 / 21,059) | -0.19pp (p = 0.562) | -0.85 to +0.46pp | Yes. Needs 18,288 per arm for 1pp; has 20,895 and 21,059. The +1pp target is ruled out |
| M1: Placed → Delivered, new users | 57.57% (5,492 / 9,540) | 57.44% (5,491 / 9,559) | -0.12pp (p = 0.861) | -1.53 to +1.28pp | No. Needs 38,302 per arm for 1pp; has 9,540 and 9,559. Smallest detectable lift is 2.00pp |
| M2: Summary → Placed, overall (guardrail) | 63.23% (22,436 / 35,485) | 62.65% (22,515 / 35,935) | -0.57pp (p = 0.114) | -1.28 to +0.14pp | Point estimate within the -1pp limit; the range cannot rule out a breach |
| M2: new users | 63.62% (7,029 / 11,048) | 63.52% (7,071 / 11,132) | -0.10pp (p = 0.874) | -1.37 to +1.16pp | Within limit; range cannot rule out a breach |
| M2: repeat users | 62.27% (15,907 / 25,544) | 61.53% (15,928 / 25,886) | -0.74pp (p = 0.083) | -1.58 to +0.10pp | Within limit; range cannot rule out a breach |
| M3: bounce rate, overall | 36.77% | 37.35% | +0.57pp | same as M2 overall, sign flipped | Same as M2 |

- **Overall M1:** not available. The dashboard has no overall Placed → Delivered card, and the new-user and repeat-user groups cannot be added because some users sit in both (test 1,083 extra, control 1,107 extra; S1).
- **Group sizes (M4):** control 36,384 and test 36,802 viewers; split check p = 0.122.
- **Decision: scale down.** Repeat users, the larger group, show no lift and rule out +1pp. New users are underpowered: confirming a 1pp lift there needs 38,302 per arm, about four times today's 9,540. The guardrail leans negative (every cut is below zero, overall -0.57pp), so there is a cost to keep running while the primary metric shows nothing. Do not scale up for significance.

### Why more users and exposure do not change the call
More users make the answer more precise; they do not change the true effect, which so far looks like zero or slightly negative (S1).
- **Repeat users:** the range is already -0.85 to +0.46pp and the +1pp target is ruled out. More traffic would only confirm no effect.
- **Guardrail:** every Summary → Placed cut leans negative (overall -0.57pp). More volume would most likely confirm a small drop, not remove it.
- **New users are the one case where scaling could help.** Their Placed → Delivered range is -1.53 to +1.28pp, so +1pp is not ruled out. A clear answer needs 38,302 users per arm against about 9,500 now, roughly four times the volume.
- **Why scale down anyway for new users:** their estimate is -0.12pp, nowhere near +1pp, and the guardrail leans negative on every cut while the test runs. This is a judgment call, not a statistical certainty. If new-user delivery matters most, extending the test on new users only is a reasonable bet, though I would not expect it to flip.
- **What scaling cannot fix:** the unconfirmed report filters (Today / Tomorrow ETAs saw no change and would dilute any real effect) and delivery maturity (recent orders may not be delivered yet). Checking both is cheaper than more traffic.

## Approved brief

**My reading of the flow:** as above.

**Objective:** Say whether the centred range improves Placed → Delivered, without hurting Summary → Placed, and whether to scale up or down.

**Scope:** data from 2026-09-19, read to date; app users with ETA over 1 day (report filters unconfirmed); test vs control, holdout excluded. Maturity: recent orders may not be delivered yet; both arms are hit equally, so the comparison holds. A second read leaving out the most recent days was proposed; it needs a new pull, so it is not done.

**Metrics and cuts**
- M1 (primary): Placed → Delivered, test vs control, by new users and repeat users (overall dropped, see above). Success = up by 1pp (Tejas).
- M2 (guardrail): Summary → Placed, overall and by new and repeat users. Limit: no drop worse than -1pp (Tejas).
- M3: bounce rate (100% minus Summary → Placed), supporting.
- M4: sample size for M1 against the 1pp lift, at 95% confidence and 80% power.

**How it will be calculated:** take the counts per variant from the saved Mixpanel cards, run the script (z-test, 95% interval, split check, sample size, limit checks), and write this note.

**Grain and columns:** one row per variant per metric; variant, users, conversions, rate, difference vs control in pp, 95% CI, p-value.

**What will be produced:** this note (v2) and a rebuilt page.

## Queries to run

| ID | Purpose | Serves | Latest file | Save the CSV as |
|----|---------|--------|-------------|-----------------|
| Q1 | Users per variant at each funnel step, from the saved Mixpanel cards (not SQL) | M1, M2, M3, M4 | `archives/eta-ranges-xp/queries-dump/2026-10-26-eta-ranges-xp-mixpanel-pull-query-v1.md` | `archives/eta-ranges-xp/raw-data/mixpanel-etaranges-dashboard-counts-2026-10-26.csv` (local only) |

No probe: the data is not from Redshift and there is no known figure to reconcile to. The second NU and RU Placed → Delivered cards (93033608, 93033587) would not load results through the connection and are not used.

## Scripts and outputs

| ID | Purpose | Serves | Latest file | Reads | Writes | Test | Run with |
|----|---------|--------|-------------|-------|--------|------|----------|
| S1 | Z-test, 95% interval, bounce, split check, sample size per segment, target and limit checks | M1, M2, M3, M4 | `archives/eta-ranges-xp/scripts/2026-10-26-aggregate-ab-readout-v3.py` | Q1's CSV | `archives/eta-ranges-xp/outputs/ab-readout-v3-2026-10-26.csv` (local only) | none needed | `python3 archives/eta-ranges-xp/scripts/2026-10-26-aggregate-ab-readout-v3.py` |

## Definitions and filters
- Window: 2026-09-19 to the read on 2026-10-26.
- Unit: unique users in each saved Mixpanel report. M1 denominator is users who placed an order in that variant; M2 denominator is users who viewed Summary.
- Variants: "test" = TG1 (A), "control" = CG (B) as labelled in the reports.
- Significance: two-proportion z-test, 95% interval, 80% power. Success and limit values are Tejas's.

## Caveats and confidence
- **Placed → Delivered is a user-level count, not orders delivered ÷ orders placed.** Recent orders may not be delivered yet, which lowers the levels (new users 57%, repeat users 86%). Both arms are measured the same way, so the comparison holds, but the levels do not. A run that drops the most recent days would give fairer levels; it needs a new pull.
- **Filters not verified.** The connection does not show each report's filters, so the PRD cohort (ETA over 1 day, app only) is unconfirmed. If Today / Tomorrow ETAs are included, they saw no change, and the effect on treated users could be larger in either direction.
- **No overall M1.** See above.
- **Segment counts overlap.** Read the cuts as separate checks.
- **Not covered:** the qualitative perception metric, a daily trend, and the holdout. Four dashboard cards would not load.
- **Claim strength:** a randomised test, so the difference is attributable to the display change, but no difference is statistically distinguishable from zero.

## Next check
- Pull the daily trend of Placed → Delivered by variant, leaving out the most recent days, to confirm the null and fix the maturity gap.
- Confirm the report filters in Mixpanel and re-run S1 if the cohort differs from the PRD.
- Correct the PRD: name Placed → Delivered as the primary metric and Summary → Placed as the guardrail.
