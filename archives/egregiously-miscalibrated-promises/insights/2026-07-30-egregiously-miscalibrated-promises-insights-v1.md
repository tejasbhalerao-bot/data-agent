# Insights — Egregiously Miscalibrated Promises

> Full numerical results for every analysis run in this project.
> One section per analysis request, cross-referenced to the analysis request log.
> Source data: `raw-data/all-orders-july-2026.csv` (~804K July 2026 orders)

---

## #1 — Total Orders Funnel

**Request:** Total order count, % egregiously miscalibrated, and early/late split within that group.

| Metric | Count | % of Total |
|--------|-------|------------|
| Total orders in dataset | 803,997 | — |
| Orders with delivery attempt | 628,806 | 78.2% |
| Orders with no delivery attempt (NULL) | 175,191 | 21.8% |
| **Egregiously miscalibrated** | **96,424** | **12.0%** |
| └─ Egregiously early | 67,482 | 8.4% |
| └─ Egregiously late | 28,942 | 3.6% |

---

## #2 — Early / On-Time / Late by Pipeline Stage (Full Egregious Set)

**Request:** For the 96,424 egregious orders, early/on-time/late % for all 6 pipeline metrics.
**Denominator:** 96,424

| Stage | Early | On-Time | Late | Unclassifiable |
|-------|-------|---------|------|----------------|
| Doctor Cx | 57.3% | 0.9% | 41.8% | 0 |
| Warehouse | 48.6% | 0.0% | 51.4% | 1 |
| Dispatch | 41.0% | 49.7% | 9.3% | 0 |
| Delivery Cx | 70.0% | 0.0% | 30.0% | 0 |
| Delivery TAT | 59.4% | 11.0% | 29.6% | 0 |
| Shipping Delivery TAT | 52.8% | 23.7% | 23.5% | 0 |

---

## #3 — Doctor Ops Early / On-Time / Late (Full Egregious Set)

**Request:** Early/on-time/late for Doctor Ops metric on the 96,424 egregious orders.
**Denominator:** 96,424

| Stage | Early | On-Time | Late | Unclassifiable |
|-------|-------|---------|------|----------------|
| Doctor Ops | 77.0% | 0.1% | 22.9% | 14 |

---

## #4 — SDD × Inventory Matrix (Full Egregious Set)

**Request:** 2×2 breakdown of SDD vs Non-SDD × Inventory vs Non-Inventory.
**Denominator:** 96,424 | 377 orders unclassifiable (missing flags)

|  | SDD | Non-SDD | Row Total |
|--|-----|---------|-----------|
| **Inventory** | 3,955 (4.1%) | 57,688 (59.8%) | 61,643 (63.9%) |
| **Non-Inventory** | 4,591 (4.8%) | 29,813 (30.9%) | 34,404 (35.7%) |
| **Col Total** | 8,546 (8.9%) | 87,501 (90.7%) | 96,424 (100%) |

---

## #5 — Early / On-Time / Late by Pipeline Stage × Segment

**Request:** All 7 pipeline metrics × 8 SDD/Inventory segments for egregious orders.
**Denominator:** Segment size in each table.

### SDD (n = 8,546)

| Stage | Early | On-Time | Late | Null |
|-------|-------|---------|------|------|
| Doctor Cx | 56.3% | 1.1% | 42.6% | 0 |
| Doctor Ops | 73.7% | 0.2% | 26.1% | 2 |
| Warehouse | 63.7% | 0.0% | 36.3% | 1 |
| Dispatch | 67.2% | 24.5% | 8.3% | 0 |
| Delivery Cx | 50.8% | 0.0% | 49.2% | 0 |
| Delivery TAT | 4.6% | 29.2% | 66.3% | 0 |
| Shipping Delivery TAT | 33.8% | 28.4% | 37.7% | 0 |

### Non-SDD (n = 87,501)

| Stage | Early | On-Time | Late | Null |
|-------|-------|---------|------|------|
| Doctor Cx | 57.4% | 0.9% | 41.7% | 0 |
| Doctor Ops | 77.3% | 0.0% | 22.6% | 12 |
| Warehouse | 47.1% | 0.0% | 52.9% | 0 |
| Dispatch | 38.4% | 52.2% | 9.4% | 0 |
| Delivery Cx | 71.8% | 0.0% | 28.2% | 0 |
| Delivery TAT | 64.8% | 9.2% | 26.0% | 0 |
| Shipping Delivery TAT | 54.7% | 23.1% | 22.2% | 0 |

### Inventory (n = 61,643)

| Stage | Early | On-Time | Late | Null |
|-------|-------|---------|------|------|
| Doctor Cx | 57.8% | 0.9% | 41.3% | 0 |
| Doctor Ops | 77.3% | 0.1% | 22.7% | 13 |
| Warehouse | 21.8% | 0.0% | 78.2% | 1 |
| Dispatch | 12.5% | 73.7% | 13.7% | 0 |
| Delivery Cx | 57.3% | 0.0% | 42.7% | 0 |
| Delivery TAT | 57.6% | 3.0% | 39.4% | 0 |
| Shipping Delivery TAT | 52.2% | 15.5% | 32.3% | 0 |

### Non-Inventory (n = 34,404)

| Stage | Early | On-Time | Late | Null |
|-------|-------|---------|------|------|
| Doctor Cx | 56.4% | 0.9% | 42.6% | 0 |
| Doctor Ops | 76.5% | 0.1% | 23.4% | 1 |
| Warehouse | 96.5% | 0.0% | 3.5% | 0 |
| Dispatch | 92.0% | 6.7% | 1.4% | 0 |
| Delivery Cx | 92.6% | 0.0% | 7.4% | 0 |
| Delivery TAT | 62.6% | 25.3% | 12.1% | 0 |
| Shipping Delivery TAT | 54.0% | 38.1% | 7.9% | 0 |

### SDD + Inventory (n = 3,955)

| Stage | Early | On-Time | Late | Null |
|-------|-------|---------|------|------|
| Doctor Cx | 53.9% | 1.4% | 44.7% | 0 |
| Doctor Ops | 70.1% | 0.1% | 29.7% | 2 |
| Warehouse | 24.8% | 0.0% | 75.2% | 1 |
| Dispatch | 32.0% | 51.7% | 16.3% | 0 |
| Delivery Cx | 4.4% | 0.0% | 95.6% | 0 |
| Delivery TAT | 4.4% | 1.5% | 94.2% | 0 |
| Shipping Delivery TAT | 15.5% | 11.4% | 73.2% | 0 |

### Non-SDD + Inventory (n = 57,688)

| Stage | Early | On-Time | Late | Null |
|-------|-------|---------|------|------|
| Doctor Cx | 58.0% | 0.9% | 41.1% | 0 |
| Doctor Ops | 77.7% | 0.1% | 22.2% | 11 |
| Warehouse | 21.6% | 0.0% | 78.4% | 0 |
| Dispatch | 11.2% | 75.3% | 13.5% | 0 |
| Delivery Cx | 61.0% | 0.0% | 39.0% | 0 |
| Delivery TAT | 61.3% | 3.1% | 35.6% | 0 |
| Shipping Delivery TAT | 54.7% | 15.8% | 29.5% | 0 |

### SDD + Non-Inventory (n = 4,591)

| Stage | Early | On-Time | Late | Null |
|-------|-------|---------|------|------|
| Doctor Cx | 58.4% | 0.9% | 40.8% | 0 |
| Doctor Ops | 76.8% | 0.2% | 23.0% | 0 |
| Warehouse | 97.2% | 0.0% | 2.8% | 0 |
| Dispatch | 97.5% | 1.1% | 1.4% | 0 |
| Delivery Cx | 90.8% | 0.0% | 9.2% | 0 |
| Delivery TAT | 4.8% | 53.0% | 42.2% | 0 |
| Shipping Delivery TAT | 49.6% | 43.2% | 7.2% | 0 |

### Non-SDD + Non-Inventory (n = 29,813)

| Stage | Early | On-Time | Late | Null |
|-------|-------|---------|------|------|
| Doctor Cx | 56.1% | 0.9% | 42.9% | 0 |
| Doctor Ops | 76.5% | 0.0% | 23.5% | 1 |
| Warehouse | 96.4% | 0.0% | 3.6% | 0 |
| Dispatch | 91.1% | 7.5% | 1.4% | 0 |
| Delivery Cx | 92.9% | 0.0% | 7.1% | 0 |
| Delivery TAT | 71.5% | 21.1% | 7.4% | 0 |
| Shipping Delivery TAT | 54.7% | 37.3% | 8.0% | 0 |

---

## #6 — Warehouse × Dispatch × Delivery Cx Cross-Tab

**Request:** For the 96,424 egregious orders, all unique Warehouse × Dispatch × Delivery Cx combinations with % of egregious orders. Sorted by size descending.
**Denominator:** 96,424 | 1 order unclassifiable

| Warehouse | Dispatch | Delivery Cx | Count | % of Egregious |
|-----------|----------|-------------|-------|----------------|
| Early | Early | Early | 34,554 | 35.8% |
| Late | On-Time | Early | 23,950 | 24.8% |
| Late | On-Time | Late | 14,106 | 14.6% |
| Late | Late | Late | 7,877 | 8.2% |
| Early | On-Time | Early | 6,382 | 6.6% |
| Early | On-Time | Late | 3,462 | 3.6% |
| Early | Early | Late | 2,065 | 2.1% |
| Late | Early | Early | 1,832 | 1.9% |
| Late | Early | Late | 1,111 | 1.2% |
| Late | Late | Early | 673 | 0.7% |
| Early | Late | Late | 320 | 0.3% |
| Early | Late | Early | 90 | 0.1% |
| On-Time | Early | Early | 1 | 0.0% |
| *(all other combinations)* | | | 0 | 0.0% |

---

## #7 — Warehouse × Dispatch × Delivery Cx Cross-Tab (Non-SDD Only)

**Request:** Rebuild the Warehouse × Dispatch × Delivery Cx cross-tab restricted to Non-SDD egregious orders (digitised_is_sdd = false).
**Denominator:** 87,501 | 0 unclassifiable

| Warehouse | Dispatch | Delivery Cx | Count | % of Non-SDD Egregious |
|-----------|----------|-------------|-------|------------------------|
| Early | Early | Early | 30,169 | 34.5% |
| Late | On-Time | Early | 23,816 | 27.2% |
| Late | On-Time | Late | 12,563 | 14.4% |
| Late | Late | Late | 7,151 | 8.2% |
| Early | On-Time | Early | 6,361 | 7.3% |
| Early | On-Time | Late | 2,915 | 3.3% |
| Late | Early | Early | 1,747 | 2.0% |
| Early | Early | Late | 1,386 | 1.6% |
| Late | Late | Early | 667 | 0.8% |
| Late | Early | Late | 330 | 0.4% |
| Early | Late | Late | 305 | 0.3% |
| Early | Late | Early | 90 | 0.1% |
| On-Time | Early | Early | 1 | 0.0% |

---

## #8 — Warehouse × Dispatch × Delivery Cx Cross-Tab (Non-SDD + Inventory and Non-SDD + Non-Inventory)

**Request:** Warehouse × Dispatch × Delivery Cx cross-tab for Non-SDD+Inventory and Non-SDD+Non-Inventory egregious orders separately.

### Non-SDD + Inventory (n = 57,688) | 0 unclassifiable

| Warehouse | Dispatch | Delivery Cx | Count | % |
|-----------|----------|-------------|-------|---|
| Late | On-Time | Early | 23,454 | 40.7% |
| Late | On-Time | Late | 12,281 | 21.3% |
| Late | Late | Late | 6,800 | 11.8% |
| Early | On-Time | Early | 5,236 | 9.1% |
| Early | Early | Early | 4,035 | 7.0% |
| Early | On-Time | Late | 2,445 | 4.2% |
| Late | Early | Early | 1,707 | 3.0% |
| Late | Late | Early | 653 | 1.1% |
| Early | Early | Late | 406 | 0.7% |
| Late | Early | Late | 316 | 0.5% |
| Early | Late | Late | 271 | 0.5% |
| Early | Late | Early | 83 | 0.1% |
| On-Time | Early | Early | 1 | 0.0% |

### Non-SDD + Non-Inventory (n = 29,813) | 0 unclassifiable

| Warehouse | Dispatch | Delivery Cx | Count | % |
|-----------|----------|-------------|-------|---|
| Early | Early | Early | 26,134 | 87.7% |
| Early | On-Time | Early | 1,125 | 3.8% |
| Early | Early | Late | 980 | 3.3% |
| Early | On-Time | Late | 470 | 1.6% |
| Late | On-Time | Early | 362 | 1.2% |
| Late | Late | Late | 351 | 1.2% |
| Late | On-Time | Late | 282 | 0.9% |
| Late | Early | Early | 40 | 0.1% |
| Early | Late | Late | 34 | 0.1% |
| Late | Early | Late | 14 | 0.0% |
| Late | Late | Early | 14 | 0.0% |
| Early | Late | Early | 7 | 0.0% |

---

## #9 — Cohort 14: Warehouse Earliness Magnitude Buckets

**Request:** For cohort 14 (Non-SDD egregious, Warehouse=Early, Dispatch=Early, Delivery=Early, n=30,169), segment by how early the warehouse packed (digitised_wh_promise − awb_sticker_printed_ts).
**Denominators:** Cohort 14 (n=30,169) and total egregious (n=96,424)

| Bucket | Count | % of Cohort 14 | % of Egregious | % Non-Inventory |
|--------|-------|----------------|----------------|-----------------|
| < 30 mins | 1,442 | 4.8% | 1.5% | 1.2% |
| 30 – 60 mins | 2,297 | 7.6% | 2.4% | 0.7% |
| 1 – 2 hrs | 398 | 1.3% | 0.4% | 46.7% |
| 2 – 4 hrs | 851 | 2.8% | 0.9% | 99.9% |
| 4 – 8 hrs | 5,551 | 18.4% | 5.8% | 100.0% |
| 8 – 12 hrs | 3,449 | 11.4% | 3.6% | 100.0% |
| 12 – 24 hrs | 2,695 | 8.9% | 2.8% | 96.5% |
| > 24 hrs | 13,486 | 44.7% | 14.0% | 99.9% |
| **Total** | **30,169** | **100.0%** | **31.3%** | **86.6%** |

---

## #11 — Cohort 14: Sample Orders per Warehouse Earliness Bucket (All Columns)

**Request:** Pull one sample order per bucket from cohort 14 to understand why orders packed slightly early in the warehouse still result in dispatch and delivery being a full day+ early.

**Key finding across all buckets:** The courier picks up the order on the same day the AWB is printed — within hours — regardless of the dispatch promise date. The dispatch promise date (always next day or later) is being ignored. AWB print is acting as the de facto pickup trigger.

| Bucket | Order ID | WH Promise | AWB Printed | WH Mins Early | Dispatch Promise | Pickup Time | Delivery Promise | Delivery Attempt |
|--------|----------|------------|-------------|---------------|-----------------|-------------|-----------------|-----------------|
| < 30 mins | 13983730 | Jul 3 18:03 | Jul 3 17:48 | 15 | Jul 4 18:00 | Jul 3 18:19 | Jul 7 | Jul 5 |
| 30–60 mins | 9093921 | Jul 15 18:34 | Jul 15 17:53 | 40 | Jul 16 17:00 | Jul 15 18:07 | Jul 20 | Jul 18 |
| 1–2 hrs | 14418699 | Jul 2 16:30 | Jul 2 15:07 | 83 | Jul 3 13:00 | Jul 2 19:29 | Jul 8 | Jul 5 |
| 4–8 hrs | 4650456 | Jul 17 22:00 | Jul 17 15:10 | 410 | Jul 18 18:00 | Jul 17 18:46 | Jul 22 | Jul 20 |
| 8–12 hrs | 4813526 | Jul 24 22:00 | Jul 24 12:40 | 560 | Jul 25 20:00 | Jul 24 13:53 | Jul 29 | Jul 26 |
| 12–24 hrs | 4171350 | Jul 4 11:00 | Jul 3 17:23 | 1,057 | Jul 4 20:00 | Jul 3 17:52 | Jul 8 | Jul 6 |
| > 24 hrs | 4779013 | Jul 9 11:00 | Jul 7 16:17 | 2,563 | Jul 9 17:00 | Jul 7 18:23 | Jul 11 | Jul 9 |
