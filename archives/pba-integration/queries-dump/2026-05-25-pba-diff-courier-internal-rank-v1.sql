-- 1.6 Base Extract: PBA's TAT estimate for Internal courier (different-courier cohort)
-- Different-courier cohort: hard_pba_partner_id != hard_internal_partner_id
-- For each order, finds where the Internal courier sits in PBA's Clickpost preference
-- array and what EDD score Clickpost assigned it.
-- Tests whether PBA's promise calibration for deprioritised couriers is accurate.
--
-- Join path for Internal courier in preference array:
--   logistics_allocation_audit.internal_partner_id
--   → logistics_delivery_partner (via SPLIT_PART(pk,'#',2)) → ankw_account_code
--   → logistics_rails_api_audit preference_array[n].account_code

WITH cte AS (
    SELECT
        order_id,
        request_id,
        allocation_metadata,
        ROW_NUMBER() OVER (PARTITION BY order_id, allocation_type ORDER BY updated_at DESC) AS rn
    FROM tmmumpsdb.logistics_allocation_audit
    WHERE allocation_type = 'HARD'
      AND selected_source = 'INTERNAL'
      AND order_id IS NOT NULL
      AND allocation_metadata.warehouse_id::int >= 17
      AND created_at >= TIMESTAMP '2026-05-10 00:00:00'
      AND created_at < CURRENT_DATE
),

filtered_orders AS (
    SELECT
        order_id,
        request_id,
        allocation_metadata.pincode::int                        AS drop_pincode,
        allocation_metadata.pba_partner_id::int                 AS hard_pba_partner_id,
        CEILING(allocation_metadata.pba_tat::int / 1440.0)      AS hard_pba_tat_days,
        allocation_metadata.internal_partner_id::int            AS hard_internal_partner_id,
        CEILING(allocation_metadata.internal_tat::int / 1440.0) AS hard_internal_tat_days
    FROM cte
    WHERE rn = 1
      AND allocation_metadata.pba_partner_id::int != allocation_metadata.internal_partner_id::int
),

-- Map internal delivery_partner_id → ankw_account_code for preference array matching
internal_courier_lookup AS (
    SELECT
        SPLIT_PART(pk, '#', 2)::int  AS delivery_partner_id,
        metadata.ankw_account_code   AS ankw_account_code
    FROM tmmumpsdb.logistics_delivery_partner
),

numbers AS (
    SELECT 0 AS idx UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
    UNION ALL SELECT 4 UNION ALL SELECT 5
),

base_payload AS (
    SELECT
        SPLIT_PART(lraa.pk, '#', 2) AS order_id,
        JSON_EXTRACT_PATH_TEXT(
            JSON_EXTRACT_ARRAY_ELEMENT_TEXT(
                JSON_EXTRACT_PATH_TEXT(lraa.response_payload, 'result'), 0
            ),
            'preference_array'
        ) AS preference_array
    FROM tmmumpsdb.logistics_rails_api_audit lraa
    INNER JOIN filtered_orders fo
        ON fo.order_id = SPLIT_PART(lraa.pk, '#', 2)
        AND fo.request_id = lraa.reference_number
    WHERE JSON_EXTRACT_PATH_TEXT(lraa.response_payload, 'meta', 'success') = 'true'
      AND api_name = 'CLICKPOST_RECOMMEND'
),

unnested AS (
    SELECT
        b.order_id,
        n.idx + 1                                                AS pba_rank,
        JSON_EXTRACT_ARRAY_ELEMENT_TEXT(b.preference_array, n.idx) AS pref_element
    FROM base_payload b
    CROSS JOIN numbers n
    WHERE JSON_EXTRACT_ARRAY_ELEMENT_TEXT(b.preference_array, n.idx) != ''
),

pref_flat AS (
    SELECT
        order_id,
        pba_rank,
        JSON_EXTRACT_PATH_TEXT(pref_element, 'account_code')                                                                                  AS account_code,
        ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'EDD') AS DECIMAL(10,2)), 2)            AS pba_edd_score
    FROM unnested
),

delivery_partner_mapping AS (
    SELECT serial_id AS delivery_partner_id, value AS partner_name
    FROM tmmumpsdb.m_system_value_master
)

SELECT
    fo.order_id,
    fo.drop_pincode,
    fo.hard_pba_partner_id,
    dp_pba.partner_name                     AS pba_partner_name,
    fo.hard_pba_tat_days,
    fo.hard_internal_partner_id,
    dp_int.partner_name                     AS internal_partner_name,
    fo.hard_internal_tat_days,
    pf.pba_rank                             AS internal_courier_pba_rank,
    pf.pba_edd_score                        AS pba_edd_for_internal_courier,
    otd.pickup_time,
    otd.delivery_attempt_time
FROM filtered_orders fo
LEFT JOIN delivery_partner_mapping dp_pba
    ON fo.hard_pba_partner_id = dp_pba.delivery_partner_id
LEFT JOIN delivery_partner_mapping dp_int
    ON fo.hard_internal_partner_id = dp_int.delivery_partner_id
LEFT JOIN internal_courier_lookup icl
    ON fo.hard_internal_partner_id = icl.delivery_partner_id
LEFT JOIN pref_flat pf
    ON fo.order_id = pf.order_id
    AND icl.ankw_account_code = pf.account_code
LEFT JOIN tmmumpsdb.order_tat_details otd
    ON fo.order_id = otd.order_id
ORDER BY fo.order_id;
