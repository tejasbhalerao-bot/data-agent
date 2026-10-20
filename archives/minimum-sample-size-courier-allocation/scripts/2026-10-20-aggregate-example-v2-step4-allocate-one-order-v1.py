# Purpose: example step 4: allocate one order, at order placed or at invoice, under today's rule and each x
# Serves: worked example only (pre-brief); no metric
# Reads: archives/minimum-sample-size-courier-allocation/raw-data/orders-2026-07.csv .. orders-2026-09.csv (shipment files)
#        archives/minimum-sample-size-courier-allocation/raw-data/op-2026-07.csv .. op-2026-09.csv (order placed files)
#        archives/minimum-sample-size-courier-allocation/raw-data/ops-speed-config-wh37.csv (ops-configured delivery days)
#        archives/minimum-sample-size-courier-allocation/raw-data/tat-adherence-master.csv (fallback adherence)
#        archives/minimum-sample-size-courier-allocation/raw-data/courier-partner-schedules.csv (courier cutoffs)
#        archives/minimum-sample-size-courier-allocation/raw-data/serviceability-<courier>.csv (pincodes served)
#        archives/minimum-sample-size-courier-allocation/outputs/goi-pincode-map.csv (from structure-goi-pincode-map-v1.py)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/example-v2-step4-<stage>-<order id>.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-example-v2-step4-allocate-one-order-v1.py <order id> <placed|invoice>
#
# The decision date is the date of the stage's timestamp: the digitised time for "placed", the invoice-create
# time for "invoice" (process flow v2). TAT and adherence are those of the nightly run on that date: orders with a
# first delivery attempt in the N days before it (7, 14, 21, 28), as in step 3 (percentile value 0.85, no drop buffers).
# Competing couriers: those among 185, 195, 225, 246, 247, 286 whose serviceability file lists the order's pincode.
# Score = Buffer Adjusted Lane TAT / (adherence as a fraction) + schedule time adjustment + pickup buffer + drop buffer.
# Schedule time adjustment = +1 when the time of day of the stage's timestamp is after the courier's cutoff for the
# warehouse (courier-partner-schedules.csv), otherwise 0. Pickup buffer and drop buffer are 0 (no data; scope v3).
# The lowest score wins; a tie is shown, not broken. The promise is the winner's lane TAT.
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
    if len(sys.argv) < 3 or sys.argv[2] not in ("placed", "invoice"):
        sys.exit("Usage: <order id> <placed|invoice>")
    oid, stage = sys.argv[1], sys.argv[2]

    ts = None
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

    print(f"Order {oid}, stage {stage}: timestamp {when:%Y-%m-%d %H:%M}, decision date {D}, history windows end {D - timedelta(days=1)}")
    print(f"Warehouse {WH}, pincode {PIN}. Serviceable among the six: {couriers}")
    out = []
    for label, x in [("today (x=1)", None)] + [(f"x={x}", x) for x in XS]:
        results = []
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
            score = tat / (adh / 100) + adj
            results.append((score, c, used, tat, adh, cut, adj))
        results.sort()
        print(f"\n--- {label}")
        print("  courier | data used | lane TAT | adherence % | cutoff | after cutoff (+1) | score")
        for score, c, used, tat, adh, cut, adj in results:
            print(f"  {c} | {used} | {tat} | {adh:.2f} | {cut} | {adj} | {score:.4f}")
            out.append([label, c, used, tat, round(adh, 2), cut, adj, round(score, 4)])
        tie = [r for r in results if abs(r[0] - results[0][0]) < 1e-9]
        win = results[0]
        print(f"  winner: {', '.join(r[1] for r in tie)}{' (tie)' if len(tie) > 1 else ''}; promise = lane TAT {win[3]} days")

    with open(P + f"outputs/example-v2-step4-{stage}-{oid}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "courier", "data_used", "lane_tat_days", "adherence_pct", "cutoff", "after_cutoff_plus1", "score"])
        w.writerows(out)


if __name__ == "__main__":
    main()
