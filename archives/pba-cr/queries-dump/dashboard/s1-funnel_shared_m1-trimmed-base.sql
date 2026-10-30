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