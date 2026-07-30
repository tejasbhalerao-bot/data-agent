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

<!--
Template:

### Metric Name

**Definition:** One-sentence description of what this measures.

**Formula:** How it is computed (reference column names from data-sources.md).

**Unit:** e.g. minutes, days, %, count

**Caveats:** Edge cases, exclusions, or gotchas.

-->
