# ETA-E3 Mixpanel dashboard counts

- **Purpose:** Users per variant at each funnel step, taken from the saved reports on the Mixpanel dashboard "ETA Ranges XP"
- **Serves:** M1, M2, M3, M4, M5
- **Grain:** one row per report per variant (control, test)
- **Tables:** none (Mixpanel, project 2900163 "Production Env", dashboard 11537748)
- **Definitions used:** none in `metrics.md`; brief definitions M1 to M5
- **Filters:** those saved inside each report (not visible through the connection); the dashboard date filter is "since 2026-09-19"; read on 2026-10-26
- **Expected shape:** 12 rows: report_id, report_name, segment, stage, variant, users_start, users_end
- **Timeout risk:** Low
- **Save the CSV as:** `archives/eta-ranges-xp/raw-data/mixpanel-etaranges-dashboard-counts-2026-10-26.csv`

Mixpanel reports read with `Get-Report` (results included). This is not SQL.

| Report ID | Report | Segment | Stage |
|-----------|--------|---------|-------|
| 93468609 | User Distribution | overall | SRM check (uniques of `order_summary_viewed`) |
| 92912492 | OS→OP Funnel Conversion | overall | OS_to_OP |
| 92912564 | NU OS→OP Funnel Conversion | NU | OS_to_OP |
| 92913233 | RU PDP→OP Funnel Conversion (its steps are `order_summary_viewed` → `app_order_placed`) | RU | OS_to_OP |
| 93033606 | NU OP -> OD Funnel | NU | OP_to_OD |
| 93033586 | RU OP -> OD Funnel | RU | OP_to_OD |

Reports 93468612, 93033578, 93033576 and 93033587 returned an error through the connection and are not used.
