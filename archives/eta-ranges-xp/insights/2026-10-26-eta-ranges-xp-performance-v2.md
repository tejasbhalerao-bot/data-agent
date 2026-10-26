---
project: eta-ranges-xp
job: measure
status: awaiting-data
awaiting: [overall Placed to Delivered by variant (Q2)]
assumptions: [primary metric is Placed to Delivered, not Summary to Placed (the PRD is mistaken, per Tejas 2026-10-26)]
signed_off: false
as_of: 2026-10-26
---

# ETA Ranges XP (ETA-E3): did the centred ±1 day range improve Placed → Delivered?

**My reading of the flow:** The customer sees a centred ±1 day ETA range on Order Summary. The aim is a more honest promise, so more placed orders end up delivered. Mixpanel records this through `app_order_placed` and `order_delivered`, split by variant. Summary → Placed is the guardrail that shows whether the new range scares buyers off.

**Assumptions and rules applied:** Primary metric is Placed → Delivered and Summary → Placed is the guardrail. The PRD names it the other way round; Tejas says the PRD is mistaken. v1 of this note used the PRD's framing and is superseded.

## Answer
Pending. Waiting on the overall Placed → Delivered pull (Q2).

## Approved brief

**Objective:** Say whether the centred range improves Placed → Delivered, without hurting Summary → Placed, and whether to scale up or down.

**Scope:** data from 2026-09-19, read to date; app users with ETA over 1 day (report filters unconfirmed); test vs control, holdout excluded. Maturity: recent orders may not be delivered yet; both arms are hit equally, so the comparison holds, and a second read leaves out the most recent days (Tejas decides).

**Metrics and cuts**
- M1 (primary): Placed → Delivered, test vs control, by new users, repeat users and overall. Success = up by 1pp (Tejas).
- M2 (guardrail): Summary → Placed, overall and by new and repeat users. Limit: no drop worse than -1pp (Tejas).
- M3: bounce rate (100% minus Summary → Placed), supporting.
- M4: sample size for M1 against the 1pp lift, at 95% confidence and 80% power.

**How it will be calculated:** (1) pull an overall Placed → Delivered funnel by variant from Mixpanel (Q2); the new-user and repeat-user groups cannot be added because some users sit in both; (2) re-run the script with M1 as primary and M2 as the guardrail, including the sample-size check; (3) save this note as v2 and rebuild the page.

**Grain and columns (unchanged):** one row per variant per metric; variant, users, conversions, rate, difference vs control in pp, 95% CI, p-value.

**What will be produced:** this note (v2) and a rebuilt page.

## Queries to run
| ID | Purpose | Serves | Latest file | Save the CSV as |
|----|---------|--------|-------------|-----------------|
| Q1 | Saved Mixpanel reports: users per variant at each step (new and repeat users, Summary → Placed, Placed → Delivered) | M1, M2, M3 | `archives/eta-ranges-xp/queries-dump/2026-10-26-eta-ranges-xp-mixpanel-pull-query-v1.md` | `archives/eta-ranges-xp/raw-data/mixpanel-etaranges-dashboard-counts-2026-10-26.csv` (local only) |
| Q2 | Overall Placed → Delivered by variant | M1, M4 | not written yet: the variant property is unknown | pending |

## Scripts and outputs
Pending (S1 v2 will be re-run on Q1 and Q2).

## Definitions and filters
Pending.

## Caveats and confidence
Pending.

## Next check
Pending.
