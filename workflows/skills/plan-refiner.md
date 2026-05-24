# Skill: Plan Refiner

Evaluates the plan produced by `plan-builder` across two layers: correctness and exhaustiveness.
Always runs after `plan-builder`. Never presents plan to Tejas without completing both layers.
Loops back to `plan-builder` with structured critique if issues found. Max 2 revision cycles.

---

## Layer 1: Correctness

Run all 6 checks. Each is pass or fail.

| # | Criterion | Passes if... | Fails if... |
|---|---|---|---|
| C1 | Objective is measurable | Outcome can be confirmed yes/no or with a number at analysis end | Objective is still directional or vague |
| C2 | Full Q→Step traceability | Every Q has ≥1 step. Every step answers ≥1 Q | Any Q with no step (gap) or step with no Q (scope creep) |
| C3 | Every step has a plausible data source | Plan lists a source that could contain the data each step needs | Any step floats with no data source behind it |
| C4 | Business logic is explicit | Every metric/term used in the plan was defined in Tejas's Step 1b answers | Any term appears undefined or inferred (e.g. "on-time" used but never defined) |
| C5 | Steps are correctly ordered | No step depends on output from a later step | Dependency ordering is broken |
| C6 | Definition of done is present and specific | Completion criteria are stated concretely | Missing entirely or vague ("analysis complete") |

**If any criterion fails:**
- Do not proceed to Layer 2
- Produce a structured critique (format below)
- Send back to `plan-builder` with critique attached

---

## Layer 2: Exhaustiveness

Only runs when all Layer 1 criteria pass.

Evaluate the plan as a senior analyst would before writing a single query. Ask:

1. **Segmentation** — Are there cuts missing that would change the conclusion? (e.g. by courier, lane, vertical, time window, pre/post cutoff, order value band)
2. **Confounders** — Is there a variable not controlled for that could explain the result? (e.g. mix shift, seasonality, sample size imbalance)
3. **Counter-hypothesis** — Is there an alternative explanation the plan doesn't test? Should it?
4. **Proxy risk** — Is the plan measuring the right thing, or a proxy that could mislead? (e.g. measuring attempt-level adherence when delivery-level matters)
5. **Actionability gap** — Would the findings as designed lead to a decision? If not, what's missing?
6. **Missing failure modes** — Are there edge cases or failure scenarios the plan ignores that could matter? (e.g. fallback logic, data sparsity in specific lanes)

For each gap identified: propose a specific addition to the plan with a one-line rationale.

**Format for proposals:**

> **Proposed addition:** [Specific step or question to add]
> **Rationale:** [Why this matters — what it would reveal or rule out]
> **Accept / Reject?**

Present all proposals together. Wait for Tejas to accept or reject each one before proceeding.

- Accepted additions → send back to `plan-builder` with specific instructions to incorporate
- All rejected or nothing to add → proceed to final presentation

---

## Critique format (used for both layers)

When sending back to `plan-builder`, always use this structure:

```
## Plan Refiner Critique — v[n]

### Layer 1: Correctness
| Criterion | Result | Finding |
|---|---|---|
| C1 Measurable objective | PASS / FAIL | [specific issue if fail] |
| C2 Q→Step traceability | PASS / FAIL | [e.g. Q3 has no step] |
| C3 Data sources | PASS / FAIL | [e.g. Step 4 has no source] |
| C4 Business logic explicit | PASS / FAIL | [e.g. "on-time" undefined] |
| C5 Step ordering | PASS / FAIL | [e.g. Step 2 depends on Step 5 output] |
| C6 Definition of done | PASS / FAIL | [specific issue if fail] |

### Layer 2: Exhaustiveness
[Only if Layer 1 all passed]
[List accepted additions with instructions for plan-builder]

### Instructions for plan-builder
- [Specific change 1]
- [Specific change 2]
```

---

## Revision limit

- After 2 revision cycles, if issues remain unresolved — stop.
- Present plan to Tejas with unresolved issues explicitly flagged. Do not loop further.
- Tejas decides whether to override or resolve.

---

## Final presentation to Tejas

When all criteria pass and exhaustiveness check is complete:

Present the plan with a brief header:

```
## Plan v[n] — Ready for approval

**Refiner status:** All correctness criteria passed. Exhaustiveness check complete.
**Additions incorporated:** [list, or "None proposed" / "None accepted"]

[Full plan below]

Approve to proceed to table-mapper, or request changes.
```

Wait for explicit approval before handing off to `table-mapper`.
