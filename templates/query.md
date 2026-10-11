# <Short name of the query>

- **Purpose:** <what it pulls, in a few words>
- **Serves:** <M-IDs from the brief; the probe serves none>
- **Grain:** <what one row is>
- **Tables:** <from schema.md>
- **Definitions used:** <metrics.md names>
- **Filters:** <filters applied, with the reason or the schema.md source>
- **Expected shape:** <columns, and roughly how many rows>
- **Timeout risk:** Low | Medium | High (and the split, if any)
- **Save the CSV as:** `archives/<project>/raw-data/<name>.csv`

```sql
-- One query per file. No aggregation, except in the probe and dashboard queries.
SELECT ...
FROM tmmumpsdb.<table>
WHERE ...
```
