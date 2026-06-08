# Courier Allocation Revamp — Impact Analysis Plan

**Date:** 2026-06-08
**Reference:** [System Workflow](../context/2026-06-08-system-workflow-v1.md) | [PRD](https://docs.google.com/document/d/1HxILz8W8_UxLKXkaaoACFW8WPpAHTxESysn6Rjaq-Bc/edit)

---

## Causal Chain

The system works through three mechanisms. Impact analysis must measure each link separately:

```
Pooled adherence scores
    → (1) Adherence score correction — the TAT/adherence score for a courier changes on thin lanes
    → (2) Courier switch — a different courier wins allocation because scores re-ranked
    → (3) Promise TAT correction — Final TAT changes because pooled distribution is more accurate
    → (4) Delivery outcome — actual adherence and TAT change as a result
```

Mechanisms 1–3 are measurable during Stage 1A (shadow, no live change). Mechanism 4 is measurable only from Stage 2 onward (live allocation).

---

## Data Sources

| Stage | What's available |
|---|---|
| Stage 1A | Instrumentation rows (shadow + existing algorithm). Historical delivery actuals from the same period. No new delivery outcomes — allocation unchanged. |
| Stage 1B | Same as 1A — threshold selection is an analysis decision, not a new data collection phase. |
| Stage 2 | Instrumentation rows (live allocation). Actual delivery outcomes for orders allocated under the new system. Stage 1A baseline for counterfactual. |
| Stage 3 | Ongoing actual delivery outcomes. |

---

## Stage 1A — Shadow Analysis (14-day window)

**Purpose:** Understand what would have happened under each of the 6 modes. No actual outcomes change — this is entirely counterfactual.

### 1.1 Courier switch rate

For each order: compare the Rank 1 courier in the existing algorithm run vs. Rank 1 in each shadow mode. An order "switches" if the two differ.

Compute per mode (all 6) and in aggregate:
- % orders where shadow Rank 1 differs from existing Rank 1
- % orders where shadow and existing agree on Rank 1

Break down by:
- Warehouse — which warehouses are switching most?
- Courier — which couriers are gaining orders, which are losing?
- Cascade level that drove the switch — was the switch caused by a pincode-level score correction (thin data directly fixed) or by geographic pooling (city/state cascade now used)?

### 1.2 Adherence score correction

For every order, the existing algorithm computed a TAT/adherence score for the winning courier using raw (thin) lane data. The shadow mode computed a score for the same courier using pooled data. The difference is the correction.

```
Score correction = shadow TAT/adherence score (for existing winner) - existing TAT/adherence score
```

Positive = shadow gives a worse score (courier looked better on thin data than pooled data shows). Negative = shadow gives a better score (courier was unfairly penalised on thin data).

Compute:
- Distribution of score corrections across all orders
- % of existing winners whose scores were inflated (thin data showed 100% adherence → pooled data shows lower)
- Avg magnitude of correction by cascade level — pincode corrections should be smaller in magnitude than city/state corrections
- Which couriers are most systematically inflated vs deflated across lanes?

### 1.3 Promise TAT correction

Even for orders that did not switch couriers, Final TAT may change because the pooled distribution shifts the stopping bucket. Measure the promise direction change for the existing winner:

```
Promise correction = shadow Final TAT (existing winner) - existing Final TAT (existing winner)
```

Compute:
- Distribution of promise corrections (days earlier / same / days later)
- % orders where shadow promise is earlier than existing (pool shows courier delivers faster than thin data suggested)
- % orders where shadow promise is later (pool shows courier delivers slower — promise was too aggressive)
- % orders where promise is unchanged

Orders where the promise gets later are the highest-risk cohort for adherence — they may reduce customer satisfaction even if they are more accurate.

### 1.4 Quality of switch — would the switch have helped?

For orders that switch couriers under shadow: assess whether the shadow winner would have been a better choice. Two lenses:

**Lens 1 — Promise direction:** Did the shadow winner offer a better (earlier) or worse (later) Final TAT than the existing winner?
- % switched orders where shadow promise is better (earlier)
- % switched orders where shadow promise is worse (later) — this is "% Switched Orders with Worse Promise" from the PRD
- % switched orders where promise is identical

**Lens 2 — Historical adherence of shadow winner vs existing winner:** Pull the shadow winner's actual historical adherence (from delivery actuals in the same 14-day window) and compare it to the existing winner's. Did the system switch to a courier that historically performs better?
- % switched orders where shadow winner had higher actual historical adherence
- % switched orders where shadow winner had lower actual historical adherence
- Median adherence delta (shadow winner - existing winner) for switched orders

This second lens is the deeper diagnostic. A switch with worse promise but higher historical adherence is a deliberate tradeoff the system is making — worth understanding before going live.

### 1.5 Courier allocation mix shift

Compare the share of orders each courier receives under shadow vs existing algorithm for the same 14-day window.

- For each courier: shadow share vs existing share, delta in pp
- Overall Herfindahl-Hirschman Index (HHI) under shadow vs existing — is pooling concentrating allocation or diversifying it?
- Flag any courier whose share would shift by more than ±10pp under shadow — those couriers have the most exposure to the live rollout

---

## Stage 1B — Threshold Selection

**Purpose:** Pick one mode from the 6 to take into live rollout.

Compute the three PRD decision metrics for each mode:

| Mode | Computation Variant | n_threshold | % Orders Switching | Avg Adherence Score Correction | % Switched with Worse Promise |
|---|---|---|---|---|---|
| Mode 1 | Computation 1 | 10 | | | |
| Mode 2 | Computation 1 | 15 | | | |
| Mode 3 | Computation 1 | 20 | | | |
| Mode 4 | Computation 2 | 10 | | | |
| Mode 5 | Computation 2 | 15 | | | |
| Mode 6 | Computation 2 | 20 | | | |

**Decision rule (from PRD):** Lowest % Switched with Worse Promise wins. Tie within 1pp → prefer lower threshold.

**Additional diagnostic:** Separate the threshold effect from the computation variant effect:
- Holding Comp1 fixed: does n=10 vs n=15 vs n=20 materially change the Worse Promise rate? (Tests whether threshold matters for promise quality, independent of variant.)
- Holding n_threshold fixed: does Comp1 vs Comp2 materially change the Worse Promise rate? (Tests whether including breach days in adherence changes outcomes.)

This diagnostic is not required for the selection decision but informs future tuning of either dimension independently.

---

## Stage 2 — Live Rollout Impact

**Purpose:** Measure actual adherence and TAT outcomes for orders now allocated by the new system. Stage 1A shadow baseline is the counterfactual — what the old system would have done.

**Important framing:** Two groups exist in the live cohort:
- **Switched orders:** Orders where new system selected a different courier than the old system would have (per Stage 1A shadow data for the selected mode).
- **Non-switched orders:** Orders where new system selected the same courier. Promise TAT may still differ due to mechanism 3.

### 2.1 Adherence delta for switched orders

For switched orders: compare actual delivery outcomes under the new system vs. what Stage 1A shadow data predicted the old system would have done.

- Actual adherence of switched orders under new system
- Predicted adherence of switched orders under old system (using historical delivery data for the old system's winner)
- Delta: did switching to the pooled-adherence winner improve actual adherence?

### 2.2 Promise accuracy improvement

For all live orders (switched and non-switched): measure how much closer Final TAT is to actual delivery date under the new system vs. the old system.

```
Promise error = |Actual Delivery Date - Final TAT|
```

Compare promise error distribution: new system vs. Stage 1A baseline period. A reduced promise error means pooled adherence is producing more calibrated TATs.

### 2.3 Logistics TAT guardrail

Compare actual delivery days (logistics TAT) for:
- Live cohort under new system
- Stage 1A baseline period (same warehouses, same lanes)

Flag if average TAT increases by any material amount. The new system might shift allocation toward couriers with better adherence but longer TATs — this is the guardrail the business is protecting against.

Compute separately for switched and non-switched orders — a TAT increase in non-switched orders would indicate a confound (external factor), while a TAT increase only in switched orders points directly to the new courier selection.

### 2.4 Courier allocation mix guardrail

Compare courier share % in the live cohort vs. Stage 1A baseline.
- Delta in pp per courier
- HHI change — is allocation concentrating?
- Flag any courier with share shift > ±10pp relative to Stage 1A baseline

### 2.5 Rollback trigger monitoring (rolling)

Track daily on a 3-day rolling window:
- % Switched Orders with Worse Promise — trigger if > 5% on any rolling window
- Net promise delta (avg Final TAT under new system - avg Final TAT under Stage 1A baseline) — trigger if degrades by > 0.1 days

These are blocking metrics. If either fires, escalate before expanding to the next rollout step.

---

## Stage 3 — Steady State

**Purpose:** Ongoing health of the system. Sanity + impact combined.

| Metric | Definition | Cadence | Alert threshold |
|---|---|---|---|
| Adherence % | % orders delivered on or before Final TAT | Weekly | Any decline vs 4-week rolling avg |
| Logistics TAT | Avg days from dispatch to delivery | Weekly | Any sustained increase vs baseline |
| Courier allocation mix | Share per courier, HHI | Weekly | Any courier ±10pp in a week |
| % evaluations falling to default | % WH × pincode × courier combos using 80% fallback | Weekly | > 5% |
| % couriers with recent national data | % active couriers with >= n_threshold orders at courier level | Weekly | < 80% |
| Nightly job success rate | % nights job completes within SLA (FC: 45 min, MFC: same) | Daily | Any failure |

---

## Output per Stage

| Stage | Output | Decision |
|---|---|---|
| 1A | Shadow analysis report: switch rate, score correction, promise correction, quality of switch, mix shift | Confirm system is behaving as designed before selecting threshold |
| 1B | Threshold selection note: 6-mode comparison table + selected mode + variant/threshold diagnostic | Pick 1 mode for live rollout |
| 2 | Live impact report at each step (5% → 25% → 50% → 100%): adherence delta, TAT guardrail, mix guardrail, rollback trigger status | Continue / pause / rollback decision at each step |
| 3 | Weekly dashboard: all steady-state metrics | No decision unless alert fires |
