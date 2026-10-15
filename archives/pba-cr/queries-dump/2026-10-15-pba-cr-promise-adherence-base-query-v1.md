# PBA promise adherence base extract (v1, superseded)

- **Status:** superseded by v2. Kept for the record; do not run.
- **Purpose:** one row per order with the soft promise (PBA and internal), the hard allocation (PBA and internal), and actuals.
- **Serves:** M1, M2, M3, M4, M5
- **Grain:** one row per order (`reference_id`), from the order's latest `serviceability_eta_details` version.
- **Tables:** `prod_silver_db.logistics.serviceability_eta_details`, `prod_silver_db.logistics.logistics_instrumentation` (ETA_INSTRUMENTATION, HARD_ALLOCATION_INSTRUMENTATION). Snowflake, not yet in `context/schema.md`.
- **Definitions used:** the v2 brief's metrics table (no `metrics.md` entries).
- **Filters:** order window 14–24 Oct on the latest version's `created_at`; instrumentation from 1 day before to 10 days after the window.
- **Expected shape:** 79 columns.
- **Timeout risk:** Medium (window functions over the full instrumentation range).
- **Save the CSV as:** not to be run.
- **Known issues (why it was replaced):**
  1. The hard CTEs group and join on `request_id`. A bulk hard allocation shares one `request_id` across many orders, so their values get mixed (one sample row had 163 partners in its internal hard array, all rank 1).
  2. `delivery_attempt_time` is NULL; `pickup_time` comes from `actual_dispatch_time`.
  3. The window starts before the CR went live (14 Oct, about 23:05).
  4. `order_placed_at` is the latest version's `created_at`, not when the order was placed.
  5. PBA buffers are blank when PBA was not served; `soft_matched` uses the recorded flag, which has a known defect.
- **Source:** engineering draft `29-pba-promise-adherence-base-query (1).sql`, received 2026-10-14.

```sql
-- PBA vs internal promise adherence — base extract (DRAFT, 2026-10-14)
-- For: archives/pba-cr/insights/2026-10-14-pba-cr-pba-vs-internal-promise-adherence-v2.md (M1–M5)
-- Sources: prod_silver_db.logistics.serviceability_eta_details (the order's promise and actuals, CDC, one row per version)
--          prod_silver_db.logistics.logistics_instrumentation (ETA_INSTRUMENTATION, HARD_ALLOCATION_INSTRUMENTATION)
-- Grain: one row per order (reference_id), driven by the order's LATEST serviceability_eta_details version.
--   Soft side = the ETA_INSTRUMENTATION record whose request_id is that version's request_id (the promise that stands).
--   Hard side = the order's last HARD_ALLOCATION_INSTRUMENTATION record.
-- Nothing is filtered out: has_soft_record / has_hard_record, flow and the *_evaluated flags let the analysis tally
-- exclusions by reason.
--
-- Notes the analysis must know:
--   * PBA soft delivery = PT + PBA TAT from 2026-10-14 ~23:05 IST (LMS !359). Records before that are dispatch + TAT.
--   * PBA hard delivery in the HARD record = dispatch + TAT until TPS !928 ships (then PT + TAT).
--   * The internal side's hard dispatch/delivery is not instrumented (legacy candidates carry only final_tat_days).
--   * Actuals (box verified, pickup, delivered) come from the same latest serviceability_eta_details version, AWB print
--     and delivery attempt are not in these tables (left NULL).
--   * VERSION is compared as a number (as text '11' sorts before '2').
--   * A latest version can be a fallback re-freeze with no promised times (DELIVERY_PARTNER_ID 0), is_fallback_promise
--     flags it so it can be excluded.
--   * ETA_INSTRUMENTATION exists from 2026-10-13 ~22:56 IST, orders frozen earlier have has_soft_record = FALSE.
--   * Partner preference arrays are in LMS order (PBA) and rank order (internal).

-- Window: edit the two dates in params (order placement time, IST). Single statement, so it runs in Metabase as is.
WITH params AS (
    SELECT '2026-10-14 00:00:00 +0530'::TIMESTAMP_TZ AS start_ts,
           '2026-10-24 00:00:00 +0530'::TIMESTAMP_TZ AS end_ts
),

frozen AS (
    SELECT d.*
    FROM prod_silver_db.logistics.serviceability_eta_details d, params p
    WHERE d.created_at >= p.start_ts AND d.created_at < p.end_ts
    QUALIFY ROW_NUMBER() OVER (PARTITION BY d.reference_id ORDER BY TRY_TO_NUMBER(d.version) DESC) = 1
),

inst AS (
    SELECT i.*,
           TRY_PARSE_JSON(TO_VARCHAR(i.eval_candidates)) AS cands
    FROM prod_silver_db.logistics.logistics_instrumentation i, params p
    WHERE i.instrumentation_type IN ('ETA_INSTRUMENTATION', 'HARD_ALLOCATION_INSTRUMENTATION')
      AND i.created_at >= DATEADD(day, -1, p.start_ts)       -- a promise can be computed shortly before the order is placed
      AND i.created_at <  DATEADD(day, 10, p.end_ts)         -- hard allocations land after the soft window
      AND TRY_TO_NUMBER(i.reference_id) > 0
),

-- ---------- SOFT: the ETA record of the promise that stands ----------
soft AS (
    SELECT i.*
    FROM inst i
    JOIN frozen f ON f.request_id = i.request_id
    WHERE i.instrumentation_type = 'ETA_INSTRUMENTATION'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY i.request_id ORDER BY i.created_at DESC) = 1
),

soft_pba AS (
    SELECT s.request_id,
           MAX(c.value:evaluated::BOOLEAN)                                             AS pba_evaluated,
           MAX(c.value:decision::STRING)                                               AS pba_decision,
           MAX(c.value:decision_detail::STRING)                                        AS pba_decision_detail,
           MAX(c.value:pba_to_internal_tat_ratio::FLOAT)                               AS pba_to_internal_tat_ratio,
           ARRAY_AGG(OBJECT_CONSTRUCT(
               'partner',        e.value:delivery_partner_id,
               'tat_in_minutes', e.value:delivery_tat_in_minutes,
               'dispatch_time',  e.value:dispatch_time,
               'delivery_time',  e.value:delivery_time,
               'eligible',       e.value:eligible,
               'is_express',     e.value:is_express,
               'cache_lookup',   e.value:cache_row:cache_lookup,
               'cache_age_minutes', e.value:cache_row:cache_age_minutes,
               'cutoff_window',  e.value:cache_row:cutoff_window
           )) WITHIN GROUP (ORDER BY e.index)                                          AS pba_soft_preference_array
    FROM soft s,
         LATERAL FLATTEN(input => s.cands) c,
         LATERAL FLATTEN(input => c.value:evaluated_candidates, OUTER => TRUE) e
    WHERE c.value:candidate_type::STRING = 'COURIER_PBA'
    GROUP BY s.request_id
),

-- PBA's pick on the soft side: the top-ranked PBA partner, whether or not it was served
soft_pba_pick AS (
    SELECT s.request_id,
           e.value:delivery_partner_id::NUMBER                                         AS pba_partner,
           e.value:delivery_tat_in_minutes::NUMBER                                     AS pba_tat_in_minutes,
           TRY_TO_TIMESTAMP_TZ(e.value:dispatch_time::STRING)                          AS pba_dispatch_time,
           TRY_TO_TIMESTAMP_TZ(e.value:delivery_time::STRING)                          AS pba_delivery_time,
           e.value:is_express::BOOLEAN                                                 AS pba_is_express,
           e.value:cache_row:cache_lookup::STRING                                      AS pba_cache_lookup,
           e.value:cache_row:cache_age_minutes::NUMBER                                 AS pba_cache_age_minutes,
           e.value:cache_row:cutoff_window::STRING                                     AS pba_cutoff_window
    FROM soft s,
         LATERAL FLATTEN(input => s.cands) c,
         LATERAL FLATTEN(input => c.value:evaluated_candidates) e
    WHERE c.value:candidate_type::STRING = 'COURIER_PBA'
      AND e.value:delivery_partner_id::NUMBER = TRY_TO_NUMBER(s.pba_top_ranked_partner_id)
    QUALIFY ROW_NUMBER() OVER (PARTITION BY s.request_id ORDER BY e.index) = 1
),

-- PBA buffers on the soft side (present when PBA was served)
soft_pba_buffer AS (
    SELECT s.request_id,
           b.value:pickup_buffer_in_minutes::NUMBER                                    AS pba_pickup_buffer,
           b.value:drop_buffer_in_minutes::NUMBER                                      AS pba_drop_buffer,
           TRY_TO_TIMESTAMP_TZ(b.value:dispatch_time::STRING)                          AS pba_buffered_dispatch_time,
           TRY_TO_TIMESTAMP_TZ(b.value:delivery_time::STRING)                          AS pba_buffered_delivery_time
    FROM soft s,
         LATERAL FLATTEN(input => s.cands) c,
         LATERAL FLATTEN(input => c.value:buffer_adjusted_candidates) b
    WHERE c.value:candidate_type::STRING = 'COURIER_PBA'
      AND b.value:rank::NUMBER = 1
),

-- Internal side on the soft path: the internal store that was evaluated (pharmacist TAT adherence or DDB adherence),
-- its candidates ranked after buffers, rank 1 is internal's pick whether or not it was served
soft_internal AS (
    SELECT s.request_id,
           MAX(c.value:candidate_type::STRING)                                         AS internal_candidate_type,
           MAX(IFF(b.value:rank::NUMBER = 1, b.value:delivery_partner_id::NUMBER, NULL))          AS internal_partner,
           MAX(IFF(b.value:rank::NUMBER = 1, b.value:delivery_tat_in_minutes::NUMBER, NULL))      AS internal_tat_in_minutes,
           MAX(IFF(b.value:rank::NUMBER = 1, TRY_TO_TIMESTAMP_TZ(b.value:dispatch_time::STRING), NULL)) AS internal_dispatch_time,
           MAX(IFF(b.value:rank::NUMBER = 1, TRY_TO_TIMESTAMP_TZ(b.value:delivery_time::STRING), NULL)) AS internal_delivery_time,
           MAX(IFF(b.value:rank::NUMBER = 1, b.value:pickup_buffer_in_minutes::NUMBER, NULL))     AS internal_pickup_buffer,
           MAX(IFF(b.value:rank::NUMBER = 1, b.value:drop_buffer_in_minutes::NUMBER, NULL))       AS internal_drop_buffer,
           MAX(IFF(b.value:rank::NUMBER = 1, b.value:is_express::BOOLEAN, NULL))                  AS internal_is_express,
           ARRAY_AGG(OBJECT_CONSTRUCT(
               'partner',        b.value:delivery_partner_id,
               'rank',           b.value:rank,
               'tat_in_minutes', b.value:delivery_tat_in_minutes,
               'dispatch_time',  b.value:dispatch_time,
               'delivery_time',  b.value:delivery_time,
               'score',          b.value:score
           )) WITHIN GROUP (ORDER BY b.value:rank::NUMBER)                             AS internal_soft_preference_array
    FROM soft s,
         LATERAL FLATTEN(input => s.cands) c,
         LATERAL FLATTEN(input => c.value:buffer_adjusted_candidates) b
    WHERE c.value:candidate_type::STRING IN ('COURIER_LEGACY_TAT_ADHERENCE', 'COURIER_DDB_TAT_ADHERENCE')
      AND c.value:evaluated::BOOLEAN
    GROUP BY s.request_id
),

-- ---------- HARD: last booking per order ----------
hard AS (
    SELECT *
    FROM inst
    WHERE instrumentation_type = 'HARD_ALLOCATION_INSTRUMENTATION'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY reference_id ORDER BY created_at DESC) = 1
),

-- PBA on the hard path (live in rollout, shadow outside it): LMS's partners in order, the first not excluded is PBA's pick
hard_pba AS (
    SELECT h.request_id,
           MAX(c.value:decision::STRING)                                               AS pba_hard_decision,
           MIN_BY(e.value:delivery_partner_id::NUMBER, IFF(e.value:excluded::BOOLEAN, 1e9, e.index))            AS pba_hard_partner,
           MIN_BY(e.value:delivery_tat_in_minutes::NUMBER, IFF(e.value:excluded::BOOLEAN, 1e9, e.index))        AS pba_hard_tat_in_minutes,
           MIN_BY(TRY_TO_TIMESTAMP_TZ(e.value:dispatch_time::STRING), IFF(e.value:excluded::BOOLEAN, 1e9, e.index)) AS pba_hard_dispatch_time,
           MIN_BY(TRY_TO_TIMESTAMP_TZ(e.value:delivery_time::STRING), IFF(e.value:excluded::BOOLEAN, 1e9, e.index)) AS pba_hard_delivery_time,
           ARRAY_AGG(OBJECT_CONSTRUCT(
               'partner',        e.value:delivery_partner_id,
               'tat_in_minutes', e.value:delivery_tat_in_minutes,
               'dispatch_time',  e.value:dispatch_time,
               'delivery_time',  e.value:delivery_time,
               'excluded',       e.value:excluded,
               'service_type',   e.value:service_type
           )) WITHIN GROUP (ORDER BY e.index)                                          AS pba_hard_preference_array
    FROM hard h,
         LATERAL FLATTEN(input => h.cands) c,
         LATERAL FLATTEN(input => c.value:evaluated_candidates) e
    WHERE c.value:candidate_type::STRING = 'COURIER_PBA'
    GROUP BY h.request_id
),

-- Internal on the hard path: rank 1 of the evaluated internal store. No dispatch/delivery is instrumented for it.
hard_internal AS (
    SELECT h.request_id,
           MAX(c.value:candidate_type::STRING)                                         AS internal_hard_candidate_type,
           MAX(IFF(b.value:rank::NUMBER = 1, b.value:delivery_partner_id::NUMBER, NULL)) AS internal_hard_partner,
           ARRAY_AGG(OBJECT_CONSTRUCT(
               'partner', b.value:delivery_partner_id,
               'rank',    b.value:rank,
               'selected', b.value:selected
           )) WITHIN GROUP (ORDER BY b.value:rank::NUMBER)                             AS internal_hard_preference_array
    FROM hard h,
         LATERAL FLATTEN(input => h.cands) c,
         LATERAL FLATTEN(input => c.value:buffer_adjusted_candidates) b
    WHERE c.value:candidate_type::STRING IN ('COURIER_LEGACY_TAT_ADHERENCE', 'COURIER_DDB_TAT_ADHERENCE')
      AND c.value:evaluated::BOOLEAN
    GROUP BY h.request_id
),

hard_internal_tat AS (
    SELECT h.request_id,
           MAX(e.value:final_tat_days::FLOAT)                                          AS internal_hard_tat_in_days
    FROM hard h
    JOIN hard_internal hi ON hi.request_id = h.request_id,
         LATERAL FLATTEN(input => h.cands) c,
         LATERAL FLATTEN(input => c.value:evaluated_candidates) e
    WHERE c.value:candidate_type::STRING = hi.internal_hard_candidate_type
      AND e.value:delivery_partner_id::NUMBER = hi.internal_hard_partner
    GROUP BY h.request_id
)

SELECT
    -- identity and cohort
    f.reference_id                                              AS order_id,
    f.customer_id,
    f.warehouse_id                                              AS wh_id,
    f.delivery_pincode                                          AS pincode,
    f.created_at                                                AS order_placed_at,
    TRY_TO_NUMBER(f.version)                                    AS eta_details_version,
    f.request_id                                                AS promise_request_id,
    f.sdd_enabled,
    f.payment_method,
    f.task_processing_type,
    (s.request_id IS NOT NULL)                                  AS has_soft_record,
    (h.request_id IS NOT NULL)                                  AS has_hard_record,
    (TRY_TO_NUMBER(f.delivery_partner_id) = 0 OR f.promised_delivery_time IS NULL) AS is_fallback_promise,
    s.flow,
    s.delivery_type,
    s.payment_mode,
    s.cfg_pba_rollout_in_rollout = 'TRUE'                       AS pba_in_rollout,
    s.created_at                                                AS soft_promise_at,
    s.client_id                                                 AS soft_caller,
    s.request_screen_context                                    AS soft_screen,

    -- the promise the customer holds (latest version)
    f.promised_warehouse_processing_time,
    f.promised_dispatch_time,
    f.promised_delivery_time,
    f.promised_delivery_partner,
    TRY_TO_NUMBER(f.delivery_tat_minutes) / 1440.0              AS promised_tat_in_days,
    s.is_cold_chain = 'TRUE'                                    AS pba_is_cold_chain,
    s.is_express_eligible = 'TRUE'                              AS pba_is_express_eligible,

    -- soft: what was served
    s.result_selected_candidate_type                            AS soft_served_candidate_type,
    s.result_delivery_partner_id                                AS soft_served_partner,
    s.result_dispatch_time                                      AS soft_served_dispatch_time,
    s.result_delivery_time                                      AS soft_served_delivery_time,
    s.result_pba_and_internal_same_partner = 'TRUE'             AS soft_matched,

    -- soft: PBA side (M1/M2)
    sp.pba_evaluated,
    sp.pba_decision,
    sp.pba_decision_detail,
    sp.pba_to_internal_tat_ratio,
    s.pba_source                                                AS pba_soft_selected_type,      -- PBA_CACHE / PBA_API / NONE
    pp.pba_partner                                              AS pba_soft_selected_delivery_partner,
    pp.pba_tat_in_minutes / 1440.0                              AS pba_soft_selected_partner_tat_in_days,
    COALESCE(pb.pba_buffered_dispatch_time, pp.pba_dispatch_time) AS pba_projected_dispatch_time,
    COALESCE(pb.pba_buffered_delivery_time, pp.pba_delivery_time) AS pba_projected_delivery_time,
    pb.pba_pickup_buffer,
    pb.pba_drop_buffer,
    pp.pba_is_express,
    pp.pba_cache_lookup,
    pp.pba_cache_age_minutes,
    pp.pba_cutoff_window,
    sp.pba_soft_preference_array,

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
    h.created_at                                                AS hard_allocated_at,
    h.result_outcome                                            AS hard_outcome,
    h.result_selected_candidate_type                            AS hard_selected_candidate_type,
    h.result_delivery_partner_id                                AS hard_booked_partner,
    h.result_delivery_tat_in_minutes / 1440.0                   AS hard_booked_tat_in_days,
    h.projected_wh_processing_time                              AS hard_wh_processing_time,
    hp.pba_hard_decision,
    hp.pba_hard_partner                                         AS pba_hard_selected_delivery_partner,
    hp.pba_hard_tat_in_minutes / 1440.0                         AS pba_hard_partner_tat_in_days,
    hp.pba_hard_dispatch_time                                   AS pba_hard_projected_dispatch_time,
    hp.pba_hard_delivery_time                                   AS pba_hard_projected_delivery_time,
    hp.pba_hard_preference_array,
    hi.internal_hard_partner                                    AS internal_hard_selected_delivery_partner,
    ht.internal_hard_tat_in_days                                AS internal_hard_partner_tat_in_days,
    NULL::TIMESTAMP_TZ                                          AS internal_hard_projected_dispatch_time,   -- not instrumented
    NULL::TIMESTAMP_TZ                                          AS internal_hard_projected_delivery_time,   -- not instrumented
    hi.internal_hard_preference_array,

    -- actuals (M3/M4), from the latest version
    f.actual_warehouse_processing_time                          AS box_verified_ts,
    NULL::TIMESTAMP_TZ                                          AS awb_print_ts,                            -- source not in these tables
    f.actual_dispatch_time                                      AS pickup_time,
    f.actual_delivery_time                                      AS delivered_time,
    NULL::TIMESTAMP_TZ                                          AS delivery_attempt_time                    -- source not in these tables
FROM frozen f
LEFT JOIN soft            s  ON s.request_id  = f.request_id
LEFT JOIN soft_pba        sp ON sp.request_id = s.request_id
LEFT JOIN soft_pba_pick   pp ON pp.request_id = s.request_id
LEFT JOIN soft_pba_buffer pb ON pb.request_id = s.request_id
LEFT JOIN soft_internal   si ON si.request_id = s.request_id
LEFT JOIN hard            h  ON h.reference_id = f.reference_id
LEFT JOIN hard_pba        hp ON hp.request_id = h.request_id
LEFT JOIN hard_internal   hi ON hi.request_id = h.request_id
LEFT JOIN hard_internal_tat ht ON ht.request_id = h.request_id
```
