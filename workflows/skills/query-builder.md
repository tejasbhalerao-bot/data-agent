# Skill: Query Builder

Translates an approved data spec from `table-mapper` into optimised, Metabase-ready SQL queries.
Never writes queries against undocumented tables. Never auto-proceeds — always waits for Tejas approval.

---

## Input

Approved data spec + expected output schema from `table-mapper`. Contains:
- One data spec section per plan step (tables, columns, joins, filters)
- Expected output schema (full column list, grain, source tables)

---

## Step 1: Pre-flight check

Before writing a single query:

1. Read `context/schema.md`
2. Verify every table in the data spec is documented
3. If any table is missing from schema.md — **stop. Flag to Tejas. Do not proceed until resolved.**

All tables must be documented before query writing begins. This is a hard stop, not a warning.

---

## Step 2: Write queries

Write one SQL query per plan step. All queries are `SELECT`-only — no aggregations.
All table names prefixed with `tmmumpsdb.`

### Optimisation rules (apply to every query)

- **Filter early** — push all WHERE conditions as close to source tables as possible, before joins
- **Select only needed columns** — no `SELECT *` on large tables; select only columns in the data spec
- **Apply date filters first** — never full-table scan then filter; date range goes in the innermost subquery or CTE
- **Avoid join fanout** — if a join could multiply rows unexpectedly, use a subquery or deduplicate first
- **Use CTEs for readability** — break complex joins into named CTEs, one per source table
- **Exclude known noise** — apply standard exclusions (e.g. `order_status NOT IN (49, 312)`) unless plan explicitly includes them

### Timeout risk rating

After writing each query, assign a timeout risk:

| Rating | Signal |
|---|---|
| Low | ≤2 table joins, narrow date range (≤30 days), small/config tables only |
| Medium | 3–4 joins, moderate date range (30–90 days), or one large transactional table |
| High | 5+ joins, wide date range (90+ days), multiple large transactional tables |

Metabase hard timeout = 10 minutes. High-risk queries must be split (see Step 3).

---

## Step 3: Split high-timeout-risk queries

For any query rated High:

1. Split into sub-queries — by date range chunks (e.g. weekly) or by partition (courier/vertical)
2. Write a Python merge script that:
   - Reads all chunk CSVs from `archives/[project]/raw-data/`
   - Concatenates into one combined CSV
   - Saves to `archives/[project]/raw-data/` with a `_combined` suffix
   - Validates row count = sum of chunk row counts
3. Save merge script via `new-file.sh`:
   ```bash
   ./workflows/scripts/new-file.sh [project] scripts merge-<query-descriptor> py
   ```

Split strategy preference: date range chunks first. Partition split only if date chunking produces too many files (>10 chunks).

---

## Step 4: Save queries

Save each query to `queries-dump/` via `new-file.sh`:

```bash
./workflows/scripts/new-file.sh [project] queries-dump [project]-<step-descriptor>-query sql
```

---

## Step 5: Present to Tejas for approval

Present all queries together. For each query:

```
### Query [#] — [step name]

**Serves:** [Q# from plan]
**Timeout risk:** Low / Medium / High — [reason]

**Plain English:**
[What this query does, which tables it joins, what columns it produces and why]

**Columns produced vs expected schema:**
| Expected column | Produced? | Notes |
|---|---|---|
| column_a | ✓ | |
| column_b | ✓ | |
| column_c | ✗ | [reason — e.g. not available in source table] |

**Optimisation decisions:**
- [e.g. Date filter pushed into CTE before join]
- [e.g. Deduplication added on order_id before joining order_tat_details]

**SQL:**
```sql
[query here]
```

[If split: include split sub-queries + merge script summary]
```

Wait for explicit approval. Do not proceed to `data-validator` until Tejas approves.
Amendments requested → revise → re-present. No revision limit.

---

## Re-entry: Query timed out

If Tejas signals a query timed out in Metabase:

1. Re-enter at Step 3 for that specific query
2. Split into chunks, write merge script
3. Re-present split queries with updated timeout risk rating
4. Wait for approval before Tejas re-runs

---

## What query-builder does NOT do

- Does not aggregate — that belongs to `script-builder`
- Does not execute queries — Tejas runs them in Metabase
- Does not update schema.md — undocumented tables are a hard stop, not a discovery trigger
- Does not combine CSVs manually — merge script handles that
