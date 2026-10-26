---
project: eta-framing-xp
job: measure
status: brief
awaiting: []
assumptions: [window 2026-09-19 to latest full day, PRD cohort and exclusions]
signed_off: false
as_of: 2026-10-26
---

# Did relative-days ETA framing (ETA-F1) lift Summary to Order Placed conversion, and should it scale?

**My reading of the flow:** Test users see "Delivery in X-Y days" on Order Summary, control sees absolute dates; Mixpanel records order_summary_viewed then app_order_placed by variant. Rests on the PRD and the ETA Framing XP dashboard only.

## Answer
Pending

## Approved brief
Approved by Tejas 2026-10-26: grain one row per variant per day; columns date, variant, user_type, summary_users, order_users.
- M1 Summary to Order Placed conversion, test vs control, overall; cuts: new vs returning, pre vs post 21 Sep ramp.
- M2 Summary bounce rate (same cuts).
- M3 Fulfilment rate (Redshift): not confirmed by Tejas; excluded until he says.
- M4 Group-size check, lift with 95% interval, sample vs 1pp MDE.
- Window: 2026-09-19 to latest full day. Decision: scale up, iterate or kill vs the PRD's 1pp.

## Queries to run
Blocked: variant labels not confirmed (see chat).
