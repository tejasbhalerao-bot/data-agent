SELECT GROUPING(TO_VARCHAR(sdd_enabled))         AS is_total,
       TO_VARCHAR(sdd_enabled)                   AS sdd_enabled_value,
       TO_VARCHAR(has_soft_record)               AS has_soft_record_value,
       TO_VARCHAR(pba_in_rollout)                AS pba_in_rollout_value,
       soft_served_candidate_type,
       COUNT(*)                                  AS n_rows,
       COUNT(DISTINCT order_id)                  AS n_orders,
       ANY_VALUE(MD5(SUBSTR(CURRENT_STATEMENT(),
                  CHARINDEX('WITH params AS (', CURRENT_STATEMENT()),
                  CHARINDEX(CHR(10) || ')' || CHR(10) || 'SELECT', CURRENT_STATEMENT()) - CHARINDEX('WITH params AS (', CURRENT_STATEMENT())))) AS base_md5
FROM base
GROUP BY GROUPING SETS ((TO_VARCHAR(sdd_enabled), TO_VARCHAR(has_soft_record), TO_VARCHAR(pba_in_rollout), soft_served_candidate_type), ())
ORDER BY is_total, sdd_enabled_value, has_soft_record_value, pba_in_rollout_value, soft_served_candidate_type
