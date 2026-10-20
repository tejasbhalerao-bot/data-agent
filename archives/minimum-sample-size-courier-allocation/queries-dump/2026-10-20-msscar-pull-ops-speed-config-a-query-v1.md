# Ops speed config pull A: MFC table, warehouses 23, 24, 25, 26, 27

- **Purpose:** the ops-configured delivery days for six couriers on 5 warehouses, one row per lane, with the repeated rows removed
- **Serves:** worked example and the last rung of the pooling ladder (project scope v6); no brief metric yet
- **Grain:** one row per warehouse x pincode x delivery partner
- **Tables:** `tmmumpsdb.pincode_delivery_tat_mfc` (Pincode Delivery TAT MFC, `schema.md`)
- **Definitions used:** none
- **Filters:** delivery partners 185, 195, 225, 246, 247, 286 (scope v4). Warehouses 23, 24, 25, 26, 27. `DISTINCT` removes rows repeated with the same values; if a lane has two different `delivery_days`, both rows come back so the CSV check catches it. No `Active` filter yet: the probe first shows whether inactive rows are present.
- **Expected shape:** `warehouse_id, pincode, delivery_partner, delivery_days`; roughly 350,000 to 450,000 rows, well under the export cap of 1,048,576
- **Timeout risk:** Low (one table, no joins, no date range)
- **Save the CSV as:** `archives/minimum-sample-size-courier-allocation/raw-data/ops-speed-config-mfc-a.csv`

```sql
SELECT DISTINCT warehouse_id, pincode, delivery_partner, delivery_days
FROM tmmumpsdb.pincode_delivery_tat_mfc
WHERE delivery_partner IN (185, 195, 225, 246, 247, 286)
  AND warehouse_id IN (23, 24, 25, 26, 27);
```
