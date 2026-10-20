# Purpose: example step 5: both adherence calculations for one order (courier unchanged, and courier changed) under today's rule and each x
# Serves: worked example only (pre-brief); no metric
# Reads: archives/minimum-sample-size-courier-allocation/raw-data/orders-2026-07.csv .. orders-2026-09.csv (shipment files)
#        archives/minimum-sample-size-courier-allocation/raw-data/op-2026-07.csv .. op-2026-09.csv (order placed files)
#        archives/minimum-sample-size-courier-allocation/raw-data/ops-speed-config-wh37.csv, tat-adherence-master.csv,
#        courier-partner-schedules.csv, serviceability-<courier>.csv (same inputs as step 4)
#        archives/minimum-sample-size-courier-allocation/outputs/goi-pincode-map.csv (from structure-goi-pincode-map-v1.py)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/example-v2-step5-<order id>.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-example-v2-step5-adherence-one-order-v1.py <order id>
#
# Allocation is as in step 4, at the order placed date (decision date = digitised date).
# Adherence A, "courier unchanged" (board section 2): the order keeps the courier that actually shipped it. Its promise is that
#   courier's projected lane TAT under the rule (today's or x), as of the order placed date. The order is classified by
#   delay days = actual days - promise (Early / On-Time / Late). This tests how accurate each courier's speed projection is
#   with the sample rule in mind. Under today's rule this should equal the real promise (PROMISE_TAT).
# Adherence B, "courier changed" (board section 3): if the winning courier under the rule is the actual shipping courier
#   (a tie counts if the actual courier is among the tied winners), classify as in A; otherwise the order is excluded.
# Actual days = DATE(first delivery attempt) - DATE(pickup). Percentile value 0.85, no drop buffers.
# Example lane: warehouse 37, pincode 271604.

import csv
import glob
import math
import sys
from datetime import datetime, date, timedelta

P = "archives/minimum-sample-size-courier-allocation/"
FMT = "%b %d, %Y, %I:%M %p"
WH, PIN = "37", "271604"
SIX = ["185", "195", "225", "246", "247", "286"]
PCT = 0.85
XS = (10, 15, 20)
WINDOWS = (7, 14, 21, 28)
GEOS = ("pincode", "micro-cluster", "macro-cluster", "state")
LADDER = [(g, n) for g in GEOS for n in WINDOWS]
DEFAULT_SUPPOSED_TAT = 3
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
        return 4 + delay
    if delay == 0:
        return 4
    return min(4 + delay, 8)


def tat_adherence(rows):
    n = len(rows)
    lane_tat = math.ceil(percentile([r[3] for r in rows], PCT))
    counts = [0] * 9
    for r in rows:
        counts[bucket(r[5])] += 1
    cum = 0
    for c in counts:
        cum += c
        if cum / n >= PCT:
            return lane_tat, 100 * cum / n
    return lane_tat, 100.0


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: <order id>")
    oid, stage = sys.argv[1], "placed"

    ts = None
    actual_courier = actual_days = real_promise = None
    for fn in sorted(glob.glob(P + "raw-data/orders-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            if r["ORDER_ID"].replace(",", "") == oid:
                a = datetime.strptime(r["DELIVERY_ATTEMPT_TIME"], FMT)
                p = datetime.strptime(r["PICKUP_TIME"], FMT)
                actual_courier, actual_days, real_promise = r["DELIVERY_PARTNER"], (a.date() - p.date()).days, int(r["PROMISE_TAT"])
    if actual_courier is None:
        sys.exit("Order not found in the shipment files")
    for fn in sorted(glob.glob(P + "raw-data/op-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            if r["ORDER_ID"].replace(",", "") == oid:
                ts = (r["DIGITISED_TS"], r["INVOICE_CREATE_TS"])
    if not ts:
        sys.exit("Order not found in the order placed files")
    when = datetime.strptime(ts[0] if stage == "placed" else ts[1], FMT)
    D = when.date()
    if not date(2026, 7, 29) <= D <= date(2026, 9, 30):
        sys.exit("Decision date outside 2026-07-29 .. 2026-09-30 (scope v5)")

    serves = {c: PIN in {r["pincode"].strip() for r in csv.DictReader(open(P + f"raw-data/serviceability-{c}.csv", encoding="utf-8-sig", newline=""))} for c in SIX}
    couriers = [c for c in SIX if serves[c]]
    sched = {}
    for r in csv.DictReader(open(P + "raw-data/courier-partner-schedules.csv", encoding="utf-8-sig", newline="")):
        sched[(r["Warehouse ID"], r["Courier Partner ID"])] = r["Courier Partner Schedule Time"][:8]

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

    hist = {c: [] for c in couriers}
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
            hist[r["DELIVERY_PARTNER"]].append((r["ORDER_ID"], r["PINCODE"], a.date(), actual, promise, actual - promise))

    cfg = {}
    for r in csv.DictReader(open(P + f"raw-data/ops-speed-config-wh{WH}.csv", encoding="utf-8-sig", newline="")):
        cfg[(r["pincode"], r["delivery_partner"])] = int(r["delivery_days"])
    master = {}
    for r in csv.DictReader(open(P + "raw-data/tat-adherence-master.csv", encoding="utf-8-sig", newline="")):
        master[(r["Warehouse ID"], r["Delivery Partner"])] = float(r["Adherence Percentage"])

    def pool(c, geo, n):
        lo, hi = D - timedelta(days=n), D - timedelta(days=1)
        return [r for r in hist[c] if lo <= r[2] <= hi and in_geo(geo, r[1])]

    def klass(delay):
        return "Early" if delay < 0 else ("On-Time" if delay == 0 else "Late")

    print(f"Order {oid}: placed {when:%Y-%m-%d %H:%M}, decision date {D}, history windows end {D - timedelta(days=1)}")
    print(f"Actually shipped by courier {actual_courier}; actual days {actual_days}; real promise (PROMISE_TAT) {real_promise} days")
    out = []
    for label, x in [("today (x=1)", None)] + [(f"x={x}", x) for x in XS]:
        results = {}
        for c in couriers:
            cache = {k: pool(c, *k) for k in LADDER}
            widest = cache[("state", 28)]
            if x is None:
                stop = ("pincode", 7) if cache[("pincode", 7)] else None
            else:
                stop = next((k for k in LADDER if len(cache[k]) >= x), None)
                if stop is None and widest:
                    stop = ("state", 28)
            if stop:
                rows = cache[stop]
                tat, adh = tat_adherence(rows)
                used = f"{stop[0]} {stop[1]}d ({len(rows)} orders)"
            else:
                tat = cfg.get((PIN, c), DEFAULT_SUPPOSED_TAT)
                adh = master[(WH, c)]
                used = "ops config + adherence master (0 orders)"
            cut = sched.get((WH, c))
            adj = 1 if cut and when.strftime("%H:%M:%S") > cut else 0
            results[c] = (tat / (adh / 100) + adj, tat, adh, used)
        best = min(v[0] for v in results.values())
        winners = [c for c, v in results.items() if abs(v[0] - best) < 1e-9]
        a_tat, a_adh, a_used = results[actual_courier][1], results[actual_courier][2], results[actual_courier][3]
        delay = actual_days - a_tat
        a_class = klass(delay)
        same = actual_courier in winners
        print(f"\n--- {label}")
        print(f"  winner(s): {', '.join(winners)} (promise {results[winners[0]][1]} days)")
        print(f"  A, courier unchanged: courier {actual_courier} projected TAT {a_tat} days from {a_used}; actual {actual_days} -> delay {delay:+d} -> {a_class}")
        if same:
            print(f"  B, courier changed: winner includes the shipping courier {actual_courier}; classified as in A -> {a_class}")
        else:
            print(f"  B, courier changed: winner {', '.join(winners)} differs from shipping courier {actual_courier} -> excluded (halt)")
        out.append([label, ",".join(winners), actual_courier, a_tat, round(a_adh, 2), actual_days, delay, a_class, "same" if same else "excluded"])

    with open(P + f"outputs/example-v2-step5-{oid}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "winners", "shipping_courier", "projected_tat_days", "adherence_pct", "actual_days", "delay_days", "class_A", "B_status"])
        w.writerows(out)


if __name__ == "__main__":
    main()
