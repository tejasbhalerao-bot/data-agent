# Ops speed config probe: duplicates and warehouse sizes, FC and MFC tables

- **Purpose:** show where the repeated rows come from and how big each warehouse's config is, before the pulls are re-run
- **Serves:** none (probe)
- **Grain:** one row per source table x warehouse
- **Tables:** `tmmumpsdb.pincode_delivery_tat` (Pincode Delivery TAT, FC) and `tmmumpsdb.pincode_delivery_tat_mfc` (Pincode Delivery TAT MFC), `schema.md`
- **Definitions used:** none
- **Filters:** delivery partners 185, 195, 225, 246, 247, 286 (scope v4). Warehouses 19 to 40, which covers every warehouse in the orders and in the two earlier config files.
- **Expected shape:** `source_table, warehouse_id, row_count, distinct_lanes, lanes_with_duplicate_rows, lanes_with_conflicting_days`; about 25 to 40 rows. `row_count` above `distinct_lanes` means repeated rows; a non-zero conflicting count means one lane has two different delivery days.
- **Timeout risk:** Low (two tables, no joins, aggregation only)
- **Save the CSV as:** `archives/minimum-sample-size-courier-allocation/raw-data/probe-ops-speed-config.csv`

```sql
WITH t AS (
    SELECT 'mfc' AS source_table, warehouse_id, pincode, delivery_partner, delivery_days
    FROM tmmumpsdb.pincode_delivery_tat_mfc
    WHERE delivery_partner IN (185, 195, 225, 246, 247, 286)
      AND warehouse_id BETWEEN 19 AND 40
    UNION ALL
    SELECT 'fc' AS source_table, warehouse_id, pincode, delivery_partner, delivery_days
    FROM tmmumpsdb.pincode_delivery_tat
    WHERE delivery_partner IN (185, 195, 225, 246, 247, 286)
      AND warehouse_id BETWEEN 19 AND 40
),
lanes AS (
    SELECT source_table, warehouse_id, pincode, delivery_partner,
           COUNT(*) AS n,
           COUNT(DISTINCT delivery_days) AS d
    FROM t
    GROUP BY source_table, warehouse_id, pincode, delivery_partner
)
SELECT source_table,
       warehouse_id,
       SUM(n) AS row_count,
       COUNT(*) AS distinct_lanes,
       SUM(CASE WHEN n > 1 THEN 1 ELSE 0 END) AS lanes_with_duplicate_rows,
       SUM(CASE WHEN d > 1 THEN 1 ELSE 0 END) AS lanes_with_conflicting_days
FROM lanes
GROUP BY source_table, warehouse_id
ORDER BY source_table, warehouse_id;
```
