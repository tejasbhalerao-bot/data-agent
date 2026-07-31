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
