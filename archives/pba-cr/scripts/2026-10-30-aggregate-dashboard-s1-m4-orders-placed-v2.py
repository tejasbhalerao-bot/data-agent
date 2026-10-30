# Purpose: Section 1 metric 4, Orders placed, PBA base vs Internal base; runs every agreed check
# Serves: Dashboard S1 M4 (field mapping 2026-10-18, signed off 2026-10-30)
# Reads: archives/pba-cr/raw-data/dashboard/s1-m2-results.json (same verified query as S1 M2)
# Writes: archives/pba-cr/outputs/dashboard-s1-m4-w2.txt
# v2 (2026-10-30): window changed to orders placed 22 Oct 12:00 to 26 Oct 00:00 IST (Tejas). Slice tests and recounts sit inside it.
# Run with: python3 archives/pba-cr/scripts/2026-10-30-aggregate-dashboard-s1-m4-orders-placed-v2.py
# Note: the query text, trimming and slice recount checks run in the S1 M2 script (its 1-minute recount covers both the PBA and the legacy type); run it first.

import json, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
lines = []
def say(t): print(t); lines.append(t)
def check(ok, label):
    say(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    if not ok: raise SystemExit(f"check failed: {label}")

R = json.load(open(f"{ROOT}/raw-data/dashboard/s1-m2-results-w2.json"))
rows = [r for r in R["full_trimmed"]["rows"] if r[0] == "false"]
INTERNAL = ("COURIER_LEGACY_TAT_ADHERENCE", "COURIER_DDB_TAT_ADHERENCE")
pba = sum(r[4] for r in rows if r[3] == "COURIER_PBA")
internal = sum(r[4] for r in rows if r[3] in INTERNAL)
none = sum(r[4] for r in rows if r[3] == "NONE")
no_soft = sum(r[4] for r in rows if r[3] is None)

say("Checks")
check(pba + internal + none + no_soft == R["m1_total_non_sdd"], f"PBA base + Internal base + served NONE + no soft record = metric 1 ({R['m1_total_non_sdd']:,})")
check(all(r[3] in (None, "NONE", "COURIER_PBA") + INTERNAL for r in rows), "no other served type exists, so the two bases cannot overlap or miss an order")
S5 = json.load(open(f"{ROOT}/raw-data/dashboard/s1-m5m6-results-w2.json"))["full_trimmed"]["rows"]
check(pba == sum(r[5] for r in S5 if r[0] == "false" and r[1] == "COURIER_PBA") and internal == sum(r[5] for r in S5 if r[0] == "false" and r[1] in INTERNAL), "bases match the separate shipment query run (cross-query consistency)")

say("")
say(f"S1 M4  Orders placed: PBA {pba:,} (100%)   Internal {internal:,} (100%)")
say(f"       Internal = legacy {sum(r[4] for r in rows if r[3] == INTERNAL[0]):,} + DDB {sum(r[4] for r in rows if r[3] == INTERNAL[1]):,}")
say(f"       Non-SDD orders in neither base: served NONE {none:,}, no soft record {no_soft:,} (run {R['run_at_utc']})")
open(f"{ROOT}/outputs/dashboard-s1-m4-w2.txt", "w").write("\n".join(lines) + "\n")
