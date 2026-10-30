WITH refs AS (
    -- Section 2 soft metric 1, independent recount, step 1 (no candidate JSON): raw records for 23 Oct 10:00-11:00 IST, no base logic applied.
    -- Orders: any promise row created in the hour and any ETA record served by COURIER_PBA (a superset of the PBA base); Python applies the rules.
    SELECT DISTINCT reference_id
    FROM prod_silver_db.logistics.serviceability_eta_details
    WHERE created_at >= '2026-10-23 10:00:00 +0530'::TIMESTAMP_TZ AND created_at < '2026-10-23 11:00:00 +0530'::TIMESTAMP_TZ
),
eta AS (
    SELECT i.reference_id, i.request_id, i.created_at, i.result_selected_candidate_type
    FROM prod_silver_db.logistics.logistics_eta_instrumentation i
    JOIN refs r ON r.reference_id = i.reference_id
    WHERE i.created_at >= '2026-10-22 10:00:00'::TIMESTAMP_NTZ AND i.created_at < '2026-11-02 11:00:00'::TIMESTAMP_NTZ
),
pba_refs AS (
    SELECT DISTINCT reference_id FROM eta WHERE result_selected_candidate_type = 'COURIER_PBA'
),
sed AS (
    SELECT d.reference_id,
           ARRAY_AGG(OBJECT_CONSTRUCT('version', d.version, 'created_at', d.created_at::STRING, 'request_id', d.request_id,
                                      'sdd_enabled', d.sdd_enabled, 'pwpt', d.promised_warehouse_processing_time::STRING)) AS sed_rows
    FROM prod_silver_db.logistics.serviceability_eta_details d
    JOIN pba_refs p ON p.reference_id = d.reference_id
    GROUP BY 1
),
er AS (
    SELECT e.reference_id,
           ARRAY_AGG(OBJECT_CONSTRUCT('request_id', e.request_id, 'created_at', e.created_at::STRING,
                                      'served', e.result_selected_candidate_type)) AS eta_rows
    FROM eta e
    JOIN pba_refs p ON p.reference_id = e.reference_id
    GROUP BY 1
),
odr AS (
    SELECT o.order_id,
           ARRAY_AGG(OBJECT_CONSTRUCT('status', o.orderstatus, 'ts', o.ingestion_ts_ist::STRING)) AS od_rows
    FROM prod_silver_db.main_db.order_details o
    WHERE o.order_id IN (SELECT TRY_TO_NUMBER(reference_id) FROM pba_refs)
    GROUP BY 1
)
SELECT p.reference_id, s.sed_rows, e.eta_rows, o.od_rows
FROM pba_refs p
LEFT JOIN sed s ON s.reference_id = p.reference_id
LEFT JOIN er  e ON e.reference_id = p.reference_id
LEFT JOIN odr o ON o.order_id = TRY_TO_NUMBER(p.reference_id)
ORDER BY 1
