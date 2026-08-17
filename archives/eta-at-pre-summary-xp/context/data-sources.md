# Data Sources — ETA at Pre-Summary XP

| File | Description | Location |
|------|-------------|----------|
| PRD | ETA-E2 experiment design, hypotheses, variant definitions, instrumentation | Google Docs: https://docs.google.com/document/d/1oxHnkQFZZ2IdPbwYQGw1ux5fns1xXrEauX8IZx4OLQc |
| Results spreadsheet | Full funnel metrics by variant: overall, RU, NU, RU Non-SDD, NU Non-SDD | Google Sheets: https://docs.google.com/spreadsheets/d/1-FFv7R19UTIFELQa7RMF2mqZSEy_ZbKS8g0O6uRRScM |
| Mixpanel funnels | 4-step funnel (pdp_viewed → cart_viewed → order_summary_viewed → app_order_placed) broken by experiment_variant property | Mixpanel: ETA-E2, since Aug 11 2026 |

## Experiment Details

- **Experiment ID:** ETA-E2
- **Randomisation:** hash(customer_id + "ETA-E2") % 100
- **Universe:** Logged-in app users only (not website), ETA ≤ 5 days
- **Traffic split:** TG1/TG2/TG3/CG = 7% each (~1% of total eligible); Holdout = 72%
- **Actual PDP sample sizes per variant:** ~3,000 (full), ~2,000 RU, ~1,000 NU
- **SDD note:** SDD samples per variant are in single/double digits — not analyzable
