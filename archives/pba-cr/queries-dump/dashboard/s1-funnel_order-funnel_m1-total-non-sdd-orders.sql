WITH base AS (
WITH params AS (
    SELECT '2026-10-22 12:00:00 +0530'::TIMESTAMP_TZ AS start_ts,
           '2026-10-26 00:00:00 +0530'::TIMESTAMP_TZ AS end_ts
),
frozen AS (
    SELECT v.*
    FROM (
        SELECT d.*,
               MIN(d.created_at) OVER (PARTITION BY d.reference_id) AS order_placed_at
        FROM prod_silver_db.logistics.serviceability_eta_details d
        QUALIFY ROW_NUMBER() OVER (PARTITION BY d.reference_id ORDER BY TRY_TO_NUMBER(d.version) DESC) = 1
    ) v
    CROSS JOIN params p
    WHERE v.order_placed_at >= p.start_ts AND v.order_placed_at < p.end_ts
)

SELECT
    f.reference_id                                              AS order_id,
    f.order_placed_at,
    f.sdd_enabled
FROM frozen f
),
od AS (
    SELECT order_id, orderstatus
    FROM prod_silver_db.main_db.order_details
    WHERE order_id IN (SELECT TRY_TO_NUMBER(order_id) FROM base)
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY ingestion_ts_ist DESC) = 1
),
placed AS (
    SELECT b.*,
           CASE WHEN od.order_id IS NULL            THEN 'no_status_row'
                WHEN od.orderstatus IN (49, 312)    THEN 'dropped'
                ELSE 'kept' END                     AS placed_flag
    FROM base b
    LEFT JOIN od ON od.order_id = TRY_TO_NUMBER(b.order_id)
)
SELECT placed_flag, TO_VARCHAR(sdd_enabled) AS sdd_enabled_value, COUNT(*) AS n_rows, COUNT(DISTINCT order_id) AS n_orders,
       TO_VARCHAR(MIN(order_placed_at)) AS min_placed, TO_VARCHAR(MAX(order_placed_at)) AS max_placed,
       ANY_VALUE(MD5(SUBSTR(CURRENT_STATEMENT(),
                  CHARINDEX('WITH params AS (', CURRENT_STATEMENT()),
                  CHARINDEX(CHR(10) || ')' || CHR(10) || 'SELECT', CURRENT_STATEMENT()) - CHARINDEX('WITH params AS (', CURRENT_STATEMENT())))) AS base_md5
FROM placed
GROUP BY 1, 2
ORDER BY 1, 2
