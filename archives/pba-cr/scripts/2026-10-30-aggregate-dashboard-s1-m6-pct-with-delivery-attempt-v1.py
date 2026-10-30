# Purpose: Section 1 metric 6, % with delivery attempt, PBA base vs Internal base, placed orders only; runs every agreed check
# Serves: Dashboard S1 M6 (field mapping 2026-10-18, signed off 2026-10-30; placed-order filter 2026-10-30)
# Reads: archives/pba-cr/raw-data/dashboard/s1-placed-results-w2.json (same verified query as S1 M5:
#        queries-dump/dashboard/s1-funnel_pba-vs-internal-funnel_m6-pct-with-delivery-attempt.sql)
# Writes: archives/pba-cr/outputs/dashboard-s1-m6-placed-w2.txt
# Run with: python3 archives/pba-cr/scripts/2026-10-30-aggregate-dashboard-s1-m6-pct-with-delivery-attempt-v1.py
# Note: query text, filter, add-back and cross-query checks run in 2026-10-30-aggregate-dashboard-s1-m1-m5-placed-v1.py (run first);
#       the raw recount that covers the delivery-attempt field runs in 2026-10-30-aggregate-dashboard-s1-m5-pct-picked-up-v2.py.

import filecmp, json, os, subprocess, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
lines = []
def say(t): print(t); lines.append(t)
def check(ok, label):
    say(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    if not ok: raise SystemExit(f"check failed: {label}")

say("Checks: the query and its verification")
Q = f"{ROOT}/queries-dump/dashboard"
check(filecmp.cmp(f"{Q}/s1-funnel_pba-vs-internal-funnel_m6-pct-with-delivery-attempt.sql", f"{Q}/s1-funnel_pba-vs-internal-funnel_m5-pct-picked-up.sql", shallow=False),
      "metric 6 query file is the same query that ran for metric 5")
for script in ("2026-10-30-aggregate-dashboard-s1-m1-m5-placed-v1.py", "2026-10-30-aggregate-dashboard-s1-m5-pct-picked-up-v2.py"):
    r = subprocess.run([sys.executable, f"{ROOT}/scripts/{script}"], capture_output=True, text=True)
    check(r.returncode == 0 and "[FAIL]" not in r.stdout, f"{script}: all {r.stdout.count('[PASS]')} checks pass")

P = json.load(open(f"{ROOT}/raw-data/dashboard/s1-placed-results-w2.json"))
INTERNAL = ("COURIER_LEGACY_TAT_ADHERENCE", "COURIER_DDB_TAT_ADHERENCE")
rows = [r for r in P["shipment"] if r[0] == "kept" and r[1] == "false"]
def side(pred):
    b = [r for r in rows if pred(r[2])]
    return (sum(r[6] for r in b), sum(r[6] for r in b if r[5] == "true"),
            sum(r[6] for r in b if r[5] == "true" and r[4] == "false"), sum(r[6] for r in b if r[4] == "true"))
pba = side(lambda t: t == "COURIER_PBA"); intl = side(lambda t: t in INTERNAL)

say("Checks: result")
check(all(r[3] == "true" for r in rows if r[5] == "true"), "an attempt time only appears on orders with a shipment record")
check(pba[1] <= pba[3] + pba[2] and intl[1] <= intl[3] + intl[2], "attempted orders = picked-up attempts + attempts with no pickup time (none lost)")
check(pba[0] == 3490 and intl[0] == 66747, "denominators are the metric 4 bases (whole base, not only picked-up orders)")

say("")
say(f"S1 M6  % with delivery attempt: PBA {pba[1] / pba[0] * 100:.1f}% ({pba[1]:,} of {pba[0]:,})   Internal {intl[1] / intl[0] * 100:.1f}% ({intl[1]:,} of {intl[0]:,})")
say(f"       of which attempted but no pickup time recorded: PBA {pba[2]}, Internal {intl[2]}")
say(f"       Run {P['run_at_utc']['shipment']}")
open(f"{ROOT}/outputs/dashboard-s1-m6-placed-w2.txt", "w").write("\n".join(lines) + "\n")
