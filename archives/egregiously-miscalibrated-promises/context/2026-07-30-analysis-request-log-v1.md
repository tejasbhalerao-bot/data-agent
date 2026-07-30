# Analysis Request Log — Egregiously Miscalibrated Promises

> Every analysis or numbers request made in this project is logged here in chronological order.
> Each entry is written to be self-contained — readable by anyone unfamiliar with the project.
> Maintained by Claude. Committed to GitHub after every entry.

---

## Log

| # | Date | Request | Output |
|---|------|---------|--------|
| 1 | 2026-07-30 | For all July 2026 orders, compute: total order count, % egregiously miscalibrated (delivery attempt ≥2 calendar days from promised delivery date), and the early/late split within that group. | 803,997 total orders; 96,424 egregiously miscalibrated (12.0%); 67,482 egregiously early (8.4%); 28,942 egregiously late (3.6%). 175,191 orders had no delivery attempt and were excluded from calibration classification. |
| 2 | 2026-07-30 | For the 96,424 egregiously miscalibrated July 2026 orders, compute early/on-time/late % for each of the six pipeline metrics: doctor confirmation, warehouse packing, dispatch, delivery, delivery TAT, and shipping delivery TAT. Denominator = 96,424 throughout. | Doctor: 57.3% early / 0.9% on-time / 41.8% late. Warehouse: 48.6% / ~0% / 51.4%. Dispatch: 41.0% / 49.7% / 9.3%. Delivery: 70.0% / 0% / 30.0%. Delivery TAT: 59.4% / 11.0% / 29.6%. Shipping Delivery TAT: 52.8% / 23.7% / 23.5%. |
| 3 | 2026-07-30 | For the 96,424 egregiously miscalibrated July 2026 orders, compute early/on-time/late % for the Doctor Ops metric (digitised_dr_promise vs actual_doctor_call_time). Denominator = 96,424. | 77.0% early / 0.1% on-time / 22.9% late. 14 orders unclassifiable due to NULL actual_doctor_call_time. |
| 4 | 2026-07-30 | For the 96,424 egregiously miscalibrated July 2026 orders, compute a 2×2 matrix of SDD vs Non-SDD (columns) × Inventory vs Non-Inventory (rows) using digitised_is_sdd and digitised_is_inventory flags. | Non-SDD + Inventory: 59.8%, Non-SDD + Non-Inventory: 30.9%, SDD + Non-Inventory: 4.8%, SDD + Inventory: 4.1%. 377 orders unclassifiable. Non-SDD dominates at 90.7%; Inventory orders are 63.9% of the egregious set. |
| 5 | 2026-07-30 | For the egregious order set, compute early/on-time/late % for all 7 pipeline metrics (Doctor Cx, Doctor Ops, Warehouse, Dispatch, Delivery Cx, Delivery TAT, Shipping Delivery TAT) across 8 segments: SDD, Non-SDD, Inventory, Non-Inventory, and all 4 SDD×Inventory combinations. Denominator = segment size in each case. | Computed and presented. Key findings: SDD+Inventory (n=3,955) is 95.6% late on Delivery Cx — the only segment with dominant late delivery. Non-Inventory segments are 91-97% early on Warehouse, Dispatch, Delivery Cx — strong over-padding. Doctor metrics are consistent (~57% early) across all segments. |
| 6 | 2026-07-30 | For the 96,424 egregious orders, compute a cross-tab of all unique Warehouse × Dispatch × Delivery Cx combinations with % of egregious orders per combination. Sorted by size descending. | 13 non-zero combinations. Top 3: Early+Early+Early (35.8%), Late+On-Time+Early (24.8%), Late+On-Time+Late (14.6%). 1 order unclassifiable. |
