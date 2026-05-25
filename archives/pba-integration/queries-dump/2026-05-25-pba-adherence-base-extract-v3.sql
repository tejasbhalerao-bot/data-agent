-- Adherence Base Extract v3
-- Adds warehouse_id to support 1.7 time-of-day cutoff analysis.
-- v2 added allocation_created_at. v3 adds warehouse_id on top.
-- All other columns unchanged.

WITH cte AS (
    SELECT
        order_id,
        allocation_metadata,
        allocation_type,
        created_at,
        ROW_NUMBER() OVER (PARTITION BY order_id, allocation_type ORDER BY updated_at DESC) AS rn
    FROM tmmumpsdb.logistics_allocation_audit
    WHERE allocation_type IN ('SOFT', 'HARD')
      AND selected_source = 'INTERNAL'
      AND order_id IS NOT NULL
      AND created_at >= TIMESTAMP '2026-05-10 00:00:00'
      AND created_at < CURRENT_DATE
),

allocation AS (
    SELECT
        order_id,
        allocation_type,
        created_at                                                    AS allocation_created_at,
        (allocation_metadata.warehouse_id)::int                      AS warehouse_id,
        (allocation_metadata.pba_partner_id)::int                    AS pba_partner_id,
        CEILING((allocation_metadata.pba_tat)::int / 1440.0)         AS pba_tat_days,
        (allocation_metadata.internal_partner_id)::int               AS internal_partner_id,
        CEILING((allocation_metadata.internal_tat)::int / 1440.0)    AS internal_tat_days
    FROM cte
    WHERE rn = 1
      AND (allocation_metadata.warehouse_id)::int >= 17
),

delivery_partner_mapping AS (
    SELECT serial_id AS delivery_partner_id, value AS partner_name
    FROM tmmumpsdb.m_system_value_master
)

SELECT
    h.order_id,
    h.allocation_created_at,
    h.warehouse_id,
    h.internal_partner_id                   AS hard_internal_partner_id,
    dp_int.partner_name                     AS internal_partner_name,
    h.internal_tat_days                     AS hard_internal_tat_days,
    h.pba_partner_id                        AS hard_pba_partner_id,
    dp_pba.partner_name                     AS pba_partner_name,
    h.pba_tat_days                          AS hard_pba_tat_days,
    otd.pickup_time,
    otd.delivery_attempt_time
FROM allocation h
LEFT JOIN tmmumpsdb.order_tat_details otd
    ON h.order_id = otd.order_id
LEFT JOIN delivery_partner_mapping dp_int
    ON h.internal_partner_id = dp_int.delivery_partner_id
LEFT JOIN delivery_partner_mapping dp_pba
    ON h.pba_partner_id = dp_pba.delivery_partner_id
WHERE h.allocation_type = 'HARD'
ORDER BY h.order_id;
