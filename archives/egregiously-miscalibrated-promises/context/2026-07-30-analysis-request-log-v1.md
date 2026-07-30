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
