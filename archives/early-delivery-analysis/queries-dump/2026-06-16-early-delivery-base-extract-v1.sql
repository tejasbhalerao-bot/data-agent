-- Early Delivery Analysis — base extract (one row per order, May digitised cohort)
-- Project: early-delivery-analysis
-- Grain: one row per order_id
-- Cohort: orders digitised in May 2026
--
-- Order Status is the only N-rows-per-order table (status history). It is collapsed to
-- one row per order via conditional aggregation (pivot 3 milestone timestamps), then every
-- other table is a clean 1:1 LEFT JOIN on order_id.
--
-- CONFIRM-BEFORE-RUN (3 items not knowable from schema.md):
--   1. order_status timestamp column assumed `created_at` (swap if created_on / status_time)
--   2. status enum strings assumed 'Order Digitised' / 'Doctor Confirmed' / 'Invoice Generated'
--   3. decode join assumed order_status_id = serial_id AND svm.name = 'Order Status'
-- Note: MIN(created_at) = FIRST occurrence of each status (re-digitise/re-invoice -> first).
-- Note: no order-status 49/312 exclusion or forward-only filter applied (per Tejas's steer).

WITH status_pivot AS (   -- collapse order_status N->1 by pivoting the 3 milestone timestamps
    SELECT
        os.order_id,
        MIN(CASE WHEN svm.value = 'Order Digitised'  THEN os.created_at END) AS order_digitised_at,
        MIN(CASE WHEN svm.value = 'Doctor Confirmed'  THEN os.created_at END) AS doctor_confirmed_at,
        MIN(CASE WHEN svm.value = 'Invoice Generated' THEN os.created_at END) AS invoice_generated_at
    FROM tmmumpsdb.order_status os
    JOIN tmmumpsdb.m_system_value_master svm
        ON os.order_status_id = svm.serial_id
       AND svm.name = 'Order Status'
    WHERE svm.value IN ('Order Digitised', 'Doctor Confirmed', 'Invoice Generated')
      AND os.created_at >= TIMESTAMP '2026-05-01 00:00:00'   -- perf: prune order_status scan
    GROUP BY os.order_id
),

cohort AS (   -- restrict to orders DIGITISED in May (confirm/invoice may spill into early June)
    SELECT *
    FROM status_pivot
    WHERE order_digitised_at >= TIMESTAMP '2026-05-01 00:00:00'
      AND order_digitised_at <  TIMESTAMP '2026-06-01 00:00:00'
)

SELECT
    c.order_id,

    -- anchors (Order Status, pivoted)
    c.order_digitised_at,
    c.doctor_confirmed_at,
    c.invoice_generated_at,

    -- promises at digitised (Delivery Date Tracker)
    ddt.promised_doctor_call_time,
    ddt.promised_warehouse_processing,
    ddt.promised_dispatch_date,
    ddt.promised_delivery_date,
    ddt.wh_processing_mins,
    ddt.delivery_tat_mins,
    DATEDIFF(minute, c.order_digitised_at, ddt.promised_doctor_call_time) AS doctor_call_tat,

    -- digitised state (S0 — promise basis)
    ddt.digitised_is_sdd,
    ddt.digitised_is_inventory,
    ddt.digitised_wh_id,
    ddt.digitised_order_category,
    ddt.digitised_is_mfc,
    ddt.digitised_delivery_pincode,
    ddt.digitised_delivery_partner,

    -- actuals (Delivery Date Tracker)
    ddt.actual_doctor_call_time,
    ddt.actual_warehouse_processing,

    -- actuals (Order TAT Details)
    otd.pickup_time,
    otd.delivery_attempt_time,
    otd.shipping_pincode,
    otd.shipping_delivery_partner,
    otd.shipped_delivery_promise,
    otd.shipping_wh_id,

    -- shipping state (S1)
    pdt.shipping_is_sdd,
    owm.shipping_is_inventory

FROM cohort c
LEFT JOIN tmmumpsdb.delivery_date_tracker    ddt ON c.order_id = ddt.order_id
LEFT JOIN tmmumpsdb.order_tat_details        otd ON c.order_id = otd.order_id
LEFT JOIN tmmumpsdb.package_details_tracking pdt ON c.order_id = pdt.order_id
LEFT JOIN tmmumpsdb.order_wh_mfc_mapping     owm ON c.order_id = owm.order_id
ORDER BY c.order_id;
