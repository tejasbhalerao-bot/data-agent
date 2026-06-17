# Instrumentation-Gap Framework (v1)

A reusable method for auditing any Truemeds system for **product/analytics instrumentation gaps** — metrics a PM needs to run the business but cannot compute today because the events or properties were never instrumented.

This is system-agnostic. Each system (Serviceability, Allocation, Promise Engine, etc.) gets its own gap-catalog doc that applies this framework. Serviceability is the first application — see `insights/2026-06-18-serviceability-instrumentation-gaps-v1.md`.

---

## 1. The exclusion rule (what is NOT a gap)

We are hunting **product metrics**, not engineering system-health metrics. The two are easy to confuse, which is exactly why PMs end up blind: eng dashboards are green while the business bleeds.

| | Engineering system-health (EXCLUDED) | Product/analytics (INCLUDED) |
|---|---|---|
| Question | Is the system up, fast, erroring? | Is the system making good business decisions? Where do we win/lose demand, money, experience? |
| Examples | API latency, uptime, 4xx/5xx rate, DB load, queue depth, replication lag | Demand turned away, revenue leaked, decision mix, fallback quality, config drift, conversion by decision |
| Who owns it | Eng / SRE | PM |
| Failure signature | Throws an error, pages someone | **Silent** — no error, nobody alerted, value quietly lost |

**The test for "is this a gap worth listing":** if the metric only tells you whether the *machine* is healthy, drop it. If it tells you whether the *business decision* is good — or sizes demand/money/experience you're currently losing silently — keep it.

Every gap record carries a "must NOT be confused with" column naming the eng-health metric it's adjacent to. That column is the spine of the whole exercise.

---

## 2. The six-lens decomposition

Trace the system's causal chain and instrument six categories. Most PM blind spots are lenses 3–6 because those failures are *silent*.

| # | Lens | What to instrument | Why it's the PM blind spot |
|---|------|--------------------|----------------------------|
| 1 | **Decisions** | Every branch the system takes: the inputs, the chosen output, and the alternatives it considered | A decision you can't see is a decision you can't optimize. Decision *mix* drives strategy. |
| 2 | **Outcomes** | The downstream result (converted? delivered? returned?), carrying a join key back to the decision | Lets you ask "did this decision actually produce a good result" instead of guessing |
| 3 | **Rejections / Leakage** | Every "no" / block, **with the attributes of the rejected population** | Turned-away demand is invisible by default — you only ever see who got through. Usually the single biggest gap. |
| 4 | **Fallbacks / Degradations** | Every silent substitution of a worse-but-still-valid option | Quality erodes without erroring, so eng never alerts and PM never notices |
| 5 | **Config / Control State** | The human/system-set parameters that drive decisions, plus their **freshness** | Stale or wrong config silently mis-routes everything downstream |
| 6 | **Experience friction** | What the *customer perceives* at the decision moment (delay, misleading UI, mid-journey flip) | Not an eng latency number — the felt experience that suppresses conversion |

### The gap test (apply per lens)
> Is there an **event**, with the right **properties**, at the right **grain**, that lets a PM compute the metric **without reverse-engineering it from downstream transactional tables**?

If the only way to get the number is to infer it backwards from orders that succeeded, it fails the test — because the rejected/non-converting population is missing from that backwards path.

---

## 3. The standard gap record

Every metric in a per-system catalog is one row with these six fields:

| Field | Meaning |
|---|---|
| **Metric** | The number itself |
| **Business question / decision it drives** | What action this number changes. If none, the metric is vanity — cut it. |
| **Required event(s) + key properties + grain** | The exact instrumentation needed (event name, properties, per-what) |
| **Current state** | `Instrumented` / `Partial` / `Missing` (mark assumptions explicitly when derived first-principles) |
| **Plug priority** | P0–P3 (see scoring below) |
| **Must NOT be confused with** | The adjacent eng-health metric — keeps the analysis honest |

---

## 4. Prioritization (plug-first scoring)

Rank each gap by three factors, then bucket:

- **Impact** — does closing this gap unlock a money or growth decision (high), an experience/quality decision (medium), or an edge-case (low)?
- **Blindness** — are we totally blind today (high), partially blind (medium), or just need a cleaner cut (low)?
- **Actionability** — once we can see it, is there an obvious lever (expand here, fix this config)?

| Tier | Profile |
|---|---|
| **P0** | High impact (money/growth) + total blindness + clear lever. Pure leakage we can't even size today. |
| **P1** | Drives a strategy/operations decision; partial blindness or one step removed from the lever. |
| **P2** | Refines a known story (conversion by segment, edge populations). |
| **P3** | Edge cases, nice-to-have, or low-volume failure modes. |

---

## 5. How to apply this to a new system

1. **Distill the system** to its decisions, outcomes, rejections, fallbacks, config, and friction points (read the system doc; do not infer behaviour from memory).
2. **Walk the six lenses**, asking the gap test at each. Name the missing event(s).
3. **Write one gap record per metric.** Force the "must NOT be confused with" column on every row.
4. **Coverage check:** every decision branch and every explicitly-documented silent failure mode must be covered by ≥1 metric.
5. **Prioritize** into P0–P3.
6. **Ground later:** before building anything, run a live audit (Mixpanel event taxonomy + the relevant transactional/instrumentation tables) to flip each `Missing`/`Partial` to a confirmed status. First-principles catalogs are hypotheses until grounded.
