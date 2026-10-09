#!/usr/bin/env python3
"""Check 2: validate a Metabase CSV against its brief before any analysis.

Usage:
  validate-csv.py FILE --key order_id [--key other] \
      --require col1,col2 --date-col digitised_ts --from 2026-07-01 --to 2026-07-31 \
      --max-null col=0.05 --probe rows=803997 --probe distinct=803997 [--tol 0.001]

Checks (each prints PASS / FAIL / WARN; exit code 1 if any FAIL):
  columns   every --require column exists
  rows      file is non-empty; --probe rows=N matches within --tol
  grain     --key columns are unique (--probe distinct=N matches within --tol)
  nulls     null share per --require column (FAIL above --max-null, default WARN above 50%)
  dates     --date-col parses, and lies inside --from/--to when given
Streams the file, so 800K-row exports are fine.
"""
import argparse, csv, sys
from datetime import datetime

FORMATS = ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
           "%Y-%m-%d", "%b %d, %Y, %I:%M %p", "%B %d, %Y, %I:%M %p"]

def parse(v):
    v = v.strip()
    for f in FORMATS:
        try:
            return datetime.strptime(v[:26] if "%f" in f else v, f)
        except ValueError:
            continue
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--key", action="append", default=[])
    ap.add_argument("--require", default="")
    ap.add_argument("--date-col")
    ap.add_argument("--from", dest="dfrom")
    ap.add_argument("--to", dest="dto")
    ap.add_argument("--max-null", action="append", default=[], help="col=share")
    ap.add_argument("--probe", action="append", default=[], help="rows=N or distinct=N")
    ap.add_argument("--tol", type=float, default=0.0, help="relative tolerance for probes")
    a = ap.parse_args()

    results = []
    def rec(status, check, msg): results.append((status, check, msg)); print(f"{status:4} {check:8} {msg}")

    req = [c for c in a.require.split(",") if c]
    maxnull = {k: float(v) for k, v in (x.split("=") for x in a.max_null)}
    probes = {k: float(v) for k, v in (x.split("=") for x in a.probe)}

    with open(a.file, newline="", encoding="utf-8-sig") as fh:
        r = csv.DictReader(fh)
        cols = r.fieldnames or []
        missing = [c for c in req + a.key + ([a.date_col] if a.date_col else []) if c not in cols]
        if missing:
            rec("FAIL", "columns", f"missing: {', '.join(missing)}")
            print(f"     found: {', '.join(cols)}"); sys.exit(1)
        rec("PASS", "columns", f"{len(cols)} columns; all required present")

        n = 0; seen = set(); dup = 0
        nulls = {c: 0 for c in req}
        dmin = dmax = None; dbad = 0
        for row in r:
            n += 1
            if a.key:
                k = tuple(row[c] for c in a.key)
                if k in seen: dup += 1
                else: seen.add(k)
            for c in req:
                if row[c].strip() in ("", "NULL", "null", "None"): nulls[c] += 1
            if a.date_col:
                d = parse(row[a.date_col]) if row[a.date_col].strip() else None
                if d is None:
                    if row[a.date_col].strip(): dbad += 1
                else:
                    dmin = d if dmin is None or d < dmin else dmin
                    dmax = d if dmax is None or d > dmax else dmax

    def close(actual, want):
        return abs(actual - want) <= a.tol * want if a.tol else actual == want

    if n == 0: rec("FAIL", "rows", "file has no data rows")
    else: rec("PASS", "rows", f"{n:,} rows")
    if "rows" in probes:
        rec("PASS" if close(n, probes["rows"]) else "FAIL", "rows", f"probe {int(probes['rows']):,} vs file {n:,}")
    if a.key:
        if dup: rec("FAIL", "grain", f"{dup:,} duplicate rows on key ({', '.join(a.key)}); {len(seen):,} distinct")
        else: rec("PASS", "grain", f"key ({', '.join(a.key)}) unique")
        if "distinct" in probes:
            rec("PASS" if close(len(seen), probes["distinct"]) else "FAIL", "grain", f"probe {int(probes['distinct']):,} vs file {len(seen):,}")
    for c in req:
        share = nulls[c] / n if n else 1
        lim = maxnull.get(c)
        if lim is not None: rec("PASS" if share <= lim else "FAIL", "nulls", f"{c}: {share:.2%} null (limit {lim:.2%})")
        elif share > 0.5: rec("WARN", "nulls", f"{c}: {share:.2%} null")
        else: rec("PASS", "nulls", f"{c}: {share:.2%} null")
    if a.date_col:
        if dmin is None: rec("FAIL", "dates", f"{a.date_col}: no parseable dates")
        else:
            ok = True
            if a.dfrom and dmin < datetime.fromisoformat(a.dfrom): ok = False
            if a.dto and dmax > datetime.fromisoformat(a.dto + " 23:59:59"): ok = False
            rec("PASS" if ok else "FAIL", "dates", f"{a.date_col}: {dmin:%Y-%m-%d} to {dmax:%Y-%m-%d}" + (f"; {dbad:,} unparseable" if dbad else ""))

    fails = [x for x in results if x[0] == "FAIL"]
    print(f"\n{'FAIL' if fails else 'PASS'}: {len(fails)} failing check(s)")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
