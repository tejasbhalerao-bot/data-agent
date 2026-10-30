# Purpose: Section 2 soft, WH to Delivery promise: metric 1 (PBA base, PBA promise) and metric 3 (Internal base, Internal promise);
#          avg, nearest-rank p25/p50/p75/p90 and cumulative % at 0 / <=1 / <=2 / <=3 / 4+ days; runs every agreed check
# Serves: Dashboard S2 M1 and M3 (field mapping 2026-10-18, signed off 2026-10-30; placed-order filter 2026-10-30)
# Reads: archives/pba-cr/raw-data/dashboard/s2/{pba,int}-side_chunk-<12h chunk>.json (local only, never pushed): the saved Metabase results of
#        queries-dump/dashboard/s2-promise_soft-promise_m1-m10-histogram_prefiltered-nolane_{pba,int}-side_chunk-<12h chunk>.sql
#        (7 chunks of 12 hours, 22 Oct 12:00 to 26 Oct 00:00 IST; counts of orders per base group, measure and promise-day value)
# Writes: archives/pba-cr/outputs/dashboard-s2-m1-m3.txt (local only)
# Run with: python3 archives/pba-cr/scripts/2026-10-30-aggregate-dashboard-s2-m1-m3-wh-to-delivery-v1.py [m1|m3]   (default: both available)
# Note: the chunk queries add a performance pre-filter to the v2.1 base (only orders with a promise row inside the window are read);
#       it gave identical counts on the 23 Oct 10-11 slice and on the full-window lane-set query. Pass/fail here does not re-prove that.

import hashlib, json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
Q = f"{ROOT}/queries-dump/dashboard"
R = f"{ROOT}/raw-data/dashboard/s2"
CHUNKS = ["22oct-12pm", "23oct-12am", "23oct-12pm", "24oct-12am", "24oct-12pm", "25oct-12am", "25oct-12pm"]
BOUNDS = ["2026-10-22 12:00:00", "2026-10-23 00:00:00", "2026-10-23 12:00:00", "2026-10-24 00:00:00",
          "2026-10-24 12:00:00", "2026-10-25 00:00:00", "2026-10-25 12:00:00", "2026-10-26 00:00:00"]
METRICS = {"m1": ("pba", "PBA", "WH_PBA", "PBA allocated orders, PBA promise"),
           "m3": ("int", "Internal", "WH_INT", "Internal allocated orders, Internal promise")}
M4_BASE = {"PBA": 3490, "Internal": 66747}   # Section 1 metric 4 (placed orders, run earlier today)

lines = []
def say(t=""): print(t); lines.append(t)
def check(ok, label):
    say(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    if not ok: raise SystemExit(f"check failed: {label}")

def load_side(side):
    hist_all, seen = [], set()
    for i, c in enumerate(CHUNKS):
        qf = f"{Q}/s2-promise_soft-promise_m1-m10-histogram_prefiltered-nolane_{side}-side_chunk-{c}.sql"
        q = open(qf).read()
        j = json.load(open(f"{R}/{side}-side_chunk-{c}.json"))
        d = j["data"]; cols = [x["name"] for x in d["cols"]]
        rows = [dict(zip(cols, r)) for r in d["rows"]]
        a, b = q.index("WITH params AS ("), q.index("\n)\nSELECT")
        check(j["json_query"]["stages"][0]["native"].strip() == q.strip(), f"{side} {c}: SQL Metabase ran is the saved file")
        check({r["BASE_MD5"] for r in rows} == {hashlib.md5(q[a:b].encode()).hexdigest()}, f"{side} {c}: in-query fingerprint matches the file")
        check(f"'{BOUNDS[i]} +0530'" in q and f"'{BOUNDS[i+1]} +0530'" in q.split("end_ts")[0], f"{side} {c}: window {BOUNDS[i]} to {BOUNDS[i+1]}")
        check(j["status"] == "completed" and not d.get("rows_truncated") and j["row_count"] == len(rows) < 2000, f"{side} {c}: complete, {len(rows)} rows, not truncated")
        key = json.dumps(sorted([(r["BASE_GROUP"], r["MEASURE"], r["DAYS"], r["N_ORDERS"]) for r in rows], key=str))
        check(key not in seen, f"{side} {c}: result differs from every other chunk")
        seen.add(key)
        hist_all.append((c, rows))
    return hist_all

def stats(hist):
    n = sum(hist.values()); ds = sorted(hist)
    avg = sum(d * k for d, k in hist.items()) / n
    def pct(p):
        cum = 0
        for d in ds:
            cum += hist[d]
            if cum * 100 >= p * n: return d
    cum = {k: sum(v for d, v in hist.items() if d <= k) * 100 / n for k in range(4)}
    return n, avg, {p: pct(p) for p in (25, 50, 75, 90)}, cum

which = sys.argv[1:] or ["m1", "m3"]
for m in which:
    side, bg, measure, label = METRICS[m]
    say(f"=== Section 2 soft, {m.upper()}: {label} (WH to Delivery, calendar days, IST) ===")
    say("Checks: the queries and their results")
    chunks = load_side(side)
    hist, null_n, neg, total, types = {}, 0, {}, 0, set()
    per_chunk = []
    for c, rows in chunks:
        mine = [r for r in rows if r["BASE_GROUP"] == bg and r["MEASURE"] == measure]
        other = [r for r in rows if r["BASE_GROUP"] == bg and r["MEASURE"] != measure]
        check(sum(r["N_ORDERS"] for r in mine) == sum(r["N_ORDERS"] for r in other), f"{c}: both measures cover the same {bg} orders (no order lost in the unpivot)")
        check(all(r["COMMON_LANE"] is False for r in rows), f"{c}: no lane flag in this query (lane-free run)")
        per_chunk.append(sum(r["N_ORDERS"] for r in mine))
        for r in mine:
            types.add(r["TS_TYPES_MIN"]); types.add(r["TS_TYPES_MAX"])
            total += r["N_ORDERS"]
            if r["DAYS"] is None: null_n += r["N_ORDERS"]
            elif r["DAYS"] < 0: neg[r["DAYS"]] = neg.get(r["DAYS"], 0) + r["N_ORDERS"]
            else: hist[r["DAYS"]] = hist.get(r["DAYS"], 0) + r["N_ORDERS"]
    check(all(t.startswith("TIMESTAMP_TZ") and t.count("TIMESTAMP_TZ") == 3 for t in types), f"all three timestamps are offset-aware (TIMESTAMP_TZ), so the IST date is exact: {sorted(types)}")
    n, avg, p, cum = stats(hist)
    check(n + null_n + sum(neg.values()) == total, "orders counted + blank + negative = whole base")
    check(cum[0] <= cum[1] <= cum[2] <= cum[3] <= 100, "cumulative % rises and stays within 100")
    for k, d in p.items():
        check(sum(v for x, v in hist.items() if x <= d) * 100 >= k * n and sum(v for x, v in hist.items() if x < d) * 100 < k * n, f"p{k} = {d} agrees with the cumulative counts (nearest rank)")
    say(f"  [INFO] {bg} base here: {total:,} orders (per 12h chunk: {per_chunk}); Section 1 metric 4 had {M4_BASE[bg]:,}; difference {total - M4_BASE[bg]:+,} (live data moved between runs)")
    say("")
    say("Result")
    say(f"  Orders in the metric (both timestamps present, days >= 0): {n:,} of {total:,} in the {bg} base")
    say(f"  Left out, a timestamp blank: {null_n:,};  left out, negative days (data error): {sum(neg.values()):,} {neg if neg else ''}")
    say(f"  Avg {avg:.1f} d | p25 {p[25]} | p50 {p[50]} | p75 {p[75]} | p90 {p[90]}")
    say(f"  Cumulative: 0 d {cum[0]:.1f}% | <=1 {cum[1]:.1f}% | <=2 {cum[2]:.1f}% | <=3 {cum[3]:.1f}% | 4+ 100.0%")
    say(f"  Distribution (days: orders): {dict(sorted(hist.items()))}")
    say("")

os.makedirs(f"{ROOT}/outputs", exist_ok=True)
open(f"{ROOT}/outputs/dashboard-s2-{'-'.join(which)}.txt", "w").write("\n".join(lines) + "\n")
