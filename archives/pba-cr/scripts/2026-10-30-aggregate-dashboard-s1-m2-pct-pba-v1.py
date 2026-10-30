# Purpose: Section 1 metric 2, % of non-SDD orders allocated through PBA, from the Metabase aggregate; runs every agreed check
# Serves: Dashboard S1 M2 (field mapping 2026-10-18, signed off 2026-10-30)
# Reads: archives/pba-cr/raw-data/dashboard/s1-m2-results.json and the raw files it names; queries-dump base and trimmed files
# Writes: archives/pba-cr/outputs/dashboard-s1-m2.txt
# Run with: python3 archives/pba-cr/scripts/2026-10-30-aggregate-dashboard-s1-m2-pct-pba-v1.py

import hashlib, json, os
from collections import Counter
from datetime import datetime, timedelta

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
lines = []
def say(t): print(t); lines.append(t)
def md5(t): return hashlib.md5(t.encode()).hexdigest()
def check(ok, label):
    say(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    if not ok: raise SystemExit(f"check failed: {label}")
def load(p):
    d = json.loads(open(p if p.startswith("/") else f"{ROOT}/{p}").read())
    return json.loads(d[0]["text"]) if isinstance(d, list) else d

R = json.load(open(f"{ROOT}/raw-data/dashboard/s1-m2-results.json"))
base = open(f"{ROOT}/queries-dump/2026-10-30-pba-cr-dashboard-base-query-v1.sql").read()
s = base.index("WITH params AS ("); body = base[s:base.index("\n;\n", s)]
slice_body = body.replace("'2026-10-22 12:00:00 +0530'", "'2026-10-23 10:00:00 +0530'").replace("'2026-10-30 00:00:00 +0530'", "'2026-10-23 11:00:00 +0530'")
trim_full = open(f"{ROOT}/queries-dump/dashboard/base-trim-soft-full.sql").read()
trim_slice = open(f"{ROOT}/queries-dump/dashboard/base-trim-soft-slice.sql").read()

say("Checks: query text")
FB = load(R["slice_1h_full_base_file"])
check(FB["data"]["rows"][0][-1] == md5(slice_body), "1-hour slice ran Tejas's base query verbatim (only window dates changed)")
check(md5(trim_slice) == R["slice_1h_trimmed"]["base_md5"] and md5(trim_full) == R["full_trimmed"]["base_md5"], "trimmed queries ran exactly as saved")
cut = trim_full[:trim_full.index("\n\n\nSELECT\n")]
check(body.startswith(cut), "trimmed query = the base query's own text up to the end of the soft step, unchanged")

say("Checks: trimming changes nothing")
fb_rows = [r[1:7] for r in FB["data"]["rows"] if r[0] == 0]
check(fb_rows == R["slice_1h_trimmed"]["rows"], "1-hour slice: full base and trimmed base give identical groups and counts")

say("Checks: independent recount (Python from raw promise versions + raw soft records, 23 Oct 10:00-10:01)")
d = load(R["slice_1m_raw_file"]); rows = d["data"]["rows"]
check(d["data"].get("rows_truncated") is None and len(rows) < 2000, "raw pull not truncated")
def ts(x): return datetime.strptime(x[:19], "%Y-%m-%d %H:%M:%S")
def vnum(v):
    try: return float(v)
    except (TypeError, ValueError): return float("-inf")
V, E = {}, {}
for src, ref, ver, req, cr, val, ro in rows: (V if src == "V" else E).setdefault(ref, []).append((ver, req, cr, val, ro))
lo, hi = datetime(2026, 10, 23, 10, 0), datetime(2026, 10, 23, 10, 1)
py = Counter()
for ref, vs in V.items():
    if not (lo <= min(ts(x[2]) for x in vs) < hi): continue
    latest = max(vs, key=lambda x: vnum(x[0]))
    cand = [e for e in E.get(ref, []) if e[1] == latest[1] and lo - timedelta(days=1) <= ts(e[2]) < hi + timedelta(days=10)]
    if cand:
        e = max(cand, key=lambda x: x[2]); py[(latest[3], "true", "true" if e[4] == "TRUE" else "false", e[3])] += 1
    else: py[(latest[3], "false", None, None)] += 1
sql = Counter({tuple(r[:4]): r[4] for r in R["slice_1m_trimmed_sql"]})
check(py == sql, f"SQL = Python on every group ({dict((k[3] or 'no soft record', v) for k, v in sql.items())})")

say("Checks: full-window result")
rows = R["full_trimmed"]["rows"]
check(all(r[4] == r[5] for r in rows) and R["full_trimmed"]["total"][0] == R["full_trimmed"]["total"][1], "one row per order")
check(sum(r[4] for r in rows) == R["full_trimmed"]["total"][0], "groups add up to all orders in the window")
non_sdd = sum(r[4] for r in rows if r[0] == "false")
check(non_sdd == R["m1_total_non_sdd"], f"non-SDD total = metric 1 ({R['m1_total_non_sdd']:,})")
types = {r[3] for r in rows}
check(types <= {None, "COURIER_PBA", "COURIER_LEGACY_TAT_ADHERENCE", "COURIER_DDB_TAT_ADHERENCE", "NONE"}, "served type only takes allowed values")
check(all(r[3] is None for r in rows if r[1] == "false") and all(r[3] is not None for r in rows if r[1] == "true"), "served type is blank exactly when there is no soft record")
pba = sum(r[4] for r in rows if r[0] == "false" and r[3] == "COURIER_PBA")
check(all(r[2] == "true" for r in rows if r[3] == "COURIER_PBA"), "every PBA-served order was in rollout")

say("")
say(f"S1 M2  % of non-SDD orders allocated through PBA = {pba / non_sdd * 100:.1f}%")
say(f"       PBA base {pba:,} / Total Non-SDD {non_sdd:,} (run {R['run_at_utc']})")
os.makedirs(f"{ROOT}/outputs", exist_ok=True)
open(f"{ROOT}/outputs/dashboard-s1-m2.txt", "w").write("\n".join(lines) + "\n")
