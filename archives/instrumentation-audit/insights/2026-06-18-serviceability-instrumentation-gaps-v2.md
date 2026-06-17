# Serviceability — What We Can't Measure Today (v2)

*Plain-language rewrite of v1. Same findings, easier to read. System #1 of the instrumentation audit.*

---

## The one-line summary

Serviceability decides **who we can serve, from where, and by which courier**. Today we only record those decisions **for orders that actually go through**. So two big things are invisible:

1. **Every customer we turn away.** A non-serviceable customer browses our (Mumbai) catalog, builds a cart, hits checkout — and gets blocked. We log nothing. They disappear with no trace.
2. **The choices we make before an order.** We decide MFC-vs-FC and hyperlocal-vs-courier for every browsing session, but only save it if an order happens. We can't see the full picture.

None of this is broken in an engineering sense. The system is up and fast. It's quietly losing demand and money while every dashboard stays green. That's exactly the kind of gap a PM should own.

> **Important caveat:** these gaps are reasoned from the system doc, not yet checked against live data. Treat each as "very likely missing — confirm in the data audit before building."

---

## How to read this

Gaps are grouped by **what to fix first**, not by theory. Each gap says:
- **Can't answer today** — the business question we're blind to
- **Why it matters** — the decision it unlocks
- **Track this** — the event/property that fixes it

---

## 🔴 Fix first (pure money & growth, totally blind today)

### 1. Where are we turning customers away?
- **Can't answer today:** How many customers do we block because their pincode isn't serviceable? What's the cart value we lose? **Which pincodes have the most blocked demand?**
- **Why it matters:** The list of most-blocked pincodes *is* your expansion roadmap. The lost cart value is the business case for expanding there. Right now this entire population vanishes silently.
- **Track this:** a `serviceability_blocked` event — pincode, cart value, item count, whether it had a cold-chain item, and where the block happened (browse / cart / checkout).
- *Not the same as the error rate eng watches — the system works fine, it just turns money away without recording it.*

### 2. "Serviceable on paper" but rejected in real life
- **Can't answer today:** For every courier except Bluedart, we only refresh which pincodes they cover when they **manually email us a file**. So our config goes stale, we accept an order, and the courier rejects it at pickup. How often does this happen, and for which couriers?
- **Why it matters:** Sizes the cost of manual config refresh — and tells us whether building auto-fetch (which only Bluedart has today) is worth it for the others.
- **Track this:** a daily snapshot of each courier's serviceable-pincode list, matched against orders the courier later rejected at pickup.
- *Not the same as Clickpost API errors — this is good config quietly going out of date.*

---

## 🟠 Fix next (drives network & hyperlocal strategy, partly blind)

### 3. What mix of choices are we actually making — across everyone, not just orders?
- **Can't answer today:** Of all browsing sessions: what % are serviceable? What % go hyperlocal vs courier? What % get served by an MFC vs an FC? We only know this for placed orders.
- **Why it matters:** This is the base data for network and hyperlocal expansion decisions.
- **Track this:** a `serviceability_resolved` event on the Cart and Summary pages — serviceable yes/no, warehouse chosen (FC/MFC), construct, courier.

### 4. How often does the nearby MFC run dry and dump the order on the slower FC?
- **Can't answer today:** When the priority MFC has no stock, we silently serve from the FC — which usually means a slower delivery promise. We can guess this for placed orders, but not for the rest.
- **Why it matters:** Directly informs MFC stocking decisions and sizes how much slower-promise pain this fallback causes.
- **Track this:** a `selection_reason` on `serviceability_resolved` (MFC had stock / MFC empty → FC / both empty → FC).

### 5. Are any couriers running on stale coverage?
- **Can't answer today:** How old is each courier's pincode-coverage config? Is our coverage silently shrinking or growing over time?
- **Why it matters:** Stale coverage = we either offer service we can't deliver, or miss service we could offer.
- **Track this:** the daily courier config snapshot from gap #2 — keep the timestamp and the pincode count over time.

---

## 🟡 Later (sharpens known stories & edge cases)

These are real but lower-urgency. Grouped briefly:

- **Does our choice actually convert better?** — Do hyperlocal orders or MFC orders convert more often? Needs the `serviceability_resolved` event linked to whether an order followed.
- **Cold-chain blocks & repeat-blocked users** — How many blocks are specifically cold-chain customers (a different fix: cold-chain infra, not general coverage)? Who keeps coming back and getting blocked (these are "notify me when you launch here" candidates)?
- **Misleading catalog** — Non-serviceable customers browse the Mumbai catalog they can't actually order from. Is that helping them discover, or just wasting their time?
- **Address-change surprises** — A customer changes their address and silently flips from serviceable to non-serviceable. How often, and does it kill the order?
- **Edge fallbacks** — Hyperlocal only ever uses the priority-1 courier (no fallback exists); when that courier can't serve, it's a silent failure. Same for warehouse priority-2 being dead config. Low volume, but worth a count.

---

## What to actually build first

**Two events unlock everything in the 🔴 "fix first" tier:**

1. **`serviceability_blocked`** → unlocks gap #1 (blocked customers, lost cart value, top blocked pincodes).
2. **Courier config snapshot + pickup-rejection match** → unlocks gap #2 (paper-vs-reality) and feeds gap #5 (stale coverage).

A third event, **`serviceability_resolved`** (on Cart + Summary), unlocks the whole 🟠 "fix next" tier.

So: **three events** cover the top ~10 gaps.

---

## Before building anything

These gaps are reasoned from the doc. Next step is a **data audit**: check the live Mixpanel events and the `delivery_date_tracker` / allocation tables to confirm what's genuinely missing vs. already there in some form. Then scope the three events with engineering.

*(Full theory, the six-lens framework, and the detailed metric-by-metric mapping live in v1 and in `context/2026-06-18-instrumentation-gap-framework-v1.md`. This v2 is the readable version.)*
