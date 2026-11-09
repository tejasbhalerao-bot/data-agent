# PBA CR dashboard: final metric queries

One Snowflake query per dashboard table, for every signed-off metric (sign-off 2026-10-30). Paste a file into Metabase (database `PROD_SILVER_DB`) and run it. Each query returns the numbers as the dashboard shows them: percentages, averages, nearest-rank percentiles and cumulative %, already rounded.

| File | Dashboard section | Metrics |
|---|---|---|
| `s1-funnel_order-funnel_m1-m3.sql` | Section 1 Funnel: Order Funnel | 1 Total non-SDD orders; 2 % allocated through PBA; 3 % failed to allocate through PBA though in rollout (2 decimals) |
| `s1-funnel_pba-vs-internal-funnel_m4-m6.sql` | Section 1 Funnel: PBA vs Internal Funnel | 4 Orders placed; 5 % picked up; 6 % with delivery attempt |
| `s2-promise_soft-promise_m1-m4_wh-to-delivery.sql` | Section 2 Promise: Soft, WH to Delivery | 1–4 |
| `s2-promise_soft-promise_m5-m8_dispatch-to-delivery.sql` | Section 2 Promise: Soft, Dispatch to Delivery | 5–8 |
| `s2-promise_lane-adjusted_m9-m10.sql` | Section 2 Promise: Lane Adjusted Promise Comparison | 9–10 |
| `s2-promise_hard-promise_m11-m12_dispatch-to-delivery.sql` | Section 2 Promise: Hard, Dispatch to Delivery | 11 Hard PBA orders, PBA hard promise; 12 Hard Internal orders, partner TAT rounded up (added 2026-11-09) |
| `s2-promise_hard-promise_m13_lane-adjusted.sql` | Section 2 Promise: Hard, Lane Adjusted | 13 PBA vs Internal on the common lane set (added 2026-11-09) |
| `s3-courier-mix_m1_pba-vs-internal-partner.sql` | Section 3 Courier Allocation Mix | 1 Soft and Hard partner mix, all lanes |
| `s3-courier-mix_m2_lane-adjusted.sql` | Section 3 Courier Allocation Mix | 2 Soft and Hard partner mix, common lanes |
| `s4-adherence_soft-promise_m1_wh-to-delivery.sql` | Section 4 Adherence: Soft | 1 WH to Delivery, all lanes and lane adjusted |
| `s4-adherence_soft-promise_m2_dispatch-to-delivery.sql` | Section 4 Adherence: Soft | 2 Dispatch to Delivery, all lanes and lane adjusted |

On hold, so no query: Section 4 hard (metrics 3–4). Section 2 hard metrics 11–13 were added on 2026-11-09 at Tejas's request; their logic was checked on a 6-order test base the same way.

## How every query is built
- **Base:** Tejas's base query v2.1 (`queries-dump/2026-10-30-pba-cr-dashboard-base-query-v1.sql`). It is used unchanged except for two things:
  - The window is orders placed 22 Oct 12:00 to 26 Oct 00:00 IST. Edit `start_ts` / `end_ts` in `params` to move it.
  - A marked speed-up filter in `frozen` reads only orders that have a promise row inside the window. It gave identical counts on a 1-hour slice and on the full window.
- **Filters:** placed orders only (latest `order_details` status not 49 or 312; discarded 174 and cancelled 57 kept), non-SDD only (blank `SDD_ENABLED` left out).
- **Bases:**
  - PBA base = soft served `COURIER_PBA`.
  - Internal base = soft served LEGACY or DDB TAT adherence.
  - Hard bases use `HARD_SELECTED_CANDIDATE_TYPE` the same way.
- **Common lane set:** lanes (warehouse | pincode) with at least one PBA-base and one Internal-base order across the whole window.
- **Dates:** all day counts use IST calendar dates. Shipment pickup and attempt times are already IST wall-clock; the other timestamps carry an offset and are converted.
- Definitions follow `context/2026-10-18-dashboard-field-mapping-v1.md`.

## Status
- **Checked:** each file's metric logic ran on a 4-order test base with hand-worked answers. Section 1 metrics 1–3, Section 2 metrics 1–4, Section 3 lane-adjusted mix and Section 4 WH-to-delivery adherence all matched. Section 1 metrics 4–6, Section 2 metrics 5–10 and the other Section 3/4 files reuse the same tested pieces.
- **Not yet run on real data:** none of the 9 files has run end to end on the live base.
- **Run time:** the base is heavy. Through the Claude–Metabase connection (about 60 s limit), queries covering the full 3.5-day window timed out. If Metabase times out, run a shorter window. Counts add across windows; percentiles and averages do not, so re-aggregate those from counts.
- **Lane-adjusted files** (`s2 … m9-m10`, `s3 … m2`, `s4 …`): on 30 Oct, heavy queries that joined lanes failed in Snowflake with internal error `300010:558931247` (incident). If you see it, the only workaround that ran was a separate, light lane query whose output was matched to orders afterwards.
- **Open point, Section 4:** the mapping doesn't say what to do with orders whose *promised* days are negative. The queries keep them and count them in `info_negative_promise_kept`.
