# Purpose: Section 1 metric 1, Total Non-SDD Orders, from the Metabase aggregate; runs every agreed check
# Serves: Dashboard S1 M1 (field mapping 2026-10-18, signed off 2026-10-30)
# Reads: archives/pba-cr/raw-data/dashboard/s1-m1-results.json (Metabase results, run 2026-10-30), the base query and trimmed-base files in queries-dump/
# Writes: archives/pba-cr/outputs/dashboard-s1-m1.txt
# Paths updated 2026-10-30 when query files were renamed by dashboard section and metric; no logic change.
# Run with: python3 archives/pba-cr/scripts/2026-10-30-aggregate-dashboard-s1-m1-total-non-sdd-v1.py

import hashlib, json, os
from datetime import datetime

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
lines = []
def say(t): print(t); lines.append(t)
def md5(t): return hashlib.md5(t.encode()).hexdigest()
def check(ok, label):
    say(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    if not ok: raise SystemExit(f"check failed: {label}")

R = json.load(open(f"{ROOT}/raw-data/dashboard/s1-m1-results.json"))
base = open(f"{ROOT}/queries-dump/2026-10-30-pba-cr-dashboard-base-query-v1.sql").read()
s = base.index("WITH params AS ("); body = base[s:base.index("\n;\n", s)]
slice_body = body.replace("'2026-10-22 12:00:00 +0530'", "'2026-10-23 10:00:00 +0530'").replace("'2026-10-30 00:00:00 +0530'", "'2026-10-23 11:00:00 +0530'")
trim_full = open(f"{ROOT}/queries-dump/dashboard/superseded/s1-funnel_shared_m1-trimmed-base_22-30oct.sql").read()
trim_slice = open(f"{ROOT}/queries-dump/dashboard/s1-funnel_shared_m1-trimmed-base_check-slice-23oct-10am-11am.sql").read()

say("Checks: query text")
check(md5(slice_body) == R["slice_1h_full_base"]["base_md5"], "1-hour slice ran Tejas's base query verbatim (only window dates changed)")
check(md5(trim_slice) == R["slice_1h_trimmed"]["base_md5"], "1-hour slice trimmed query = saved trimmed text")
check(md5(trim_full) == R["full_trimmed"]["base_md5"], "full-window trimmed query = saved trimmed text")
check(trim_full.split("\nSELECT")[0].replace("\n),\nfrozen", "\n),\n\n\n-- the same window") in body or all(b in body for b in (trim_full[:trim_full.index("frozen AS (")].rstrip()[:-1], trim_full[trim_full.index("frozen AS ("):trim_full.index("\n)\n")+2])), "trimmed CTEs are copied word for word from the base query")

say("Checks: trimming changes nothing")
check(R["slice_1h_full_base"]["rows"] == R["slice_1h_trimmed"]["rows"], "1-hour slice: full base and trimmed base give identical counts")

say("Checks: independent recount (Python from raw promise versions, 23 Oct 10:00-10:02)")
d = json.loads(open(R["slice_2m_raw_versions_file"]).read()); d = json.loads(d[0]["text"]) if isinstance(d, list) else d
rows = d["data"]["rows"]
check(d["data"].get("rows_truncated") is None and len(rows) < 2000, "raw pull not truncated")
def ts(x): return datetime.strptime(x[:19], "%Y-%m-%d %H:%M:%S")
def vnum(v):
    try: return float(v)
    except (TypeError, ValueError): return float("-inf")
orders = {}
for ref, ver, cr, sdd in rows: orders.setdefault(ref, []).append((ver, cr, sdd))
py = {"false": 0, "true": 0}; n = 0
for vs in orders.values():
    if not (datetime(2026, 10, 23, 10, 0) <= min(ts(c) for _, c, _ in vs) < datetime(2026, 10, 23, 10, 2)): continue
    latest = max(vs, key=lambda x: vnum(x[0])); py[latest[2]] = py.get(latest[2], 0) + 1; n += 1
sql = {r[0]: r[1] for r in R["slice_2m_trimmed_sql"]["rows"]}
check(py.get("false") == sql["false"] and py.get("true") == sql["true"] and n == sql["TOTAL"], f"SQL = Python on the slice (false {sql['false']}, true {sql['true']}, total {sql['TOTAL']})")

say("Checks: full-window result")
F = {str(r[0]): r for r in R["full_trimmed"]["rows"]}
check(all(r[1] == r[2] for r in R["full_trimmed"]["rows"]), "one row per order in every group")
check(F["false"][1] + F["true"][1] + F["None"][1] == F["TOTAL"][1], "false + true + blank = all orders")
check(F["None"][3] == F["None"][1] and F["false"][3] == 0 and F["true"][3] == 0, "every blank SDD_ENABLED order has a non-numeric (TM...) ID, and no other order does")
check(R["full_trimmed"]["min_placed"] >= R["window"][0] and R["full_trimmed"]["max_placed"] < R["window"][1], "every order placed inside the window")

say("")
say(f"S1 M1  Total Non-SDD Orders = {F['false'][1]:,}")
say(f"       Window: {R['window'][0]} to {R['window'][1]} (run {R['run_at_utc']})")
say(f"       Left out (blank SDD_ENABLED): {F['None'][1]:,}   SDD orders: {F['true'][1]:,}   All orders in window: {F['TOTAL'][1]:,}")
os.makedirs(f"{ROOT}/outputs", exist_ok=True)
open(f"{ROOT}/outputs/dashboard-s1-m1.txt", "w").write("\n".join(lines) + "\n")
