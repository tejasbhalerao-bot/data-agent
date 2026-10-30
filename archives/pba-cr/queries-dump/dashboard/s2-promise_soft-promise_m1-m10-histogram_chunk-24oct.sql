WITH base AS (
WITH params AS (
    SELECT '2026-10-24 00:00:00 +0530'::TIMESTAMP_TZ AS start_ts,
           '2026-10-25 00:00:00 +0530'::TIMESTAMP_TZ AS end_ts
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
),


soft_pba AS (
    SELECT s.reference_id,
           MAX(c.value:evaluated::BOOLEAN)                                             AS pba_evaluated,
           MAX(c.value:decision::STRING)                                               AS pba_decision,
           MAX(c.value:decision_detail::STRING)                                        AS pba_decision_detail,
           MAX(c.value:pba_to_internal_tat_ratio::FLOAT)                               AS pba_to_internal_tat_ratio,
           MAX(c.value:source::STRING)                                                 AS pba_source,
           ARRAY_AGG(OBJECT_CONSTRUCT(
               'partner',           e.value:delivery_partner_id,
               'tat_in_minutes',    e.value:delivery_tat_in_minutes,
               'dispatch_time',     e.value:dispatch_time,
               'delivery_time',     e.value:delivery_time,
               'eligible',          e.value:eligible,
               'is_express',        e.value:is_express,
               'cache_lookup',      e.value:cache_row:cache_lookup,
               'cache_age_minutes', e.value:cache_row:cache_age_minutes,
               'cutoff_window',     e.value:cache_row:cutoff_window
           )) WITHIN GROUP (ORDER BY e.index)                                          AS pba_soft_preference_array
    FROM soft s,
         LATERAL FLATTEN(input => s.cands) c,
         LATERAL FLATTEN(input => c.value:evaluated_candidates, OUTER => TRUE) e
    WHERE c.value:candidate_type::STRING = 'COURIER_PBA'
    GROUP BY s.reference_id
),


-- PBA's soft pick: the top-ranked PBA partner (first eligible in PBA's order), whether or not it was served
soft_pba_pick AS (
    SELECT s.reference_id,
           e.value:delivery_partner_id::NUMBER                                         AS pba_partner,
           e.value:delivery_tat_in_minutes::NUMBER                                     AS pba_tat_in_minutes,
           TRY_TO_TIMESTAMP_TZ(e.value:dispatch_time::STRING)                          AS pba_dispatch_time,
           TRY_TO_TIMESTAMP_TZ(e.value:delivery_time::STRING)                          AS pba_delivery_time,
           e.value:is_express::BOOLEAN                                                 AS pba_is_express,
           e.value:cache_row:cache_lookup::STRING                                      AS pba_cache_lookup,
           e.value:cache_row:cache_age_minutes::NUMBER                                 AS pba_cache_age_minutes,
           e.value:cache_row:cutoff_window::STRING                                     AS pba_cutoff_window,
           TRY_TO_TIMESTAMP_TZ(e.value:cache_row:last_cached_at::STRING)               AS pba_cache_last_cached_at
    FROM soft s,
         LATERAL FLATTEN(input => s.cands) c,
         LATERAL FLATTEN(input => c.value:evaluated_candidates) e
    WHERE c.value:candidate_type::STRING = 'COURIER_PBA'
      AND e.value:eligible::BOOLEAN
    QUALIFY ROW_NUMBER() OVER (PARTITION BY s.reference_id ORDER BY e.index) = 1
),


-- PBA buffers and buffered times on the soft side (present only when PBA was served)
soft_pba_buffer AS (
    SELECT s.reference_id,
           b.value:pickup_buffer_in_minutes::NUMBER                                    AS pba_pickup_buffer,
           b.value:drop_buffer_in_minutes::NUMBER                                      AS pba_drop_buffer,
           TRY_TO_TIMESTAMP_TZ(b.value:dispatch_time::STRING)                          AS pba_buffered_dispatch_time,
           TRY_TO_TIMESTAMP_TZ(b.value:delivery_time::STRING)                          AS pba_buffered_delivery_time
    FROM soft s,
         LATERAL FLATTEN(input => s.cands) c,
         LATERAL FLATTEN(input => c.value:buffer_adjusted_candidates) b
    WHERE c.value:candidate_type::STRING = 'COURIER_PBA'
      AND b.value:rank::NUMBER = 1
    QUALIFY ROW_NUMBER() OVER (PARTITION BY s.reference_id ORDER BY b.index) = 1
),


-- Internal soft side: the evaluated internal store (pharmacist or DDB TAT adherence), ranked after buffers.
-- Rank 1 is internal's pick whether or not it was served.
soft_internal AS (
    SELECT s.reference_id,
           MAX(c.value:candidate_type::STRING)                                                          AS internal_candidate_type,
           MAX(IFF(b.value:rank::NUMBER = 1, b.value:delivery_partner_id::NUMBER, NULL))                AS internal_partner,
           MAX(IFF(b.value:rank::NUMBER = 1, b.value:delivery_tat_in_minutes::NUMBER, NULL))            AS internal_tat_in_minutes,
           MAX(IFF(b.value:rank::NUMBER = 1, TRY_TO_TIMESTAMP_TZ(b.value:dispatch_time::STRING), NULL)) AS internal_dispatch_time,
           MAX(IFF(b.value:rank::NUMBER = 1, TRY_TO_TIMESTAMP_TZ(b.value:delivery_time::STRING), NULL)) AS internal_delivery_time,
           MAX(IFF(b.value:rank::NUMBER = 1, b.value:pickup_buffer_in_minutes::NUMBER, NULL))           AS internal_pickup_buffer,
           MAX(IFF(b.value:rank::NUMBER = 1, b.value:drop_buffer_in_minutes::NUMBER, NULL))             AS internal_drop_buffer,
           MAX(IFF(b.value:rank::NUMBER = 1, b.value:is_express::BOOLEAN, NULL))                        AS internal_is_express,
           ARRAY_AGG(OBJECT_CONSTRUCT(
               'partner',        b.value:delivery_partner_id,
               'rank',           b.value:rank,
               'tat_in_minutes', b.value:delivery_tat_in_minutes,
               'dispatch_time',  b.value:dispatch_time,
               'delivery_time',  b.value:delivery_time,
               'score',          b.value:score
           )) WITHIN GROUP (ORDER BY b.value:rank::NUMBER)                                              AS internal_soft_preference_array
    FROM soft s,
         LATERAL FLATTEN(input => s.cands) c,
         LATERAL FLATTEN(input => c.value:buffer_adjusted_candidates) b
    WHERE c.value:candidate_type::STRING IN ('COURIER_LEGACY_TAT_ADHERENCE', 'COURIER_DDB_TAT_ADHERENCE')
      AND c.value:evaluated::BOOLEAN
    GROUP BY s.reference_id
)


SELECT
    f.reference_id                                              AS order_id,
    f.order_placed_at,
    f.sdd_enabled,
    f.warehouse_id                                              AS wh_id,
    f.delivery_pincode                                          AS pincode,
    (s.reference_id IS NOT NULL)                                AS has_soft_record,
    s.result_selected_candidate_type                            AS soft_served_candidate_type,
    f.promised_warehouse_processing_time,
    COALESCE(pb.pba_buffered_dispatch_time, pp.pba_dispatch_time) AS pba_projected_dispatch_time,
    COALESCE(pb.pba_buffered_delivery_time, pp.pba_delivery_time) AS pba_projected_delivery_time,
    si.internal_dispatch_time                                   AS internal_projected_dispatch_time,
    si.internal_delivery_time                                   AS internal_projected_delivery_time
FROM frozen f
LEFT JOIN soft            s   ON s.reference_id   = f.reference_id
LEFT JOIN soft_pba_pick   pp  ON pp.reference_id  = f.reference_id
LEFT JOIN soft_pba_buffer pb  ON pb.reference_id  = f.reference_id
LEFT JOIN soft_internal   si  ON si.reference_id  = f.reference_id
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
base_l AS (
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
),
kb AS (
    SELECT p.*,
           CASE WHEN soft_served_candidate_type = 'COURIER_PBA' THEN 'PBA'
                WHEN soft_served_candidate_type IN ('COURIER_LEGACY_TAT_ADHERENCE', 'COURIER_DDB_TAT_ADHERENCE') THEN 'Internal' END AS base_group,
           TO_VARCHAR(wh_id) || '|' || TO_VARCHAR(pincode) AS lane
    FROM placed p
    WHERE placed_flag = 'kept' AND sdd_enabled = FALSE
),
kb_l AS (
    SELECT CASE WHEN soft_served_candidate_type = 'COURIER_PBA' THEN 'PBA'
                WHEN soft_served_candidate_type IN ('COURIER_LEGACY_TAT_ADHERENCE', 'COURIER_DDB_TAT_ADHERENCE') THEN 'Internal' END AS base_group,
           TO_VARCHAR(wh_id) || '|' || TO_VARCHAR(pincode) AS lane
    FROM placed_l
    WHERE placed_flag = 'kept' AND sdd_enabled = FALSE
),
common_lanes AS (
    SELECT lane FROM kb_l WHERE base_group IS NOT NULL
    GROUP BY lane
    HAVING COUNT_IF(base_group = 'PBA') > 0 AND COUNT_IF(base_group = 'Internal') > 0
),
d AS (
    SELECT kb.base_group,
           (cl.lane IS NOT NULL) AS common_lane,
           DATEDIFF(day, TO_DATE(CONVERT_TIMEZONE('Asia/Kolkata', promised_warehouse_processing_time)), TO_DATE(CONVERT_TIMEZONE('Asia/Kolkata', pba_projected_delivery_time)))      AS wh_pba,
           DATEDIFF(day, TO_DATE(CONVERT_TIMEZONE('Asia/Kolkata', promised_warehouse_processing_time)), TO_DATE(CONVERT_TIMEZONE('Asia/Kolkata', internal_projected_delivery_time))) AS wh_int,
           DATEDIFF(day, TO_DATE(CONVERT_TIMEZONE('Asia/Kolkata', pba_projected_dispatch_time)), TO_DATE(CONVERT_TIMEZONE('Asia/Kolkata', pba_projected_delivery_time)))                 AS dd_pba,
           DATEDIFF(day, TO_DATE(CONVERT_TIMEZONE('Asia/Kolkata', internal_projected_dispatch_time)), TO_DATE(CONVERT_TIMEZONE('Asia/Kolkata', internal_projected_delivery_time)))       AS dd_int,
           SYSTEM$TYPEOF(promised_warehouse_processing_time) || ' / ' || SYSTEM$TYPEOF(pba_projected_delivery_time) || ' / ' || SYSTEM$TYPEOF(internal_projected_delivery_time) AS ts_types
    FROM kb
    LEFT JOIN common_lanes cl ON cl.lane = kb.lane
    WHERE kb.base_group IS NOT NULL
),
u AS (
    SELECT base_group, common_lane, measure, days, ts_types
    FROM d UNPIVOT INCLUDE NULLS (days FOR measure IN (wh_pba, wh_int, dd_pba, dd_int))
)
SELECT base_group, common_lane, measure, days, COUNT(*) AS n_orders, MIN(ts_types) AS ts_types_min, MAX(ts_types) AS ts_types_max,
       (SELECT COUNT(*) FROM common_lanes) AS n_common_lanes,
       ANY_VALUE(MD5(SUBSTR(CURRENT_STATEMENT(),
                  CHARINDEX('WITH params AS (', CURRENT_STATEMENT()),
                  CHARINDEX(CHR(10) || ')' || CHR(10) || 'SELECT', CURRENT_STATEMENT()) - CHARINDEX('WITH params AS (', CURRENT_STATEMENT())))) AS base_md5
FROM u
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3, 4
