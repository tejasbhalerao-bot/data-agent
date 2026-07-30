# Metric Definitions — Egregiously Miscalibrated Promises

> Living document. Add a definition here whenever a new metric is built or agreed upon.
> Format: metric name, definition, formula/derivation, and any known caveats.

---

## Definitions

### Egregiously Miscalibrated Order

**Definition:** An order where the delivery attempt date deviated from the promised delivery date by 2 or more calendar days in either direction.

**Formula:** `|DATE(digitised_delivery_promise) − DATE(delivery_attempt_time)| >= 2`

**Unit:** Calendar days

**Variants:**
- **Egregiously early:** `DATE(digitised_delivery_promise) − DATE(delivery_attempt_time) >= 2` — courier attempted delivery at least 2 days before the promise date
- **Egregiously late:** `DATE(delivery_attempt_time) − DATE(digitised_delivery_promise) >= 2` — courier attempted delivery at least 2 days after the promise date

**Caveats:**
- Uses `delivery_attempt_time` (first OFD attempt), not `actual_delivery_date`. Orders with NULL `delivery_attempt_time` are excluded — they were never attempted.
- Date comparison strips the time component. A promise of `2026-07-08 20:00` and an attempt of `2026-07-06 23:59` counts as a 2-day gap and is included.
- `digitised_delivery_promise` reflects the promise shown to the customer at order placement — this is the correct anchor, not any downstream shipping promise.

---

### Doctor Early / On-Time / Late

**Definition:** Whether the doctor confirmed the order before, exactly at, or after the promised confirmation time.

**Inputs:**
- A = `digitised_dr_promise` — time the doctor was promised to confirm the order
- B = `dr_confirm_ts` — time the doctor actually confirmed the order

**Formula:**

| Condition | Classification |
|-----------|---------------|
| A > B | Early — doctor confirmed before the promised time |
| A = B | On-time — doctor confirmed exactly at the promised time |
| A < B | Late — doctor confirmed after the promised time |

**Unit:** Timestamp comparison (no date truncation — full timestamp used)

**Caveats:**
- `dr_confirm_ts` is doctor confirmation time, not call time — these are distinct events.
- Orders with NULL `dr_confirm_ts` are excluded — doctor never confirmed.

---

### Warehouse Early / On-Time / Late

**Definition:** Whether the warehouse finished packing the order before, exactly at, or after the promised packing completion time.

**Inputs:**
- A = `digitised_wh_promise` — time the warehouse was promised to finish packing the order
- B = `awb_sticker_printed_ts` — time the warehouse actually finished packing (proxied by AWB sticker print time)

**Formula:**

| Condition | Classification |
|-----------|---------------|
| A > B | Early — warehouse finished packing before the promised time |
| A = B | On-time — warehouse finished packing exactly at the promised time |
| A < B | Late — warehouse finished packing after the promised time |

**Unit:** Timestamp comparison (no date truncation — full timestamp used)

**Caveats:**
- AWB sticker print time is used as the proxy for warehouse packing completion — it is the closest system-recorded event to when the order was ready for courier pickup.
- Orders with NULL `awb_sticker_printed_ts` are excluded — warehouse never completed packing.

<!--
Template:

### Metric Name

**Definition:** One-sentence description of what this measures.

**Formula:** How it is computed (reference column names from data-sources.md).

**Unit:** e.g. minutes, days, %, count

**Caveats:** Edge cases, exclusions, or gotchas.

-->
