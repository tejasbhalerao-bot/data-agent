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

---

### Dispatch Early / On-Time / Late

**Definition:** Whether the courier picked up the order before, exactly on, or after the promised dispatch date.

**Inputs:**
- A = `DATE(digitised_dispatch_promise)` — calendar date the courier was promised to pick up the order
- B = `DATE(pickup_time)` — calendar date the courier actually picked up the order

**Formula:**

| Condition | Classification |
|-----------|---------------|
| A > B | Early — courier picked up before the promised dispatch date |
| A = B | On-time — courier picked up on the promised dispatch date |
| A < B | Late — courier picked up after the promised dispatch date |

**Unit:** Calendar date comparison (time component stripped from both timestamps)

**Caveats:**
- Uses DATE() truncation — a promise of `2026-07-13 23:59` and a pickup of `2026-07-13 00:01` are both `2026-07-13` and count as on-time.
- Orders with NULL `pickup_time` are excluded — courier never picked up the order.

---

### Delivery Early / On-Time / Late

**Definition:** Whether the courier attempted delivery before, exactly on, or after the promised delivery date.

**Inputs:**
- A = `DATE(digitised_delivery_promise)` — calendar date the courier was promised to deliver the order
- B = `DATE(delivery_attempt_time)` — calendar date the courier actually attempted delivery

**Formula:**

| Condition | Classification |
|-----------|---------------|
| A > B | Early — courier attempted delivery before the promised date |
| A = B | On-time — courier attempted delivery on the promised date |
| A < B | Late — courier attempted delivery after the promised date |

**Unit:** Calendar date comparison (time component stripped from both timestamps)

**Caveats:**
- Uses DATE() truncation — a promise of `2026-07-08 20:00` and an attempt at `2026-07-08 13:04` are both `2026-07-08` and count as on-time.
- Orders with NULL `delivery_attempt_time` are excluded — courier never attempted delivery.
- This metric classifies all deviations including ±1 day. The **Egregiously Miscalibrated Order** metric is a subset of early/late, capturing only cases where |A − B| ≥ 2 days.

---

### Delivery TAT Early / On-Time / Late

**Definition:** Whether the courier's actual transit time (pickup → delivery attempt) was shorter, equal to, or longer than the promised transit time (promised dispatch → promised delivery).

**Inputs:**
- A = `DATE(digitised_delivery_promise) − DATE(digitised_dispatch_promise)` — promised TAT in calendar days
- B = `DATE(delivery_attempt_time) − DATE(pickup_time)` — actual TAT in calendar days

**Formula:**

| Condition | Classification |
|-----------|---------------|
| A > B | Early — courier delivered in fewer days than promised |
| A = B | On-time — courier matched the promised TAT exactly |
| A < B | Late — courier took more days than promised |

**Unit:** Calendar days (integer difference between dates)

**Caveats:**
- All four timestamps must be non-NULL — orders missing any of them are excluded.
- Uses DATE() truncation on all four timestamps before computing differences.
- This measures courier transit performance only — it does not capture whether dispatch itself happened on time (see **Dispatch Early / On-Time / Late**).

---

### Shipping Delivery TAT Early / On-Time / Late

**Definition:** Whether the courier's actual transit time (pickup → delivery attempt) was shorter, equal to, or longer than the TAT promised by the courier who actually shipped the order.

**Inputs:**
- A = `shipping_delivery_promise` — TAT in days promised by the courier who actually shipped the order
- B = `DATE(delivery_attempt_time) − DATE(pickup_time)` — actual TAT in calendar days

**Formula:**

| Condition | Classification |
|-----------|---------------|
| A > B | Early — courier delivered in fewer days than their shipping TAT promise |
| A = B | On-time — courier matched their shipping TAT promise exactly |
| A < B | Late — courier took more days than their shipping TAT promise |

**Unit:** Days (A is already in days; B is an integer date difference)

**Caveats:**
- `shipping_delivery_promise` is the TAT of the courier who actually shipped the order — it may differ from the digitised promise if the order was rerouted to a different courier or warehouse after placement (see **Delivery TAT Early / On-Time / Late** for the digitised-promise equivalent).
- Orders with NULL `delivery_attempt_time` or `pickup_time` are excluded.
- Uses DATE() truncation on `delivery_attempt_time` and `pickup_time` before computing B.

<!--
Template:

### Metric Name

**Definition:** One-sentence description of what this measures.

**Formula:** How it is computed (reference column names from data-sources.md).

**Unit:** e.g. minutes, days, %, count

**Caveats:** Edge cases, exclusions, or gotchas.

-->
