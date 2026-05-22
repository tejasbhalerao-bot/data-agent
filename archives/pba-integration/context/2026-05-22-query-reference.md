# PBA Query Reference
**Date:** 2026-05-22

All Redshift tables prefixed with `tmmumpsdb.`

---

## Tables

| Table | Purpose |
|---|---|
| `logistics_allocation_audit` | One record per order per allocation type (SOFT/HARD). Stores both PBA and internal courier decisions + TATs in `allocation_metadata` JSON |
| `logistics_rails_api_audit` | Raw Clickpost API response logs. Contains full `preference_array` — every courier Clickpost considered + scoring params |
| `logistics_delivery_partner` | Maps internal `delivery_partner_id` ↔ Clickpost `cp_id` + `ankw_account_code`. PK format: `#delivery_partner_id` |
| `order_status` | Order lifecycle events. `order_status_id = 344` = PBA-eligible placed order. `order_status_id = 39` = order created timestamp |
| `order_tat_details` | `pickup_time`, `delivery_attempt_time` per order |
| `delivery_date_tracker` | `actual_delivery_date`, `promised_delivery_date` (surface), `promised_air_delivery_date` (express) |
| `m_system_value_master` | Master lookup. `serial_id = delivery_partner_id`, `value = partner_name` |

---

## Key Field Notes

- `allocation_metadata` fields (from `logistics_allocation_audit`):
  - `pba_partner_id`, `pba_tat` (minutes — divide by 1440 for days)
  - `internal_partner_id`, `internal_tat` (minutes — divide by 1440 for days)
  - `warehouse_id`, `pincode`, `projected_dispatch_time` (epoch ms)
- `selected_source = 'INTERNAL'` — confirms shadow mode. Internal courier always executes. PBA is counterfactual.
- `warehouse_id >= 17` — active warehouses only. Older warehouses shut down.
- `preference_array` path: `response_payload → result[0] → preference_array`
- Per courier in preference_array: `cp_id`, `account_code`, `courier_name`, `priority`, `delivery_type`, `scores_computation.scoring_params_actual.EDD/PRICING/AVERAGE_TAT`, `scores_computation.total_score`
- `promised_delivery_date` selection: use `promised_air_delivery_date` if courier is express-type, else `promised_delivery_date`. Determined by `partner_name ILIKE '%express%'` from `m_system_value_master`

---

## Allocation Ranking Logic (Clickpost)

EDD ASC → PRICING ASC → AVERAGE_TAT ASC → TOTAL_SCORE ASC → PRIORITY ASC

---

## Excluded Couriers

Shiprocket and Shadowfax excluded from PBA analysis scope.

---

## Base Query 1 — Allocation Output (PBA vs Internal + Actuals)

One row per order. Soft + Hard side-by-side. Includes actual delivery date and promised date.

```sql
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
```

---

## Base Query 2 — Preference Array (Full Clickpost Ranked List per Order)

One row per order per courier in Clickpost's preference array. Includes internal courier's rank position and TAT comparison.

```sql
WITH numbers AS (
    SELECT 0 AS idx UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3
    UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7
    UNION ALL SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11
    UNION ALL SELECT 12 UNION ALL SELECT 13 UNION ALL SELECT 14 UNION ALL SELECT 15
    UNION ALL SELECT 16 UNION ALL SELECT 17 UNION ALL SELECT 18 UNION ALL SELECT 19
),
delivery_partner_mapping AS (
    SELECT 
        SPLIT_PART(pk, '#', 2) AS delivery_partner_id,
        metadata.clickpost_partner_id AS cp_id,
        metadata.ankw_account_code AS ankw_account_code
    FROM tmmumpsdb.logistics_delivery_partner
),
base_payload AS (
    SELECT 
        SPLIT_PART(pk, '#', 2) AS order_id,
        response_payload,
        JSON_EXTRACT_PATH_TEXT(response_payload, 'meta', 'success') AS meta_success,
        JSON_EXTRACT_PATH_TEXT(
            JSON_EXTRACT_ARRAY_ELEMENT_TEXT(
                JSON_EXTRACT_PATH_TEXT(response_payload, 'result'), 0
            ),
            'preference_array'
        ) AS preference_array,
        ROW_NUMBER() OVER (PARTITION BY pk ORDER BY created_at DESC) AS rn
    FROM tmmumpsdb.logistics_rails_api_audit
    WHERE JSON_EXTRACT_PATH_TEXT(response_payload, 'meta', 'success') = 'true'
),
unnested AS (
    SELECT
        b.*,
        n.idx,
        JSON_EXTRACT_ARRAY_ELEMENT_TEXT(b.preference_array, n.idx) AS pref_element
    FROM base_payload b
    CROSS JOIN numbers n
    WHERE JSON_EXTRACT_ARRAY_ELEMENT_TEXT(b.preference_array, n.idx) != ''
    AND rn = 1
),
json_extract AS (
    SELECT 
        order_id,
        JSON_EXTRACT_PATH_TEXT(pref_element, 'cp_id') AS cp_id,
        JSON_EXTRACT_PATH_TEXT(pref_element, 'account_code') AS account_code,
        JSON_EXTRACT_PATH_TEXT(pref_element, 'courier_name') AS courier_name,
        JSON_EXTRACT_PATH_TEXT(pref_element, 'priority') AS priority,
        JSON_EXTRACT_PATH_TEXT(pref_element, 'delivery_type') AS delivery_type,
        JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'PRICING') AS actual_pricing,
        JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'EDD') AS actual_edd,
        JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'scoring_params_actual', 'AVERAGE_TAT') AS actual_average_tat,
        JSON_EXTRACT_PATH_TEXT(pref_element, 'scores_computation', 'total_score') AS total_score
    FROM unnested
),
allocation_cte AS (
    SELECT *
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY order_id, allocation_type
                   ORDER BY updated_at DESC
               ) AS rn
        FROM tmmumpsdb.logistics_allocation_audit
    ) sub
    WHERE rn = 1 
),
base AS (
    SELECT 
        laa.order_id,
        laa.decision_reason,
        laa.selected_source,
        laa.allocation_type, 
        laa.selected_partner_id,
        allocation_metadata.pba_partner_id::int AS pba_partner_id,
        ceiling(allocation_metadata.pba_tat::int*1.00/1440) as pba_tat_in_days,
        allocation_metadata.internal_partner_id::int AS internal_partner_id,
        ceiling(allocation_metadata.internal_tat::int*1.00/1440) as internal_tat_in_days
    FROM allocation_cte laa
    INNER JOIN tmmumpsdb.order_status od 
        ON laa.order_id = od.order_id 
        AND od.order_status_id = 344
    WHERE modified_on > TIMESTAMP '2026-02-18 12:00:00'
        AND laa.order_id IS NOT NULL
        AND allocation_type = 'HARD'
        AND selected_source = 'INTERNAL' 
        AND pba_partner_id IS NOT NULL 
        AND internal_partner_id IS NOT NULL 
),
combined AS (
    SELECT 
        b.*,
        j.cp_id,
        j.account_code,
        j.courier_name,
        j.priority,
        j.delivery_type,
        j.actual_pricing,
        j.actual_edd,
        j.actual_average_tat,
        j.total_score
    FROM base b 
    INNER JOIN json_extract j 
        ON b.order_id = j.order_id
),
with_delivery_partner AS (
    SELECT 
        c.*,
        dp.delivery_partner_id
    FROM combined c
    LEFT JOIN delivery_partner_mapping dp
        ON c.cp_id = dp.cp_id 
        AND c.account_code = dp.ankw_account_code
),
ranked AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY order_id, allocation_type
            ORDER BY 
                CAST(actual_edd AS DECIMAL(10,2)) ASC NULLS LAST,
                CAST(actual_pricing AS DECIMAL(10,2)) ASC NULLS LAST,
                CAST(actual_average_tat AS DECIMAL(10,2)) ASC NULLS LAST,
                CAST(total_score AS DECIMAL(10,2)) ASC NULLS LAST,
                CAST(priority AS DECIMAL(10,2)) ASC NULLS LAST
        ) AS our_rank
    FROM with_delivery_partner
),
final AS (
    SELECT 
        r.*,
        CASE 
            WHEN selected_source IN ('PBA_CACHE', 'PBA_API') 
                AND our_rank = 1 
                AND CAST(pba_partner_id AS VARCHAR) = CAST(delivery_partner_id AS VARCHAR)
            THEN TRUE
            WHEN selected_source IN ('PBA_CACHE', 'PBA_API') 
                AND our_rank = 1 
                AND CAST(pba_partner_id AS VARCHAR) != CAST(delivery_partner_id AS VARCHAR)
            THEN FALSE
            ELSE NULL
        END AS pba_matches_rank1,
        CASE 
            WHEN CAST(internal_partner_id AS VARCHAR) = CAST(delivery_partner_id AS VARCHAR)
            THEN our_rank
            ELSE NULL
        END AS internal_actual_rank
    FROM ranked r
),
internal_rankings AS (
    SELECT DISTINCT
        order_id,
        allocation_type,
        selected_source,
        pba_partner_id,
        pba_tat_in_days,
        internal_partner_id,
        internal_tat_in_days,
        delivery_partner_id,
        account_code,
        courier_name,
        our_rank,
        actual_edd,
        actual_pricing,
        actual_average_tat,
        pba_matches_rank1,
        internal_actual_rank,
        (pba_tat_in_days - internal_tat_in_days) AS tat_difference_days,
        CASE
            WHEN (pba_tat_in_days - internal_tat_in_days) = 0 THEN 'SAME_TAT'
            WHEN (pba_tat_in_days - internal_tat_in_days) < 0 THEN 'PBA_FASTER'
            WHEN (pba_tat_in_days - internal_tat_in_days) > 0 THEN 'INTERNAL_FASTER'
            ELSE 'TAT_COMPARISON_NA'
        END AS tat_comparison
    FROM final
    WHERE internal_actual_rank IS NOT NULL
)

SELECT
    internal_actual_rank AS rank,
    tat_comparison,
    COUNT(DISTINCT order_id) AS order_count,
    ROUND(COUNT(DISTINCT order_id) * 100.0 / SUM(COUNT(DISTINCT order_id)) OVER (PARTITION BY internal_actual_rank), 2) AS percentage_within_rank,
    ROUND(COUNT(DISTINCT order_id) * 100.0 / SUM(COUNT(DISTINCT order_id)) OVER (), 2) AS percentage_of_total,
    AVG(tat_difference_days) AS avg_tat_diff_days,
    MIN(tat_difference_days) AS min_tat_diff_days,
    MAX(tat_difference_days) AS max_tat_diff_days
FROM internal_rankings
GROUP BY internal_actual_rank, tat_comparison
ORDER BY internal_actual_rank, tat_comparison
```

---

## Coverage Notes

- Query 1 date filter: `2026-05-08` (PBA go-live)
- Query 2 date filter: `2026-02-18` (broader — used for ranking signal analysis)
- Query 2 excludes orders where internal courier does not appear in Clickpost's preference array (`internal_actual_rank IS NOT NULL` filter)
- `pba_matches_rank1` in Query 2 is NULL for all rows in shadow mode (`selected_source = 'INTERNAL'`). Only meaningful if query is reused without the `selected_source` filter.
