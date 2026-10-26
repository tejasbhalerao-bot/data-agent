---
project: eta-ranges-xp
job: measure
status: saved
awaiting: []
assumptions: [dashboard reports apply the PRD cohort (ETA > 1 day, app, logged in), conversion window as saved in each report]
signed_off: false
as_of: 2026-10-26
---

# ETA Ranges XP (ETA-E3): did the ±1 day centred range lift Summary → Order Placed?

**My reading of the flow:** On the Order Summary screen the customer sees an ETA. Control sees the current end-anchored range; test sees a range centred on the calculated date, ±1 day. Mixpanel records it through `order_summary_viewed`, `app_order_placed` and `order_delivered`, split by variant. No Redshift tables are used.

**Assumptions and rules applied:** none from `rules.md` (empty). Counts are Mixpanel unique users from the dashboard's saved reports.

## Answer

**Stage:** final result  **Launch date:** 2026-09-18 (data from 2026-09-19; 5% scale-up 2026-09-21)  **Compared against:** control (variant B). Holdout excluded.  **Earlier notes used:** none

### Headline
Scale down. The centred range did not lift conversion: test is 0.57pp below control (95% interval -1.28 to +0.14pp, p = 0.114). The +1pp the PRD hoped for is outside the interval, and the test already has the sample the PRD planned for, so scaling up to chase significance would only confirm a null or slightly negative result (M1, S1).

### Final result
| Metric | Control | Test | Difference | 95% interval | Enough data? |
|--------|---------|------|------------|--------------|--------------|
| M1: Summary → Order Placed, overall | 63.23% (22,436 / 35,485) | 62.65% (22,515 / 35,935) | -0.57pp | -1.28 to +0.14pp (p = 0.114) | Yes for the planned 1pp (36,456 per arm needed, 35,485 and 35,935 seen) |
| M2: new users (NU) | 63.62% (7,029 / 11,048) | 63.52% (7,071 / 11,132) | -0.10pp | -1.37 to +1.16pp (p = 0.874) | Cannot rule out ±1pp |
| M2: repeat users (RU) | 62.27% (15,907 / 25,544) | 61.53% (15,928 / 25,886) | -0.74pp | -1.58 to +0.10pp (p = 0.083) | Directional |
| M3: bounce rate, overall | 36.77% | 37.35% | +0.57pp | same interval as M1, sign flipped | Same as M1 |
| M4: Placed → Delivered, NU (guardrail proxy) | 57.57% (5,492 / 9,540) | 57.44% (5,491 / 9,559) | -0.12pp | -1.53 to +1.28pp (p = 0.861) | No difference seen |
| M4: Placed → Delivered, RU | 86.52% (18,078 / 20,895) | 86.32% (18,179 / 21,059) | -0.19pp | -0.85 to +0.46pp (p = 0.562) | No difference seen |

M3 figures are the `bounce_pct` column of the S1 output.

- **Group sizes (M5):** control 36,384 and test 36,802 viewers; split check p = 0.122, so assignment looks fine. The smallest lift this sample could detect at 80% power is 1.01pp, about the planned 1pp. Detecting the observed -0.57pp would need about 112,206 users per arm, 3.2 times the current size.
- **Cuts (directional):** both segments point the same way, a small negative. The repeat-user drop (-0.74pp, p = 0.083) is larger and closer to significant than the new-user result (-0.10pp). Segment splits were not planned, so treat them as directional.
- **Side effects:** no sign of change in placed-to-delivered for either segment. Not a full fulfilment-rate check (see caveats).
- **Decision: kill** the centred-range variant as built. Do not scale to 5% → 10% or more for significance. The point estimate is negative, and even the optimistic end of the interval (+0.14pp) is 14% of the target lift (S1).

## Approved brief

**My reading of the flow:** On the Order Summary screen the customer sees an ETA. Control sees the current end-anchored range; test sees a range centred on the calculated date, ±1 day. Mixpanel records it through `order_summary_viewed`, `app_order_placed` and `order_delivered`, split by variant.

**Objective:** Say whether the centred ±1 day range lifts Summary → Order Placed conversion, and whether to scale up for significance or scale down.

**Scope:** window 19 Sep onward (launch 18 Sep mid-day; 5% scale-up 21 Sep), full window to date. Cohort: app users with ETA > 1 day, as the PRD says (filters on the saved Mixpanel reports not visible, to be confirmed). Comparison: test (variant A) vs control (variant B); holdout excluded. Cuts: overall, new users (NU), repeat users (RU).

**Metrics and cuts**
- M1: Summary → Order Placed conversion, test vs control, overall (success metric)
- M2: M1 by NU and RU
- M3: Summary bounce rate (100% minus M1)
- M4: Order Placed → Delivered by NU and RU (proxy for the fulfilment-rate guardrail)
- M5: Sample-size check: users per arm needed for 1pp at 95% confidence and 80% power, against what we have

**Metric definitions:** conversion = unique users who placed an order ÷ unique users who viewed Summary, within the funnel window saved in each Mixpanel report. Mixpanel counts are used as they are; Redshift is not queried.

**How it will be calculated:** (1) take the counts per variant from Mixpanel; (2) a script runs the two-proportion z-test, the difference in pp with its 95% interval, and the split check; (3) the same script runs the NU and RU cuts and the guardrail; (4) the same script does the sample-size check; (5) every number in this note comes from that script.

**What will be produced:** this note.

**Grain and columns (decided by Tejas):** one row per variant per metric; columns: variant, users, conversions, rate, difference vs control in pp, 95% CI, p-value.

## Queries to run

| ID | Purpose | Serves | Latest file | Save the CSV as |
|----|---------|--------|-------------|-----------------|
| Q1 | Users per variant at each funnel step, from the saved Mixpanel reports (not SQL) | M1, M2, M3, M4, M5 | `archives/eta-ranges-xp/queries-dump/2026-10-26-eta-ranges-xp-mixpanel-pull-query-v1.md` | `archives/eta-ranges-xp/raw-data/mixpanel-etaranges-dashboard-counts-2026-10-26.csv` (local only) |

No probe: the data is not from Redshift and there is no known figure to reconcile to.

## Scripts and outputs

| ID | Purpose | Serves | Latest file | Reads | Writes | Test | Run with |
|----|---------|--------|-------------|-------|--------|------|----------|
| S1 | Z-test, 95% interval, split check and sample size per variant | M1, M2, M3, M4, M5 | `archives/eta-ranges-xp/scripts/2026-10-26-aggregate-ab-readout-v2.py` | Q1's CSV | `archives/eta-ranges-xp/outputs/ab-readout-2026-10-26.csv` (local only) | none needed | `python3 archives/eta-ranges-xp/scripts/2026-10-26-aggregate-ab-readout-v2.py` |

## Definitions and filters
- Window: 2026-09-19 to the read on 2026-10-26 (the dashboard filter "since 19 Sep").
- Unit: unique users in each Mixpanel report; denominator for M1 is users who viewed Summary in that variant.
- Variants: "test" = TG1 (A), "control" = CG (B) as labelled in the reports. Holdout (C) is not in the reports.
- Significance: two-proportion z-test, 95% interval, 80% power, 1pp planned lift (PRD).

## Caveats and confidence
- **Filters not verified.** The connection does not show each report's filters, so I could not confirm the PRD cohort (ETA > 1 day, app only, logged in) is applied. If the reports include Today / Tomorrow ETAs, which see no change, the true effect on the treated group is diluted, so the real effect on treated users could be larger in size, in either direction.
- **Segment counts overlap.** NU and RU viewers add up to more than the overall viewers (test 37,018 vs 35,935, 1,083 extra; control 36,592 vs 35,485, 1,107 extra; S1), so some users count in both segments (probably new users who return during the window). Segment figures are directional.
- **Report label.** The "RU PDP→OP" report's steps are `order_summary_viewed` → `app_order_placed`; I used it as RU Summary → Placed.
- **Guardrail is a proxy.** M4 is the share of users who placed an order and got a delivery event, not orders delivered ÷ orders placed. Recent orders may not be delivered yet. The two arms are measured the same way, so the comparison holds, but the levels do not (NU 57.4% vs RU 86.3% in test, S1).
- **Not covered:** the qualitative customer-perception metric, a day-by-day trend (to check for novelty or a late shift), and the holdout. Four other dashboard reports could not be read.
- **Claim strength:** this was a randomised test, so the difference is attributable to the display change, but it is not statistically different from zero.

## Next check
- Pull the daily trend of M1 by variant to confirm the gap is stable and not driven by a few days.
- Confirm the report filters in Mixpanel and re-run S1 if the cohort differs from the PRD.
- If you still want to test range framing, change the idea rather than the sample size (for example a narrower or one-sided range), since this one shows no lift.
