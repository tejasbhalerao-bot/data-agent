WITH base AS (
WITH params AS (
    SELECT '2026-10-22 12:00:00 +0530'::TIMESTAMP_TZ AS start_ts,
           '2026-10-26 00:00:00 +0530'::TIMESTAMP_TZ AS end_ts
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
        -- performance pre-filter (added 2026-10-30, not in the v2.1 base): keeps every row of any order with a promise row inside the window;
        -- an order kept by the placed-at filter below always has one, so results are unchanged (proven on slice and on full window)
        WHERE d.reference_id IN (SELECT w.reference_id FROM prod_silver_db.logistics.serviceability_eta_details w CROSS JOIN params p
                                 WHERE w.created_at >= p.start_ts AND w.created_at < p.end_ts)
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
    f.sdd_enabled,
    f.warehouse_id                                              AS wh_id,
    f.delivery_pincode                                          AS pincode,
    s.result_selected_candidate_type                            AS soft_served_candidate_type
FROM frozen f
LEFT JOIN soft            s   ON s.reference_id   = f.reference_id
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
),
kb AS (
    SELECT order_id,
           CASE WHEN soft_served_candidate_type = 'COURIER_PBA' THEN 'PBA'
                WHEN soft_served_candidate_type IN ('COURIER_LEGACY_TAT_ADHERENCE', 'COURIER_DDB_TAT_ADHERENCE') THEN 'Internal' END AS base_group,
           TO_VARCHAR(wh_id) || '|' || TO_VARCHAR(pincode) AS lane
    FROM placed
    WHERE placed_flag = 'kept' AND sdd_enabled = FALSE
),
lanes AS (
    SELECT lane, COUNT_IF(base_group = 'PBA') AS n_pba, COUNT_IF(base_group = 'Internal') AS n_internal
    FROM kb WHERE base_group IS NOT NULL
    GROUP BY lane
),
ko AS (
    SELECT kb.order_id, kb.base_group, kb.lane, (l.n_pba > 0 AND l.n_internal > 0) AS is_common
    FROM kb
    JOIN lanes l ON l.lane = kb.lane
    WHERE kb.base_group IS NOT NULL
)
SELECT base_group, is_common, COUNT(*) AS n_orders, COUNT(DISTINCT order_id) AS n_distinct_orders, COUNT(DISTINCT lane) AS n_lanes,
       LISTAGG(IFF(is_common, order_id, NULL), ',') WITHIN GROUP (ORDER BY order_id) AS order_list,
       ANY_VALUE(MD5(SUBSTR(CURRENT_STATEMENT(),
                  CHARINDEX('WITH params AS (', CURRENT_STATEMENT()),
                  CHARINDEX(CHR(10) || ')' || CHR(10) || 'SELECT', CURRENT_STATEMENT()) - CHARINDEX('WITH params AS (', CURRENT_STATEMENT())))) AS base_md5
FROM ko
GROUP BY 1, 2
ORDER BY 1, 2
