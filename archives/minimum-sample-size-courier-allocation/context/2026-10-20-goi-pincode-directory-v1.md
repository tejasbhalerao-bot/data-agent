# GOI All India Pincode Directory (Sept 2026)

Supplied by Tejas on 2026-10-20 as `/Users/Tejas/Downloads/5c2f62fe-5afa-4119-a499-fec9d604d5bd.csv`. Saved locally as `raw-data/goi-pincode-directory.csv` (not pushed). Source sheet: https://docs.google.com/spreadsheets/d/164WsAYPyAfxyfOjYlz8aHfx5lr5cQCDeQUJLwfj4xIc

Used to build micro-clusters (same division of the same district) and the state rung of the pooling ladder (see `2026-10-20-simulation-scope-v2.md`).

## Shape
- 165,627 rows, 19,586 distinct pincodes. **One row per post office**, so a pincode repeats.
- Columns: `circlename, regionname, divisionname, officename, pincode, officetype, delivery, district, statename, latitude, longitude`.
- All pincodes are 6 digits. No blank values in the columns the ladder needs (`pincode, divisionname, district, statename`).
- 37 distinct state names.

## Quirks found
- **A pincode does not map to one district, division or state.**
  - 1,478 pincodes list more than one district. In 220 of them the only difference is an `NA`. In the other 1,258 the post offices name different districts (for example 504273: KUMURAM BHEEM ASIFABAD on 9 rows, MANCHERIAL on 5).
  - 129 pincodes list more than one division.
  - 290 pincodes list more than one state. In 238 the only difference is an `NA`. In 52 the states genuinely differ (for example 506003: TELANGANA on 10 rows, ANDHRA PRADESH on 1).
- `NA` appears as a text value in `district` and `statename` (715 rows each), not as a blank.
- `latitude` and `longitude` are `NA` on some rows. Not needed here.

## Decision pending
How to give each pincode a single district, division and state. Proposed: take the value on the most post-office rows, ignoring `NA`; flag ties. Tejas decides.
