# Option Table and Scoring — How Couriers Are Evaluated

**Project:** Egregiously Miscalibrated Promises
**Date:** 2026-08-25

---

## The two business dials

These two numbers are set by the business before anything else runs:

| Dial | Default value | Meaning |
|------|---------------|---------|
| Late cap | 20% | Never promise a day where more than 20 out of 100 orders end up late |
| Day price | 15 points | One extra promised day is only worth it if it buys more than 15 on-time percentage points |

---

## Building the option table (Steps 4–6 of the 14-step system)

**Step 4 — Build the option table.**
For every possible promise day, work out three numbers:
- **Early** — orders that arrived before that day
- **On-time** — orders that arrived exactly on that day
- **Late** — orders that arrived after that day

**Step 5 — Delete the unsafe rows.**
Remove any row where Late is above 20%.

**Step 6 — Keep the best row that's left.**
For each surviving row, compute: `On-time% − (15 × promise days)`. Keep the row with the highest score.

---

## Scoring at order time (Steps 10–11)

**Step 10 — Score each courier.**

```
Score = On-time% − (15 × Total days)
```

**Step 11 — Highest score wins.**
If two couriers tie, pick one at random. This keeps orders flowing to both so their option tables stay fresh.

---

## Worked example: Mumbai → 411001

| Courier | Total days | On-time% | Score calculation | Score |
|---------|-----------|----------|-------------------|-------|
| A | 3 | 70% | 70 − (15 × 3) | **25** |
| B | 2 | 62% | 62 − (15 × 2) | **32** |

Courier B wins. At the same late-cap constraint, B delivers 2-day promises with 62% on-time — and the day price of 15 means the 8pp lower on-time rate does not outweigh saving a day.

**What happens if the day price changes to 5:**

| Courier | Score at day price = 5 |
|---------|------------------------|
| A | 70 − (5 × 3) = **55** |
| B | 62 − (5 × 2) = **52** |

A wins. This demonstrates that day price is a single dial that shifts the entire selection outcome. There are no buffers to tune — only two numbers.

---

## Why mode, not p80, for promise placement

- **p80** maximises a late-risk cap — it is the right tool when the goal is "never exceed X% late."
- **Mode (busiest day)** is the correct promise estimator to maximise on-time% — it picks the day most orders actually arrive.

The difference between p80 and the best-safe-day (the top-scoring row after Step 6) is mostly invisible at the aggregate level. The real gains from the new system come from courier selection, not from shifting the promise date itself.

---

## Rolling window instability

With 30 orders on a lane, one order = 3.3 percentage points of on-time%. Normal weekly variation of 2–3 orders = **7–10 points of score movement**. This is large enough to flip a 2-point gap between couriers every night, causing the winner to alternate without any real change in courier performance.

This is why sample floors matter — see `2026-08-25-sample-floor-and-exploration-v1.md`.

---

## Schedule time flag

The system applies a schedule time flag to account for warehouse cutoff:

```
If order placed after warehouse cutoff time for this courier:
    schedule_time_flag = 1
Else:
    schedule_time_flag = 0
```

**Open question (unresolved):** Is `schedule_time` (+1 day) applied before or after courier selection? The PRD prose and the formula give conflicting answers. This matters because applying it before selection changes which couriers survive the late cap filter; applying it after selection changes the promised date without affecting which courier wins.
