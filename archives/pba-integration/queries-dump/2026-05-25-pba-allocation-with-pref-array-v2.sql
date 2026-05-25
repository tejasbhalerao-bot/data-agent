-- Query: Allocation + Preference Array v2 (Pivoted Wide)
-- Extends v1 with:
--   1. AVERAGE_TAT score per dp slot (3rd tie-breaker after EDD → PRICING)
--   2. delivery_partner_id per dp slot (resolved via logistics_delivery_partner.ankw_account_code)
--      Enables direct comparison of allocated PBA courier vs rank-1 courier in Python.
--
-- One row per order. HARD allocation only. Same-courier + different-courier orders included.
-- Preference array joined via request_id = reference_number (exact match).
--
-- Used by: 4.0 ranking logic audit script
-- Date filter: update before each production run.

WITH cte AS (
    SELECT
        order_id,
        request_id,
        allocation_metadata,
        updated_at,
        ROW_NUMBER() OVER (
            PARTITION BY order_id, allocation_type
            ORDER BY updated_at DESC
        ) AS rn
    FROM tmmumpsdb.logistics_allocation_audit
    WHERE allocation_type = 'HARD'
      AND selected_source = 'INTERNAL'
      AND allocation_metadata.warehouse_id::int >= 17
      AND order_id IS NOT NULL
      AND created_at >= TIMESTAMP '2026-05-22 19:00:00'
),

filtered_orders AS (
    SELECT
        laa.order_id,
        laa.request_id,
        allocation_metadata.pincode::int                        AS drop_pincode,
        allocation_metadata.pba_partner_id::int                 AS hard_pba_partner_id,
        CEILING(allocation_metadata.pba_tat::int / 1440.0)      AS hard_pba_tat_in_days,
        allocation_metadata.internal_partner_id::int            AS hard_internal_partner_id,
        CEILING(allocation_metadata.internal_tat::int / 1440.0) AS hard_internal_tat_in_days
    FROM cte laa
    WHERE laa.rn = 1
),

partner_name_map AS (
    SELECT serial_id AS delivery_partner_id, value AS partner_name
    FROM tmmumpsdb.m_system_value_master
),

numbers AS (
    SELECT 0 AS idx UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
    UNION ALL SELECT 4 UNION ALL SELECT 5
),

base_payload AS (
    SELECT
        SPLIT_PART(lraa.pk, '#', 2) AS order_id,
        lraa.reference_number,
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
        b.reference_number,
        n.idx,
        JSON_EXTRACT_ARRAY_ELEMENT_TEXT(b.preference_array, n.idx) AS pref_element
    FROM base_payload b
    CROSS JOIN numbers n
    WHERE JSON_EXTRACT_ARRAY_ELEMENT_TEXT(b.preference_array, n.idx) != ''
),

preference_pivoted AS (
    SELECT
        order_id,
        reference_number,

        -- dp1
        MAX(CASE WHEN idx = 0 THEN JSON_EXTRACT_PATH_TEXT(pref_element, 'account_code') END)                                                                                       AS dp1_account_code,
        MAX(CASE WHEN idx = 0 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'EDD')          AS DECIMAL(10,2)), 2) END)       AS dp1_edd,
        MAX(CASE WHEN idx = 0 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'PRICING')       AS DECIMAL(10,2)), 2) END)       AS dp1_pricing,
        MAX(CASE WHEN idx = 0 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'AVERAGE_TAT')   AS DECIMAL(10,2)), 2) END)       AS dp1_avg_tat,
        MAX(CASE WHEN idx = 0 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'total_score')                            AS DECIMAL(10,2)), 2) END)       AS dp1_total_score,

        -- dp2
        MAX(CASE WHEN idx = 1 THEN JSON_EXTRACT_PATH_TEXT(pref_element, 'account_code') END)                                                                                       AS dp2_account_code,
        MAX(CASE WHEN idx = 1 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'EDD')          AS DECIMAL(10,2)), 2) END)       AS dp2_edd,
        MAX(CASE WHEN idx = 1 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'PRICING')       AS DECIMAL(10,2)), 2) END)       AS dp2_pricing,
        MAX(CASE WHEN idx = 1 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'AVERAGE_TAT')   AS DECIMAL(10,2)), 2) END)       AS dp2_avg_tat,
        MAX(CASE WHEN idx = 1 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'total_score')                            AS DECIMAL(10,2)), 2) END)       AS dp2_total_score,

        -- dp3
        MAX(CASE WHEN idx = 2 THEN JSON_EXTRACT_PATH_TEXT(pref_element, 'account_code') END)                                                                                       AS dp3_account_code,
        MAX(CASE WHEN idx = 2 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'EDD')          AS DECIMAL(10,2)), 2) END)       AS dp3_edd,
        MAX(CASE WHEN idx = 2 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'PRICING')       AS DECIMAL(10,2)), 2) END)       AS dp3_pricing,
        MAX(CASE WHEN idx = 2 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'AVERAGE_TAT')   AS DECIMAL(10,2)), 2) END)       AS dp3_avg_tat,
        MAX(CASE WHEN idx = 2 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'total_score')                            AS DECIMAL(10,2)), 2) END)       AS dp3_total_score,

        -- dp4
        MAX(CASE WHEN idx = 3 THEN JSON_EXTRACT_PATH_TEXT(pref_element, 'account_code') END)                                                                                       AS dp4_account_code,
        MAX(CASE WHEN idx = 3 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'EDD')          AS DECIMAL(10,2)), 2) END)       AS dp4_edd,
        MAX(CASE WHEN idx = 3 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'PRICING')       AS DECIMAL(10,2)), 2) END)       AS dp4_pricing,
        MAX(CASE WHEN idx = 3 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'AVERAGE_TAT')   AS DECIMAL(10,2)), 2) END)       AS dp4_avg_tat,
        MAX(CASE WHEN idx = 3 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'total_score')                            AS DECIMAL(10,2)), 2) END)       AS dp4_total_score,

        -- dp5
        MAX(CASE WHEN idx = 4 THEN JSON_EXTRACT_PATH_TEXT(pref_element, 'account_code') END)                                                                                       AS dp5_account_code,
        MAX(CASE WHEN idx = 4 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'EDD')          AS DECIMAL(10,2)), 2) END)       AS dp5_edd,
        MAX(CASE WHEN idx = 4 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'PRICING')       AS DECIMAL(10,2)), 2) END)       AS dp5_pricing,
        MAX(CASE WHEN idx = 4 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'AVERAGE_TAT')   AS DECIMAL(10,2)), 2) END)       AS dp5_avg_tat,
        MAX(CASE WHEN idx = 4 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'total_score')                            AS DECIMAL(10,2)), 2) END)       AS dp5_total_score,

        -- dp6
        MAX(CASE WHEN idx = 5 THEN JSON_EXTRACT_PATH_TEXT(pref_element, 'account_code') END)                                                                                       AS dp6_account_code,
        MAX(CASE WHEN idx = 5 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'EDD')          AS DECIMAL(10,2)), 2) END)       AS dp6_edd,
        MAX(CASE WHEN idx = 5 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'PRICING')       AS DECIMAL(10,2)), 2) END)       AS dp6_pricing,
        MAX(CASE WHEN idx = 5 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'AVERAGE_TAT')   AS DECIMAL(10,2)), 2) END)       AS dp6_avg_tat,
        MAX(CASE WHEN idx = 5 THEN ROUND(CAST(JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'total_score')                            AS DECIMAL(10,2)), 2) END)       AS dp6_total_score

    FROM unnested
    GROUP BY order_id, reference_number
)

SELECT
    fo.order_id,
    fo.request_id,
    fo.drop_pincode,
    pp.reference_number,

    fo.hard_pba_partner_id,
    dp_pba.partner_name                    AS pba_partner_name,
    fo.hard_pba_tat_in_days                AS pba_partner_tat_days,

    fo.hard_internal_partner_id,
    dp_int.partner_name                    AS internal_partner_name,
    fo.hard_internal_tat_in_days           AS internal_partner_tat_days,

    -- Rank-1 delivery partner ID (resolved from account_code via logistics_delivery_partner)
    -- Used by 4.0 script to check: hard_pba_partner_id == dp1_partner_id
    ldp1.delivery_partner_id               AS dp1_partner_id,
    pp.dp1_account_code,
    pp.dp1_edd,
    pp.dp1_pricing,
    pp.dp1_avg_tat,
    pp.dp1_total_score,

    ldp2.delivery_partner_id               AS dp2_partner_id,
    pp.dp2_account_code,
    pp.dp2_edd,
    pp.dp2_pricing,
    pp.dp2_avg_tat,
    pp.dp2_total_score,

    ldp3.delivery_partner_id               AS dp3_partner_id,
    pp.dp3_account_code,
    pp.dp3_edd,
    pp.dp3_pricing,
    pp.dp3_avg_tat,
    pp.dp3_total_score,

    ldp4.delivery_partner_id               AS dp4_partner_id,
    pp.dp4_account_code,
    pp.dp4_edd,
    pp.dp4_pricing,
    pp.dp4_avg_tat,
    pp.dp4_total_score,

    ldp5.delivery_partner_id               AS dp5_partner_id,
    pp.dp5_account_code,
    pp.dp5_edd,
    pp.dp5_pricing,
    pp.dp5_avg_tat,
    pp.dp5_total_score,

    ldp6.delivery_partner_id               AS dp6_partner_id,
    pp.dp6_account_code,
    pp.dp6_edd,
    pp.dp6_pricing,
    pp.dp6_avg_tat,
    pp.dp6_total_score

FROM filtered_orders fo
INNER JOIN preference_pivoted pp
    ON fo.order_id = pp.order_id
LEFT JOIN partner_name_map dp_pba
    ON fo.hard_pba_partner_id::VARCHAR = dp_pba.delivery_partner_id
LEFT JOIN partner_name_map dp_int
    ON fo.hard_internal_partner_id::VARCHAR = dp_int.delivery_partner_id
-- Resolve each dp slot's account_code → internal delivery_partner_id
LEFT JOIN tmmumpsdb.logistics_delivery_partner ldp1 ON ldp1.ankw_account_code = pp.dp1_account_code
LEFT JOIN tmmumpsdb.logistics_delivery_partner ldp2 ON ldp2.ankw_account_code = pp.dp2_account_code
LEFT JOIN tmmumpsdb.logistics_delivery_partner ldp3 ON ldp3.ankw_account_code = pp.dp3_account_code
LEFT JOIN tmmumpsdb.logistics_delivery_partner ldp4 ON ldp4.ankw_account_code = pp.dp4_account_code
LEFT JOIN tmmumpsdb.logistics_delivery_partner ldp5 ON ldp5.ankw_account_code = pp.dp5_account_code
LEFT JOIN tmmumpsdb.logistics_delivery_partner ldp6 ON ldp6.ankw_account_code = pp.dp6_account_code
ORDER BY fo.order_id;
