# Purpose: example step 6: allocate each order at order placed and at invoice, and calculate both adherence types, under today's rule and each x
# Serves: worked example only (pre-brief); no metric
# Reads: archives/minimum-sample-size-courier-allocation/raw-data/orders-2026-07.csv .. orders-2026-09.csv (shipment files)
#        archives/minimum-sample-size-courier-allocation/raw-data/op-2026-07.csv .. op-2026-09.csv (order placed files)
#        archives/minimum-sample-size-courier-allocation/raw-data/ops-speed-config-wh37.csv, tat-adherence-master.csv,
#        courier-partner-schedules.csv, serviceability-<courier>.csv
#        archives/minimum-sample-size-courier-allocation/outputs/goi-pincode-map.csv (from structure-goi-pincode-map-v1.py)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/example-v2-step6-orders-<D>.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-example-v2-step6-allocate-and-adherence-v1.py [order id ...]
#           (no order id: every order placed on the example date on the example lane)
#
# Process flow v4. Example lane: warehouse 37, pincode 271604; order placed date D = 2026-09-21.
# Lane key for history = warehouse x pincode x courier; same for micro-cluster, macro-cluster and state (Tejas).
# History = orders with a first delivery attempt in the N days before the decision date (7, 14, 21, 28).
# Lane TAT = ROUNDUP(85th percentile, linear) of actual days; adherence = running share of delay-day buckets until it first
# reaches 0.85; no drop buffers (scope v3). Ops config and adherence master are today's snapshot (Tejas).
# Score = lane TAT / adherence + schedule time adjustment + pickup buffer (0) + drop buffer (0); lowest wins.
# Schedule time adjustment (Tejas):
#   at order placed: +1 if the promised warehouse processing time (DIGITISED_WH_PROMISE), by time of day, is after the courier's cutoff;
#   at invoice: +1 if the invoice-create time, by time of day, is after the courier's cutoff.
# Tie-break priority (Tejas): 195 > 185 > 225 > 246 > 286 > 247.
# Decision date: order placed stage = digitised date; invoice stage = invoice-create date. Both must be in 2026-07-29 .. 2026-09-30.
# Adherence A, courier unchanged: the order keeps the courier that shipped it; promise = that courier's projected lane TAT under the
#   rule at the order placed stage; classify actual days - promise as Early / On-Time / Late.
# Adherence B, courier changed: if the invoice-stage winner is the shipping courier, classify actual days against the promise
#   the customer saw in the simulated world, which is the order-placed-stage winner's lane TAT; otherwise the order is excluded.

import csv
import glob
import math
import sys
from datetime import datetime, date, timedelta

P = "archives/minimum-sample-size-courier-allocation/"
FMT = "%b %d, %Y, %I:%M %p"
WH, PIN = "37", "271604"
D0 = date(2026, 9, 21)
SIX = ["185", "195", "225", "246", "247", "286"]
PRIORITY = ["195", "185", "225", "246", "286", "247"]
PCT = 0.85
XS = (10, 15, 20)
WINDOWS = (7, 14, 21, 28)
GEOS = ("pincode", "micro-cluster", "macro-cluster", "state")
LADDER = [(g, n) for g in GEOS for n in WINDOWS]
DEFAULT_SUPPOSED_TAT = 3
CASES = [("today", None)] + [(f"x={x}", x) for x in XS]


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


def klass(delay):
    return "Early" if delay < 0 else ("On-Time" if delay == 0 else "Late")


def main():
    ids = sys.argv[1:]
    # order placed rows
    op = {}
    for fn in sorted(glob.glob(P + "raw-data/op-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            d = datetime.strptime(r["DIGITISED_TS"], FMT)
            inv = r["INVOICE_CREATE_TS"]
            whp = r["DIGITISED_WH_PROMISE"]
            op[r["ORDER_ID"].replace(",", "")] = (d,
                                                 datetime.strptime(inv, FMT) if inv else None,
                                                 datetime.strptime(whp, FMT) if whp else None)

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
    orders = {}
    for fn in sorted(glob.glob(P + "raw-data/orders-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            if r["WAREHOUSE_ID"] != WH:
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
            o = r["ORDER_ID"].replace(",", "")
            if r["DELIVERY_PARTNER"] in hist:
                hist[r["DELIVERY_PARTNER"]].append((o, r["PINCODE"], a.date(), actual, promise, actual - promise))
            if r["PINCODE"] == PIN and r["DELIVERY_PARTNER"] in SIX:
                orders[o] = (r["DELIVERY_PARTNER"], actual, promise)

    if not ids:
        ids = sorted((o for o in orders if o in op and op[o][0].date() == D0), key=lambda o: op[o][0])

    cfg = {}
    for r in csv.DictReader(open(P + f"raw-data/ops-speed-config-wh{WH}.csv", encoding="utf-8-sig", newline="")):
        cfg[(r["pincode"], r["delivery_partner"])] = int(r["delivery_days"])
    master = {}
    for r in csv.DictReader(open(P + "raw-data/tat-adherence-master.csv", encoding="utf-8-sig", newline="")):
        master[(r["Warehouse ID"], r["Delivery Partner"])] = float(r["Adherence Percentage"])

    cache_tat = {}

    def base(c, D, x):
        """TAT, adherence and data used for courier c on decision date D under the rule (no schedule adjustment)."""
        key = (c, D, x)
        if key in cache_tat:
            return cache_tat[key]

        def pool(geo, n):
            lo, hi = D - timedelta(days=n), D - timedelta(days=1)
            return [r for r in hist[c] if lo <= r[2] <= hi and in_geo(geo, r[1])]

        stop, rows = None, None
        if x is None:
            rows = pool("pincode", 7)
            stop = ("pincode", 7) if rows else None
        else:
            for k in LADDER:
                rr = pool(*k)
                if len(rr) >= x:
                    stop, rows = k, rr
                    break
            if stop is None:
                rr = pool("state", 28)
                if rr:
                    stop, rows = ("state", 28), rr
        if stop:
            tat, adh = tat_adherence(rows)
            res = (tat, adh, f"{stop[0]} {stop[1]}d ({len(rows)})")
        else:
            res = (cfg.get((PIN, c), DEFAULT_SUPPOSED_TAT), master[(WH, c)], "ops config")
        cache_tat[key] = res
        return res

    def allocate(D, clock, x):
        """Winner and the full score table. clock = the datetime whose time of day is tested against the cutoff."""
        table = {}
        for c in couriers:
            tat, adh, used = base(c, D, x)
            cut = sched.get((WH, c))
            adj = 1 if cut and clock and clock.strftime("%H:%M:%S") > cut else 0
            table[c] = (tat / (adh / 100) + adj, tat, adh, used, adj)
        best = min(v[0] for v in table.values())
        tied = [c for c in couriers if abs(table[c][0] - best) < 1e-9]
        winner = min(tied, key=PRIORITY.index)
        return winner, tied, table

    out = []
    print(f"Lane: warehouse {WH}, pincode {PIN}; orders placed {D0}; percentile {PCT}; tie-break {' > '.join(PRIORITY)}")
    for o in ids:
        if o not in orders or o not in op:
            print(f"\nOrder {o}: not found in both the shipment and order-placed files, skipped")
            continue
        placed, invoice, whp = op[o]
        actual_c, actual_days, real_promise = orders[o]
        if invoice is None or whp is None:
            print(f"\nOrder {o}: blank invoice or promised-warehouse time, skipped")
            continue
        Dp, Di = placed.date(), invoice.date()
        if not (date(2026, 7, 29) <= Dp <= date(2026, 9, 30) and date(2026, 7, 29) <= Di <= date(2026, 9, 30)):
            print(f"\nOrder {o}: decision date outside July to September window, skipped")
            continue
        print(f"\n=== Order {o}: placed {placed:%Y-%m-%d %H:%M}, promised WH processing {whp:%Y-%m-%d %H:%M}, invoiced {invoice:%Y-%m-%d %H:%M}; shipped by {actual_c}, actual {actual_days} days, real promise {real_promise}")
        for label, x in CASES:
            wp, tp, tabp = allocate(Dp, whp, x)
            wi, ti, tabi = allocate(Di, invoice, x)
            a_tat = base(actual_c, Dp, x)[0] if actual_c in couriers else None
            a_delay = actual_days - a_tat if a_tat is not None else None
            sim_promise = tabp[wp][1]
            same = wi == actual_c
            b_class = klass(actual_days - sim_promise) if same else "excluded"
            print(f"  {label:7s} placed-stage winner {wp}{' (tie ' + ','.join(tp) + ')' if len(tp) > 1 else ''}, promise {sim_promise}d | invoice-stage winner {wi}{' (tie ' + ','.join(ti) + ')' if len(ti) > 1 else ''} | A: {actual_c} projected {a_tat}d -> {klass(a_delay) if a_tat is not None else 'n/a'} | B: {b_class}")
            out.append([o, label, wp, sim_promise, wi, actual_c, a_tat, klass(a_delay) if a_tat is not None else "", b_class])

    with open(P + f"outputs/example-v2-step6-orders-{D0.isoformat()}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "rule", "placed_stage_winner", "simulated_promise_days", "invoice_stage_winner",
                    "shipping_courier", "A_projected_tat_days", "A_class", "B_class"])
        w.writerows(out)


if __name__ == "__main__":
    main()
