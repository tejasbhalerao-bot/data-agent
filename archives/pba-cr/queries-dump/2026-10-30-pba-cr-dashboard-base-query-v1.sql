-- PBA vs internal promise adherence — base extract (DRAFT v2.1, 2026-10-19)
-- For: archives/pba-cr/insights/2026-10-14-pba-cr-pba-vs-internal-promise-adherence-v2.md (M1–M5)
-- v2.1 = the Metabase v2 query repointed at DE's per-type instrumentation tables. Logic and output columns are v2's,
-- plus four new columns at the end of the soft PBA block (switch and cache-regime facts).
--
-- Sources (prod_silver_db.logistics)
--   serviceability_eta_details               the promise the customer holds, box verified, delivered (CDC, latest version wins)
--   logistics_eta_instrumentation            ETA_INSTRUMENTATION records (soft)     — was logistics_instrumentation
--   logistics_hard_allocation_instrumentation HARD_ALLOCATION_INSTRUMENTATION records (hard) — was logistics_instrumentation
--   logistics_shipment_details               pickup and first delivery attempt (CDC, latest version wins)
--
-- Grain: one row per order (reference_id). Every CTE is keyed on reference_id, never on request_id alone, because one
-- hard-allocation request_id can cover many orders.
--   Soft record = the ETA_INSTRUMENTATION row of the same order whose request_id is the latest
--                 serviceability_eta_details version's request_id (the promise that stands).
--   Hard record = the order's last HARD_ALLOCATION_INSTRUMENTATION row.
-- Nothing is filtered out: has_soft_record, has_hard_record, has_shipment_record, is_fallback_promise, flow and the
-- *_evaluated fields let the analysis tally exclusions by reason.
--
-- Read before analysing
--   * The instrumentation tables store times WITHOUT an offset, as IST wall-clock (TIMESTAMP_NTZ). The window filter
--     on them therefore uses IST NTZ bounds (start_ist / end_ist). Times read from inside the JSON candidates carry
--     their own offset and stay TIMESTAMP_TZ.
--   * pba_soft_selected_type comes from the PBA candidate group's `source`; the PBA pick is the first ELIGIBLE partner
--     in the PBA group's evaluated_candidates (the old flattened pba_top_ranked_partner_id).
--   * PBA soft delivery anchor:
--       - 14 Oct ~23:05 IST (LMS !359) to the flip of PBA_DELIVERY_FROM_PROCESSING_ENABLED: WH processing time + PBA TAT
--       - after the flip: dispatch (after pickup buffer) + PBA TAT. pba_delivery_from_processing_enabled says which;
--         NULL on records before the 19 Oct 19:16 IST LMS release (= processing-time anchor).
--   * PBA TAT source: ClickPost cutoff configs were removed ~19:00 IST 19 Oct; rows cached before that carry the
--     cutoff-adjusted EDD (AFTER window = +1 day). pba_cache_last_cached_at tells which regime a pick used.
--   * PBA buffers: pickup on in prod; drop on from the 19 Oct 19:16 IST rollout. pba_pickup/drop_buffer_enabled are as
--     recorded per call. A missing buffer value reads as 0 when PBA was evaluated (no buffer row = no buffer applied).
--   * PBA hard delivery in the HARD record stays dispatch + TAT until TPS !928 ships.
--   * The internal side's hard dispatch and delivery are never written at hard (legacy carries only final_tat_days).
--   * box_verified_ts = actual_warehouse_processing_time (stamped by the box-verification event).
--   * pickup_time and delivery_attempt_time come from logistics_shipment_details (IST, no offset in silver).
--   * delivered_time = actual_delivery_time (ClickPost status 8 Delivered). awb_print_ts has no source here (NULL).
--   * VERSION is compared as a number (as text '11' sorts before '2').
--   * soft_matched is recomputed from the two picks (the record's flag has a known defect), soft_matched_flag is the
--     flag as recorded.
--   * The new tables only hold Kafka-era records; check their earliest EVENT_TIMESTAMP covers the window (see the
--     check at the end of this file).
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
),


-- ---------- HARD: last booking per order ----------
hard AS (
    SELECT *
    FROM hard_inst
    QUALIFY ROW_NUMBER() OVER (PARTITION BY reference_id ORDER BY created_at DESC) = 1
),


-- PBA's hard partners in LMS order (live in rollout, shadow outside it)
hard_pba_list AS (
    SELECT h.reference_id,
           c.value:decision::STRING                                                    AS pba_hard_decision,
           e.index                                                                     AS idx,
           e.value:delivery_partner_id::NUMBER                                         AS partner,
           e.value:delivery_tat_in_minutes::NUMBER                                     AS tat_in_minutes,
           TRY_TO_TIMESTAMP_TZ(e.value:dispatch_time::STRING)                          AS dispatch_time,
           TRY_TO_TIMESTAMP_TZ(e.value:delivery_time::STRING)                          AS delivery_time,
           COALESCE(e.value:excluded::BOOLEAN, FALSE)                                  AS excluded,
           e.value:service_type::STRING                                                AS service_type
    FROM hard h,
         LATERAL FLATTEN(input => h.cands) c,
         LATERAL FLATTEN(input => c.value:evaluated_candidates) e
    WHERE c.value:candidate_type::STRING = 'COURIER_PBA'
),


-- PBA's hard pick: the first partner it returned that is not excluded (FIRST_MAPPED_PARTNER)
hard_pba_pick AS (
    SELECT *
    FROM hard_pba_list
    WHERE NOT excluded
    QUALIFY ROW_NUMBER() OVER (PARTITION BY reference_id ORDER BY idx) = 1
),


hard_pba_array AS (
    SELECT reference_id,
           MAX(pba_hard_decision)                                                      AS pba_hard_decision,
           ARRAY_AGG(OBJECT_CONSTRUCT(
               'partner',        partner,
               'tat_in_minutes', tat_in_minutes,
               'dispatch_time',  dispatch_time,
               'delivery_time',  delivery_time,
               'excluded',       excluded,
               'service_type',   service_type
           )) WITHIN GROUP (ORDER BY idx)                                              AS pba_hard_preference_array
    FROM hard_pba_list
    GROUP BY reference_id
),


-- Internal hard side: the evaluated internal store's ranked candidates
hard_internal_list AS (
    SELECT h.reference_id,
           c.value:candidate_type::STRING                                              AS candidate_type,
           b.value:delivery_partner_id::NUMBER                                         AS partner,
           b.value:rank::NUMBER                                                        AS rnk,
           b.value:selected::BOOLEAN                                                   AS selected
    FROM hard h,
         LATERAL FLATTEN(input => h.cands) c,
         LATERAL FLATTEN(input => c.value:buffer_adjusted_candidates) b
    WHERE c.value:candidate_type::STRING IN ('COURIER_LEGACY_TAT_ADHERENCE', 'COURIER_DDB_TAT_ADHERENCE')
      AND c.value:evaluated::BOOLEAN
),


-- each internal partner's final TAT on the hard path, from the same store's evaluated candidates
hard_internal_tat AS (
    SELECT h.reference_id,
           c.value:candidate_type::STRING                                              AS candidate_type,
           t.value:delivery_partner_id::NUMBER                                         AS partner,
           MAX(t.value:final_tat_days::FLOAT)                                          AS final_tat_days
    FROM hard h,
         LATERAL FLATTEN(input => h.cands) c,
         LATERAL FLATTEN(input => c.value:evaluated_candidates) t
    WHERE c.value:candidate_type::STRING IN ('COURIER_LEGACY_TAT_ADHERENCE', 'COURIER_DDB_TAT_ADHERENCE')
      AND c.value:evaluated::BOOLEAN
    GROUP BY 1, 2, 3
),


hard_internal AS (
    SELECT l.reference_id,
           MAX(l.candidate_type)                                                       AS internal_hard_candidate_type,
           MIN_BY(l.partner, l.rnk)                                                    AS internal_hard_partner,
           MIN_BY(t.final_tat_days, l.rnk)                                             AS internal_hard_tat_in_days,
           ARRAY_AGG(OBJECT_CONSTRUCT(
               'partner',        l.partner,
               'rank',           l.rnk,
               'selected',       l.selected,
               'final_tat_days', t.final_tat_days
           )) WITHIN GROUP (ORDER BY l.rnk)                                            AS internal_hard_preference_array
    FROM hard_internal_list l
    LEFT JOIN hard_internal_tat t
           ON t.reference_id = l.reference_id AND t.candidate_type = l.candidate_type AND t.partner = l.partner
    GROUP BY l.reference_id
)


SELECT
    -- identity and cohort
    f.reference_id                                              AS order_id,
    f.customer_id,
    f.warehouse_id                                              AS wh_id,
    f.delivery_pincode                                          AS pincode,
    f.order_placed_at,
    TRY_TO_NUMBER(f.version)                                    AS eta_details_version,
    f.request_id                                                AS promise_request_id,
    f.sdd_enabled,
    f.payment_method,
    f.task_processing_type,
    (s.reference_id IS NOT NULL)                                AS has_soft_record,
    (h.reference_id IS NOT NULL)                                AS has_hard_record,
    (sh.reference_id IS NOT NULL)                               AS has_shipment_record,
    (TRY_TO_NUMBER(f.delivery_partner_id) = 0 OR f.promised_delivery_time IS NULL) AS is_fallback_promise,
    s.fact_flow                                                 AS flow,
    s.fact_delivery_type                                        AS delivery_type,
    s.fact_payment_mode                                         AS payment_mode,
    s.cfg_pba_rollout_in_rollout = 'TRUE'                       AS pba_in_rollout,
    s.created_at                                                AS soft_promise_at,
    s.fact_client_id                                            AS soft_caller,
    s.req_context_screen_context                                AS soft_screen,


    -- the promise the customer holds (latest version)
    f.promised_warehouse_processing_time,
    f.promised_dispatch_time,
    f.promised_delivery_time,
    f.promised_delivery_partner,
    TRY_TO_NUMBER(f.delivery_tat_minutes) / 1440.0              AS promised_tat_in_days,
    s.fact_is_cold_chain                                        AS pba_is_cold_chain,
    s.fact_is_express_eligible                                  AS pba_is_express_eligible,


    -- soft: what was served
    s.result_selected_candidate_type                            AS soft_served_candidate_type,
    s.result_delivery_partner_id                                AS soft_served_partner,
    s.result_dispatch_time                                      AS soft_served_dispatch_time,
    s.result_delivery_time                                      AS soft_served_delivery_time,
    (pp.pba_partner IS NOT NULL AND si.internal_partner IS NOT NULL
        AND pp.pba_partner = si.internal_partner)               AS soft_matched,
    s.result_pba_and_internal_same_partner                      AS soft_matched_flag,


    -- soft: PBA side (M1/M2)
    sp.pba_evaluated,
    sp.pba_decision,
    sp.pba_decision_detail,
    sp.pba_to_internal_tat_ratio,
    sp.pba_source                                               AS pba_soft_selected_type,      -- PBA_CACHE / PBA_API / NONE
    pp.pba_partner                                              AS pba_soft_selected_delivery_partner,
    pp.pba_tat_in_minutes / 1440.0                              AS pba_soft_selected_partner_tat_in_days,
    COALESCE(pb.pba_buffered_dispatch_time, pp.pba_dispatch_time) AS pba_projected_dispatch_time,
    COALESCE(pb.pba_buffered_delivery_time, pp.pba_delivery_time) AS pba_projected_delivery_time,
    IFF(sp.pba_evaluated, COALESCE(pb.pba_pickup_buffer, 0), NULL) AS pba_pickup_buffer,
    IFF(sp.pba_evaluated, COALESCE(pb.pba_drop_buffer, 0), NULL)   AS pba_drop_buffer,
    pp.pba_is_express,
    pp.pba_cache_lookup,
    pp.pba_cache_age_minutes,
    pp.pba_cutoff_window,
    sp.pba_soft_preference_array,
    s.payload:evaluation:configurations:pba_delivery_from_processing_enabled::BOOLEAN AS pba_delivery_from_processing_enabled,
    s.cfg_pba_pickup_buffer_enabled                             AS pba_pickup_buffer_enabled,
    s.cfg_pba_drop_buffer_enabled                               AS pba_drop_buffer_enabled,
    pp.pba_cache_last_cached_at,


    -- soft: internal side (M1/M2)
    si.internal_candidate_type,
    si.internal_partner                                         AS internal_soft_selected_delivery_partner,
    si.internal_tat_in_minutes / 1440.0                         AS internal_soft_selected_partner_tat_in_days,
    si.internal_dispatch_time                                   AS internal_projected_dispatch_time,
    si.internal_delivery_time                                   AS internal_projected_delivery_time,
    si.internal_pickup_buffer,
    si.internal_drop_buffer,
    si.internal_is_express,
    si.internal_soft_preference_array,


    -- hard (M3/M4/M5)
    h.request_id                                                AS hard_request_id,
    h.created_at                                                AS hard_allocated_at,
    h.result_outcome                                            AS hard_outcome,
    h.result_selected_candidate_type                            AS hard_selected_candidate_type,
    h.result_delivery_partner_id                                AS hard_booked_partner,
    h.result_delivery_tat_in_minutes / 1440.0                   AS hard_booked_tat_in_days,
    h.fact_projected_wh_processing_time                         AS hard_wh_processing_time,
    hpa.pba_hard_decision,
    hpp.partner                                                 AS pba_hard_selected_delivery_partner,
    hpp.tat_in_minutes / 1440.0                                 AS pba_hard_partner_tat_in_days,
    hpp.dispatch_time                                           AS pba_hard_projected_dispatch_time,
    hpp.delivery_time                                           AS pba_hard_projected_delivery_time,
    hpa.pba_hard_preference_array,
    hi.internal_hard_candidate_type,
    hi.internal_hard_partner                                    AS internal_hard_selected_delivery_partner,
    hi.internal_hard_tat_in_days                                AS internal_hard_partner_tat_in_days,
    NULL::TIMESTAMP_TZ                                          AS internal_hard_projected_dispatch_time,   -- never written at hard
    NULL::TIMESTAMP_TZ                                          AS internal_hard_projected_delivery_time,   -- never written at hard
    hi.internal_hard_preference_array,


    -- actuals (M3/M4)
    f.actual_warehouse_processing_time                          AS box_verified_ts,
    NULL::TIMESTAMP_TZ                                          AS awb_print_ts,                            -- no source in these tables
    sh.pickup_time,
    sh.first_delivery_attempt_time                              AS delivery_attempt_time,
    f.actual_delivery_time                                      AS delivered_time,
    sh.delivery_partner_id                                      AS shipped_delivery_partner,
    sh.promised_delivery_in_minutes                             AS shipment_promised_delivery_in_minutes,
    sh.applied_drop_buffer_in_minutes                           AS shipment_applied_drop_buffer_in_minutes
FROM frozen f
LEFT JOIN soft            s   ON s.reference_id   = f.reference_id
LEFT JOIN soft_pba        sp  ON sp.reference_id  = f.reference_id
LEFT JOIN soft_pba_pick   pp  ON pp.reference_id  = f.reference_id
LEFT JOIN soft_pba_buffer pb  ON pb.reference_id  = f.reference_id
LEFT JOIN soft_internal   si  ON si.reference_id  = f.reference_id
LEFT JOIN hard            h   ON h.reference_id   = f.reference_id
LEFT JOIN hard_pba_pick   hpp ON hpp.reference_id = f.reference_id
LEFT JOIN hard_pba_array  hpa ON hpa.reference_id = f.reference_id
LEFT JOIN hard_internal   hi  ON hi.reference_id  = f.reference_id
LEFT JOIN shipment        sh  ON sh.reference_id  = f.reference_id
;


-- Check (run on its own): do the old and new instrumentation tables cover the window?
-- SELECT 'old logistics_instrumentation' AS src, MIN(created_at), MAX(created_at)
-- FROM prod_silver_db.logistics.logistics_instrumentation
-- WHERE instrumentation_type IN ('ETA_INSTRUMENTATION', 'HARD_ALLOCATION_INSTRUMENTATION')
-- UNION ALL SELECT 'logistics_eta_instrumentation', MIN(created_at), MAX(created_at)
-- FROM prod_silver_db.logistics.logistics_eta_instrumentation
-- UNION ALL SELECT 'logistics_hard_allocation_instrumentation', MIN(created_at), MAX(created_at)
-- FROM prod_silver_db.logistics.logistics_hard_allocation_instrumentation;
