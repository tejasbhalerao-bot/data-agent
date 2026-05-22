-- Base Query 1: Allocation Output (PBA vs Internal + Actuals)
-- One row per order. Soft + Hard side-by-side.
-- Includes actual delivery date and promised delivery date.

WITH filtered_laa AS (
    SELECT order_id,
           allocation_metadata,
           allocation_type,
           updated_at,
           ROW_NUMBER() OVER (
            PARTITION BY order_id, allocation_type
            ORDER BY updated_at DESC
        ) AS rn
    FROM tmmumpsdb.logistics_allocation_audit laa
    WHERE allocation_type IN ('SOFT','HARD')
      AND laa.selected_source = 'INTERNAL'
      AND laa.order_id IS NOT NULL
      AND laa.updated_at >= TIMESTAMP '2026-05-08 00:00:00'
      AND laa.updated_at < CURRENT_DATE
)

,allocation AS (
    SELECT
        laa.order_id,
        laa.allocation_type,

        (allocation_metadata.warehouse_id)::int AS warehouse_id,
        (allocation_metadata.pincode)::int AS pincode,

        timestamp 'epoch' + ((allocation_metadata.projected_dispatch_time)::bigint / 1000) * interval '1 second'
            AS projected_dispatch_time,

        (allocation_metadata.pba_partner_id)::int AS pba_partner_id,
        CEILING((allocation_metadata.pba_tat)::int / 1440.0) AS pba_tat_days,

        (allocation_metadata.internal_partner_id)::int AS internal_partner_id,
        CEILING((allocation_metadata.internal_tat)::int / 1440.0) AS internal_tat_days

    FROM filtered_laa laa

    INNER JOIN tmmumpsdb.order_status od
        ON laa.order_id = od.order_id
       AND od.order_status_id = 344
       AND od.modified_on > TIMESTAMP '2026-05-08 00:00:00'

    WHERE laa.rn = 1
      AND (allocation_metadata.warehouse_id)::int >= 17
)

,combined_data AS (
    SELECT
        s.order_id,
        s.warehouse_id,
        s.pincode,
        s.projected_dispatch_time,

        s.pba_partner_id AS soft_pba_partner_id,
        s.pba_tat_days AS soft_pba_tat_in_days,
        s.internal_partner_id AS soft_internal_partner_id,
        s.internal_tat_days AS soft_internal_tat_in_days,

        h.pba_partner_id AS hard_pba_partner_id,
        h.pba_tat_days AS hard_pba_tat_in_days,
        h.internal_partner_id AS hard_internal_partner_id,
        h.internal_tat_days AS hard_internal_tat_in_days,

        otd.pickup_time,
        otd.delivery_attempt_time

    FROM allocation s

    INNER JOIN allocation h
        ON s.order_id = h.order_id
       AND h.allocation_type = 'HARD'

    INNER JOIN tmmumpsdb.order_tat_details otd
        ON s.order_id = otd.order_id

    WHERE s.allocation_type = 'SOFT'
)

,delivery_partner_mapping AS (
    SELECT
        serial_id AS delivery_partner_id,
        value AS partner_name
    FROM tmmumpsdb.m_system_value_master
)

SELECT
    s.*,
    os.modified_on AS created_on,
    ddt.actual_delivery_date,

    CASE
        WHEN dpm.partner_name ILIKE '%express%'
            THEN ddt.promised_air_delivery_date
        ELSE ddt.promised_delivery_date
    END AS promised_delivery_date

FROM combined_data s

LEFT JOIN tmmumpsdb.delivery_date_tracker ddt
    ON s.order_id = ddt.order_id

INNER JOIN delivery_partner_mapping dpm
    ON s.hard_internal_partner_id = dpm.delivery_partner_id

INNER JOIN tmmumpsdb.order_status os
    ON s.order_id = os.order_id
   AND os.order_status_id = 39
