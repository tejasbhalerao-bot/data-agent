# Purpose: Section 1 metric 5, % picked up, PBA base vs Internal base; runs every agreed check
# Serves: Dashboard S1 M5 (field mapping 2026-10-18, signed off 2026-10-30). The same results also serve S1 M6.
# Reads: archives/pba-cr/raw-data/dashboard/s1-m5m6-results.json and the raw files it names; queries-dump base and trimmed files
# Writes: archives/pba-cr/outputs/dashboard-s1-m5.txt
# Run with: python3 archives/pba-cr/scripts/2026-10-30-aggregate-dashboard-s1-m5-pct-picked-up-v1.py

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
    d = json.loads(open(f"{ROOT}/{p}").read())
    return json.loads(d[0]["text"]) if isinstance(d, list) else d
def ts(x): return datetime.strptime(x[:19], "%Y-%m-%d %H:%M:%S")
def vnum(v):
    try: return float(v)
    except (TypeError, ValueError): return float("-inf")

R = json.load(open(f"{ROOT}/raw-data/dashboard/s1-m5m6-results.json"))
base = open(f"{ROOT}/queries-dump/2026-10-30-pba-cr-dashboard-base-query-v1.sql").read()
s = base.index("WITH params AS ("); body = base[s:base.index("\n;\n", s)]
slice_body = body.replace("'2026-10-22 12:00:00 +0530'", "'2026-10-23 10:00:00 +0530'").replace("'2026-10-30 00:00:00 +0530'", "'2026-10-23 11:00:00 +0530'")
trim_full = open(f"{ROOT}/queries-dump/dashboard/base-trim-shipment-full.sql").read()
trim_slice = open(f"{ROOT}/queries-dump/dashboard/base-trim-shipment-slice.sql").read()

say("Checks: query text")
FB = load(R["slice_1h_full_base_file"])
check(FB["data"]["rows"][0][-1] == md5(slice_body), "1-hour slice ran Tejas's base query verbatim (only window dates changed)")
check(md5(trim_slice) == R["slice_1h_trimmed"]["base_md5"] and md5(trim_full) == R["full_trimmed"]["base_md5"], "trimmed queries ran exactly as saved")
check(body.startswith(trim_full[:trim_full.index("\n\n\nSELECT\n")]), "trimmed query = the base query's own text up to the end of the soft step, unchanged")
sel = trim_full[trim_full.index("\n\n\nSELECT\n") + 10:].splitlines()
check(all(l.strip().rstrip(",") in body for l in sel if l.strip()), "every line of the trimmed final SELECT and joins is copied from the base query")

say("Checks: trimming changes nothing")
check([r[1:8] for r in FB["data"]["rows"] if r[0] == 0] == R["slice_1h_trimmed"]["rows"], "1-hour slice: full base and trimmed base give identical groups and counts")

say("Checks: independent recount (Python from raw promise versions, soft records and shipment rows, 23 Oct 10:00:00-10:00:30)")
d = load(R["slice_30s_raw_file"]); rows = d["data"]["rows"]
check(d["data"].get("rows_truncated") is None and len(rows) < 2000, "raw pull not truncated")
V, E, S = {}, {}, {}
for src, ref, ver, req, t1, val, t2, t3 in rows: {"V": V, "E": E, "S": S}[src].setdefault(ref, []).append((ver, req, t1, val, t2, t3))
lo, hi = datetime(2026, 10, 23, 10, 0, 0), datetime(2026, 10, 23, 10, 0, 30)
py = Counter()
for ref, vs in V.items():
    if not (lo <= min(ts(x[2]) for x in vs) < hi): continue
    latest = max(vs, key=lambda x: vnum(x[0]))
    cand = [e for e in E.get(ref, []) if e[1] == latest[1] and lo - timedelta(days=1) <= ts(e[2]) < hi + timedelta(days=10)]
    typ = max(cand, key=lambda x: x[2])[3] if cand else None
    live = [x for x in S.get(ref, []) if x[3] in (None, "false")]
    sh = max(live, key=lambda x: vnum(x[0])) if live else None
    py[(latest[3], typ, "true" if sh else "false", "true" if sh and sh[4] else "false", "true" if sh and sh[5] else "false")] += 1
check(py == Counter({tuple(r[:5]): r[5] for r in R["slice_30s_trimmed_sql"]}), "SQL = Python on every group")

say("Checks: full-window result")
rows = R["full_trimmed"]["rows"]
check(all(r[5] == r[6] for r in rows) and sum(r[5] for r in rows) == R["full_trimmed"]["total"][0], "one row per order; groups add up to all orders")
check(sum(r[5] for r in rows if r[0] == "false") == R["m1_total_non_sdd"], "non-SDD total = metric 1")
INTERNAL = ("COURIER_LEGACY_TAT_ADHERENCE", "COURIER_DDB_TAT_ADHERENCE")
base_pba = sum(r[5] for r in rows if r[0] == "false" and r[1] == "COURIER_PBA")
base_int = sum(r[5] for r in rows if r[0] == "false" and r[1] in INTERNAL)
check(base_pba == R["s1_m4_bases"]["pba"] and base_int == R["s1_m4_bases"]["internal"], "PBA and Internal bases = metric 4 (17,804 and 338,386)")
check(all(r[2] == "true" for r in rows if r[3] == "true" or r[4] == "true"), "a pickup or attempt time only appears on orders with a shipment record")
pk_pba = sum(r[5] for r in rows if r[0] == "false" and r[1] == "COURIER_PBA" and r[3] == "true")
pk_int = sum(r[5] for r in rows if r[0] == "false" and r[1] in INTERNAL and r[3] == "true")
no_pk_att = {k: sum(r[5] for r in rows if r[0] == "false" and (r[1] == "COURIER_PBA" if k == "PBA" else r[1] in INTERNAL) and r[3] == "false" and r[4] == "true") for k in ("PBA", "Internal")}

say("")
say(f"S1 M5  % picked up: PBA {pk_pba / base_pba * 100:.1f}% ({pk_pba:,} of {base_pba:,})   Internal {pk_int / base_int * 100:.1f}% ({pk_int:,} of {base_int:,})")
say(f"       Data note: orders with a delivery attempt but no pickup time: PBA {no_pk_att['PBA']}, Internal {no_pk_att['Internal']} (counted as not picked up)")
say(f"       Run {R['run_at_utc']}")
open(f"{ROOT}/outputs/dashboard-s1-m5.txt", "w").write("\n".join(lines) + "\n")
