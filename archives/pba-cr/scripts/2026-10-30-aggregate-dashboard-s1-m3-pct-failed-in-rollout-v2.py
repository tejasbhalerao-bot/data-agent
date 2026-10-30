# Purpose: Section 1 metric 3, % of non-SDD orders that failed to allocate through PBA while in rollout; runs every agreed check
# Serves: Dashboard S1 M3 (field mapping 2026-10-18, signed off 2026-10-30)
# Reads: archives/pba-cr/raw-data/dashboard/s1-m2-results.json (same verified query as S1 M2), s1-m3-numerator-raw-part{0,1,2}.json
# Writes: archives/pba-cr/outputs/dashboard-s1-m3-w2.txt
# v2 (2026-10-30): window changed to orders placed 22 Oct 12:00 to 26 Oct 00:00 IST (Tejas). Slice tests and recounts sit inside it.
# Run with: python3 archives/pba-cr/scripts/2026-10-30-aggregate-dashboard-s1-m3-pct-failed-in-rollout-v2.py
# Note: the query text, trimming and slice recount checks for this query run in the S1 M2 script; run it first.

import json, os
from datetime import datetime

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
lines = []
def say(t): print(t); lines.append(t)
def check(ok, label):
    say(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    if not ok: raise SystemExit(f"check failed: {label}")

R = json.load(open(f"{ROOT}/raw-data/dashboard/s1-m2-results-w2.json"))
FAILED = ("COURIER_LEGACY_TAT_ADHERENCE", "COURIER_DDB_TAT_ADHERENCE", "NONE")
rows = R["full_trimmed"]["rows"]
non_sdd = sum(r[4] for r in rows if r[0] == "false")
num = sum(r[4] for r in rows if r[0] == "false" and r[2] == "true" and r[3] in FAILED)

say("Checks: numerator, order by order from raw records (all orders in the numerator)")
def ts(x): return datetime.strptime(x[:19], "%Y-%m-%d %H:%M:%S")
def vnum(v):
    try: return float(v)
    except (TypeError, ValueError): return float("-inf")
V, E = {}, {}
for k in range(3):
    d = json.loads(open(f"{ROOT}/raw-data/dashboard/s1-m3-numerator-raw-part{k}.json").read()); d = json.loads(d[0]["text"]) if isinstance(d, list) else d
    check(d["data"].get("rows_truncated") is None and d["row_count"] < 2000, f"raw pull part {k} not truncated ({d['row_count']} rows)")
    for src, ref, ver, req, cr, val, ro in d["data"]["rows"]:
        (V if src == "V" else E).setdefault(ref, []).append((ver, req, cr, val, ro))
check(len(V) >= num, f"raw pulls (all in-rollout failures from the 22-30 Oct run, {len(V)}) cover the new window's numerator ({num})")
ok = 0
for ref, vs in V.items():
    latest = max(vs, key=lambda x: vnum(x[0]))
    in_win = datetime(2026, 10, 22, 12) <= min(ts(x[2]) for x in vs) < datetime(2026, 10, 26)
    cand = [e for e in E.get(ref, []) if e[1] == latest[1] and datetime(2026, 10, 21, 12) <= ts(e[2]) < datetime(2026, 11, 5)]
    e = max(cand, key=lambda x: x[2]) if cand else None
    ok += bool(in_win and latest[3] == "false" and e and e[4] == "TRUE" and e[3] in FAILED)
check(ok == num, f"orders placed in the new window that meet the definition on its raw records: placed in window, SDD false, in rollout, not served by PBA ({ok}/{num})")

say("Checks: result")
check(non_sdd == R["m1_total_non_sdd"], f"denominator = metric 1 ({non_sdd:,})")
check(num + sum(r[4] for r in rows if r[0] == "false" and r[2] == "true" and r[3] == "COURIER_PBA") == sum(r[4] for r in rows if r[0] == "false" and r[2] == "true"), "in-rollout orders = served by PBA + failed")

say("")
say(f"S1 M3  % of non-SDD orders failed to allocate through PBA while in rollout = {num / non_sdd * 100:.2f}%  (shown as {num / non_sdd * 100:.1f}%)")
for t in FAILED:
    say(f"       served by {t}: {sum(r[4] for r in rows if r[0] == 'false' and r[2] == 'true' and r[3] == t):,}")
say(f"       {num:,} / Total Non-SDD {non_sdd:,} (run {R['run_at_utc']})")
open(f"{ROOT}/outputs/dashboard-s1-m3-w2.txt", "w").write("\n".join(lines) + "\n")
