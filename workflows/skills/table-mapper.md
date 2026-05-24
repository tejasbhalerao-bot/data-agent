# Skill: Table Mapper

Translates an approved analysis plan into a data specification and expected output schema.
Always runs after Tejas approves the plan from `plan-refiner`.
Never hands off to `query-builder` without explicit Tejas approval — even if everything looks clean.

---

## Input

Approved analysis plan from `plan-refiner`. Contains:
- Objective
- Questions to answer (Q1, Q2, ...)
- Steps with data sources (high level)
- Business logic definitions from Step 1b

---

## Step 1: Translate plan steps to data requirements

For each step in the plan, identify:
- Which tables are needed
- Which columns are needed from each table
- How tables join together (join keys + expected cardinality)
- What filters apply (date range, inclusion/exclusion rules)

All filter and inclusion/exclusion logic must come from Tejas's Step 1b answers in plan-builder.
Never infer filters from column names or prior session memory.

**For each table referenced:**
- Check `context/schema.md`
- If documented → use column definitions from schema.md directly
- If not documented → do not proceed. Ask Tejas. Wait for clarification before continuing.

---

## Step 2: Build the data spec

One section per plan step:

```
Step [#] — [step name]
  Tables:          [table_a, table_b, ...]
  Columns needed:  [col1 (table_a), col2 (table_a), col3 (table_b), ...]
  Join:            table_a.[key] → table_b.[key] (cardinality: 1:1 / 1:many / many:1)
  Filters:         [e.g. created_at >= 2026-05-08, order_status NOT IN (49, 312)]
  Risks:           [None / specific flag — e.g. "join key unverified in schema.md"]
```

**No aggregations.** Data spec covers only base table assembly via simple joins and selects.
Aggregations belong to `script-builder`.

---

## Step 3: Define expected output schema

Define the full column list of the CSV that will result from executing these queries.
This is the contract all downstream skills check against.

```
## Expected Output Schema

Grain: one row = [what does each row represent — e.g. one shipment attempt]

| Column | Source Table | Type | Description |
|--------|-------------|------|-------------|
| order_id | logistics_allocation_audit | varchar | ... |
| allocated_courier | logistics_allocation_audit | varchar | ... |
| promised_tat_pba | logistics_allocation_audit | int | ... |
| ... | ... | ... | ... |
```

Include every column that will appear in the output CSV.
Do not omit columns because they seem obvious — be exhaustive.

---

## Step 4: Present to Tejas for approval

Present data spec + expected output schema + risks together in one message.

Format:

```
## Table Mapper Output — ready for review

### Data Spec
[Full data spec, one section per step]

### Expected Output Schema
[Full column table]

### Risks & open questions
[List, or "None identified"]

Approve to proceed to query-builder, or request amendments.
```

**Wait for explicit approval.**
Do not proceed to `query-builder` under any circumstance until Tejas says so.
Amendments requested → revise spec → re-present. No revision limit.
