# Skill: Schema Discovery

Invoked when any query, script, or analysis references a table not documented in `context/schema.md`.

---

## Trigger

Before writing any SQL or script, scan all table names referenced against `context/schema.md`.
If any table is missing — stop. Run this skill. Do not proceed until schema is approved and pushed.

---

## Steps

### 1. Read existing schema

Read `context/schema.md` in full. Identify which referenced tables are already documented and which are new.

### 2. Query Metabase for each new table

For each undocumented table, run two queries in Metabase:

**Columns + types:**
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'tmmumpsdb'
  AND table_name = '<table_name>'
ORDER BY ordinal_position;
```

**Sample rows (10):**
```sql
SELECT *
FROM tmmumpsdb.<table_name>
LIMIT 10;
```

### 3. Draft schema addition

Produce a draft section in the format already used in `context/schema.md`:

```markdown
#### <Table Display Name>
**Purpose:** <one sentence — what this table tracks>
**Written by:** <who populates it — system, ops upload, API, etc.>
**Granularity:** <one row = what?>
**Key date column:** <column name used for date filtering>

| Column | Type | Definition |
|--------|------|------------|
| column_a | varchar | ... |
| column_b | timestamp | ... |

**Join keys:**
- `<column>` → `<other_table>.<column>` (<what it resolves to>)

**Known quirks:** <anything unexpected seen in sample rows, or "None discovered">
```

### 4. Present to Tejas for approval

Show the draft addition(s). State clearly:
- How many new tables being added
- Any unexpected values or nulls seen in sample rows
- Any join key assumptions that need confirmation

Wait for explicit approval. Do not update schema.md until approved.
Amendments requested → revise draft → re-present.

### 5. Update schema.md

Once approved:
1. Append new section(s) to `context/schema.md` under the correct category heading
2. Update the `Last updated` date at the top of the file

### 6. Push to GitHub

```bash
git add context/schema.md
git commit -m "context: add <table-name> schema to schema.md"
git push origin main
```

---

## Rules

- Never infer column definitions from column names alone — always use sample rows to validate meaning
- If sample rows show unexpected nulls in a column expected to be populated, flag it explicitly before approval
- If a join key assumption cannot be confirmed from sample data, mark it as **unverified** in the draft
- Schema.md is the source of truth — never write a query that relies on undocumented table behaviour
