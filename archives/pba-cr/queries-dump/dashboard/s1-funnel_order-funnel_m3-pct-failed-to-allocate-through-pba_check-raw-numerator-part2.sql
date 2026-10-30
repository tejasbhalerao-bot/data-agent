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
),
ids AS (
    SELECT order_id AS reference_id
    FROM base
    WHERE sdd_enabled = FALSE AND pba_in_rollout
      AND soft_served_candidate_type IN ('COURIER_LEGACY_TAT_ADHERENCE', 'COURIER_DDB_TAT_ADHERENCE', 'NONE')
      AND MOD(ABS(HASH(order_id)), 3) = 2
)
SELECT 'V' AS src, d.reference_id, TO_VARCHAR(d.version) AS version, d.request_id, TO_VARCHAR(d.created_at) AS created_at, TO_VARCHAR(d.sdd_enabled) AS val, NULL AS rollout
FROM prod_silver_db.logistics.serviceability_eta_details d JOIN ids USING (reference_id)
UNION ALL
SELECT 'E', i.reference_id, NULL, i.request_id, TO_VARCHAR(i.created_at), i.result_selected_candidate_type, TO_VARCHAR(i.cfg_pba_rollout_in_rollout)
FROM prod_silver_db.logistics.logistics_eta_instrumentation i JOIN ids USING (reference_id)
WHERE i.created_at >= '2026-10-21 12:00:00'::TIMESTAMP_NTZ AND i.created_at < '2026-11-09 00:00:00'::TIMESTAMP_NTZ
ORDER BY 2, 1, 5
