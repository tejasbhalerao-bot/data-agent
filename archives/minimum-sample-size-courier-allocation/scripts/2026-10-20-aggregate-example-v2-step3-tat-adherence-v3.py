# Purpose: example steps 2 and 3 for every competing courier: where the ladder stops for each x, and the lane TAT and adherence there
# Serves: worked example only (pre-brief); no metric
# Reads: archives/minimum-sample-size-courier-allocation/raw-data/orders-2026-07.csv .. orders-2026-09.csv (shipment files)
#        archives/minimum-sample-size-courier-allocation/raw-data/ops-speed-config-wh37.csv (ops-configured delivery days)
#        archives/minimum-sample-size-courier-allocation/raw-data/tat-adherence-master.csv (fallback adherence)
#        archives/minimum-sample-size-courier-allocation/outputs/goi-pincode-map.csv (from structure-goi-pincode-map-v1.py)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/example-v2-step3-all-couriers-<D>.csv
#         archives/minimum-sample-size-courier-allocation/outputs/example-v2-step3-all-couriers-pools-<D>.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-example-v2-step3-tat-adherence-v3.py [YYYY-MM-DD]
#
# Same method as v2 (performance-based-speed-calculation-and-allocation.md, no drop buffers, percentile value 0.85):
#   Actual speed = DATE(first delivery attempt) - DATE(pickup); Lane TAT = ROUNDUP(85th percentile, linear);
#   delay days = actual speed - the order's own PROMISE_TAT; adherence = running share, from Early 4+ upward,
#   at the first bucket where it is >= 0.85.
# Rules per process flow v2: stop at the first ladder step with at least x orders (time first, then geography);
# if none reaches x but the widest pool (state, 28 days) has orders, use it; if it has none, use the ops-configured
# TAT (default 3 days when there is no config row) and the TAT Adherence Master adherence.
# "Today" (x = 1) uses the pincode over 7 days when it has any order, otherwise the ops config and TAT Adherence Master.
# Defaults: warehouse 37, pincode 271604, decision date 2026-09-21, couriers 195, 225, 246, 247
# (the couriers serviceable on the pincode, from the serviceability files).

import csv
import glob
import math
import sys
from datetime import datetime, date, timedelta

P = "archives/minimum-sample-size-courier-allocation/"
FMT = "%b %d, %Y, %I:%M %p"
WH, PIN = "37", "271604"
COURIERS = ["195", "225", "246", "247"]
D = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date(2026, 9, 21)
if not date(2026, 7, 29) <= D <= date(2026, 9, 30):
    sys.exit("Decision date must be between 2026-07-29 and 2026-09-30 (scope v5)")
PCT = 0.85
XS = (10, 15, 20)
WINDOWS = (7, 14, 21, 28)
GEOS = ("pincode", "micro-cluster", "macro-cluster", "state")
LADDER = [(g, n) for g in GEOS for n in WINDOWS]
BUCKETS = ["Early 4+", "Early 3", "Early 2", "Early 1", "On-Time", "Late 1", "Late 2", "Late 3", "Late 4+"]
DEFAULT_SUPPOSED_TAT = 3


def percentile(vals, p):
    s = sorted(vals)
    pos = p * (len(s) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def bucket(delay):
    if delay <= -4:
        return 0
    if delay < 0:
        return 4 + delay
    if delay == 0:
        return 4
    return min(4 + delay, 8)


def tat_adherence(rows):
    n = len(rows)
    actuals = [r[3] for r in rows]
    lane_tat = math.ceil(percentile(actuals, PCT))
    counts = [0] * 9
    for r in rows:
        counts[bucket(r[5])] += 1
    cum = 0
    for i, c in enumerate(counts):
        cum += c
        if cum / n >= PCT:
            return lane_tat, round(100 * cum / n, 2), BUCKETS[i], counts
    return lane_tat, 100.0, BUCKETS[-1], counts


def main():
    gmap = {}
    with open(P + "outputs/goi-pincode-map.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            gmap[r["pincode"]] = (r["macro_cluster"], r["state"], r["district"], r["division"])
    macro, state, district, division = gmap[PIN]

    def in_geo(geo, pin):
        g = gmap.get(pin)
        if geo == "pincode":
            return pin == PIN
        if not g:
            return False
        if geo == "micro-cluster":
            return (g[1], g[2], g[3]) == (state, district, division)
        if geo == "macro-cluster":
            return g[0] == macro
        return g[1] == state

    hist = {c: [] for c in COURIERS}
    for fn in sorted(glob.glob(P + "raw-data/orders-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            if r["WAREHOUSE_ID"] != WH or r["DELIVERY_PARTNER"] not in hist:
                continue
            try:
                a = datetime.strptime(r["DELIVERY_ATTEMPT_TIME"], FMT)
                p = datetime.strptime(r["PICKUP_TIME"], FMT)
            except ValueError:
                continue
            if a < p:
                continue
            actual = (a.date() - p.date()).days
            promise = int(r["PROMISE_TAT"])
            hist[r["DELIVERY_PARTNER"]].append((r["ORDER_ID"].replace(",", ""), r["PINCODE"], a.date(), actual, promise, actual - promise))

    cfg = {}
    for r in csv.DictReader(open(P + f"raw-data/ops-speed-config-wh{WH}.csv", encoding="utf-8-sig", newline="")):
        cfg[(r["pincode"], r["delivery_partner"])] = int(r["delivery_days"])
    master = {}
    for r in csv.DictReader(open(P + "raw-data/tat-adherence-master.csv", encoding="utf-8-sig", newline="")):
        master[(r["Warehouse ID"], r["Delivery Partner"])] = float(r["Adherence Percentage"])

    def pool(c, geo, n):
        lo, hi = D - timedelta(days=n), D - timedelta(days=1)
        return [r for r in hist[c] if lo <= r[2] <= hi and in_geo(geo, r[1])]

    def ops_config(c):
        days = cfg.get((PIN, c))
        src = "ops config" if days is not None else f"no config row, default {DEFAULT_SUPPOSED_TAT} days"
        return (days if days is not None else DEFAULT_SUPPOSED_TAT), master.get((WH, c)), src

    out, pools_out = [], []
    print(f"Warehouse {WH}, pincode {PIN}, decision date {D}, percentile {PCT}; windows end {D - timedelta(days=1)}")
    for c in COURIERS:
        cache = {}
        for geo, n in LADDER:
            cache[(geo, n)] = pool(c, geo, n)
        widest = cache[("state", 28)]
        cases = [("today (x=1)", None)] + [(f"x={x}", x) for x in XS]
        print(f"\n===== Courier {c}")
        for label, x in cases:
            if x is None:
                rows = cache[("pincode", 7)]
                if rows:
                    stop = ("pincode", 7)
                else:
                    stop = None
            else:
                stop = next((k for k in LADDER if len(cache[k]) >= x), None)
                if stop is None and widest:
                    stop = ("state", 28)
                    how = "widest pool, below x"
                else:
                    how = "reached x" if stop else ""
            if stop:
                rows = cache[stop]
                tat, adh, at, counts = tat_adherence(rows)
                key = (c, stop[0], stop[1])
                if key not in [(p[0], p[1], p[2]) for p in pools_out]:
                    pools_out.append([c, stop[0], stop[1], len(rows)] + counts)
                row = [c, label, f"{stop[0]} {stop[1]}d", len(rows), tat, adh, at, "orders"]
                print(f"  {label:12s} -> {stop[0]} over {stop[1]} days, {len(rows)} orders: Lane TAT {tat} days, adherence {adh}% (reached at {at})")
            else:
                days, adh, src = ops_config(c)
                row = [c, label, "ops config", 0, days, adh, "", src]
                print(f"  {label:12s} -> no orders at any step: ops config TAT {days} days ({src}), adherence master {adh}%")
            out.append(row)

    tag = D.isoformat()
    with open(P + f"outputs/example-v2-step3-all-couriers-{tag}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["courier", "case", "data_used", "orders", "tat_days", "adherence_pct", "adherence_reached_at", "source"])
        w.writerows(out)
    with open(P + f"outputs/example-v2-step3-all-couriers-pools-{tag}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["courier", "geography", "window_days", "orders"] + BUCKETS)
        w.writerows(pools_out)


if __name__ == "__main__":
    main()
