SELECT GROUPING(TO_VARCHAR(sdd_enabled))           AS is_total,
       TO_VARCHAR(sdd_enabled)                     AS sdd_enabled_value,
       soft_served_candidate_type,
       TO_VARCHAR(has_shipment_record)             AS has_shipment_record_value,
       TO_VARCHAR(pickup_time IS NOT NULL)         AS has_pickup,
       TO_VARCHAR(delivery_attempt_time IS NOT NULL) AS has_attempt,
       COUNT(*)                                    AS n_rows,
       COUNT(DISTINCT order_id)                    AS n_orders,
       MIN(SYSTEM$TYPEOF(pickup_time))             AS pickup_type,
       MIN(SYSTEM$TYPEOF(delivery_attempt_time))   AS attempt_type,
       ANY_VALUE(MD5(SUBSTR(CURRENT_STATEMENT(),
                  CHARINDEX('WITH params AS (', CURRENT_STATEMENT()),
                  CHARINDEX(CHR(10) || ')' || CHR(10) || 'SELECT', CURRENT_STATEMENT()) - CHARINDEX('WITH params AS (', CURRENT_STATEMENT())))) AS base_md5
FROM base
GROUP BY GROUPING SETS ((TO_VARCHAR(sdd_enabled), soft_served_candidate_type, TO_VARCHAR(has_shipment_record), TO_VARCHAR(pickup_time IS NOT NULL), TO_VARCHAR(delivery_attempt_time IS NOT NULL)), ())
ORDER BY 1, 2, 3, 4, 5, 6
