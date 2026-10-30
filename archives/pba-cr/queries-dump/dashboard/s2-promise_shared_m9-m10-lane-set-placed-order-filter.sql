),
od_l AS (
    SELECT order_id, orderstatus
    FROM prod_silver_db.main_db.order_details
    WHERE order_id IN (SELECT TRY_TO_NUMBER(order_id) FROM base_l)
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY ingestion_ts_ist DESC) = 1
),
placed_l AS (
    SELECT b.*,
           CASE WHEN od.order_id IS NULL            THEN 'no_status_row'
                WHEN od.orderstatus IN (49, 312)    THEN 'dropped'
                ELSE 'kept' END                     AS placed_flag
    FROM base_l b
    LEFT JOIN od_l od ON od.order_id = TRY_TO_NUMBER(b.order_id)