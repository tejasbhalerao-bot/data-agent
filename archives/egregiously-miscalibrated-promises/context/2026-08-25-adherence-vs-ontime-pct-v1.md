# Adherence vs On-Time % — The Core Metric Flaw

**Project:** Egregiously Miscalibrated Promises
**Date:** 2026-08-25

---

## What the current metric measures

`adherence_percentage` is computed as a cumulative sum starting at `Early4plusday` and stopping the moment it crosses `percentile_value`. This means:

1. It **pays couriers for being early** — early parcels count the same as on-time parcels toward the threshold.
2. It **only ever varies between 0.8 and 1.0** — a feature with 0.2 of range that is a step function of bucket boundaries is a bad feature.

The low variance of `adherence_percentage` is exactly why the weighting in the scoring formula looks broken. A feature that barely moves cannot meaningfully differentiate couriers.

---

## The 44-order gap example

On the same lane, at the same promised date, the formula picked the courier with **44 fewer on-time orders**. Why:

| Courier | Early | On-Time | Total (Early + On-Time) | Adherence |
|---------|-------|---------|------------------------|-----------|
| B       | 55    | 30      | 85                     | 85%       |
| A       | 0     | 74      | 74                     | 74%       |

Courier B's adherence looks better (85% vs 74%) because 55 of its 85 parcels are early. But only 30 are actually on-time. The formula treats an early parcel and an on-time parcel as identical. A courier can look more reliable purely by being early a lot — which is a miss, not a success.

---

## The minimum viable fix

> Keep p80 exactly as it is. Change nothing about the promise. Just replace adherence with on-time% in the selection score. Same promise logic, same late cap, one field swapped.

This is a single-field swap in the scoring step. It does not touch the promise date calculation, the late cap, or any other part of the pipeline.

---

## Why the current system is a padding engine, not a prediction engine

The adherence loop iterates late-days until ≥80% is met, then stops. That calibrates every lane to its **80th percentile**. A promise set at the 80th percentile gets missed ~20% of the time by construction.

Current production performance:

| Leg | Early | On-Time | Late |
|-----|-------|---------|------|
| Logistics leg | 23.2% | 54.8% | 22.0% |
| End-to-end ETA | 33.0% | 51.4% | 15.6% |

The design floor is ≥80% not-late (i.e. ≤20% late). Production is at 84.4% not-late end-to-end — technically above spec — but the 33% early rate is what the system is paying for that margin. The 15.6% late rate is not a failure; it is the design spec working as built.

---

## Structural accuracy problems (three root causes)

### 1. Whole-day quantization

Every term in the promise formula — ideal TAT, late-day loop, schedule time, pickup buffer, drop buffer — is expressed in whole days. The minimum error unit is therefore 24 hours. A lane that truly runs 1.3 days gets promised 2 or 3. Sub-day resolution is structurally impossible.

### 2. Buffers stack additively when variance doesn't

Four independently-conservative terms summed together over-cover badly. Real variance compounds closer to root-sum-of-squares, not simple addition. This is the arithmetic reason a third of orders land early.

### 3. The TAT/Adherence division secretly sets a different day price per lane

The `TAT / Adherence` division prices one extra day at different on-time points depending on the lane — approximately **42 percentage points on fast lanes** and **17 percentage points on slow lanes** — with no one having chosen those numbers. The asymmetry is a hidden artefact of the formula structure, not a deliberate calibration.

---

## Summary of changes implied

| Current | Replacement |
|---------|-------------|
| `adherence_percentage` (range 0.8–1.0, includes early) | `on_time_pct` (range 0–1, excludes early) |
| Courier selection favours early-heavy couriers | Courier selection favours genuinely on-time couriers |
| Score feature has ~0.2 effective range | Score feature uses full 0–1 range |
