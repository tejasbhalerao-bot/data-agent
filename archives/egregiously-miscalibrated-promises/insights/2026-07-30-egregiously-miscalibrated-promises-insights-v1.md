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

---

## #12 — Cohort 40: Warehouse Earliness Magnitude Buckets

**Request:** For cohort 40 (Non-SDD Non-Inventory egregious, Warehouse=Early, Dispatch=Early, Delivery=Early, n=26,134), segment by how early the warehouse packed (digitised_wh_promise − awb_sticker_printed_ts).
**Denominators:** Cohort 40 (n=26,134) and total egregious (n=96,424)

| Bucket | Count | % of Cohort 40 | % of Egregious |
|--------|------:|---------------:|---------------:|
| < 30 mins | 18 | 0.1% | 0.0% |
| 30 – 60 mins | 15 | 0.1% | 0.0% |
| 1 – 2 hrs | 186 | 0.7% | 0.2% |
| 2 – 4 hrs | 850 | 3.3% | 0.9% |
| 4 – 8 hrs | 5,549 | 21.2% | 5.8% |
| 8 – 12 hrs | 3,449 | 13.2% | 3.6% |
| 12 – 24 hrs | 2,601 | 10.0% | 2.7% |
| > 24 hrs | 13,466 | 51.5% | 14.0% |
| **Total** | **26,134** | **100.0%** | **27.1%** |

---

## #13 — Cohort 40: Warehouse Bucket × Dispatch Days Early × Delivery TAT Days Early Matrix

**Request:** For cohort 40, build a 3-way matrix of warehouse earliness bucket × dispatch days early × delivery TAT days early. Each cell = % of cohort 40 (n=26,134).
**Delivery TAT days early** = [DATE(digitised_delivery_promise) − DATE(digitised_dispatch_promise)] − [DATE(delivery_attempt_time) − DATE(pickup_time)]. Positive = courier delivered in fewer days than promised.

| WH Bucket | Dispatch | TAT -1d (late) | TAT 0d | TAT 1d early | TAT 2d early | TAT 3d+ early | Row % | n |
|---|---|---|---|---|---|---|---|---|
| 4–8 hrs | 1d early | 0.0% | 0.0% | 15.5% | 4.2% | 0.6% | 20.3% | 5,302 |
| 4–8 hrs | 2d early | 0.0% | 0.7% | 0.2% | 0.0% | 0.0% | 0.9% | 247 |
| 8–12 hrs | 1d early | 0.0% | 0.0% | 9.3% | 2.8% | 0.5% | 12.6% | 3,301 |
| 8–12 hrs | 2d early | 0.0% | 0.4% | 0.2% | 0.0% | 0.0% | 0.6% | 148 |
| 12–24 hrs | 1d early | 0.0% | 0.0% | 6.8% | 1.5% | 0.2% | 8.5% | 2,216 |
| 12–24 hrs | 2d early | 0.0% | 0.9% | 0.4% | 0.1% | 0.0% | 1.4% | 368 |
| 12–24 hrs | 3d+ early | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.1% | 17 |
| > 24 hrs | 1d early | 0.0% | 0.0% | 10.5% | 2.9% | 0.4% | 13.9% | 3,625 |
| > 24 hrs | 2d early | 0.0% | 19.5% | 10.8% | 2.9% | 0.4% | 33.5% | 8,759 |
| > 24 hrs | 3d+ early | 0.8% | 2.0% | 1.0% | 0.3% | 0.0% | 4.1% | 1,082 |
| **Col Total** | | **0.9%** | **23.5%** | **54.6%** | **14.8%** | **2.2%** | **95.9%** | **25,065** |

*1,069 cohort 40 orders (4.1%) unclassifiable — NULL dispatch promise, pickup time, or TAT fields.*

---

## #14 — SDD Egregious: Warehouse × Dispatch × Delivery Cx Cross-Tabs

**Request:** Build Warehouse × Dispatch × Delivery Cx cross-tab for all SDD egregious orders, SDD Inventory, and SDD Non-Inventory. Cohort numbering continues from 49.

### ALL SDD Egregious (n=8,545 | 8.9% of all egregious)

| Cohort | Warehouse | Dispatch | Delivery Cx | Count | % of SDD Egregious |
|---|---|---|---|---|---|
| 49 | Early | Early | Early | 4,212 | 49.3% |
| 50 | Late | On-Time | Late | 1,505 | 17.6% |
| 51 | Late | Early | Late | 777 | 9.1% |
| 52 | Late | Late | Late | 693 | 8.1% |
| 53 | Early | Early | Late | 673 | 7.9% |
| 54 | Early | On-Time | Late | 539 | 6.3% |
| 55 | Late | Early | Early | 82 | 1.0% |
| 56 | Late | On-Time | Early | 46 | 0.5% |
| 57 | Early | Late | Late | 15 | 0.2% |
| 58 | Early | On-Time | Early | 3 | 0.0% |

### ALL SDD Inventory Egregious (n=3,954 | 46.3% of SDD egregious)

| Cohort | Warehouse | Dispatch | Delivery Cx | Count | % of SDD Inventory |
|---|---|---|---|---|---|
| 59 | Late | On-Time | Late | 1,468 | 37.1% |
| 60 | Late | Early | Late | 742 | 18.8% |
| 61 | Late | Late | Late | 637 | 16.1% |
| 62 | Early | On-Time | Late | 525 | 13.3% |
| 63 | Early | Early | Late | 399 | 10.1% |
| 64 | Late | Early | Early | 81 | 2.0% |
| 65 | Late | On-Time | Early | 46 | 1.2% |
| 66 | Early | Early | Early | 45 | 1.1% |
| 67 | Early | Late | Late | 8 | 0.2% |
| 68 | Early | On-Time | Early | 3 | 0.1% |

### ALL SDD Non-Inventory Egregious (n=4,591 | 53.7% of SDD egregious)

| Cohort | Warehouse | Dispatch | Delivery Cx | Count | % of SDD Non-Inventory |
|---|---|---|---|---|---|
| 69 | Early | Early | Early | 4,167 | 90.8% |
| 70 | Early | Early | Late | 274 | 6.0% |
| 71 | Late | Late | Late | 56 | 1.2% |
| 72 | Late | On-Time | Late | 37 | 0.8% |
| 73 | Late | Early | Late | 35 | 0.8% |
| 74 | Early | On-Time | Late | 14 | 0.3% |
| 75 | Early | Late | Late | 7 | 0.2% |
| 76 | Late | Early | Early | 1 | 0.0% |

---

## #15 — Cohort 41: Warehouse Earliness Buckets & WH × Delivery TAT Matrix

**Request:** For cohort 41 (Non-SDD Non-Inventory egregious, Warehouse=Early, Dispatch=On-Time, Delivery=Early, n=1,125), build warehouse earliness magnitude buckets and WH bucket × Delivery TAT days early matrix. Dispatch column dropped — all orders are on-time on dispatch.

### View 1: Warehouse Earliness Magnitude Buckets

| Bucket | Count | % of Cohort 41 | % of Egregious |
|---|---|---|---|
| < 30 mins | 44 | 3.9% | 0.0% |
| 30 – 60 mins | 66 | 5.9% | 0.1% |
| 1 – 2 hrs | 150 | 13.3% | 0.2% |
| 2 – 4 hrs | 309 | 27.5% | 0.3% |
| 4 – 8 hrs | 308 | 27.4% | 0.3% |
| 8 – 12 hrs | 40 | 3.6% | 0.0% |
| 12 – 24 hrs | 174 | 15.5% | 0.2% |
| > 24 hrs | 34 | 3.0% | 0.0% |
| **Total** | **1,125** | **100.0%** | **1.2%** |

### View 2: WH Bucket × Delivery TAT Days Early (% of Cohort 41)

*Dispatch is on-time for all orders; TAT early = delivery Cx days early (min 2d for egregious orders — TAT -1d/0d/1d are mathematically impossible here).*

| WH Bucket | TAT -1d (late) | TAT 0d | TAT 1d | TAT 2d early | TAT 3d+ early | Row % | n |
|---|---|---|---|---|---|---|---|
| < 30 mins | 0.0% | 0.0% | 0.0% | 3.6% | 0.3% | 3.9% | 44 |
| 30 – 60 mins | 0.0% | 0.0% | 0.0% | 4.4% | 1.4% | 5.9% | 66 |
| 1 – 2 hrs | 0.0% | 0.0% | 0.0% | 11.7% | 1.6% | 13.3% | 150 |
| 2 – 4 hrs | 0.0% | 0.0% | 0.0% | 24.3% | 3.2% | 27.5% | 309 |
| 4 – 8 hrs | 0.0% | 0.0% | 0.0% | 23.2% | 4.2% | 27.4% | 308 |
| 8 – 12 hrs | 0.0% | 0.0% | 0.0% | 2.6% | 1.0% | 3.6% | 40 |
| 12 – 24 hrs | 0.0% | 0.0% | 0.0% | 13.5% | 2.0% | 15.5% | 174 |
| > 24 hrs | 0.0% | 0.0% | 0.0% | 2.5% | 0.5% | 3.0% | 34 |
| **Col Total** | **0.0%** | **0.0%** | **0.0%** | **85.9%** | **14.1%** | **100.0%** | **1,125** |

---

## #17 — Non-Inventory Share of All July 2026 Orders

**Request:** What % of all July 2026 orders are Non-Inventory at digitised?

| Segment | Count | % of All Orders |
|---|---|---|
| Inventory | 646,010 | 80.3% |
| Non-Inventory | 156,171 | 19.4% |
| Unclassifiable (NULL) | 1,816 | 0.2% |
| **Total** | **803,997** | **100.0%** |

Non-Inventory is 19.4% of all orders but 30.9% of the egregious set — approximately 1.6× overrepresented.

---

## #18 — Day-on-Day Non-Inventory % by Order Placement Date

**Request:** Day-on-day breakdown of Non-Inventory % across July 2026, using digitised_ts as the placement date.

| Date | Total | Inventory | Inv % | Non-Inventory | Non-Inv % |
|---|---|---|---|---|---|
| 2026-07-01 | 28,778 | 23,130 | 80.4% | 5,606 | 19.5% |
| 2026-07-02 | 30,066 | 24,248 | 80.6% | 5,503 | 18.3% |
| 2026-07-03 | 28,974 | 23,519 | 81.2% | 5,154 | 17.8% |
| 2026-07-04 | 28,144 | 23,060 | 81.9% | 5,072 | 18.0% |
| 2026-07-05 | 28,760 | 23,267 | 80.9% | 5,485 | 19.1% |
| 2026-07-06 | 27,321 | 22,125 | 81.0% | 5,191 | 19.0% |
| 2026-07-07 | 27,886 | 22,717 | 81.5% | 5,155 | 18.5% |
| 2026-07-08 | 27,892 | 22,682 | 81.3% | 5,201 | 18.6% |
| 2026-07-09 | 27,751 | 22,617 | 81.5% | 5,125 | 18.5% |
| 2026-07-10 | 27,092 | 21,987 | 81.2% | 5,093 | 18.8% |
| 2026-07-11 | 28,566 | 22,402 | 78.4% | 6,153 | 21.5% |
| 2026-07-12 | 27,955 | 21,574 | 77.2% | 6,367 | 22.8% |
| 2026-07-13 | 28,036 | 21,676 | 77.3% | 6,351 | 22.7% |
| 2026-07-14 | 27,408 | 22,222 | 81.1% | 5,145 | 18.8% |
| 2026-07-15 | 26,491 | 21,324 | 80.5% | 5,153 | 19.5% |
| 2026-07-16 | 26,059 | 21,057 | 80.8% | 4,989 | 19.1% |
| 2026-07-17 | 25,411 | 20,653 | 81.3% | 4,751 | 18.7% |
| 2026-07-18 | 25,908 | 20,849 | 80.5% | 5,059 | 19.5% |
| 2026-07-19 | 25,630 | 20,602 | 80.4% | 5,028 | 19.6% |
| 2026-07-20 | 25,652 | 20,319 | 79.2% | 5,333 | 20.8% |
| 2026-07-21 | 26,003 | 20,905 | 80.4% | 5,098 | 19.6% |
| 2026-07-22 | 26,436 | 21,421 | 81.0% | 5,014 | 19.0% |
| 2026-07-23 | 26,056 | 21,324 | 81.8% | 4,732 | 18.2% |
| 2026-07-24 | 25,221 | 20,573 | 81.6% | 4,648 | 18.4% |
| 2026-07-25 | 26,832 | 21,799 | 81.2% | 5,032 | 18.8% |
| 2026-07-26 | 27,029 | 21,762 | 80.5% | 5,210 | 19.3% |
| 2026-07-27 | 27,469 | 21,719 | 79.1% | 5,474 | 19.9% |
| 2026-07-28 | 27,846 | 22,012 | 79.0% | 5,571 | 20.0% |
| 2026-07-29 | 27,445 | 21,530 | 78.4% | 5,666 | 20.6% |
| 2026-07-30 | 13,880 | 10,935 | 78.8% | 2,812 | 20.3% |

*Jul 30 is a partial day (~half volume). Jul 11–13 spike: 21.5%–22.8% Non-Inventory vs typical 18–20%.*

---

## #19 — Egregious Non-SDD Non-Inventory Superset: WH Magnitude Buckets

**Request:** For the egregious Non-SDD Non-Inventory superset (n=29,813), plot warehouse earliness/lateness magnitude buckets.
**Denominators:** Superset (n=29,813) and total egregious (n=96,424)

| WH Bucket | Count | % of Superset | % of Egregious |
|---|---|---|---|
| **── WAREHOUSE EARLY ──** | | | |
| Early < 30 mins | 84 | 0.3% | 0.1% |
| Early 30 – 60 mins | 114 | 0.4% | 0.1% |
| Early 1 – 2 hrs | 426 | 1.4% | 0.4% |
| Early 2 – 4 hrs | 1,381 | 4.6% | 1.4% |
| Early 4 – 8 hrs | 6,227 | 20.9% | 6.5% |
| Early 8 – 12 hrs | 3,643 | 12.2% | 3.8% |
| Early 12 – 24 hrs | 3,058 | 10.3% | 3.2% |
| Early > 24 hrs | 13,817 | 46.3% | 14.3% |
| **Subtotal Early** | **28,750** | **96.4%** | **29.8%** |
| **── WAREHOUSE ON-TIME ──** | | | |
| On-Time | 0 | 0.0% | 0.0% |
| **── WAREHOUSE LATE ──** | | | |
| Late < 30 mins | 41 | 0.1% | 0.0% |
| Late 30 – 60 mins | 52 | 0.2% | 0.1% |
| Late 1 – 2 hrs | 76 | 0.3% | 0.1% |
| Late 2 – 4 hrs | 116 | 0.4% | 0.1% |
| Late 4 – 8 hrs | 76 | 0.3% | 0.1% |
| Late 8 – 12 hrs | 71 | 0.2% | 0.1% |
| Late 12 – 24 hrs | 453 | 1.5% | 0.5% |
| Late > 24 hrs | 178 | 0.6% | 0.2% |
| **Subtotal Late** | **1,063** | **3.6%** | **1.1%** |
| **TOTAL** | **29,813** | **100.0%** | **30.9%** |

---

## #20 — Egregious Non-SDD Non-Inventory Superset: Dispatch & Delivery TAT Magnitude Tables

**Request:** Progressive magnitude tables for dispatch days early/late and delivery TAT days early/late for the superset (n=29,813).

### Dispatch

| Deviation | Count | % of Superset | % of Egregious |
|---|---|---|---|
| Early 3d+ | 1,115 | 3.7% | 1.2% |
| Early 2d | 9,726 | 32.6% | 10.1% |
| Early 1d | 16,327 | 54.8% | 16.9% |
| On-Time | 2,239 | 7.5% | 2.3% |
| Late 1d | 235 | 0.8% | 0.2% |
| Late 2d | 82 | 0.3% | 0.1% |
| Late 3d+ | 89 | 0.3% | 0.1% |
| **Total** | **29,813** | **100.0%** | **30.9%** |

### Delivery TAT

| Deviation | Count | % of Superset | % of Egregious |
|---|---|---|---|
| Early 4d+ | 26 | 0.1% | 0.0% |
| Early 3d | 804 | 2.7% | 0.8% |
| Early 2d | 5,384 | 18.1% | 5.6% |
| Early 1d | 15,101 | 50.7% | 15.7% |
| On-Time | 6,277 | 21.1% | 6.5% |
| Late 1d | 407 | 1.4% | 0.4% |
| Late 2d | 489 | 1.6% | 0.5% |
| Late 3d | 597 | 2.0% | 0.6% |
| Late 4d | 360 | 1.2% | 0.4% |
| Late 5d | 170 | 0.6% | 0.2% |
| Late 6d+ | 198 | 0.7% | 0.2% |
| **Total** | **29,813** | **100.0%** | **30.9%** |

---

## #21 — Egregious Non-SDD Inventory Superset: WH, Dispatch & Delivery TAT Magnitude Tables

**Request:** Progressive magnitude tables for WH, dispatch days early/late, and delivery TAT days early/late for the Non-SDD Inventory egregious superset (n=57,688).

### Warehouse

| Deviation | Count | % of Superset | % of Egregious |
|---|---|---|---|
| Early > 24 hrs | 21 | 0.0% | 0.0% |
| Early 12 – 24 hrs | 156 | 0.3% | 0.2% |
| Early 1 – 2 hrs | 443 | 0.8% | 0.5% |
| Early 30 – 60 mins | 5,815 | 10.1% | 6.0% |
| Early < 30 mins | 6,030 | 10.5% | 6.3% |
| On-Time | 1 | 0.0% | 0.0% |
| Late < 30 mins | 4,135 | 7.2% | 4.3% |
| Late 30 – 60 mins | 3,293 | 5.7% | 3.4% |
| Late 1 – 2 hrs | 5,351 | 9.3% | 5.5% |
| Late 2 – 4 hrs | 7,359 | 12.8% | 7.6% |
| Late 4 – 8 hrs | 7,816 | 13.5% | 8.1% |
| Late 8 – 12 hrs | 1,340 | 2.3% | 1.4% |
| Late 12 – 24 hrs | 12,277 | 21.3% | 12.7% |
| Late > 24 hrs | 3,640 | 6.3% | 3.8% |
| **Total** | **57,688** | **100.0%** | **59.8%** |

### Dispatch

| Deviation | Count | % of Superset | % of Egregious |
|---|---|---|---|
| Early 2d+ | 258 | 0.4% | 0.3% |
| Early 1d | 6,207 | 10.8% | 6.4% |
| On-Time | 43,416 | 75.3% | 45.0% |
| Late 1d | 5,240 | 9.1% | 5.4% |
| Late 2d | 1,786 | 3.1% | 1.9% |
| Late 3d | 361 | 0.6% | 0.4% |
| Late 4d | 145 | 0.3% | 0.2% |
| Late 5d | 74 | 0.1% | 0.1% |
| Late 6d+ | 201 | 0.3% | 0.2% |
| **Total** | **57,688** | **100.0%** | **59.8%** |

### Delivery TAT

| Deviation | Count | % of Superset | % of Egregious |
|---|---|---|---|
| Early 5d+ | 101 | 0.2% | 0.1% |
| Early 4d | 670 | 1.2% | 0.7% |
| Early 3d | 4,920 | 8.5% | 5.1% |
| Early 2d | 25,355 | 44.0% | 26.3% |
| Early 1d | 4,298 | 7.5% | 4.5% |
| On-Time | 1,779 | 3.1% | 1.8% |
| Late 1d | 3,331 | 5.8% | 3.5% |
| Late 2d | 9,978 | 17.3% | 10.3% |
| Late 3d | 3,774 | 6.5% | 3.9% |
| Late 4d | 1,694 | 2.9% | 1.8% |
| Late 5d | 816 | 1.4% | 0.8% |
| Late 6d+ | 972 | 1.7% | 1.0% |
| **Total** | **57,688** | **100.0%** | **59.8%** |

---

## #16 — Cohorts 27–33: WH Magnitude Buckets & WH × Dispatch × TAT Matrices

**Request:** For each of cohorts 27–33 (Non-SDD Inventory egregious sub-cohorts), build WH magnitude buckets (earliness or lateness) and WH × dispatch × TAT matrices individually.

---

### Cohort 27 — WH=Late | Dispatch=On-Time | Delivery=Early (n=23,454 | 24.3% of egregious)

**WH Lateness Magnitude**

| Bucket | Count | % of Cohort | % of Egregious |
|---|---|---|---|
| < 30 mins | 2,166 | 9.2% | 2.2% |
| 30 – 60 mins | 1,840 | 7.8% | 1.9% |
| 1 – 2 hrs | 3,069 | 13.1% | 3.2% |
| 2 – 4 hrs | 4,289 | 18.3% | 4.4% |
| 4 – 8 hrs | 4,481 | 19.1% | 4.6% |
| 8 – 12 hrs | 695 | 3.0% | 0.7% |
| 12 – 24 hrs | 6,895 | 29.4% | 7.2% |
| > 24 hrs | 19 | 0.1% | 0.0% |
| **Total** | **23,454** | **100.0%** | **24.3%** |

**WH Bucket × Delivery TAT (dispatch on-time — fixed)**

| WH Bucket | TAT 2d early | TAT 3d early | TAT 4d+ early | Row % | n |
|---|---|---|---|---|---|
| < 30 mins | 7.5% | 1.5% | 0.3% | 9.2% | 2,166 |
| 30 – 60 mins | 6.5% | 1.2% | 0.2% | 7.8% | 1,840 |
| 1 – 2 hrs | 11.0% | 1.8% | 0.3% | 13.1% | 3,069 |
| 2 – 4 hrs | 15.6% | 2.4% | 0.3% | 18.3% | 4,289 |
| 4 – 8 hrs | 16.6% | 2.3% | 0.2% | 19.1% | 4,481 |
| 8 – 12 hrs | 2.6% | 0.3% | 0.1% | 3.0% | 695 |
| 12 – 24 hrs | 24.6% | 4.2% | 0.6% | 29.4% | 6,895 |
| > 24 hrs | 0.1% | 0.0% | 0.0% | 0.1% | 19 |
| **Col Total** | **84.3%** | **13.7%** | **2.0%** | **100.0%** | **23,454** |

---

### Cohort 28 — WH=Late | Dispatch=On-Time | Delivery=Late (n=12,281 | 12.7% of egregious)

**WH Lateness Magnitude**

| Bucket | Count | % of Cohort | % of Egregious |
|---|---|---|---|
| < 30 mins | 1,093 | 8.9% | 1.1% |
| 30 – 60 mins | 916 | 7.5% | 0.9% |
| 1 – 2 hrs | 1,596 | 13.0% | 1.7% |
| 2 – 4 hrs | 2,216 | 18.0% | 2.3% |
| 4 – 8 hrs | 2,496 | 20.3% | 2.6% |
| 8 – 12 hrs | 418 | 3.4% | 0.4% |
| 12 – 24 hrs | 3,489 | 28.4% | 3.6% |
| > 24 hrs | 57 | 0.5% | 0.1% |
| **Total** | **12,281** | **100.0%** | **12.7%** |

**WH Bucket × Delivery TAT (dispatch on-time — fixed)**

| WH Bucket | TAT 2d late | TAT 3d+ late | Row % | n |
|---|---|---|---|---|
| < 30 mins | 5.2% | 3.7% | 8.9% | 1,093 |
| 30 – 60 mins | 4.6% | 2.9% | 7.5% | 916 |
| 1 – 2 hrs | 8.1% | 4.9% | 13.0% | 1,596 |
| 2 – 4 hrs | 11.1% | 6.9% | 18.0% | 2,216 |
| 4 – 8 hrs | 12.5% | 7.8% | 20.3% | 2,496 |
| 8 – 12 hrs | 2.1% | 1.3% | 3.4% | 418 |
| 12 – 24 hrs | 17.4% | 11.0% | 28.4% | 3,489 |
| > 24 hrs | 0.4% | 0.1% | 0.5% | 57 |
| **Col Total** | **61.3%** | **38.7%** | **100.0%** | **12,281** |

---

### Cohort 29 — WH=Late | Dispatch=Late | Delivery=Late (n=6,800 | 7.1% of egregious)

**WH Lateness Magnitude**

| Bucket | Count | % of Cohort | % of Egregious |
|---|---|---|---|
| < 30 mins | 167 | 2.5% | 0.2% |
| 30 – 60 mins | 140 | 2.1% | 0.1% |
| 1 – 2 hrs | 253 | 3.7% | 0.3% |
| 2 – 4 hrs | 450 | 6.6% | 0.5% |
| 4 – 8 hrs | 625 | 9.2% | 0.6% |
| 8 – 12 hrs | 181 | 2.7% | 0.2% |
| 12 – 24 hrs | 1,511 | 22.2% | 1.6% |
| > 24 hrs | 3,473 | 51.1% | 3.6% |
| **Total** | **6,800** | **100.0%** | **7.1%** |

**WH Bucket × Dispatch Days Late × Delivery TAT**

| WH Bucket | Dispatch | TAT 3d+ late | TAT 2d late | TAT 1d late | TAT 0d | TAT 1d early | Row % | n |
|---|---|---|---|---|---|---|---|---|
| < 30 mins | 1d late | 0.4% | 0.4% | 1.2% | 0.0% | 0.0% | 2.1% | 140 |
| | 2d late | 0.0% | 0.0% | 0.1% | 0.1% | 0.0% | 0.3% | 18 |
| | 3d+ late | 0.0% | 0.0% | 0.0% | 0.1% | 0.0% | 0.1% | 9 |
| 30 – 60 mins | 1d late | 0.4% | 0.3% | 1.1% | 0.0% | 0.0% | 1.7% | 118 |
| | 2d late | 0.0% | 0.0% | 0.0% | 0.1% | 0.0% | 0.1% | 9 |
| | 3d+ late | 0.0% | 0.0% | 0.0% | 0.0% | 0.1% | 0.2% | 13 |
| 1 – 2 hrs | 1d late | 0.6% | 0.7% | 1.9% | 0.0% | 0.0% | 3.2% | 220 |
| | 2d+ late | 0.0% | 0.0% | 0.1% | 0.2% | 0.1% | 0.5% | 33 |
| 2 – 4 hrs | 1d late | 1.1% | 1.0% | 3.6% | 0.0% | 0.0% | 5.8% | 391 |
| | 2d+ late | 0.1% | 0.0% | 0.1% | 0.5% | 0.1% | 0.9% | 59 |
| 4 – 8 hrs | 1d late | 1.7% | 1.6% | 4.8% | 0.0% | 0.0% | 8.1% | 550 |
| | 2d+ late | 0.1% | 0.0% | 0.1% | 0.7% | 0.1% | 1.1% | 75 |
| 8 – 12 hrs | 1d late | 0.5% | 0.5% | 1.4% | 0.0% | 0.0% | 2.3% | 159 |
| | 2d+ late | 0.0% | 0.0% | 0.0% | 0.2% | 0.0% | 0.3% | 22 |
| 12 – 24 hrs | 1d late | 2.5% | 3.9% | 11.9% | 0.0% | 0.0% | 18.3% | 1,245 |
| | 2d+ late | 0.1% | 0.3% | 0.7% | 2.3% | 0.4% | 4.0% | 266 |
| > 24 hrs | 1d late | 2.9% | 3.7% | 14.9% | 0.0% | 0.0% | 21.5% | 1,461 |
| | 2d late | 0.6% | 0.7% | 3.7% | 15.1% | 0.0% | 20.2% | 1,375 |
| | 3d+ late | 0.2% | 0.2% | 1.0% | 4.1% | 3.8% | 9.4% | 637 |
| **Col Total** | | **11.2%** | **13.4%** | **46.9%** | **23.7%** | **4.0%** | **100.0%** | **6,800** |

---

### Cohort 30 — WH=Early | Dispatch=On-Time | Delivery=Early (n=5,236 | 5.4% of egregious)

**WH Earliness Magnitude**

| Bucket | Count | % of Cohort | % of Egregious |
|---|---|---|---|
| < 30 mins | 2,821 | 53.9% | 2.9% |
| 30 – 60 mins | 2,252 | 43.0% | 2.3% |
| 1 – 2 hrs | 137 | 2.6% | 0.1% |
| 2 – 4 hrs | 4 | 0.1% | 0.0% |
| 12 – 24 hrs | 22 | 0.4% | 0.0% |
| **Total** | **5,236** | **100.0%** | **5.4%** |

**WH Bucket × Delivery TAT (dispatch on-time — fixed)**

| WH Bucket | TAT 2d early | TAT 3d early | TAT 4d+ early | Row % | n |
|---|---|---|---|---|---|
| < 30 mins | 45.1% | 7.8% | 1.1% | 53.9% | 2,821 |
| 30 – 60 mins | 34.0% | 7.7% | 1.3% | 43.0% | 2,252 |
| 1 – 2 hrs | 2.0% | 0.5% | 0.1% | 2.6% | 137 |
| 2 – 4 hrs | 0.1% | 0.0% | 0.0% | 0.1% | 4 |
| 12 – 24 hrs | 0.4% | 0.0% | 0.0% | 0.4% | 22 |
| **Col Total** | **81.6%** | **16.0%** | **2.4%** | **100.0%** | **5,236** |

---

### Cohort 31 — WH=Early | Dispatch=Early | Delivery=Early (n=4,035 | 4.2% of egregious)

**WH Earliness Magnitude**

| Bucket | Count | % of Cohort | % of Egregious |
|---|---|---|---|
| < 30 mins | 1,424 | 35.3% | 1.5% |
| 30 – 60 mins | 2,282 | 56.6% | 2.4% |
| 1 – 2 hrs | 212 | 5.3% | 0.2% |
| 12 – 24 hrs | 94 | 2.3% | 0.1% |
| > 24 hrs | 20 | 0.5% | 0.0% |
| **Total** | **4,035** | **100.0%** | **4.2%** |

**WH Bucket × Dispatch Days Early × Delivery TAT**

| WH Bucket | Dispatch | TAT 0d | TAT 1d early | TAT 2d early | TAT 3d early | TAT 4d+ early | Row % | n |
|---|---|---|---|---|---|---|---|---|
| < 30 mins | 1d early | 0.0% | 23.9% | 8.1% | 1.6% | 0.2% | 33.8% | 1,363 |
| | 2d early | 1.0% | 0.4% | 0.1% | 0.0% | 0.0% | 1.5% | 61 |
| 30 – 60 mins | 1d early | 0.0% | 40.4% | 11.2% | 2.4% | 0.3% | 54.3% | 2,193 |
| | 2d early | 1.3% | 0.8% | 0.1% | 0.0% | 0.0% | 2.2% | 87 |
| 1 – 2 hrs | 1d early | 0.0% | 3.9% | 1.1% | 0.1% | 0.0% | 5.2% | 209 |
| | 2d early | 0.1% | 0.0% | 0.0% | 0.0% | 0.0% | 0.1% | 3 |
| 12 – 24 hrs | 1d early | 0.0% | 1.7% | 0.5% | 0.0% | 0.0% | 2.2% | 89 |
| | 2d early | 0.1% | 0.0% | 0.0% | 0.0% | 0.0% | 0.1% | 5 |
| > 24 hrs | 2d+ early | 0.3% | 0.1% | 0.0% | 0.0% | 0.0% | 0.5% | 19 |
| **Col Total** | | **2.8%** | **71.2%** | **21.2%** | **4.2%** | **0.5%** | **100.0%** | **4,035** |

---

### Cohort 32 — WH=Early | Dispatch=On-Time | Delivery=Late (n=2,445 | 2.5% of egregious)

**WH Earliness Magnitude**

| Bucket | Count | % of Cohort | % of Egregious |
|---|---|---|---|
| < 30 mins | 1,382 | 56.5% | 1.4% |
| 30 – 60 mins | 958 | 39.2% | 1.0% |
| 1 – 2 hrs | 80 | 3.3% | 0.1% |
| 2 – 4 hrs | 4 | 0.2% | 0.0% |
| 12 – 24 hrs | 21 | 0.9% | 0.0% |
| **Total** | **2,445** | **100.0%** | **2.5%** |

**WH Bucket × Delivery TAT (dispatch on-time — fixed)**

| WH Bucket | TAT 2d late | TAT 3d+ late | Row % | n |
|---|---|---|---|---|
| < 30 mins | 34.8% | 21.8% | 56.5% | 1,382 |
| 30 – 60 mins | 23.6% | 15.6% | 39.2% | 958 |
| 1 – 2 hrs | 2.0% | 1.3% | 3.3% | 80 |
| 2 – 4 hrs | 0.0% | 0.2% | 0.2% | 4 |
| 12 – 24 hrs | 0.5% | 0.3% | 0.9% | 21 |
| **Col Total** | **60.8%** | **39.2%** | **100.0%** | **2,445** |

---

### Cohort 33 — WH=Late | Dispatch=Early | Delivery=Early (n=1,707 | 1.8% of egregious)

**WH Lateness Magnitude**

| Bucket | Count | % of Cohort | % of Egregious |
|---|---|---|---|
| < 30 mins | 594 | 34.8% | 0.6% |
| 30 – 60 mins | 308 | 18.0% | 0.3% |
| 1 – 2 hrs | 315 | 18.5% | 0.3% |
| 2 – 4 hrs | 261 | 15.3% | 0.3% |
| 4 – 8 hrs | 106 | 6.2% | 0.1% |
| 8 – 12 hrs | 12 | 0.7% | 0.0% |
| 12 – 24 hrs | 111 | 6.5% | 0.1% |
| **Total** | **1,707** | **100.0%** | **1.8%** |

**WH Bucket × Dispatch Days Early × Delivery TAT**

| WH Bucket | Dispatch | TAT 0d | TAT 1d early | TAT 2d early | TAT 3d early | TAT 4d+ early | Row % | n |
|---|---|---|---|---|---|---|---|---|
| < 30 mins | 1d early | 0.0% | 22.7% | 8.2% | 1.9% | 0.2% | 33.0% | 564 |
| | 2d early | 1.1% | 0.5% | 0.1% | 0.0% | 0.0% | 1.8% | 30 |
| 30 – 60 mins | 1d early | 0.0% | 11.2% | 4.6% | 1.1% | 0.1% | 17.1% | 292 |
| | 2d early | 0.6% | 0.3% | 0.0% | 0.0% | 0.0% | 0.9% | 16 |
| 1 – 2 hrs | 1d early | 0.0% | 11.8% | 4.2% | 1.1% | 0.4% | 17.5% | 299 |
| | 2d early | 0.6% | 0.2% | 0.1% | 0.0% | 0.0% | 0.9% | 16 |
| 2 – 4 hrs | 1d early | 0.0% | 9.8% | 4.2% | 0.9% | 0.1% | 14.9% | 255 |
| | 2d early | 0.2% | 0.2% | 0.0% | 0.0% | 0.0% | 0.4% | 6 |
| 4 – 8 hrs | 1d early | 0.0% | 4.4% | 1.2% | 0.2% | 0.1% | 5.9% | 101 |
| | 2d early | 0.3% | 0.0% | 0.0% | 0.0% | 0.0% | 0.3% | 5 |
| 8 – 12 hrs | 1d early | 0.0% | 0.6% | 0.0% | 0.1% | 0.0% | 0.7% | 12 |
| 12 – 24 hrs | 1d early | 0.0% | 5.2% | 1.1% | 0.2% | 0.0% | 6.5% | 111 |
| **Col Total** | | **2.9%** | **66.9%** | **23.8%** | **5.6%** | **0.9%** | **100.0%** | **1,707** |

---

## #23 — Digitised vs Shipping vs Actual TAT Distribution and Deviation (Non-SDD Inventory Egregious Superset)

**Request:** For the Non-SDD Inventory egregious superset (n=57,688), compare raw distributions of digitised TAT promise (`digitised_delivery_tat_mins` converted to days), shipping TAT promise (`shipping_delivery_promise` in days), and actual courier TAT (`delivery_attempt_date − pickup_date`); and compute the deviation (promised − actual) for both promise fields.

### Raw TAT distribution

| TAT days | Digitised | Dig % | Shipping | Ship % | Actual | Act % |
|----------|-----------|-------|----------|--------|--------|-------|
| 0d or less | 52 | 0.1% | 1 | 0.0% | 660 | 1.1% |
| 1d | 6,279 | 10.9% | 7,510 | 13.0% | 10,012 | 17.4% |
| 2d | 8,289 | 14.4% | 12,826 | 22.2% | 19,753 | 34.2% |
| 3d | 13,441 | 23.3% | 16,664 | 28.9% | 10,338 | 17.9% |
| 4d | 17,575 | 30.5% | 11,073 | 19.2% | 5,912 | 10.2% |
| 5d | 10,608 | 18.4% | 5,180 | 9.0% | 4,037 | 7.0% |
| 6d | 1,285 | 2.2% | 2,022 | 3.5% | 2,770 | 4.8% |
| 7d+ | 159 | 0.3% | 2,412 | 4.2% | 4,206 | 7.3% |
| **Total** | **57,688** | **100.0%** | **57,688** | **100.0%** | **57,688** | **100.0%** |

Digitised peaks at 4d (30.5%), shipping peaks at 3d (28.9%), actual peaks at 2d (34.2%). Both promises are right-shifted by ~1–2 days vs reality.

### TAT deviation (promised − actual)

Positive = courier faster than promised (early for customer). Negative = courier slower (late for customer).

| Deviation | Digitised | Dig % | Shipping | Ship % |
|-----------|-----------|-------|----------|--------|
| Early 3d+ | 5,683 | 9.9% | 3,980 | 6.9% |
| Early 2d | 25,351 | 43.9% | 9,602 | 16.6% |
| Early 1d | 4,272 | 7.4% | 17,976 | 31.2% |
| On-Time | 1,770 | 3.1% | 9,107 | 15.8% |
| Late 1d | 3,341 | 5.8% | 4,186 | 7.3% |
| Late 2d | 10,004 | 17.3% | 6,853 | 11.9% |
| Late 3d+ | 7,267 | 12.6% | 5,984 | 10.4% |
| **Total Early** | **35,306** | **61.2%** | **31,558** | **54.7%** |
| **On-Time** | **1,770** | **3.1%** | **9,107** | **15.8%** |
| **Total Late** | **20,612** | **35.7%** | **17,023** | **29.5%** |

**Key findings:**
- Digitised TAT (dominant bucket: Early 2d at 43.9%): over-estimates TAT for 61.2% of routes — the model is promising 4–5d for routes the courier completes in 2–3d. On-time rate is only 3.1%. Late tail is 35.7% (courier slower than digitised TAT for those routes).
- Shipping TAT (dominant bucket: Early 1d at 31.2%): better calibrated than digitised — on-time improves to 15.8%, and the dominant over-estimate shifts to Early 1d rather than Early 2d — but still 54.7% early. Late tail is 29.5%, nearly identical to digitised, confirming shipping does not capture slow routes any better.
- Both promises are directionally biased upward (over-estimating actual TAT for the majority), but neither captures the ~30% late tail — indicating high variance in actual courier performance that neither model accounts for.

---

## #24 — Hypothesis 1: SDD State Change as Driver of TAT Deviation (Non-SDD Inventory Egregious Superset)

**Request:** Test whether delivery TAT earliness/lateness in the Non-SDD Inventory egregious superset (n=57,688) is explained by an SDD state change between digitised and shipping (digitised_is_sdd ≠ shipping_is_sdd). Per TAT deviation bucket, compute % of orders with SDD state change.

TAT deviation = `(digitised_delivery_promise − digitised_dispatch_promise) − (delivery_attempt − pickup)` in days.

| Deviation | Count | SDD chg n | SDD chg % |
|-----------|-------|-----------|-----------|
| Early 5d+ | 101 | 25 | 24.8% |
| Early 4d | 670 | 153 | 22.8% |
| Early 3d | 4,920 | 436 | 8.9% |
| Early 2d | 25,355 | 520 | 2.1% |
| Early 1d | 4,298 | 146 | 3.4% |
| On-Time | 1,779 | 12 | 0.7% |
| Late 1d | 3,331 | 0 | 0.0% |
| Late 2d | 9,978 | 2 | 0.0% |
| Late 3d | 3,774 | 5 | 0.1% |
| Late 4d | 1,694 | 3 | 0.2% |
| Late 5d | 816 | 0 | 0.0% |
| Late 6d+ | 972 | 2 | 0.2% |
| **Total** | **57,688** | **1,304** | **2.3%** |

**Verdict: Hypothesis rejected.** Only 2.3% of orders overall had an SDD state change. Late buckets are 0.0–0.2% — no signal. Early extreme tail (Early 4d+: 23–25%) shows minor signal, but the dominant Early 2d bucket (44% of superset) is only 2.1%. SDD rerouting is not a meaningful driver of TAT miscalibration.

---

## #25 — Hypothesis 2: Warehouse Change as Driver of TAT Deviation (Non-SDD Inventory Egregious Superset)

**Request:** Test whether delivery TAT earliness/lateness in the Non-SDD Inventory egregious superset (n=57,688) is explained by a warehouse change between digitised and shipping (digitised_wh_id ≠ shipping_warehouse). Per TAT deviation bucket, compute % of orders with warehouse change.

| Deviation | Count | WH chg n | WH chg % |
|-----------|-------|----------|----------|
| Early 5d+ | 101 | 46 | 45.5% |
| Early 4d | 670 | 354 | 52.8% |
| Early 3d | 4,920 | 1,337 | 27.2% |
| Early 2d | 25,355 | 2,294 | 9.0% |
| Early 1d | 4,298 | 359 | 8.4% |
| On-Time | 1,779 | 40 | 2.2% |
| Late 1d | 3,331 | 124 | 3.7% |
| Late 2d | 9,978 | 365 | 3.7% |
| Late 3d | 3,774 | 142 | 3.8% |
| Late 4d | 1,694 | 54 | 3.2% |
| Late 5d | 816 | 23 | 2.8% |
| Late 6d+ | 972 | 23 | 2.4% |
| **Total** | **57,688** | **5,161** | **8.9%** |

**Verdict: Hypothesis partially interesting in the early tail, rejected everywhere else.** Late buckets are flat at 2.4–3.8% — no signal. Early extreme tail (Early 4d+: 45–53%) shows meaningful signal — warehouse rerouting to a closer WH likely compresses both WH processing and courier TAT. However the dominant Early 2d bucket is only 9.0%; 91% of those 25,355 orders are same-warehouse throughout and still run 2d faster than promised. WH change is more explanatory than SDD change (8.9% vs 2.3% overall) but explains only a small fraction of the bulk miscalibration.

---

## #26 — Hypothesis 3: Courier Change as Driver of TAT Deviation (Non-SDD Inventory Egregious Superset)

**Request:** Test whether delivery TAT earliness/lateness in the Non-SDD Inventory egregious superset (n=57,688) is explained by a courier change between digitised and shipping (digitised_delivery_partner ≠ shipping_delivery_partner). Per TAT deviation bucket, compute % of orders with courier change.

| Deviation | Count | Courier chg n | Courier chg % |
|-----------|-------|--------------|---------------|
| Early 5d+ | 101 | 44 | 43.6% |
| Early 4d | 670 | 226 | 33.7% |
| Early 3d | 4,920 | 1,752 | 35.6% |
| Early 2d | 25,355 | 5,406 | 21.3% |
| Early 1d | 4,298 | 1,367 | 31.8% |
| On-Time | 1,779 | 391 | 22.0% |
| Late 1d | 3,331 | 1,328 | 39.9% |
| Late 2d | 9,978 | 3,521 | 35.3% |
| Late 3d | 3,774 | 1,624 | 43.0% |
| Late 4d | 1,694 | 732 | 43.2% |
| Late 5d | 816 | 342 | 41.9% |
| Late 6d+ | 972 | 427 | 43.9% |
| **Total** | **57,688** | **17,160** | **29.7%** |

**Verdict: Hypothesis partially supported — most nuanced of the three.** Late buckets consistently elevated at 35–44% vs on-time baseline of 22% (~15–20pp lift), suggesting courier rerouting is a real contributor to late TAT. The dominant Early 2d bucket (44% of superset) sits at 21.3% — essentially at on-time baseline — meaning courier change is not driving the bulk of early TAT miscalibration. Overall 29.7% of orders had a courier change, far higher than SDD (2.3%) or WH (8.9%) changes, indicating courier rerouting is a common event in this superset.

---

## #27 — Hypothesis 4: Promise Change (Digitised vs Shipping TAT) as Driver of TAT Deviation (Non-SDD Inventory Egregious Superset)

**Request:** Test whether delivery TAT earliness/lateness in the Non-SDD Inventory egregious superset (n=57,688) is explained by a promise change between digitised and shipping, defined as `DATE(digitised_delivery_promise) − DATE(digitised_dispatch_promise) ≠ shipping_delivery_promise`. Per TAT deviation bucket, compute % of orders where the TAT promise changed.

| Deviation | Count | Promise chg n | Promise chg % |
|-----------|-------|--------------|---------------|
| Early 5d+ | 101 | 98 | 97.0% |
| Early 4d | 670 | 611 | 91.2% |
| Early 3d | 4,920 | 3,966 | 80.6% |
| Early 2d | 25,355 | 18,146 | 71.6% |
| Early 1d | 4,298 | 1,879 | 43.7% |
| On-Time | 1,779 | 402 | 22.6% |
| Late 1d | 3,331 | 1,335 | 40.1% |
| Late 2d | 9,978 | 4,069 | 40.8% |
| Late 3d | 3,774 | 1,794 | 47.5% |
| Late 4d | 1,694 | 788 | 46.5% |
| Late 5d | 816 | 407 | 49.9% |
| Late 6d+ | 972 | 487 | 50.1% |
| **Total** | **57,688** | **33,982** | **58.9%** |

**Verdict: Strongly supported for the early side — strongest hypothesis of the four.** Clear monotonic relationship on the early side: 43.7% → 71.6% → 80.6% → 91.2% → 97.0% as deviation increases from Early 1d to Early 5d+. Dominant Early 2d bucket at 71.6% is 49pp above the on-time baseline of 22.6%. Mechanism: shipping recalibrates TAT downward → courier fulfills the shorter shipping promise → egregiously early vs original digitised promise. Key implication: if digitised TAT were calibrated to what shipping ends up promising, ~71.6% of the dominant Early 2d cohort would not be egregious. Late side elevated but flat at 40–50% (~20pp lift over baseline) with no monotonic pattern — promise extension at shipping correlates with late delivery but is not the sole driver.

---

## #28 — Hypotheses 5–8: Promise Change × Courier Change 2×2 Cross-Tab Per TAT Deviation Bucket

**Request:** For the Non-SDD Inventory egregious superset (n=52,788 with non-NULL shipping promise), compute a 2×2 cross-tab of promise change (yes/no) × courier change (yes/no) per TAT deviation bucket.
- H5: Promise Changed AND Courier Changed
- H6: Promise Unchanged AND Courier Changed
- H7: Promise Unchanged AND Courier Unchanged
- H8: Promise Changed AND Courier Unchanged

Promise changed = `DATE(digitised_delivery_promise) − DATE(digitised_dispatch_promise) ≠ shipping_delivery_promise`.
Courier changed = `digitised_delivery_partner ≠ shipping_delivery_partner`.

| Deviation | Count | H5: Prom✓ Cour✓ | H6: Prom✗ Cour✓ | H7: Prom✗ Cour✗ | H8: Prom✓ Cour✗ |
|-----------|-------|-----------------|-----------------|-----------------|-----------------|
| Early 5d+ | 101 | 43.6% | 0.0% | 3.0% | 20.8% |
| Early 4d | 670 | 30.1% | 3.6% | 4.8% | 25.5% |
| Early 3d | 4,920 | 27.9% | 7.7% | 11.3% | 34.1% |
| Early 2d | 25,355 | 15.6% | 5.7% | 21.9% | 48.8% |
| Early 1d | 4,298 | 16.7% | 15.1% | 37.5% | 20.8% |
| On-Time | 1,779 | 13.4% | 8.5% | 65.7% | 7.6% |
| Late 1d | 3,331 | 28.9% | 10.9% | 46.4% | 8.3% |
| Late 2d | 9,978 | 28.3% | 7.0% | 50.2% | 9.3% |
| Late 3d | 3,774 | 35.5% | 7.6% | 43.1% | 8.2% |
| Late 4d | 1,694 | 34.9% | 8.3% | 43.6% | 7.7% |
| Late 5d | 816 | 35.2% | 6.7% | 40.1% | 11.0% |
| Late 6d+ | 972 | 36.0% | 7.9% | 38.8% | 9.4% |
| **Total** | **52,788** | **24.4%** | **8.1%** | **35.1%** | **32.4%** |

**H8 (Promise changed, courier unchanged)** is the primary driver of Early 2d at 48.8% — nearly half the dominant cohort. Mechanism: digitised over-promises TAT, shipping corrects it downward, same courier fulfills the shorter shipping promise → egregiously early vs digitised. Signal fades on the late side (8–11%). Fix is at digitised promise calibration.

**H7 (Nothing changed)** dominates On-Time (65.7%) and Late 1d–2d (46–50%). For late orders this is the hardest failure mode — no structural change, just courier underperformance vs promise. Requires better TAT estimation at digitised/shipping.

**H5 (Both changed)** ramps from 15.6% at Early 2d to 28–36% in the Late 3d+ tail. Compounding disruption from simultaneous promise and courier change drives the most severe late deliveries. Also elevated in extreme early tail (27–44% in Early 3d+).

**H6 (Courier changed, promise unchanged)** is flat at 7–15% with no directional signal — minor contributor in either direction.

---

## #29 — H3–H8 on Inventory-Stable Subset (shipping_is_inventory=TRUE)

**Request:** Rerun H3–H8 on Non-SDD Inventory egregious orders where shipping_is_inventory=TRUE (n=57,482), to test whether controlling for inventory state change between digitised and shipping alters the hypothesis findings.

Inventory state change is extremely rare: only 206 orders excluded from the full superset of 57,688 (0.4%).

### H3 — Courier change

| Deviation | Count | Cour chg n | Cour chg % |
|-----------|-------|-----------|-----------|
| Early 5d+ | 101 | 44 | 43.6% |
| Early 4d | 670 | 226 | 33.7% |
| Early 3d | 4,909 | 1,746 | 35.6% |
| Early 2d | 25,305 | 5,391 | 21.3% |
| Early 1d | 4,290 | 1,363 | 31.8% |
| On-Time | 1,752 | 383 | 21.9% |
| Late 1d | 3,283 | 1,309 | 39.9% |
| Late 2d | 9,936 | 3,501 | 35.2% |
| Late 3d | 3,764 | 1,619 | 43.0% |
| Late 4d | 1,689 | 730 | 43.2% |
| Late 5d | 814 | 342 | 42.0% |
| Late 6d+ | 969 | 424 | 43.8% |
| **Total** | **57,482** | **17,078** | **29.7%** |

### H4 — Promise change

| Deviation | Count | Prom chg n | Prom chg % |
|-----------|-------|-----------|-----------|
| Early 5d+ | 101 | 98 | 97.0% |
| Early 4d | 670 | 611 | 91.2% |
| Early 3d | 4,909 | 3,958 | 80.6% |
| Early 2d | 25,305 | 18,110 | 71.6% |
| Early 1d | 4,290 | 1,874 | 43.7% |
| On-Time | 1,752 | 395 | 22.5% |
| Late 1d | 3,283 | 1,313 | 40.0% |
| Late 2d | 9,936 | 4,045 | 40.7% |
| Late 3d | 3,764 | 1,790 | 47.6% |
| Late 4d | 1,689 | 787 | 46.6% |
| Late 5d | 814 | 406 | 49.9% |
| Late 6d+ | 969 | 485 | 50.1% |
| **Total** | **57,482** | **33,872** | **58.9%** |

### H5–H8 — Promise change × Courier change 2×2

| Deviation | Count | H5: P✓C✓ | H6: P✗C✓ | H7: P✗C✗ | H8: P✓C✗ |
|-----------|-------|----------|----------|----------|----------|
| Early 5d+ | 101 | 43.6% | 0.0% | 3.0% | 53.5% |
| Early 4d | 670 | 30.1% | 3.6% | 5.2% | 61.0% |
| Early 3d | 4,909 | 27.9% | 7.7% | 11.7% | 52.8% |
| Early 2d | 25,305 | 15.6% | 5.7% | 22.7% | 56.0% |
| Early 1d | 4,290 | 16.7% | 15.1% | 41.2% | 27.0% |
| On-Time | 1,752 | 13.4% | 8.4% | 69.0% | 9.1% |
| Late 1d | 3,283 | 28.9% | 11.0% | 49.0% | 11.1% |
| Late 2d | 9,936 | 28.2% | 7.0% | 52.3% | 12.5% |
| Late 3d | 3,764 | 35.5% | 7.5% | 44.9% | 12.1% |
| Late 4d | 1,689 | 35.0% | 8.2% | 45.2% | 11.6% |
| Late 5d | 814 | 35.3% | 6.8% | 43.4% | 14.6% |
| Late 6d+ | 969 | 35.9% | 7.8% | 42.1% | 14.1% |
| **Total** | **57,482** | **22.3%** | **7.4%** | **33.7%** | **36.6%** |

**Verdict: All H3–H8 findings confirmed with higher confidence.** H4 and H3 patterns are completely unchanged (71.6% and 29.7%). H8 strengthens in the early buckets — Early 2d rises from 48.8% to 56.0%, Early 4d from 25.5% to 61.0% — because the NULL-shipping-promise orders removed from the cross-tab denominator were disproportionately in the small inventory-change group. The structural problem is squarely in the TAT promise model, not operational reclassifications.

---

## #30 — Consolidated H1–H8 Table (Inventory-Stable Subset)

**Request:** Produce a single consolidated table with all eight hypotheses side-by-side per TAT deviation bucket on the inventory-stable Non-SDD Inventory egregious subset (n=57,482). H1–H4 denominator = bucket Count. H5–H8 denominator = orders with non-NULL shipping promise (= 57,482, all orders in this subset).

| Deviation | Count | H1:SDD | H2:WH | H3:Cour | H4:Prom | H5:P✓C✓ | H6:P✗C✓ | H7:P✗C✗ | H8:P✓C✗ |
|-----------|-------|--------|-------|---------|---------|---------|---------|---------|---------|
| Early 5d+ | 101 | 24.8% | 45.5% | 43.6% | 97.0% | 43.6% | 0.0% | 3.0% | 53.5% |
| Early 4d | 670 | 22.8% | 52.8% | 33.7% | 91.2% | 30.1% | 3.6% | 5.2% | 61.0% |
| Early 3d | 4,909 | 8.9% | 27.2% | 35.6% | 80.6% | 27.9% | 7.7% | 11.7% | 52.8% |
| Early 2d | 25,305 | 2.1% | 9.0% | 21.3% | 71.6% | 15.6% | 5.7% | 22.7% | 56.0% |
| Early 1d | 4,290 | 3.4% | 8.3% | 31.8% | 43.7% | 16.7% | 15.1% | 41.2% | 27.0% |
| On-Time | 1,752 | 0.7% | 2.1% | 21.9% | 22.5% | 13.4% | 8.4% | 69.0% | 9.1% |
| Late 1d | 3,283 | 0.0% | 3.5% | 39.9% | 40.0% | 28.9% | 11.0% | 49.0% | 11.1% |
| Late 2d | 9,936 | 0.0% | 3.5% | 35.2% | 40.7% | 28.2% | 7.0% | 52.3% | 12.5% |
| Late 3d | 3,764 | 0.1% | 3.7% | 43.0% | 47.6% | 35.5% | 7.5% | 44.9% | 12.1% |
| Late 4d | 1,689 | 0.2% | 3.2% | 43.2% | 46.6% | 35.0% | 8.2% | 45.2% | 11.6% |
| Late 5d | 814 | 0.0% | 2.8% | 42.0% | 49.9% | 35.3% | 6.8% | 43.4% | 14.6% |
| Late 6d+ | 969 | 0.2% | 2.4% | 43.8% | 50.1% | 35.9% | 7.8% | 42.1% | 14.1% |
| **Total** | **57,482** | **2.3%** | **8.9%** | **29.7%** | **58.9%** | **22.3%** | **7.4%** | **33.7%** | **36.6%** |

**Three failure modes emerge cleanly:**

1. **Early 2d–5d+ (the bulk of early egregious):** H4 (71–97%) and H8 (53–61%) dominate. Promise shortened at shipping, same courier delivers to the shorter promise → egregiously early vs digitised. H1 and H2 near zero — SDD and WH changes uninvolved.

2. **Late 1d–2d:** H7 dominates (49–52%) — nothing changed, pure courier underperformance vs unchanged promise. H5 elevated at 28% — when both change, still tends to produce late outcomes.

3. **Late 3d+ (severe lates):** H5 (~35%) and H7 (~43–45%) split roughly equally. Severe late deliveries come either from compounding disruption (both promise and courier change, courier still fails) or from stubborn underperformance with no changes at all. H1 and H2 remain near zero throughout the entire late side.

---

## #31 — Hypothesis 9: Payment Pending as Driver of WH Deviation (Non-SDD Inventory Egregious Superset)

**Request:** For the Non-SDD Inventory egregious superset (n=57,688), test whether WH earliness/lateness is explained by orders entering payment pending state (payment_pending_ts non-NULL). Per WH deviation bucket, compute % of orders with a payment pending event.

WH deviation = `digitised_wh_promise − awb_sticker_printed_ts` in minutes (positive = early, negative = late).

| WH Deviation | Count | Pay Pend n | Pay Pend % |
|---|---|---|---|
| Early > 24 hrs | 21 | 6 | 28.6% |
| Early 12 – 24 hrs | 156 | 4 | 2.6% |
| Early 1 – 2 hrs | 443 | 9 | 2.0% |
| Early 30 – 60 mins | 5,813 | 87 | 1.5% |
| Early < 30 mins | 6,032 | 147 | 2.4% |
| On-Time | 1 | 0 | 0.0% |
| Late < 30 mins | 4,138 | 96 | 2.3% |
| Late 30 – 60 mins | 3,291 | 86 | 2.6% |
| Late 1 – 2 hrs | 5,352 | 178 | 3.3% |
| Late 2 – 4 hrs | 7,358 | 268 | 3.6% |
| Late 4 – 8 hrs | 7,815 | 416 | 5.3% |
| Late 8 – 12 hrs | 1,340 | 161 | 12.0% |
| Late 12 – 24 hrs | 12,277 | 1,550 | 12.6% |
| **Late > 24 hrs** | **3,640** | **2,330** | **64.0%** |
| **Total** | **57,688** | **5,342** | **9.3%** |

*(Early 2–12 hrs: 11 orders, omitted — too small to be meaningful)*

**Verdict: Hypothesis strongly supported for the late tail.** Early side is flat at 1.5–2.6% — no signal (payment pending can only delay, not accelerate). Late side shows clear monotonic escalation: Late <30 mins 2.3% → Late 4–8 hrs 5.3% → Late 8–12 hrs 12.0% → Late 12–24 hrs 12.6% → **Late >24 hrs 64.0%**. Two in every three orders in the most extreme late WH bucket had a payment pending event. Mechanism: payment not confirmed → warehouse holds order → AWB printed only after payment clears → WH appears egregiously late vs digitised promise which assumed no payment delay. Overall 9.3% of superset had a payment pending event, concentrated almost entirely in the severe late WH tail.

---

## #32 — Hypothesis 10: Inventory→Non-Inventory Switch as Driver of WH Deviation (Non-SDD Inventory Egregious Superset)

**Request:** For the Non-SDD Inventory egregious superset (n=57,688), test whether WH earliness/lateness is explained by an inventory→non-inventory switch between digitised and shipping (digitised_is_inventory=TRUE, shipping_is_inventory=FALSE). Per WH deviation bucket, compute % of orders with this switch.

| WH Deviation | Count | Inv→NonInv n | Inv→NonInv % |
|---|---|---|---|
| Early > 24 hrs | 21 | 1 | 4.8% |
| Early 12 – 24 hrs | 156 | 0 | 0.0% |
| Early 1 – 2 hrs | 443 | 0 | 0.0% |
| Early 30 – 60 mins | 5,813 | 0 | 0.0% |
| Early < 30 mins | 6,032 | 9 | 0.1% |
| On-Time | 1 | 0 | 0.0% |
| Late < 30 mins | 4,138 | 1 | 0.0% |
| Late 30 – 60 mins | 3,291 | 6 | 0.2% |
| Late 1 – 2 hrs | 5,352 | 8 | 0.1% |
| Late 2 – 4 hrs | 7,358 | 17 | 0.2% |
| Late 4 – 8 hrs | 7,815 | 23 | 0.3% |
| Late 8 – 12 hrs | 1,340 | 5 | 0.4% |
| Late 12 – 24 hrs | 12,277 | 44 | 0.4% |
| Late > 24 hrs | 3,640 | 75 | 2.1% |
| **Total** | **57,688** | **189** | **0.3%** |

**Verdict: Hypothesis rejected.** Only 189 orders (0.3%) switched inventory status at shipping. Even the most extreme late bucket tops out at 2.1%. No signal in either direction. WH deviation has nothing to do with inventory reclassification. H9 (payment pending, 64% at Late >24 hrs) is the dominant explanation for extreme WH lateness; H10 is not.

---

## #33 — Hypothesis 11: Doctor Leg as Driver of WH Deviation (Non-SDD Inventory Egregious Superset)

**Request:** For the Non-SDD Inventory egregious superset (n=57,688), test whether WH earliness/lateness is explained by the doctor leg (digitised_dr_promise vs actual_doctor_call_time at timestamp level). Per WH deviation bucket, compute % early / on-time / late on the doctor leg.

| WH Deviation | Count | Dr Early | Dr On-Time | Dr Late |
|---|---|---|---|---|
| Early > 24 hrs | 21 | 100.0% | 0.0% | 0.0% |
| Early 12 – 24 hrs | 156 | 68.6% | 0.0% | 31.4% |
| Early 1 – 2 hrs | 454 | 95.2% | 0.0% | 4.8% |
| Early 30 – 60 mins | 5,813 | 80.5% | 0.1% | 19.4% |
| Early < 30 mins | 6,032 | 74.0% | 0.1% | 25.9% |
| On-Time | 1 | 100.0% | 0.0% | 0.0% |
| Late < 30 mins | 4,138 | 76.2% | 0.0% | 23.7% |
| Late 30 – 60 mins | 3,291 | 78.8% | 0.0% | 21.2% |
| Late 1 – 2 hrs | 5,352 | 79.3% | 0.1% | 20.6% |
| Late 2 – 4 hrs | 7,358 | 77.3% | 0.0% | 22.6% |
| Late 4 – 8 hrs | 7,815 | 72.1% | 0.0% | 27.8% |
| Late 8 – 12 hrs | 1,340 | 69.4% | 0.1% | 30.5% |
| Late 12 – 24 hrs | 12,277 | 80.8% | 0.1% | 19.1% |
| Late > 24 hrs | 3,640 | 81.8% | 0.1% | 18.2% |
| **Total** | **57,688** | **77.7%** | **0.1%** | **22.2%** |

**Verdict: Hypothesis rejected.** Doctor late % is flat at ~20–30% across all WH buckets with no monotonic pattern. The most extreme WH late buckets are actually below the overall average: Late >24 hrs = 18.2%, Late 12–24 hrs = 19.1% vs 22.2% overall. A driver hypothesis would require escalating doctor lateness as WH deviation worsens — the data shows the opposite. Doctor call timing is background noise, not a causal factor in WH deviation.

---

## #34 — Hypothesis 12: Doctor Confirmation as Driver of WH Deviation (Non-SDD Inventory Egregious Superset)

**Request:** Same as H11 but using doctor confirmation (dr_confirm_ts) instead of actual_doctor_call_time. For the Non-SDD Inventory egregious superset (n=57,688), per WH deviation bucket, compute % of orders where doctor confirmation was early, on-time, or late vs digitised_dr_promise.

| WH Deviation | Count | Dr Early | Dr On-Time | Dr Late |
|---|---|---|---|---|
| Early > 24 hrs | 21 | 100.0% | 0.0% | 0.0% |
| Early 12 – 24 hrs | 156 | 67.9% | 1.3% | 30.8% |
| Early 1 – 2 hrs | 454 | 94.9% | 0.0% | 5.1% |
| Early 30 – 60 mins | 5,813 | 80.2% | 0.7% | 19.1% |
| Early < 30 mins | 6,032 | 65.6% | 1.1% | 33.3% |
| On-Time | 1 | 100.0% | 0.0% | 0.0% |
| Late < 30 mins | 4,138 | 59.4% | 0.7% | 39.9% |
| Late 30 – 60 mins | 3,291 | 55.4% | 1.0% | 43.5% |
| Late 1 – 2 hrs | 5,352 | 56.1% | 1.1% | 42.8% |
| Late 2 – 4 hrs | 7,358 | 51.5% | 1.0% | 47.5% |
| Late 4 – 8 hrs | 7,815 | 49.3% | 1.2% | 49.5% |
| Late 8 – 12 hrs | 1,340 | 50.6% | 1.0% | 48.4% |
| Late 12 – 24 hrs | 12,277 | 57.6% | 0.8% | 41.6% |
| Late > 24 hrs | 3,640 | 44.5% | 0.4% | 55.2% |
| **Total** | **57,688** | **58.0%** | **0.9%** | **41.1%** |

**Verdict: Hypothesis supported.** Unlike H11 (actual doctor call), doctor confirmation shows a clear signal. Early WH buckets: 0–33% late confirmation. Late WH buckets: 40–55% late confirmation, with visible gradient peaking at Late 4–8 hrs (49.5%) and Late >24 hrs (55.2%). Mechanism: `dr_confirm_ts` is what triggers WH to start processing — a late confirmation holds the warehouse even if the doctor call itself was on time. The doctor call (H11) and confirmation (H12) are measuring different pipeline events. Note: Late >24 hrs overlap with H9 (payment pending 64%) is likely non-independent — payment pending likely delays the doctor confirmation as well.

---

## #35 — H11 and H12 re-analysis: magnitude of doctor deviation per WH bucket

**Request:** Re-examine H11 (actual_doctor_call_time) and H12 (dr_confirm_ts) by showing the magnitude distribution of doctor deviation (not just early/on-time/late binary) per WH deviation bucket, to allow confident conclusions about whether the doctor leg drives WH lateness.

**Doctor deviation sign convention:** positive = doctor acted before digitised_dr_promise (early), negative = after (late). Units: minutes.

**Buckets for doctor deviation:** Early >24 hrs / Early 12–24 hrs / Early 1–12 hrs / Early 5–60 mins / Early <5 mins / On-Time / Late <5 mins / Late 5–60 mins / Late 1–4 hrs / Late 4–12 hrs / Late 12–24 hrs / Late >24 hrs.

---

### H12 magnitude: dr_confirm_ts vs digitised_dr_promise (each cell = % of WH bucket row)

| WH Dev | n | E>24h | E12-24h | E1-12h | E5-60m | E<5m | On-Time | L<5m | L5-60m | L1-4h | L4-12h | L12-24h | L>24h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Early > 24 hrs | 21 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Early 12 – 24 hrs | 156 | 0.0% | 1.9% | 0.0% | 47.4% | 18.6% | 1.3% | 25.0% | 5.8% | 0.0% | 0.0% | 0.0% | 0.0% |
| Early 1 – 2 hrs | 454 | 0.2% | 0.0% | 1.1% | 91.2% | 2.4% | 0.0% | 3.7% | 1.3% | 0.0% | 0.0% | 0.0% | 0.0% |
| Early 30 – 60 mins | 5,813 | 0.0% | 0.0% | 0.1% | 67.3% | 12.9% | 0.7% | 16.8% | 2.2% | 0.1% | 0.0% | 0.0% | 0.0% |
| Early < 30 mins | 6,032 | 0.0% | 0.0% | 0.0% | 49.6% | 16.0% | 1.1% | 22.7% | 10.4% | 0.1% | 0.0% | 0.0% | 0.0% |
| On-Time | 1 | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Late < 30 mins | 4,138 | 0.0% | 0.0% | 0.1% | 43.4% | 15.9% | 0.7% | 19.3% | 19.6% | 1.1% | 0.0% | 0.0% | 0.0% |
| Late 30 – 60 mins | 3,291 | 0.1% | 0.0% | 0.2% | 41.8% | 13.4% | 1.0% | 17.7% | 20.9% | 4.8% | 0.0% | 0.0% | 0.0% |
| Late 1 – 2 hrs | 5,352 | 0.0% | 0.0% | 0.2% | 41.2% | 14.7% | 1.1% | 15.1% | 17.2% | 10.3% | 0.1% | 0.1% | 0.0% |
| Late 2 – 4 hrs | 7,358 | 0.0% | 0.0% | 0.3% | 37.5% | 13.6% | 1.0% | 15.1% | 16.0% | 15.1% | 1.2% | 0.2% | 0.0% |
| Late 4 – 8 hrs | 7,815 | 0.1% | 0.0% | 0.1% | 35.3% | 13.8% | 1.2% | 15.8% | 10.7% | 11.1% | 11.0% | 0.9% | 0.0% |
| Late 8 – 12 hrs | 1,340 | 0.1% | 0.0% | 0.3% | 33.2% | 17.0% | 1.0% | 18.4% | 9.3% | 4.0% | 11.3% | 5.5% | 0.0% |
| Late 12 – 24 hrs | 12,277 | 0.0% | 0.0% | 0.1% | 43.3% | 14.2% | 0.8% | 16.3% | 15.6% | 6.2% | 2.3% | 1.3% | 0.0% |
| Late > 24 hrs | 3,640 | 0.1% | 0.1% | 0.3% | 34.1% | 10.0% | 0.4% | 10.1% | 14.5% | 9.8% | 10.8% | 4.6% | 5.4% |
| **Total** | **57,688** | **0.1%** | **0.0%** | **0.1%** | **43.8%** | **14.0%** | **0.9%** | **16.6%** | **13.5%** | **6.8%** | **3.1%** | **0.8%** | **0.3%** |

---

### H11 magnitude: actual_doctor_call_time vs digitised_dr_promise (each cell = % of WH bucket row)

| WH Dev | n | E>24h | E12-24h | E1-12h | E5-60m | E<5m | On-Time | L<5m | L5-60m | L1-4h | L4-12h | L12-24h | L>24h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Early > 24 hrs | 21 | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Early 12 – 24 hrs | 156 | 0.6% | 1.3% | 2.6% | 54.5% | 9.6% | 0.0% | 30.8% | 0.6% | 0.0% | 0.0% | 0.0% | 0.0% |
| Early 1 – 2 hrs | 454 | 0.4% | 0.0% | 5.3% | 88.3% | 1.1% | 0.0% | 4.8% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Early 30 – 60 mins | 5,813 | 0.0% | 0.1% | 2.9% | 72.4% | 5.1% | 0.1% | 19.2% | 0.2% | 0.0% | 0.0% | 0.0% | 0.0% |
| Early < 30 mins | 6,032 | 0.0% | 0.2% | 3.3% | 63.6% | 6.9% | 0.1% | 25.0% | 0.9% | 0.0% | 0.0% | 0.0% | 0.0% |
| On-Time | 1 | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Late < 30 mins | 4,138 | 0.0% | 0.3% | 3.7% | 64.6% | 7.5% | 0.0% | 22.3% | 1.4% | 0.0% | 0.0% | 0.0% | 0.0% |
| Late 30 – 60 mins | 3,291 | 0.1% | 0.3% | 3.7% | 67.9% | 6.7% | 0.0% | 19.4% | 1.4% | 0.3% | 0.0% | 0.0% | 0.0% |
| Late 1 – 2 hrs | 5,352 | 0.1% | 0.3% | 4.3% | 67.3% | 7.3% | 0.1% | 17.8% | 1.4% | 1.4% | 0.0% | 0.0% | 0.0% |
| Late 2 – 4 hrs | 7,358 | 0.1% | 0.6% | 4.4% | 65.2% | 7.1% | 0.0% | 17.7% | 2.3% | 2.5% | 0.1% | 0.0% | 0.0% |
| Late 4 – 8 hrs | 7,815 | 0.1% | 0.4% | 3.0% | 62.7% | 5.9% | 0.0% | 20.8% | 2.3% | 3.7% | 1.0% | 0.1% | 0.0% |
| Late 8 – 12 hrs | 1,340 | 0.2% | 0.4% | 3.2% | 58.9% | 6.7% | 0.1% | 25.4% | 1.3% | 1.8% | 1.6% | 0.4% | 0.0% |
| Late 12 – 24 hrs | 12,277 | 0.1% | 0.1% | 3.0% | 70.9% | 6.7% | 0.1% | 17.5% | 0.9% | 0.4% | 0.1% | 0.1% | 0.0% |
| Late > 24 hrs | 3,640 | 0.9% | 0.8% | 4.9% | 69.0% | 6.2% | 0.1% | 9.7% | 2.2% | 2.4% | 1.4% | 1.1% | 1.3% |

---

### % of orders with doctor deviation ≥1 hr late — summary comparison

| WH Deviation Bucket | n | H12: confirm ≥1h late | H11: call ≥1h late |
|---|---|---|---|
| Early > 24 hrs | 21 | 0.0% | 0.0% |
| Early 12 – 24 hrs | 156 | 0.0% | 0.0% |
| Early 1 – 2 hrs | 454 | 0.0% | 0.0% |
| Early 30 – 60 mins | 5,813 | 0.1% | 0.0% |
| Early < 30 mins | 6,032 | 0.1% | 0.0% |
| On-Time | 1 | 0.0% | 0.0% |
| Late < 30 mins | 4,138 | 1.1% | 0.0% |
| Late 30 – 60 mins | 3,291 | 4.8% | 0.3% |
| Late 1 – 2 hrs | 5,352 | 10.5% | 1.4% |
| Late 2 – 4 hrs | 7,358 | 16.5% | 2.6% |
| Late 4 – 8 hrs | 7,815 | 23.0% | 4.8% |
| Late 8 – 12 hrs | 1,340 | 20.8% | 3.8% |
| Late 12 – 24 hrs | 12,277 | 9.8% | 0.6% |
| Late > 24 hrs | 3,640 | 30.6% | 6.2% |

---

**Revised verdict on H12:** The "Dr Late" signal in H12 (40–55%) was heavily padded by sub-hour lateness — confirmations arriving a few seconds or minutes after the promise — which cannot plausibly delay AWB printing by hours. When restricted to ≥1 hr late confirmation (the threshold with any mechanistic plausibility for multi-hour WH delays), a clear gradient exists from 0.1% in WH-early buckets to 30.6% in WH Late >24 hrs. H12 is a real but partial driver: approximately 1-in-3 orders in the most extreme late WH bucket have a genuinely late confirmation (≥1 hr). The other ~70% of WH Late >24 hrs orders are unexplained by doctor confirmation timing alone.

**WH Late 12–24 hrs anomaly:** Despite being the largest late WH bucket (12,277 orders), only 9.8% have ≥1 hr late confirmation — lower than the 23% in WH Late 4–8 hrs. This is consistent with H9: Late 12–24 hrs had 12.6% payment pending (high, but mostly independent of doctor timing), whereas Late 4–8 hrs had 5.3% payment pending and shows a cleaner doctor signal.

**Revised verdict on H11:** Definitively rejected even with magnitude analysis. At the ≥1 hr late threshold, the call time shows only 0–6% across all WH buckets — flat noise with no meaningful gradient. The call itself never triggered WH processing; only the confirmation does. H11 is conclusively dead.

**Overall H11/H12 conclusion:** Doctor confirmation is a real but minority driver (~20–30% of severe late WH orders have ≥1 hr late confirmation). The majority of WH lateness — especially the Late 12–24 hrs cohort (n=12,277) — is explained primarily by H9 (payment pending) and other as-yet-untested factors, not by doctor timing.

---

## #36 — WH deviation mechanism decomposition: A/B/C/X classification across all non-H10 orders

**Request:** Classify every non-H10 (shipping_is_inventory=TRUE) egregious Non-SDD Inventory order by which mechanism explains its WH deviation. For late WH orders, apply a hierarchical classification: A = doctor confirmed after WH promise; B = doctor on time but invoice created after WH promise; C = invoice on time but AWB still late; X = missing data. H9 (payment pending) retained as a separate prior-priority class for late orders.

**Classification logic (mutually exclusive, applied in order):**
- WH dev ≥ 0 → Over-padded promise (AWB before WH promise)
- WH dev < 0 + payment_pending_ts non-NULL → H9: Payment pending
- WH dev < 0 + dr_confirm_ts > wh_prom → A: Doctor confirmed after WH promise
- WH dev < 0 + invoice_create_ts > wh_prom → B: Invoice created after WH promise (doctor on time)
- WH dev < 0 + invoice_create_ts ≤ wh_prom → C: Invoice on time, AWB printing delayed
- WH dev < 0 + insufficient timestamps → X: Missing data

| WH Deviation | n | Over-padded | H9 Pmt Pend | A: Dr late | B: Inv late | C: AWB hold | X: No data | Covered |
|---|---|---|---|---|---|---|---|---|
| Early > 24 hrs | 20 | 100.0% | — | — | — | — | — | 100% |
| Early 12–24 hrs | 156 | 100.0% | — | — | — | — | — | 100% |
| Early 1–2 hrs | 454 | 100.0% | — | — | — | — | — | 100% |
| Early 30–60 mins | 5,810 | 100.0% | — | — | — | — | — | 100% |
| Early < 30 mins | 6,024 | 100.0% | — | — | — | — | — | 100% |
| On-Time | 1 | 100.0% | — | — | — | — | — | 100% |
| Late < 30 mins | 4,137 | — | 2.3% | 0.9% | 28.7% | 67.9% | 0.1% | 99.9% |
| Late 30–60 mins | 3,285 | — | 2.6% | 4.7% | 70.7% | 22.0% | 0.0% | 100% |
| Late 1–2 hrs | 5,341 | — | 3.3% | 9.9% | 80.8% | 5.9% | 0.0% | 100% |
| Late 2–4 hrs | 7,337 | — | 3.7% | 15.8% | 79.6% | 1.0% | 0.0% | 100% |
| Late 4–8 hrs | 7,791 | — | 5.3% | 21.6% | 73.0% | 0.1% | 0.0% | 100% |
| Late 8–12 hrs | 1,333 | — | 12.0% | 17.6% | 69.0% | 1.4% | 0.0% | 100% |
| Late 12–24 hrs | 12,231 | — | 12.6% | 8.4% | 78.6% | 0.4% | 0.0% | 100% |
| Late > 24 hrs | 3,562 | — | 65.0% | 13.1% | 20.1% | 1.7% | 0.0% | 100% |
| **Total** | **57,482** | **21.7%** | **8.8%** | **9.2%** | **53.2%** | **7.0%** | **0.0%** | **100%** |

**Key findings:**
1. **Early buckets (100% over-padded):** Every WH-early order is fully explained by the promise being set too conservatively. Zero exceptions.
2. **B: Invoice delay is the dominant driver of WH lateness** across all moderate-late buckets (70–81% of Late 30-60 mins through Late 12-24 hrs). All B-classified orders have dr_confirm_ts present and confirmed before the WH promise — doctor was on time, but the invoice generation pipeline fired hours late. This is a new hypothesis (H13) not yet formally tested.
3. **H9 dominates only the most extreme bucket** (Late >24 hrs: 65%) and has a gradient (2.3% → 12.6% → 65%).
4. **A (doctor late)** is a real but minority driver, peaking at Late 4–8 hrs (21.6%).
5. **C (AWB hold)** is only relevant for Late <30 mins (67.9%) — noise-level latenesses where invoice was ready but AWB printing had a minor queue delay.
6. **X = 0.0% across all buckets.** The classification is exhaustive — no unexplained orders remain.

---

## #37 — Hypothesis 15: Dispatch miscalibrated due to payment pending (Non-SDD Inventory egregious superset)

**Request:** For the Non-SDD Inventory egregious superset (n=57,688), test whether dispatch earliness/lateness is explained by orders entering payment pending state (payment_pending_ts non-NULL). dispatch_dev = DATE(digitised_dispatch_promise) − DATE(pickup_time) in days; positive = early (pickup before promise), negative = late.

| Dispatch Dev | Count | % of set | Pmt Pend | % Pmt Pend |
|---|---|---|---|---|
| Early 3d+ | 17 | 0.0% | 3 | 17.6% |
| Early 2d | 241 | 0.4% | 9 | 3.7% |
| Early 1d | 6,207 | 10.8% | 102 | 1.6% |
| On-Time | 43,416 | 75.3% | 1,913 | 4.4% |
| Late 1d | 5,240 | 9.1% | 1,975 | 37.7% |
| Late 2d | 1,786 | 3.1% | 1,218 | 68.2% |
| Late 3d | 361 | 0.6% | 96 | 26.6% |
| Late 4d+ | 420 | 0.7% | 26 | 6.2% |
| **Total** | **57,688** | **100%** | **5,342** | **9.3%** |

**Verdict: Hypothesis supported for Late 1d and Late 2d; partially for Late 3d; rejected for Late 3d+.**

Clear monotonic relationship from On-Time (4.4% baseline) through Late 1d (37.7%) to Late 2d (68.2%) — then drops sharply to 26.6% at Late 3d and 6.2% at Late 4d+.

**Mechanism:** Payment pending → WH holds order (H9) → AWB printed late → courier picks up late → dispatch is late. H15 is not independent of H9; it is the downstream cascade of the same payment pending event manifesting at the dispatch leg instead of the WH leg.

**Anomaly — Late 3d and Late 4d+:** Payment pending rate drops sharply after Late 2d (26.6% at Late 3d, 6.2% at Late 4d+). These most-extreme late dispatch buckets are small (n=361 and n=420) and appear driven by a different mechanism — likely operational holds, courier capacity failures, or stockouts — not payment flow.

---

## #38 — What drives Early 1d and Late 3d+ dispatch in the Non-SDD Inventory egregious set

**Request:** Investigate the mechanism behind Early 1d (n=6,207) and Late 3d+ (n=781) dispatch deviation buckets — separate from the H15 payment pending driver already confirmed for Late 1d–2d.

**Early 1d findings:**
- Dispatch promise hour: 51.9% afternoon (12–16h), 47.9% evening (17–20h); no late-night promises.
- AWB printed 1 full calendar day before dispatch promise: 98.7% of orders.
- Courier picked up on the same day AWB was printed: 98.7% of orders.
- Mechanism: dispatch promise built in a 1-day courier lead time ("pack today, courier tomorrow"), but couriers always collect on the day the AWB is ready — not the scheduled day. Early 1d = AWB ready 1 day early, courier collected same day.

**Late 3d+ findings:**
- WH Late >24h in 71.5% (Late 3d) → 94.5% (Late 6d+) of orders — intensifies with each bucket.
- Courier picks up same day AWB is printed in 45–81% of orders; AWB itself is printed exactly N days late = dispatch N days late.
- DOCTOR_AND_HA_CALL_REQUIRED category represents ~50% of every late bucket (Late 3d through Late 6d+) — far above its share in the general population.
- Payment pending explains only 5–27% of these orders; the dominant driver is the HA call leg not completing.
- For Late 6d+, AWB offsets range from +5d to +66d after dispatch promise — the HA call simply didn't complete for weeks in extreme cases.
- No particular courier concentration; no courier failure involved — the delay is entirely pre-AWB.
- Proposed as H16: Late 3d+ dispatch is driven by the HA call leg having no enforced SLA, causing unbounded AWB delay for DOCTOR_AND_HA_CALL_REQUIRED orders.

---

## #39 — Proof table: Early 1d dispatch mechanism — AWB offset and pickup gap cross-tab

**Request:** Produce a structured table proving the Early 1d dispatch mechanism (AWB printed 1d before dispatch promise + same-day courier pickup) vs On-Time and Late 1d for comparison.

**TABLE 1 — AWB date vs dispatch promise date** (positive = AWB before promise)

| AWB offset | Early 1d (n=6,207) | On-Time (n=43,416) | Late 1d (n=5,240) |
|---|---|---|---|
| 1d AFTER promise | 0 (0.0%) | 1 (0.0%) | 2,488 (47.5%) |
| Same day as promise | 0 (0.0%) | 40,011 (92.2%) | 2,671 (51.0%) |
| 1d before promise | 6,125 (98.7%) | 3,392 (7.8%) | 80 (1.5%) |
| 2d before promise | 81 (1.3%) | 12 (0.0%) | 1 (0.0%) |

**TABLE 2 — Pickup date vs AWB print date** (0 = same day)

| Pickup gap | Early 1d (n=6,207) | On-Time (n=43,416) | Late 1d (n=5,240) |
|---|---|---|---|
| Same day (0d) | 6,125 (98.7%) | 40,011 (92.2%) | 2,488 (47.5%) |
| +1d after AWB | 81 (1.3%) | 3,392 (7.8%) | 2,671 (51.0%) |
| +2d after AWB | 1 (0.0%) | 12 (0.0%) | 80 (1.5%) |

**TABLE 3 — Summary**

| | Early 1d | On-Time | Late 1d |
|---|---|---|---|
| AWB 1d before dispatch promise | 98.7% | 7.8% | 1.5% |
| AWB same day as dispatch promise | 0.0% | 92.2% | 51.0% |
| AWB 1d after dispatch promise | 0.0% | 0.0% | 47.5% |
| Pickup same day as AWB | 98.7% | 92.2% | 47.5% |
| Pickup 1d after AWB | 1.3% | 7.8% | 51.0% |

**Verdict:** The mechanism is proven. Courier same-day pickup behaviour is essentially constant across all three buckets (~92–99%). The ONLY differentiator is when the AWB is printed relative to the dispatch promise. Early 1d = AWB printed 1 day early, courier collects same day. On-Time = AWB printed on promise day, courier collects same day. Late 1d = AWB printed same day as promise but courier collects next day (51%) OR AWB printed 1 day late and courier collects same day (47.5%). The dispatch deviation is a function of AWB timing alone — not courier behaviour.

---

## #40 — H16: Late 3d+ dispatch driven by DOCTOR_AND_HA_CALL_REQUIRED / HA call with no SLA

**Request:** Quantify the % of DOCTOR_AND_HA_CALL_REQUIRED orders per dispatch deviation bucket to test whether HA call (no SLA) drives Late 3d+ dispatch, analogous to how H9 (payment pending) was tested.

**Order category breakdown by dispatch bucket** (Non-SDD Inventory egregious superset, n=57,688, 0 missing dispatch/pickup):

| Dispatch Bucket | N | Dr+HA% | HA-only% | Dr-only% | No-call% | PmtPend% |
|---|---|---|---|---|---|---|
| Early 2d+ | 258 | 32.6% | 6.2% | 23.6% | 37.6% | 4.7% |
| Early 1d | 6,207 | 36.6% | 6.2% | 23.6% | 33.6% | 1.6% |
| On-Time | 43,416 | 38.9% | 5.7% | 24.1% | 31.3% | 4.4% |
| Late 1d | 5,240 | 47.2% | 9.8% | 18.7% | 24.4% | 37.7% |
| Late 2d | 1,786 | 55.4% | 11.5% | 15.7% | 17.4% | 68.2% |
| Late 3d | 361 | 50.7% | 6.4% | 19.9% | 23.0% | 26.6% |
| Late 4d | 145 | 48.3% | 4.1% | 23.4% | 24.1% | 6.2% |
| Late 5d | 74 | 52.7% | 9.5% | 14.9% | 23.0% | 9.5% |
| Late 6d+ | 201 | 50.7% | 6.5% | 18.9% | 23.9% | 5.0% |

**HA-involved total (Dr+HA + HA-only) vs payment pending:**

| Dispatch Bucket | N | HA-involved% | PmtPend% |
|---|---|---|---|
| Early 2d+ | 258 | 38.8% | 4.7% |
| Early 1d | 6,207 | 42.7% | 1.6% |
| On-Time | 43,416 | 44.6% | 4.4% |
| Late 1d | 5,240 | 57.0% | 37.7% |
| Late 2d | 1,786 | 67.0% | 68.2% |
| Late 3d | 361 | 57.1% | 26.6% |
| Late 4d | 145 | 52.4% | 6.2% |
| Late 5d | 74 | 62.2% | 9.5% |
| Late 6d+ | 201 | 57.2% | 5.0% |

**Verdicts:**

- **H9 for dispatch (Late 1d/2d):** Payment pending is the dominant driver for Late 1d (37.7%) and especially Late 2d (68.2%). These orders are stuck awaiting payment completion before AWB can print.
- **H16 — SUPPORTED (Late 3d+):** Payment pending collapses from 68.2% at Late 2d to 26.6% at Late 3d, and further to 5–10% at Late 4d–6d+. It is not the driver of severe late dispatch. Instead, HA-involved (DOCTOR_AND_HA_CALL_REQUIRED + HA_CALL_REQUIRED) stays elevated at 52–62% across all Late 3d+ buckets, compared to a 44.6% baseline in On-Time orders — a persistent +8 to +18pp elevation.
- **Mechanism:** For DOCTOR_AND_HA_CALL_REQUIRED orders, the sequence is: doctor call → HA call → invoice → AWB → pickup. The HA call has no enforced SLA. If the HA call takes 3, 4, or 5+ days, the AWB cannot print until it completes, and courier always collects same-day. These orders cannot be rescued by any upstream fix that only targets doctor confirmation or payment — the HA call leg itself is the bottleneck.
- **Scale:** Late 3d+ total = 781 orders (1.4% of egregious superset). Of these, ~52–62% (≈410–485 orders) are HA-involved. This is a concentrated failure mode, not a diffuse one.

---

## #41 — Early 1d dispatch: courier switch rate and WH deviation breakdown by courier group

**Request:** Within Early 1d dispatch orders, determine (a) what % had a courier change from digitised to shipping, (b) whether same-courier Early 1d is driven by WH packing early (before WH promise), and (c) whether switched-courier Early 1d is driven by WH packing on time/late with the new courier enabling same-day pickup.

**Courier switch rate for Early 1d (n=6,207) vs adjacent buckets:**

| Dispatch Bucket | N | Switched% | Same% | Null% |
|---|---|---|---|---|
| Early 2d+ | 258 | 39.1% | 41.5% | 19.4% |
| Early 1d | 6,207 | 36.6% | 51.5% | 11.9% |
| On-Time | 43,416 | 26.9% | 64.9% | 8.1% |
| Late 1d | 5,240 | 45.2% | 46.5% | 8.4% |

Note: 51.5 + 36.6 = 88.1%; the remaining 11.9% have a null on either digitised or shipping partner and cannot be classified.

**WH deviation (AWB vs WH promise) by courier group within Early 1d:**

| WH deviation | Same courier (n=3,195) | Switched courier (n=2,273) | Null courier (n=739) |
|---|---|---|---|
| Early >2h | 2.3% | 0.8% | 1.9% |
| Early 30m–2h | 52.6% | 27.4% | 42.5% |
| Early 0–30m | 27.8% | 21.2% | 22.3% |
| Late 0–30m | 8.3% | 13.5% | 10.6% |
| Late 30m–2h | 5.2% | 19.5% | 13.3% |
| Late >2h | 3.8% | 17.6% | 9.5% |
| **WH early (total)** | **82.6%** | **49.5%** | **66.7%** |
| **WH late (total)** | **17.3%** | **50.5%** | **33.3%** |

**Verdicts:**

- **Same courier (51.5% of Early 1d) — confirmed WH packed early:** 82.6% have AWB printed before WH promise. Mechanism: WH promise was set after the courier cutoff (hence D+1 dispatch promise), but WH packed early enough that AWB was ready before cutoff. Same courier came same day. Dispatch was 1 day early vs promise. The 17.3% WH-late same-courier cases cannot be fully explained without courier cutoff timestamps.
- **Switched courier (36.6% of Early 1d) — confirmed courier switch enabled same-day pickup for WH-late orders:** 50.5% have AWB printed after WH promise (WH packed late). Original courier's cutoff was already missed; a replacement courier with a later cutoff was assigned, enabling same-day pickup, which (given D+1 dispatch promise) produced Early 1d dispatch. The other 49.5% have WH packing early — for those, both WH early and courier switch occurred, and either factor alone could explain the early dispatch.
- **Null courier (11.9%):** Partner data missing; cannot classify mechanism.

---

## #42 — Delivery TAT Early 2d: promised vs actual TAT distribution and courier switch breakdown

**Request:** Explore what is happening in the Delivery TAT Early 2d cohort (n=25,355, 44% of Non-SDD Inventory egregious superset) — the largest untouched highlighted cohort. Delivery TAT Early 2d = actual transit (pickup → delivery attempt) was exactly 2 days faster than promised transit (dispatch promise → delivery promise).

**Promised vs actual TAT combos (every order is exactly promised − actual = 2d):**

| Promised TAT | Actual TAT | Count | % |
|---|---|---|---|
| 4d | 2d | 12,881 | 50.8% |
| 3d | 1d | 6,505 | 25.7% |
| 5d | 3d | 5,192 | 20.5% |
| 6d | 4d | 505 | 2.0% |
| 2d | 0d | 233 | 0.9% |
| 7d | 5d | 36 | 0.1% |
| 8d | 6d | 3 | 0.0% |

**Courier switch breakdown:**

| Group | Count | % |
|---|---|---|
| Same courier (digitised = shipping) | 17,915 | 70.7% |
| Switched courier | 5,406 | 21.3% |
| Null (partner data missing) | 2,034 | 8.0% |

**Verdict:** The deviation is perfectly uniform — every order is exactly 2 days early, with no irregular combinations. 70.7% had no courier switch. The courier is not underperforming or changing — the digitised delivery promise is systematically built with a transit TAT that is 2 days longer than what the courier actually takes. This is a promise construction problem: the system over-pads the transit window by 2 days for the pincode/courier/zone combinations represented in this cohort.

---

## #43 — Delivery TAT Early 2d: digitised vs shipping vs actual TAT for same-courier and switched-courier groups

**Request:** For the 70.7% same-courier and 21.3% switched-courier orders in the Delivery TAT Early 2d cohort, compare digitised promised TAT vs shipping promised TAT vs actual TAT to determine whether (a) courier performance improved from digitised to shipping (shipping ≈ actual, digitised >> actual), or (b) the system adds buffers that actuals beat every time regardless of courier.

**Same courier (n=17,915) — Shipping TAT vs Actual TAT:**

| Shipping TAT − Actual TAT | Count | % |
|---|---|---|
| +0d (shipping = actual) | 1,928 | 10.8% |
| +1d (shipping 1d over actual) | 10,321 | 57.6% |
| +2d (shipping = digitised, 2d over actual) | 5,542 | 30.9% |
| Other | 124 | 0.7% |

Top combos (digitised TAT / shipping TAT / actual TAT):

| Dig | Ship | Actual | % |
|---|---|---|---|
| 4d | 3d | 2d | 33.4% |
| 4d | 4d | 2d | 17.3% |
| 3d | 2d | 1d | 14.7% |
| 5d | 4d | 3d | 8.4% |
| 3d | 3d | 1d | 7.6% |

**Switched courier (n=5,406) — Shipping TAT vs Actual TAT:**

| Shipping TAT − Actual TAT | Count | % |
|---|---|---|
| +0d (shipping = actual) | 735 | 13.6% |
| +1d | 2,128 | 39.4% |
| +2d | 1,457 | 27.0% |
| +3d or more | 903 | 16.7% |
| Under actual (−1d) | 48 | 0.9% |

**Verdicts:**

- **Same courier:** Neither hypothesis is confirmed cleanly. The shipping promise has partially adjusted downward from digitised (by 1d in 57.6% of cases), but actual performance beats even the shipping promise in 89.2% of orders. Only 10.8% have shipping TAT = actual TAT. The system over-estimates transit time at both the digitised and shipping layers — actual courier performance is outpacing both. This is a structural calibration gap in the transit TAT lookup, not courier improvement captured by the shipping layer.
- **Switched courier:** The new courier's shipping promise also does not match actual — only 13.6% do, nearly identical to same-courier (10.8%). A notable tail (16.7%) has the new courier promising 3d+ more than actual, and some combos (e.g. dig=5d / ship=7d / actual=3d) show the replacement courier promising even longer TAT than the original, yet actual is still 2d faster than digitised. The switched-courier group does not reveal a "better courier was allocated" story — the lane itself performs faster than any courier promises it.
- **Combined conclusion:** The Delivery TAT Early 2d cohort is driven by a systemic transit TAT over-estimation baked into both the digitised and shipping promise layers for specific pincode/courier/zone lanes. Neither layer has accurately captured actual courier performance. Fix direction: recalibrate transit TAT lookup tables using recent actuals for the affected lanes.

---

## #44 — Delivery TAT remaining cohorts (Early 1d, Early 3d, Late 1d, Late 2d, Late 3d, Late 4d): digitised vs shipping vs actual TAT

**Request:** Run the same digitised / shipping / actual TAT comparison across all six remaining highlighted Delivery TAT cohorts to test whether the same systemic transit TAT miscalibration finding from Early 2d holds universally.

**Early cohorts — same courier shipping TAT vs actual TAT:**

| Cohort | n (same courier) | Ship = Actual (+0d) | Ship 1d over (+1d) | Ship 2d+ over |
|---|---|---|---|---|
| Early 1d | 2,505 | 34.3% | 64.3% | 0.7% |
| Early 3d | 2,234 | 5.3% | 22.2% | 72.0% |

Early 1d: shipping partially adjusts (64.3% ship is 1d over actual, 34.3% matches). Early 3d: shipping barely moves — 72% still 2–3d over actual, only 5.3% match.

**Late cohorts — same courier shipping TAT vs actual TAT:**

| Cohort | n (same courier) | Ship = Dig (no adjustment) | Ship gap vs actual |
|---|---|---|---|
| Late 1d | 1,823 | ~85% | −1d in 84.8% |
| Late 2d | 5,932 | ~84% | −2d in 84.4% |
| Late 3d | 1,935 | ~84% | −3d in 84.0% |
| Late 4d | 869 | ~85% | −4d in 85.0% |

For all late cohorts, the shipping TAT is identical to the digitised TAT in 84–85% of same-courier cases — the shipping layer makes zero downward adjustment. Both layers under-promise transit by exactly the cohort's deviation magnitude.

Representative combos (late cohorts, same courier):
- Late 2d: `dig=2d / ship=2d / actual=4d` — 30.3% of same-courier Late 2d orders
- Late 3d: `dig=2d / ship=2d / actual=5d` — 26.9%
- Late 4d: `dig=2d / ship=2d / actual=6d` — 24.6%

**Switched courier:** All cohorts show high variance in ship gap (ranging from −6d to +15d depending on cohort), with no consistent improvement over digitised. Some replacement couriers promise even longer TATs than the original.

**Unified verdict across all 7 Delivery TAT cohorts (Early 1d through Late 4d):**

The transit TAT lookup table driving both digitised and shipping promises has stale values for specific pincode/courier/zone lanes. The shipping layer does not recalibrate it — for late cohorts it is copy-pasted directly from digitised; for early cohorts there is marginal partial adjustment but never enough to match actual. Two failure modes:
- **Early cohorts:** lookup over-estimates transit → customer receives order N days early
- **Late cohorts:** lookup under-estimates transit → customer receives order N days late

One fix addresses all seven cohorts: recalibrate the transit TAT lookup table using rolling actuals per lane.

---

## #45 — Non-SDD Non-Inventory Cohort 40: WH deviation using invoice_create_ts vs digitised_wh_promise

**Request:** For Cohort 40 of the Non-SDD Non-Inventory egregious set (WH Early + Dispatch Early + Delivery Cx Early, n=26,134), rebuild the WH earliness distribution using `invoice_create_ts` instead of `awb_sticker_printed_ts` as the comparison point against `digitised_wh_promise`. Rationale: invoice creation precedes AWB printing and is unaffected by payment pending holds, giving a cleaner view of the procurement + preparation leg.

**Comparison: AWB-based vs invoice-based WH earliness distribution (Cohort 40, n=26,134):**

| WH Early by | AWB-based (n) | AWB-based % | Invoice-based (n) | Invoice-based % |
|---|---|---|---|---|
| <30 mins | 18 | 0.1% | 8 | 0.0% |
| 30–60 mins | 15 | 0.1% | 14 | 0.1% |
| 1–2 hrs | 186 | 0.7% | 79 | 0.3% |
| 2–4 hrs | 850 | 3.3% | 655 | 2.5% |
| 4–8 hrs | 5,549 | 21.2% | 5,101 | 19.5% |
| 8–12 hrs | 3,449 | 13.2% | 3,918 | 15.0% |
| 12–24 hrs | 2,601 | 10.0% | 2,389 | 9.1% |
| **>24 hrs** | **13,466** | **51.5%** | **13,961** | **53.4%** |
| Late (after WH promise) | — | — | 0 | 0.0% |

**Verdicts:**

- **Payment pending is irrelevant to Cohort 40.** Zero orders have invoice_create_ts after digitised_wh_promise. The preparation leg was complete before the WH promise in every single Cohort 40 order. The earliness is driven entirely by procurement + preparation completing faster than the WH promise anticipated — not by any payment-related delay being absent at the AWB step.
- **The distribution is nearly identical using either timestamp**, with a slight shift toward more extreme early when using invoice (>24 hrs grows from 51.5% → 53.4%). This is expected — invoice always precedes AWB, so it is even further from the WH promise. The dominant story is unchanged: 53.4% of Cohort 40 had the order invoiced more than 24 hours before the WH promise. SKUs were procured and ready far earlier than the system expected.

---

## #46 — Non-SDD Non-Inventory full set: AWB-based vs invoice-based WH deviation distribution

**Request:** Extend the AWB vs invoice WH deviation comparison to the entire Non-SDD Non-Inventory egregious superset (n=29,813) — not just Cohort 40 — to measure the payment pending footprint across all orders.

**Full distribution (AWB-based vs invoice-based), n=29,813:**

| WH Deviation | AWB count | AWB % | Invoice count | Invoice % | Delta |
|---|---|---|---|---|---|
| Early >24 hrs | 13,817 | 46.3% | 14,424 | 48.4% | +2.1pp |
| Early 12–24 hrs | 3,058 | 10.3% | 2,901 | 9.7% | −0.5pp |
| Early 8–12 hrs | 3,641 | 12.2% | 4,189 | 14.1% | +1.8pp |
| Early 4–8 hrs | 6,229 | 20.9% | 5,948 | 20.0% | −0.9pp |
| Early 2–4 hrs | 1,381 | 4.6% | 1,118 | 3.8% | −0.9pp |
| Early 1–2 hrs | 426 | 1.4% | 299 | 1.0% | −0.4pp |
| Early 30–60 mins | 114 | 0.4% | 124 | 0.4% | 0.0pp |
| Early <30 mins | 84 | 0.3% | 60 | 0.2% | −0.1pp |
| Late 12–24 hrs | 453 | 1.5% | 237 | 0.8% | −0.7pp |
| Late >24 hrs | 178 | 0.6% | 125 | 0.4% | −0.2pp |
| All other late | 432 | 1.4% | 378 | 1.3% | −0.2pp |
| **Total Early** | **28,750** | **96.4%** | **29,063** | **97.5%** | **+1.1pp** |
| **Total Late** | **1,063** | **3.6%** | **740** | **2.5%** | **−1.1pp** |

**Verdicts:**

- **Payment pending footprint is 1.1pp** — 328 orders appear WH Late on AWB but WH Early on invoice. These are exactly the orders where invoice was created before the WH promise but AWB printing was delayed by payment resolution. Payment pending's footprint in Non-SDD Non-Inventory is negligible compared to its 68.2% dominance in the Inventory Late 2d dispatch cohort.
- **96.4–97.5% of the entire Non-SDD Non-Inventory egregious set had the order ready (AWB or invoice) before the WH promise.** The warehouse (procurement) effect is total — SKUs arrive and are invoiced far earlier than the system anticipated. Late WH buckets are noise at 2.5–3.6%. The analysis space is almost entirely about why the WH promise is so wrong on the early side.

---

## #47 — Non-SDD Non-Inventory: AWB-based vs invoice-based WH deviation side-by-side comparative table

**Request:** Produce a comparative 7-column table showing AWB-based and invoice-based WH deviation distributions side by side for the full Non-SDD Non-Inventory egregious set (n=29,813), to allow direct visual comparison of the two measurement approaches.

| WH Deviation | AWB Count | AWB % Non-SDD Non-Inv | AWB % Egregious | Invoice Count | Invoice % Non-SDD Non-Inv | Invoice % Egregious |
|---|---|---|---|---|---|---|
| Early >24 hrs | 13,817 | 46.3% | 14.3% | 14,424 | 48.4% | 15.0% |
| Early 12–24 hrs | 3,058 | 10.3% | 3.2% | 2,901 | 9.7% | 3.0% |
| Early 8–12 hrs | 3,641 | 12.2% | 3.8% | 4,189 | 14.1% | 4.3% |
| Early 4–8 hrs | 6,229 | 20.9% | 6.5% | 5,948 | 20.0% | 6.2% |
| Early 2–4 hrs | 1,381 | 4.6% | 1.4% | 1,118 | 3.8% | 1.2% |
| Early 1–2 hrs | 426 | 1.4% | 0.4% | 299 | 1.0% | 0.3% |
| Early 30–60 mins | 114 | 0.4% | 0.1% | 124 | 0.4% | 0.1% |
| Early <30 mins | 84 | 0.3% | 0.1% | 60 | 0.2% | 0.1% |
| On-Time | 0 | 0.0% | 0.0% | 0 | 0.0% | 0.0% |
| Late <30 mins | 41 | 0.1% | 0.0% | 42 | 0.1% | 0.0% |
| Late 30–60 mins | 52 | 0.2% | 0.1% | 38 | 0.1% | 0.0% |
| Late 1–2 hrs | 76 | 0.3% | 0.1% | 87 | 0.3% | 0.1% |
| Late 2–4 hrs | 116 | 0.4% | 0.1% | 107 | 0.4% | 0.1% |
| Late 4–8 hrs | 76 | 0.3% | 0.1% | 78 | 0.3% | 0.1% |
| Late 8–12 hrs | 71 | 0.2% | 0.1% | 26 | 0.1% | 0.0% |
| Late 12–24 hrs | 453 | 1.5% | 0.5% | 237 | 0.8% | 0.2% |
| Late >24 hrs | 178 | 0.6% | 0.2% | 125 | 0.4% | 0.1% |
| **Total Early** | **28,750** | **96.4%** | **29.8%** | **29,063** | **97.5%** | **30.1%** |
| **Total Late** | **1,063** | **3.6%** | **1.1%** | **740** | **2.5%** | **0.8%** |

*Invoice total = 29,803 (10 orders with no invoice_create_ts excluded). AWB total = 29,813. Denominators: % of Non-SDD Non-Inv uses 29,813 throughout; % of Egregious uses 96,424.*

**Key observations:**

- Both distributions are nearly identical — the two measurement approaches converge. This confirms that payment pending (the only mechanism that creates AWB/invoice divergence) is not a meaningful driver in this segment.
- The meaningful deltas are concentrated in the late tail: Late 12–24 hrs drops from 1.5% (AWB) to 0.8% (invoice) and Late >24 hrs from 0.6% to 0.4%. These 328 orders (1.1pp delta) are exactly the payment-pending-affected orders from #46 — orders where the invoice was created before the WH promise but AWB printing was held for payment clearance.
- Early >24 hrs is the dominant bucket in both views (46.3% AWB / 48.4% invoice) — SKUs are being procured and invoiced more than a full day before the system's WH promise window opens. The WH promise is structurally miscalibrated for this segment.

---

## #48 — Non-SDD Non-Inventory: delivery TAT deviation exploratory study (H3/H4/H5–H8)

**Request:** Exploratory study to determine whether there is a delivery TAT deviation component in the Non-SDD Non-Inventory egregious set that is independent of the warehouse/dispatch contribution — mirroring the H1–H8 tests run for Inventory.

**Script:** `archives/egregiously-miscalibrated-promises/scripts/2026-08-02-aggregate-non-inv-delivery-tat-deviation-v1.py`

---

### Part 1 — Raw TAT distributions

| TAT (d) | Dig n | Dig % | Ship n | Ship % | Act n | Act % |
|---|---|---|---|---|---|---|
| 0 | 0 | 0.0% | 0 | 0.0% | 80 | 0.3% |
| 1 | 1,971 | 6.6% | 2,884 | 9.7% | 5,216 | 17.5% |
| 2 | 6,135 | 20.6% | 7,882 | 26.4% | 13,038 | 43.7% |
| 3 | 9,903 | 33.2% | 10,064 | 33.8% | 7,223 | 24.2% |
| 4 | 7,351 | 24.7% | 5,936 | 19.9% | 2,440 | 8.2% |
| 5 | 4,070 | 13.7% | 2,102 | 7.1% | 710 | 2.4% |
| 6 | 361 | 1.2% | 552 | 1.9% | 411 | 1.4% |
| 7+ | 22 | 0.1% | 393 | 1.3% | 695 | 2.3% |

Digitised TAT peaks at 3d (33.2%) and 4d (24.7%). Actual TAT peaks at 2d (43.7%) and 1d (17.5%). Both promise layers are systematically 1–2 days longer than what couriers actually deliver — same stale transit TAT lookup table signature as Inventory.

---

### Part 2 — TAT deviation buckets (digitised TAT − actual TAT, in days)

| Bucket | n | % of Non-SDD Non-Inv | % of Egregious |
|---|---|---|---|
| Early 4d+ | 26 | 0.1% | 0.0% |
| Early 3d | 804 | 2.7% | 0.8% |
| Early 2d | 5,384 | 18.1% | 5.6% |
| Early 1d | 15,101 | 50.7% | 15.7% |
| On-Time | 6,277 | 21.1% | 6.5% |
| Late 1d | 407 | 1.4% | 0.4% |
| Late 2d | 489 | 1.6% | 0.5% |
| Late 3d+ | 1,325 | 4.4% | 1.4% |

**68.8% of Non-Inventory egregious orders have early delivery TAT** — courier delivers faster than promised, independent of when dispatch happened. Late 3d+ at 4.4% (n=1,325) is a meaningful tail in the opposite direction.

---

### Part 3 — H3: Courier change per TAT deviation bucket

| Bucket | n | Courier chg n | Courier chg % |
|---|---|---|---|
| Early 4d+ | 26 | 14 | 53.8% |
| Early 3d | 804 | 424 | 52.7% |
| Early 2d | 5,384 | 1,878 | 34.9% |
| Early 1d | 15,101 | 3,364 | 22.3% |
| On-Time | 6,277 | 1,405 | 22.4% |
| Late 1d | 407 | 216 | 53.1% |
| Late 2d | 489 | 224 | 45.8% |
| Late 3d+ | 1,325 | 668 | 50.4% |

Courier change is **not** a driver of the dominant Early 1d bucket (22.3% = on-time baseline of 22.4%). Elevated in the extreme early tail (Early 3d+: 52–54%) and throughout the late tail (45–53%).

---

### Part 4 — H4: Promise change per TAT deviation bucket

| Bucket | n | Has ship TAT | Promise chg | % |
|---|---|---|---|---|
| Early 4d+ | 26 | 26 | 20 | 76.9% |
| Early 3d | 804 | 804 | 658 | 81.8% |
| Early 2d | 5,384 | 5,384 | 3,922 | 72.8% |
| Early 1d | 15,101 | 15,101 | 6,104 | 40.4% |
| On-Time | 6,277 | 6,277 | 1,110 | 17.7% |
| Late 1d | 407 | 407 | 206 | 50.6% |
| Late 2d | 489 | 489 | 236 | 48.3% |
| Late 3d+ | 1,325 | 1,325 | 673 | 50.8% |

Clear monotonic early pattern: 76.9% → 81.8% → 72.8% → 40.4% → 17.7% baseline. Same stale TAT lookup table signature as Inventory H4.

---

### Part 5 — H5–H8 cross-tab: Promise change × Courier change

| Bucket | Has ship | H5 both% | H6 Cx% | H7 neither% | H8 Px% |
|---|---|---|---|---|---|
| Early 4d+ | 26 | 42.3% | 11.5% | 11.5% | 34.6% |
| Early 3d | 804 | 42.5% | 10.2% | 8.0% | **39.3%** |
| Early 2d | 5,384 | 26.4% | 8.5% | 18.6% | **46.5%** |
| Early 1d | 15,101 | 11.9% | 10.4% | **49.2%** | 28.5% |
| On-Time | 6,277 | 11.4% | 11.0% | **71.3%** | 6.3% |
| Late 1d | 407 | 41.5% | 11.5% | 37.8% | 9.1% |
| Late 2d | 489 | 38.0% | 7.8% | 44.0% | 10.2% |
| Late 3d+ | 1,325 | 38.3% | 12.1% | 37.1% | 12.5% |

**Key divergence from Inventory:**
- Early 2d follows Inventory — H8 dominant (46.5%): shipping shortens TAT, same courier delivers to it, egregiously early vs digitised promise.
- **Early 1d is dominated by H7 (49.2%)**: neither courier nor promise changed. The courier routinely delivers 1d faster than both digitised and shipping promise. The shipping layer is not correcting for these lanes at all — unlike Inventory where shipping partially adjusted.
- Late 1d–2d: H5 (both changed, 38–42%) and H7 (38–44%) split — either compounding disruption or pure courier underperformance with no system correction.
- Late 3d+: H5 (38.3%) and H7 (37.1%) roughly equal — severe late deliveries from compounding disruption or genuinely hard routes.

---

### Part 6 — Same-courier combos: does shipping correct the digitised promise?

**Early 1d same-courier (n=11,737):**

| Dig TAT | Ship TAT | Act TAT | n | % |
|---|---|---|---|---|
| 3 | 3 | 2 | 3,848 | 32.8% |
| 4 | 4 | 3 | 1,854 | 15.8% |
| 3 | 2 | 2 | 1,841 | 15.7% |
| 2 | 2 | 1 | 1,427 | 12.2% |
| 4 | 3 | 3 | 1,154 | 9.8% |
| 2 | 1 | 1 | 728 | 6.2% |

Top 3 combos (dig=ship, courier faster): 32.8% + 15.8% + 12.2% = 60.8% of same-courier Early 1d — shipping made no correction, courier delivers 1d faster than both layers consistently. Next 2 combos (shipping corrected by 1d, courier delivered to shipping promise — still 1d early vs digitised): 15.7% + 9.8% = 25.5%.

**Early 2d same-courier (n=3,506):**

| Dig TAT | Ship TAT | Act TAT | n | % |
|---|---|---|---|---|
| 4 | 3 | 2 | 1,254 | 35.8% |
| 4 | 4 | 2 | 564 | 16.1% |
| 5 | 4 | 3 | 563 | 16.1% |
| 3 | 2 | 1 | 309 | 8.8% |

Shipping partially corrects (35.8% ship=3 vs dig=4) but undershoots — courier still delivers 1d faster than shipping promised. 16.1% shipping made no correction at all (dig=ship=4, act=2, 2d faster than either).

**Late 3d+ same-courier (n=657):**

| Dig TAT | Ship TAT | Act TAT | n | % |
|---|---|---|---|---|
| 2 | 2 | 5 | 76 | 11.6% |
| 3 | 3 | 6 | 65 | 9.9% |
| 1 | 1 | 4 | 54 | 8.2% |

Courier consistently takes 3+ days more than both promises predict. No system correction whatsoever — the lookup table has no visibility into these hard routes.

---

### Verdicts

1. **Delivery TAT component is real and large (68.8% early TAT)** — independent of dispatch timing; warehouse does not explain this.
2. **Root cause is the same stale transit TAT lookup table** — both digitised and shipping promise TATs that couriers reliably beat (or fail to meet) on specific lanes.
3. **Non-Inventory diverges from Inventory in one key way:** the shipping layer makes zero correction for the dominant Early 1d bucket (H7=49.2%). In Inventory, shipping partially corrected via H8. Non-Inventory routes are either not in the recalibration loop or the lane-level actuals are not being fed back.
4. **Late 3d+ (n=1,325, 4.4%)** is a distinct failure mode: H5+H7 dominant, couriers missing promises by 3+ days with no system correction. Likely specific pincode/zone combinations where courier capacity or routing creates systematic underperformance vs the lookup table.

---

## #49 — Payment pending rate by dispatch group and day (Non-SDD Inventory)

Request: Quantify payment pending rates across Early/On-Time/Late dispatch groups and at day-level granularity for the Non-SDD Inventory egregious superset (n=57,688).

Script: `archives/egregiously-miscalibrated-promises/scripts/2026-08-03-aggregate-inv-payment-pending-dispatch-v1.py`

### Part 1 — Group-level payment pending rate

| Group | n | % of superset | Pmt pending n | Pmt pending % |
|---|---|---|---|---|
| Early | 7,039 | 12.2% | 311 | 4.4% |
| On-Time | 43,378 | 75.2% | 1,878 | 4.3% |
| Late | 7,771 | 13.5% | 3,301 | 42.5% |

Payment pending rate in the Late group is 10× the Early/On-Time baseline. 5.74% of the full superset (42.5% × 13.5%) are both late-dispatched and payment-pending.

### Part 2 — Day-level payment pending rate

| Dev (days) | Label | n | % of superset | Pmt pending n | Pmt pending % |
|---|---|---|---|---|---|
| +2 | Early 2d | 849 | 1.5% | 18 | 2.1% |
| +1 | Early 1d | 6,190 | 10.7% | 293 | 4.7% |
| 0 | On-Time | 43,378 | 75.2% | 1,878 | 4.3% |
| −1 | Late 1d | 5,244 | 9.1% | 1,979 | 37.7% |
| −2 | Late 2d | 1,786 | 3.1% | 1,218 | 68.2% |
| −3 | Late 3d | 361 | 0.6% | 96 | 26.6% |
| −4 | Late 4d | 150 | 0.3% | 8 | 5.3% |
| −5+ | Late 5d+ | 230 | 0.4% | 0 | 0.0% |

Payment pending rate peaks at Late 2d (68.2%) and is still very elevated at Late 1d (37.7%), then collapses at Late 3d+ (≤26.6%). Late 3d+ is driven by other mechanisms.

---

## #50 — Invoice→AWB gap: payment-pending vs non-pmt by dispatch group (Non-SDD Inventory)

Request: Measure median invoice→AWB gap hours for payment-pending vs non-pmt orders per dispatch group.

Script: same as #49 (Part 3 of aggregate script).

### Part 3a — Group-level invoice→AWB gap

| Group | Pmt n | Pmt median | Pmt p25 | Pmt p75 | Non-pmt n | Non-pmt median | Non-pmt p25 | Non-pmt p75 |
|---|---|---|---|---|---|---|---|---|
| Early | 311 | 0.9h | 0.3h | 1.9h | 6,728 | 0.4h | 0.2h | 0.7h |
| On-Time | 1,878 | 1.1h | 0.2h | 5.3h | 41,500 | 0.4h | 0.2h | 0.7h |
| Late | 3,301 | 24.5h | 21.4h | 28.1h | 4,470 | 0.4h | 0.2h | 0.7h |

Non-pmt baseline is constant at 0.4h (23m) across all three groups. Payment pending in the Late group imposes a median 24.5h hold (IQR 21.4–28.1h). Payment pending in Early/On-Time groups resolves quickly (0.9h–1.1h) — the payment hold clears before AWB needs to print for those orders.

### Part 3b — Day-level invoice→AWB gap (material rows)

| Dev | Label | Pmt n | Pmt median | Pmt p25 | Pmt p75 | Non-pmt n | Non-pmt median |
|---|---|---|---|---|---|---|---|
| +1 | Early 1d | 293 | 0.8h | 0.3h | 1.7h | 5,897 | 0.4h |
| 0 | On-Time | 1,878 | 1.1h | 0.2h | 5.3h | 41,500 | 0.4h |
| −1 | Late 1d | 1,979 | 23.2h | 20.6h | 26.0h | 3,265 | 0.4h |
| −2 | Late 2d | 1,218 | 26.6h | 24.1h | 28.6h | 568 | 0.4h |

Mechanism confirmed: payment pending imposes a 23–27h AWB print hold on Late orders. The hold duration maps directly to the dispatch deviation: 23h hold → courier misses same-day pickup → Late 1d. 26.6h hold → courier misses next-day pickup also → Late 2d. Non-pmt baseline of 0.4h is identical regardless of dispatch deviation.

---

## #51 — Counterfactual simulation: eliminating payment pending (Non-SDD Inventory)

Request: Simulate dispatch deviation distribution if all pmt-pending orders received AWB at invoice_create_ts + 0.4h (non-pmt baseline), keeping same-day courier pickup assumption.

Script: `archives/egregiously-miscalibrated-promises/scripts/2026-08-03-simulate-no-payment-pending-v1.py`

Superset n: 57,688. Effective n (with dispatch/pickup ts): 57,688. Pmt orders simulated: 5,341. Pmt without invoice ts: ~0.

### Dispatch deviation distribution — actual vs simulated

| Bucket | Actual n | Actual % | Sim n | Sim % | Delta n | Delta pp |
|---|---|---|---|---|---|---|
| Early 3d+ | 189 | 0.3% | 191 | 0.3% | +2 | 0.0pp |
| Early 2d | 849 | 1.5% | 849 | 1.5% | 0 | 0.0pp |
| Early 1d | 6,190 | 10.8% | 6,737 | 11.7% | +547 | +1.1pp |
| On-Time | 43,378 | 75.3% | 45,794 | 79.5% | +2,416 | +4.2pp |
| Late 1d | 5,244 | 9.1% | 3,452 | 6.0% | −1,792 | −3.1pp |
| Late 2d | 1,786 | 3.1% | 580 | 1.0% | −1,206 | −2.1pp |
| Late 3d | 361 | 0.6% | 269 | 0.5% | −92 | −0.2pp |
| Late 4d+ | 420 | 0.7% | 404 | 0.7% | −16 | 0.0pp |

### Group summary

| Group | Actual % | Sim % | Delta pp |
|---|---|---|---|
| Early | 12.6% | 13.4% | +1.1pp |
| On-Time | 75.3% | 79.5% | +4.2pp |
| Late | 13.5% | 8.1% | −5.4pp |

### Where payment-pending orders move to (n=5,341 pmt orders)

| From bucket | To bucket | n | % of pmt |
|---|---|---|---|
| Late 1d | On-Time | 1,844 | 34.5% |
| On-Time | On-Time | 1,361 | 25.5% |
| Late 2d | On-Time | 1,107 | 20.7% |
| On-Time | Early 1d ⚠ | 547 | 10.2% |
| Late 2d | Late 1d | 104 | 1.9% |
| Late 3d / 4d+ | Late 1d / 2d / unchanged | 108 | 2.0% |
| Early 1d | Early 1d / 2d / 3d | 102 | 1.9% |
| Late 1d | Early 1d / unchanged | 130 | 2.4% |

Eliminating payment pending recovers 5.4pp of lateness. The 547 On-Time→Early 1d side effect occurs because these orders' invoices are created early enough that simulated AWB at invoice+0.4h falls one calendar day before the dispatch promise.

---

## #52 — Residual Late 1d cohort: sample orders and AWB/invoice timing (Non-SDD Inventory)

Request: Investigate timing patterns for the residual Late 1d cohort (dispatch_dev=−1, payment_pending_ts=NULL, n=3,265) to triangulate what is causing late AWB print.

Script: `archives/egregiously-miscalibrated-promises/scripts/2026-08-03-investigate-residual-late-1d-v1.py`

Cohort sizes: Residual Late 1d = 3,265. On-Time (no pmt) baseline = 41,500.

### Part 2 — AWB print date vs dispatch promise date

| AWB vs promise (days) | Late 1d n | Late 1d % | On-Time n | On-Time % |
|---|---|---|---|---|
| −2 (2d early) | 0 | 0.0% | 1,014 | 2.4% |
| −1 (1d early) | 0 | 0.0% | 36,428 | 87.8% |
| 0 (same day) | 2,261 | 69.2% | 4,058 | 9.8% |
| +1 (1d late) | 933 | 28.6% | 0 | 0.0% |
| +2 (2d late) | 71 | 2.2% | 0 | 0.0% |

For On-Time orders: 90.2% have AWB printed 1–2 days before the dispatch promise (courier picks up same day as AWB, giving dispatch on the promise date). For Late 1d: 69.2% print AWB on the promise date itself — courier collects same day but it's too late (promise date is past), or courier cannot collect until next day. 28.6% print AWB 1d after promise — entirely outside the window.

### Part 3 — Invoice date vs dispatch promise date

Invoice patterns mirror AWB exactly (invoice→AWB gap is ~25m, confirmed in #53). The delay is upstream of invoice creation.

### Part 7 — AWB print hour of day (selected rows)

| Hour | Late 1d % | On-Time % |
|---|---|---|
| 09:00–12:00 | 21% | 41% |
| 12:00–17:00 | 47% | 36% |
| 17:00+ | 32% | 23% |

Late 1d AWB prints skew afternoon/evening vs morning-heavy On-Time baseline. Orders completing invoice creation late in the day miss the courier's collection window.

No skew in order category mix or courier mix between Late 1d and On-Time cohorts.

---

## #53 — H1 and H2 elimination tests for residual Late 1d (Non-SDD Inventory)

Request: H1: Is invoice also delayed (not just AWB), and is the invoice→AWB gap constant? H2: Is lateness driven by orders switching digitised_is_inventory=TRUE → shipping_is_inventory=FALSE at shipping?

Script: scratchpad (h1h2_test.py — not archived, results captured here).

### H1: Invoice timing vs dispatch promise

| Invoice vs promise (days) | Late 1d n | Late 1d % | On-Time n | On-Time % |
|---|---|---|---|---|
| −1 (1d early) | 0 | 0.0% | 36,428 | 87.8% |
| 0 (same day) | 2,261 | 69.2% | 4,058 | 9.8% |
| +1 (1d late) | 933 | 28.6% | 0 | 0.0% |
| +2 (2d late) | 71 | 2.2% | 0 | 0.0% |

Invoice date distribution is identical to AWB date distribution (Part 2 of #52). Invoice is delayed identically to AWB.

Invoice→AWB gap by dispatch bucket (median, non-pmt orders only):

| Dispatch bucket | Invoice→AWB median |
|---|---|
| Early 1d | 0.4h |
| On-Time | 0.4h |
| Late 1d | 0.4h (~25m) |
| Late 2d | 0.4h (~25m) |

Gap is constant at ~25m regardless of dispatch deviation. The AWB prints within 25 minutes of invoice creation for every bucket. The delay is entirely upstream of invoice.

**H1 conclusion:** Invoice creation is the delay point. AWB-to-AWB gap is not the bottleneck.

### H2: Inventory switch rate

| | n | % of Late 1d cohort |
|---|---|---|
| Residual Late 1d cohort total | 3,265 | 100% |
| shipping_is_inventory = FALSE | 54 | 1.7% |

Only 54 orders switched inventory state at shipping. **H2 eliminated** — negligible.

---

## #54 — Invoice creation driver analysis for residual Late 1d (Non-SDD Inventory)

Request: Decompose residual Late 1d (n=3,265) into call-required and non-call order categories; measure per-leg time gaps vs On-Time baseline to identify what drives late invoice creation.

Script: scratchpad (invoice_drivers.py — not archived, results captured here).

### Call-required orders (DOCTOR_CALL_REQUIRED + DOCTOR_AND_HA_CALL_REQUIRED)

Cohort sizes: Late 1d n = 2,264 (69.3% of 3,265). On-Time n = 28,274.

| Leg | Late 1d median | On-Time median | Ratio |
|---|---|---|---|
| dr_promise → dr_confirm | 169m | 41m | 4.1× |
| dr_confirm → invoice | 233m | 185m | 1.3× |

**Primary bottleneck: dr_promise → dr_confirm gap.** Doctor confirmation is arriving 169 minutes after the promised slot vs 41 minutes for On-Time orders — a 4× gap. The downstream leg (dr_confirm → invoice) is similar for both cohorts (233m vs 185m), confirming it is not the bottleneck. Late doctor confirmation cascades to late invoice creation, which cascades to late AWB print (gap constant at 25m), which cascades to late dispatch.

### Non-call orders (AUTO_CONFIRM / NO_CALL and similar)

Cohort sizes: Late 1d n = 1,001 (30.7% of 3,265). On-Time n = 13,229.

| Leg | Late 1d median | On-Time median | Ratio |
|---|---|---|---|
| wh_promise → invoice | 499m | 245m | 2.0× |

**Primary bottleneck: wh_promise → invoice gap.** The warehouse-to-invoice pipeline takes 2× longer for Late 1d non-call orders. No doctor call leg exists to explain this — the delay is entirely within the warehouse processing or system handoff between wh_promise and invoice creation. Origin is not yet identified.

### Summary

| Category | Share of residual Late 1d | Primary driver | Bottleneck gap (Late 1d vs On-Time) |
|---|---|---|---|
| Call-required | 69% | Late doctor confirmation | dr_promise→dr_confirm: 169m vs 41m (4×) |
| Non-call | 31% | Unknown WH pipeline delay | wh_promise→invoice: 499m vs 245m (2×) |
