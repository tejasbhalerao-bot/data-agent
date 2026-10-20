# Purpose: example step 3: lane TAT and adherence for one courier from the orders at the chosen ladder step
# Serves: worked example only (pre-brief); no metric
# Reads: archives/minimum-sample-size-courier-allocation/raw-data/orders-2026-07.csv .. orders-2026-09.csv (shipment files)
#        archives/minimum-sample-size-courier-allocation/outputs/goi-pincode-map.csv (from structure-goi-pincode-map-v2.py)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/example-v2-step3-pool-<label>-<courier>-<D>.csv (the orders used)
#         archives/minimum-sample-size-courier-allocation/outputs/example-v2-step3-summary-<courier>-<D>.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-example-v2-step3-tat-adherence-v2.py [courier] [YYYY-MM-DD]
#
# Method: performance-based-speed-calculation-and-allocation.md, with no drop buffers (scope v3).
#   Actual speed = DATE(first delivery attempt) - DATE(pickup).
#   Lane TAT = ROUNDUP(PERCENTILE(actual speeds, 0.85)); Buffer Adjusted Lane TAT = Lane TAT (drop buffer 0).
#   Delay days = actual speed - the promise the order was given (PROMISE_TAT, days); negative values are kept.
#   Buckets: Early 4+, Early 3, Early 2, Early 1, On-Time, Late 1, Late 2, Late 3, Late 4+.
#   Adherence = running share of orders, from Early 4+ upward, at the first bucket where it is >= 0.85.
# The percentile uses linear interpolation (position = 0.85 x (n - 1)); the document does not name a method.
# Two pools are shown: the pool the ladder stops at (micro-cluster, 7 days) and today's rule x = 1 (pincode, 7 days).
# Defaults: warehouse 37, pincode 271604, courier 195, decision date 2026-09-21.

import csv
import glob
import math
import sys
from datetime import datetime, date, timedelta

P = "archives/minimum-sample-size-courier-allocation/"
FMT = "%b %d, %Y, %I:%M %p"
WH, PIN = "37", "271604"
COURIER = sys.argv[1] if len(sys.argv) > 1 else "195"
D = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date(2026, 9, 21)
if not date(2026, 7, 29) <= D <= date(2026, 9, 30):
    sys.exit("Decision date must be between 2026-07-29 and 2026-09-30 (scope v5)")
PCT = 0.85  # percentile value: 85%, not the document's default 80% (Tejas, 2026-10-20)
BUCKETS = ["Early 4+", "Early 3", "Early 2", "Early 1", "On-Time", "Late 1", "Late 2", "Late 3", "Late 4+"]


def percentile(vals, p):
    s = sorted(vals)
    pos = p * (len(s) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def bucket(delay):
    if delay <= -4:
        return 0
    if delay < 0:
        return 4 + delay  # -3 -> 1, -2 -> 2, -1 -> 3
    if delay == 0:
        return 4
    return min(4 + delay, 8)


def main():
    gmap = {}
    with open(P + "outputs/goi-pincode-map.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            gmap[r["pincode"]] = (r["macro_cluster"], r["state"], r["district"], r["division"])
    me = gmap[PIN]
    macro, state, district, division = me

    def in_micro(pin):
        g = gmap.get(pin)
        return bool(g) and (g[1], g[2], g[3]) == (state, district, division)

    lo7, hi7 = D - timedelta(days=7), D - timedelta(days=1)
    pools = {"micro-cluster-7d": [], "pincode-7d": []}
    for fn in sorted(glob.glob(P + "raw-data/orders-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            if r["WAREHOUSE_ID"] != WH or r["DELIVERY_PARTNER"] != COURIER:
                continue
            try:
                a = datetime.strptime(r["DELIVERY_ATTEMPT_TIME"], FMT)
                p = datetime.strptime(r["PICKUP_TIME"], FMT)
            except ValueError:
                continue
            if a < p or not lo7 <= a.date() <= hi7:
                continue
            actual = (a.date() - p.date()).days
            promise = int(r["PROMISE_TAT"])
            row = [r["ORDER_ID"].replace(",", ""), r["PINCODE"], a.date().isoformat(), actual, promise, actual - promise]
            if in_micro(r["PINCODE"]):
                pools["micro-cluster-7d"].append(row)
            if r["PINCODE"] == PIN:
                pools["pincode-7d"].append(row)

    tag = f"{COURIER}-{D.isoformat()}"
    summary = []
    print(f"Warehouse {WH}, courier {COURIER}, decision date {D}; history window {lo7} to {hi7}; percentile {PCT}")
    for label, rows in pools.items():
        rows.sort(key=lambda x: (x[2], x[0]))
        with open(P + f"outputs/example-v2-step3-pool-{label}-{tag}.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["order_id", "pincode", "attempt_date", "actual_days", "promise_days", "delay_days"])
            w.writerows(rows)
        n = len(rows)
        actuals = [r[3] for r in rows]
        raw_p = percentile(actuals, PCT)
        lane_tat = math.ceil(raw_p)
        counts = [0] * 9
        for r in rows:
            counts[bucket(r[5])] += 1
        cum, adh, at = 0, None, None
        for i, c in enumerate(counts):
            cum += c
            if adh is None and cum / n >= PCT:
                adh, at = cum / n, BUCKETS[i]
        dist = {}
        for v in actuals:
            dist[v] = dist.get(v, 0) + 1
        print(f"\n== Pool {label}: {n} orders")
        print("   actual days -> orders:", dict(sorted(dist.items())))
        print(f"   85th percentile of actual days (linear): {raw_p:.4f} -> Lane TAT (rounded up) = {lane_tat} days")
        print("   delay-day buckets (orders):", {BUCKETS[i]: counts[i] for i in range(9)})
        run, cums = 0, []
        for c in counts:
            run += c
            cums.append(round(100 * run / n, 2))
        print("   cumulative % from Early 4+:", dict(zip(BUCKETS, cums)))
        print(f"   adherence reached at {at}: {100 * adh:.2f}%")
        summary.append([label, n, round(raw_p, 4), lane_tat, at, round(100 * adh, 2)] + counts)

    with open(P + f"outputs/example-v2-step3-summary-{tag}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pool", "orders", "p80_actual_days", "lane_tat_days", "adherence_reached_at", "adherence_pct"] + BUCKETS)
        w.writerows(summary)


if __name__ == "__main__":
    main()
