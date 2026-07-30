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
