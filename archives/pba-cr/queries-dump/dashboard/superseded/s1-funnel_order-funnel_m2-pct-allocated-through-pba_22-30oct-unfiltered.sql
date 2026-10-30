WITH base AS (
WITH params AS (
    SELECT '2026-10-22 12:00:00 +0530'::TIMESTAMP_TZ AS start_ts,
           '2026-10-30 00:00:00 +0530'::TIMESTAMP_TZ AS end_ts
),


-- the same window as IST wall-clock, for the NTZ instrumentation tables
params_ist AS (
    SELECT CONVERT_TIMEZONE('Asia/Kolkata', start_ts)::TIMESTAMP_NTZ AS start_ist,
           CONVERT_TIMEZONE('Asia/Kolkata', end_ts)::TIMESTAMP_NTZ   AS end_ist
    FROM params
),


-- latest version of each order's promise, with its placement time taken over all versions
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
),


shipment AS (
    SELECT s.*
    FROM prod_silver_db.logistics.logistics_shipment_details s
    JOIN frozen f ON f.reference_id = s.reference_id
    WHERE COALESCE(s.is_deleted, FALSE) = FALSE
    QUALIFY ROW_NUMBER() OVER (PARTITION BY s.reference_id ORDER BY TRY_TO_NUMBER(s.version) DESC) = 1
),


-- ETA records of the cohort's orders
eta_inst AS (
    SELECT i.*,
           TRY_PARSE_JSON(TO_VARCHAR(i.eval_candidates)) AS cands
    FROM prod_silver_db.logistics.logistics_eta_instrumentation i
    JOIN frozen f ON f.reference_id = i.reference_id
    CROSS JOIN params_ist p
    WHERE i.created_at >= DATEADD(day, -1, p.start_ist)      -- a promise can be computed shortly before the order is placed
      AND i.created_at <  DATEADD(day, 10, p.end_ist)
),


-- hard-allocation records of the cohort's orders
hard_inst AS (
    SELECT i.*,
           TRY_PARSE_JSON(TO_VARCHAR(i.eval_candidates)) AS cands
    FROM prod_silver_db.logistics.logistics_hard_allocation_instrumentation i
    JOIN frozen f ON f.reference_id = i.reference_id
    CROSS JOIN params_ist p
    WHERE i.created_at >= DATEADD(day, -1, p.start_ist)
      AND i.created_at <  DATEADD(day, 10, p.end_ist)        -- hard allocations land after the soft window
),


-- ---------- SOFT: the ETA record of the promise that stands ----------
soft AS (
    SELECT i.*
    FROM eta_inst i
    JOIN frozen f ON f.reference_id = i.reference_id AND f.request_id = i.request_id
    QUALIFY ROW_NUMBER() OVER (PARTITION BY i.reference_id ORDER BY i.created_at DESC) = 1
)


SELECT
    f.reference_id                                              AS order_id,
    f.order_placed_at,
    f.sdd_enabled,
    (s.reference_id IS NOT NULL)                                AS has_soft_record,
    s.cfg_pba_rollout_in_rollout = 'TRUE'                       AS pba_in_rollout,
    s.result_selected_candidate_type                            AS soft_served_candidate_type
FROM frozen f
LEFT JOIN soft            s   ON s.reference_id   = f.reference_id
)
SELECT GROUPING(TO_VARCHAR(sdd_enabled))         AS is_total,
       TO_VARCHAR(sdd_enabled)                   AS sdd_enabled_value,
       TO_VARCHAR(has_soft_record)               AS has_soft_record_value,
       TO_VARCHAR(pba_in_rollout)                AS pba_in_rollout_value,
       soft_served_candidate_type,
       COUNT(*)                                  AS n_rows,
       COUNT(DISTINCT order_id)                  AS n_orders,
       ANY_VALUE(MD5(SUBSTR(CURRENT_STATEMENT(),
                  CHARINDEX('WITH params AS (', CURRENT_STATEMENT()),
                  CHARINDEX(CHR(10) || ')' || CHR(10) || 'SELECT', CURRENT_STATEMENT()) - CHARINDEX('WITH params AS (', CURRENT_STATEMENT())))) AS base_md5
FROM base
GROUP BY GROUPING SETS ((TO_VARCHAR(sdd_enabled), TO_VARCHAR(has_soft_record), TO_VARCHAR(pba_in_rollout), soft_served_candidate_type), ())
ORDER BY is_total, sdd_enabled_value, has_soft_record_value, pba_in_rollout_value, soft_served_candidate_type
