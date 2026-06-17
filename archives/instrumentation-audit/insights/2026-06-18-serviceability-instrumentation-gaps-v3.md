# Serviceability — What We Can't Measure Today (v3)

*Plain-language gap catalog. System #1 of the instrumentation audit.*

**What changed since v2:** we now know one piece of instrumentation already exists — an event property **`is_sdd_eligible`** (boolean: was this hyperlocal-eligible?). That partly closes the "construct mix" gap (#3) but comes with three catches, and it raises a new cheap first task: figure out which pages it actually fires on. Details in gap #3 and the new "Step 0" below.

---

## The one-line summary

Serviceability decides **who we can serve, from where, and by which courier**. Today we mostly record those decisions **for orders that go through** — plus one early signal (`is_sdd_eligible`) whose page coverage we haven't confirmed. So two big things stay invisible:

1. **Every customer we turn away.** A non-serviceable customer browses our (Mumbai) catalog, builds a cart, hits checkout — and gets blocked. We log nothing. They disappear.
2. **The choices we make before an order.** We decide MFC-vs-FC and which courier for every session, but only save it if an order happens. (The lone exception is hyperlocal *eligibility* — see #3.)

None of this is broken in an engineering sense. The system is up and fast. It's quietly losing demand and money while every dashboard stays green. That's the kind of gap a PM should own.

> **Caveat:** these gaps are reasoned from the system doc + the one property you flagged. Still not fully checked against live data — confirm in the data audit before building.

---

## How to read this

Gaps grouped by **what to fix first**. Each gap says: **Can't answer today** → **Why it matters** → **Track this**.

---

## ⚪ Step 0 — Cheap, do this before building anything

### 0. Where does `is_sdd_eligible` actually fire — PDP, Cart, or Summary?
- **Can't answer today:** We have the property but don't know which pages emit it. Until we do, we don't know which funnel stage it lets us measure.
- **Why it matters:** This is a 1-day data check, not an engineering build. If it already fires on all three pages, half of gap #3 is solved for free. If it only fires at Summary (or on the order), we know exactly what to extend.
- **Do this:** pull the event in Mixpanel, break down by page/screen, confirm coverage across PDP / Cart / Summary. Also check whether it fires for **non-serviceable** sessions (relevant to gap #1).

---

## 🔴 Fix first (pure money & growth, totally blind today)

### 1. Where are we turning customers away?
- **Can't answer today:** How many customers do we block because their pincode isn't serviceable? What's the cart value we lose? **Which pincodes have the most blocked demand?**
- **Why it matters:** The list of most-blocked pincodes *is* your expansion roadmap. The lost cart value is the business case for expanding there. This entire population vanishes silently today.
- **Track this:** a `serviceability_blocked` event — pincode, cart value, item count, whether it had a cold-chain item, and where the block happened (browse / cart / checkout).
- *Not the same as the error rate eng watches — the system works fine, it just turns money away without recording it.*

### 2. "Serviceable on paper" but rejected in real life
- **Can't answer today:** For every courier except Bluedart, we only refresh which pincodes they cover when they **manually email us a file**. So config goes stale, we accept an order, and the courier rejects it at pickup. How often, and for which couriers?
- **Why it matters:** Sizes the cost of manual config refresh — and whether building auto-fetch (which only Bluedart has) is worth it for the others.
- **Track this:** a daily snapshot of each courier's serviceable-pincode list, matched against orders the courier later rejected at pickup.
- *Not the same as Clickpost API errors — this is good config quietly going out of date.*

---

## 🟠 Fix next (drives network & hyperlocal strategy, partly blind)

### 3. What mix of choices are we actually making — across everyone, not just orders?
**This is the gap `is_sdd_eligible` partly addresses.** Here's what we have and what's still missing.

- **What we already have:** `is_sdd_eligible` tells us, per event, whether the session/order was **hyperlocal-eligible**. Good — that's the construct signal, at least as a yes/no.
- **Catch 1 — eligibility ≠ what happened.** Eligible means it *could* go hyperlocal, not that it *did*. A hyperlocal-eligible order can still end up on courier. So we can measure the **eligibility rate**, but not the **true construct mix** (what actually shipped hyperlocal vs courier).
- **Catch 2 — page coverage unknown.** See Step 0. If it doesn't fire on PDP/Cart/Summary consistently, we can't read the mix at each funnel stage.
- **Catch 3 — it's only the hyperlocal boolean.** Still blind to: serviceable yes/no, FC vs MFC, which courier, cold-chain deliverability.
- **Why it matters:** This is the base data for network and hyperlocal expansion decisions.
- **Track this:** don't build from scratch — **extend the existing `is_sdd_eligible` event** into a fuller `serviceability_resolved` payload (add: `is_serviceable`, `wh_selected_type` FC/MFC, `selection_reason`, `courier`, `is_cold_chain_required/deliverable`) and make sure it fires on all of PDP / Cart / Summary. Keep `is_sdd_eligible` as one field inside it.

### 4. How often does the nearby MFC run dry and dump the order on the slower FC?
- **Can't answer today:** When the priority MFC has no stock, we silently serve from the FC — usually a slower promise. We can guess for placed orders, not for the rest.
- **Why it matters:** Directly informs MFC stocking decisions and sizes the slower-promise pain.
- **Track this:** a `selection_reason` on the resolved event (MFC had stock / MFC empty → FC / both empty → FC).

### 5. Are any couriers running on stale coverage?
- **Can't answer today:** How old is each courier's pincode-coverage config? Is our coverage silently shrinking or growing?
- **Why it matters:** Stale coverage = we either offer service we can't deliver, or miss service we could offer.
- **Track this:** the daily courier config snapshot from gap #2 — keep the timestamp and pincode count over time.

---

## 🟡 Later (sharpens known stories & edge cases)

- **Does our choice actually convert better?** — Do hyperlocal-eligible orders or MFC orders convert more? Needs the resolved event linked to whether an order followed. (Now partly reachable via `is_sdd_eligible` once page coverage is known.)
- **Cold-chain blocks & repeat-blocked users** — How many blocks are cold-chain customers (a different fix: cold-chain infra, not general coverage)? Who keeps coming back and getting blocked (these are "notify me when you launch here" candidates)?
- **Misleading catalog** — Non-serviceable customers browse the Mumbai catalog they can't order from. Helping discovery, or wasting time?
- **Address-change surprises** — A customer changes address and silently flips from serviceable to non-serviceable. How often, and does it kill the order?
- **Edge fallbacks** — Hyperlocal only ever uses the priority-1 courier (no fallback exists); when it can't serve, it's a silent failure. Same for warehouse priority-2 being dead config. Low volume, worth a count.

---

## What to actually build first

**Step 0 (cheap):** confirm `is_sdd_eligible` page coverage in Mixpanel. No build required.

**Then two events unlock the 🔴 "fix first" tier:**
1. **`serviceability_blocked`** → blocked customers, lost cart value, top blocked pincodes (gap #1).
2. **Courier config snapshot + pickup-rejection match** → paper-vs-reality (gap #2) + feeds stale coverage (gap #5).

**Then enrich what exists** → take `is_sdd_eligible` and grow it into the fuller `serviceability_resolved` event (gap #3/#4), firing on all three pages.

So: **1 audit + 2 new events + 1 enrichment** covers the top ~10 gaps.

---

## Before building anything

Run the **data audit**: confirm `is_sdd_eligible` page coverage, then check the live Mixpanel events and the `delivery_date_tracker` / allocation tables for anything else already partly instrumented. Then scope the work with engineering.

*(Full theory + the six-lens framework live in v1 and `context/2026-06-18-instrumentation-gap-framework-v1.md`. v2/v3 are the readable versions; v3 supersedes v2.)*
