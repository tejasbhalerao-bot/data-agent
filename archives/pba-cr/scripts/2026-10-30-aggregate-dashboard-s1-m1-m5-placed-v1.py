# Purpose: Section 1 metrics 1-5 on placed orders only (incomplete and scrapped carts dropped); runs every agreed check
# Serves: Dashboard S1 M1-M5 (field mapping 2026-10-18, signed off 2026-10-30; placed-order filter added 2026-10-30)
# Reads: archives/pba-cr/raw-data/dashboard/s1-placed-results-w2.json; the unfiltered verified runs s1-m1-results-w2.json, s1-m2-results-w2.json,
#        s1-m5m6-results-w2.json; queries-dump base query, trimmed files and placed-filter.sql
# Writes: archives/pba-cr/outputs/dashboard-s1-m1-m5-placed-w2.txt
# Run with: python3 archives/pba-cr/scripts/2026-10-30-aggregate-dashboard-s1-m1-m5-placed-v1.py
# Note: trimming equivalence and the raw recounts were checked in the S1 M1, M2 and M5 scripts (v2); this script ties the filtered runs back to them.

import hashlib, json, os
from collections import Counter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
lines = []
def say(t): print(t); lines.append(t)
def md5(t): return hashlib.md5(t.encode()).hexdigest()
def check(ok, label):
    say(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    if not ok: raise SystemExit(f"check failed: {label}")
D = f"{ROOT}/raw-data/dashboard"; Q = f"{ROOT}/queries-dump/dashboard"
P = json.load(open(f"{D}/s1-placed-results-w2.json"))
U1 = json.load(open(f"{D}/s1-m1-results-w2.json")); U2 = json.load(open(f"{D}/s1-m2-results-w2.json")); U5 = json.load(open(f"{D}/s1-m5m6-results-w2.json"))
flt = open(f"{Q}/placed-filter.sql").read().rstrip("\n")
base = open(f"{ROOT}/queries-dump/2026-10-30-pba-cr-dashboard-base-query-v1.sql").read()
s = base.index("WITH params AS ("); body_w2 = base[s:base.index("\n;\n", s)].replace("'2026-10-30 00:00:00 +0530'", "'2026-10-26 00:00:00 +0530'")
INTERNAL = ("COURIER_LEGACY_TAT_ADHERENCE", "COURIER_DDB_TAT_ADHERENCE")

say("Checks: query text")
for n in ("frozen", "soft", "shipment"):
    t = open(f"{Q}/base-trim-{n}-w2.sql").read()
    check(md5(t + "\n" + flt) == P["md5"][n], f"{n} query ran exactly as saved: trimmed base + placed-order filter")
    if n != "frozen":
        check(body_w2.startswith(t[:t.index("\n\n\nSELECT\n")]), f"{n}: trimmed part is the base query's own text (window end 26 Oct)")
check("WHEN od.orderstatus IN (49, 312)    THEN 'dropped'" in flt and "174" not in flt and "57" not in flt, "filter drops only statuses 49 and 312; discarded (174) and cancelled (57) are kept")

say("Checks: the filter reads the right status")
check(P["status_sample"]["snowflake_od"] == P["status_sample"]["redshift_od"], "Snowflake order_details (latest copy) = Redshift order_details for all 30 sample orders")

say("Checks: kept + dropped add back to the verified unfiltered runs")
fz = Counter(); [fz.update({r[1]: r[2]}) for r in P["frozen"]]
u1 = {str(r[0]): r[1] for r in U1["full_trimmed"]["rows"]}
check(sum(fz.values()) == u1["TOTAL"] and fz[None] == u1["None"], "metric 1 query: same total orders as the unfiltered run, same blank-SDD orders")
say(f"     orders that changed SDD flag between the two runs (live data, 12 minutes apart): non-SDD {fz['false'] - u1['false']:+d}, SDD {fz['true'] - u1['true']:+d}")
sf = Counter(); [sf.update({tuple(r[1:5]): r[5]}) for r in P["soft"]]
u2 = Counter({tuple(r[:4]): r[4] for r in U2["full_trimmed"]["rows"]})
check(sum(sf.values()) == sum(u2.values()), "metrics 2-4 query: same total orders as the unfiltered run")
say(f"     groups that moved between the two runs: { {k: sf[k] - u2[k] for k in set(sf) | set(u2) if sf[k] != u2[k]} or 'none'}")
fz2 = Counter(); [fz2.update({r[1]: r[5]}) for r in P["soft"]]
check(fz2 == fz, "filtered runs agree with each other: metric 1 query and metrics 2-4 query give the same SDD split, kept and dropped")
sh = Counter(); [sh.update({tuple(r[1:6]): r[6]}) for r in P["shipment"]]
u5 = Counter({tuple(r[:5]): r[5] for r in U5["full_trimmed"]["rows"]})
diff = {k: sh[k] - u5[k] for k in set(sh) | set(u5) if sh[k] != u5[k]}
check(sum(sh.values()) == sum(u5.values()), "metric 5 query: same total orders as the unfiltered run")
say(f"     shipment groups that moved between the two runs (pickups/attempts recorded in the 12 minutes between them): {diff if diff else 'none'}")
sh_flag = Counter(); [sh_flag.update({(r[0], r[1], r[2]): r[6]}) for r in P["shipment"]]
sf_flag = Counter(); [sf_flag.update({(r[0], r[1], r[4]): r[5]}) for r in P["soft"]]
check(sh_flag == sf_flag, "filtered runs agree with each other: metric 5 query and metrics 2-4 query give the same orders per base, kept and dropped")
check(all(r[3] == "false" and r[4] == "false" for r in P["shipment"] if r[0] == "dropped"), "no dropped order (incomplete or scrapped) has a shipment, pickup or attempt")
check(all(r[0] == "no_status_row" and r[1] is None for r in P["frozen"] if r[0] == "no_status_row"), "the only orders with no status row are the blank-SDD_ENABLED orders already left out")

def k(rows, pred, idx): return sum(r[idx] for r in rows if pred(r))
non_sdd = k(P["frozen"], lambda r: r[0] == "kept" and r[1] == "false", 2)
pba = k(P["soft"], lambda r: r[0] == "kept" and r[1] == "false" and r[4] == "COURIER_PBA", 5)
intl = k(P["soft"], lambda r: r[0] == "kept" and r[1] == "false" and r[4] in INTERNAL, 5)
none_ = k(P["soft"], lambda r: r[0] == "kept" and r[1] == "false" and r[4] == "NONE", 5)
nosoft = k(P["soft"], lambda r: r[0] == "kept" and r[1] == "false" and r[4] is None, 5)
fail = k(P["soft"], lambda r: r[0] == "kept" and r[1] == "false" and r[3] == "true" and r[4] in INTERNAL + ("NONE",), 5)
pk_p = k(P["shipment"], lambda r: r[0] == "kept" and r[1] == "false" and r[2] == "COURIER_PBA" and r[4] == "true", 6)
pk_i = k(P["shipment"], lambda r: r[0] == "kept" and r[1] == "false" and r[2] in INTERNAL and r[4] == "true", 6)
b5_p = k(P["shipment"], lambda r: r[0] == "kept" and r[1] == "false" and r[2] == "COURIER_PBA", 6)
b5_i = k(P["shipment"], lambda r: r[0] == "kept" and r[1] == "false" and r[2] in INTERNAL, 6)

say("Checks: result")
check(non_sdd == k(P["soft"], lambda r: r[0] == "kept" and r[1] == "false", 5), "metric 1 = non-SDD total in the metrics 2-4 query")
check(pba + intl + none_ + nosoft == non_sdd, "PBA base + Internal base + served NONE + no soft record = metric 1")
check(b5_p == pba and b5_i == intl, "metric 5 bases = metric 4 bases (separate query run)")
check(all(r[2] == "true" for r in P["soft"] if r[4] == "COURIER_PBA"), "every PBA-served order was in rollout")

say("")
say(f"S1 M1  Total Non-SDD Orders = {non_sdd:,}   (dropped as incomplete/scrapped: {fz['false'] - non_sdd:,} non-SDD; blank SDD flag left out: {fz[None]:,})")
say(f"S1 M2  % allocated through PBA = {pba / non_sdd * 100:.1f}%   ({pba:,} / {non_sdd:,})")
say(f"S1 M3  % failed through PBA in rollout = {fail / non_sdd * 100:.2f}%   ({fail:,} / {non_sdd:,})")
say(f"S1 M4  Orders placed: PBA {pba:,}   Internal {intl:,}   (neither: served NONE {none_:,}, no soft record {nosoft:,})")
say(f"S1 M5  % picked up: PBA {pk_p / pba * 100:.1f}% ({pk_p:,} of {pba:,})   Internal {pk_i / intl * 100:.1f}% ({pk_i:,} of {intl:,})")
open(f"{ROOT}/outputs/dashboard-s1-m1-m5-placed-w2.txt", "w").write("\n".join(lines) + "\n")
