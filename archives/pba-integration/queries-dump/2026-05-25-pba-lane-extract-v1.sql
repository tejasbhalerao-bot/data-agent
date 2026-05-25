-- 1.8 Lane Extract
-- One row per order. Pulls warehouse_id + drop_pincode from allocation_metadata.
-- Joined to base extract in script on order_id.
-- Same filters as adherence base extract (HARD, INTERNAL, warehouse_id >= 17).

WITH cte AS (
    SELECT
        order_id,
        allocation_metadata,
        ROW_NUMBER() OVER (PARTITION BY order_id, allocation_type ORDER BY updated_at DESC) AS rn
    FROM tmmumpsdb.logistics_allocation_audit
    WHERE allocation_type = 'HARD'
      AND selected_source = 'INTERNAL'
      AND order_id IS NOT NULL
      AND created_at >= TIMESTAMP '2026-05-10 00:00:00'
      AND created_at < CURRENT_DATE
)

SELECT
    order_id,
    (allocation_metadata.warehouse_id)::int  AS warehouse_id,
    (allocation_metadata.pincode)::int        AS drop_pincode
FROM cte
WHERE rn = 1
  AND (allocation_metadata.warehouse_id)::int >= 17
ORDER BY order_id;
