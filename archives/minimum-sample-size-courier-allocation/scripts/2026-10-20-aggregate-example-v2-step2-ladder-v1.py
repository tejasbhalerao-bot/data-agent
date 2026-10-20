# Purpose: example step 2: order counts at each step of the data ladder for one lane and courier, and where the ladder stops for each x
# Serves: worked example only (pre-brief); no metric
# Reads: archives/minimum-sample-size-courier-allocation/raw-data/orders-2026-07.csv .. orders-2026-09.csv (shipment files)
#        archives/minimum-sample-size-courier-allocation/outputs/goi-pincode-map.csv (from structure-goi-pincode-map-v1.py)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/example-v2-step2-ladder-counts-<courier>-<D>.csv
#         archives/minimum-sample-size-courier-allocation/outputs/example-v2-step2-ladder-stops-<courier>-<D>.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-example-v2-step2-ladder-v1.py [courier] [YYYY-MM-DD]
#
# Defaults: warehouse 37, pincode 271604, courier 195, decision date D = 2026-09-21 (the order placed date).
# History = orders with a first delivery attempt in the N days before D (D-N .. D-1), N = 7, 14, 21, 28 (scope v3).
# Orders with a blank pickup time or an attempt before the pickup are excluded (as before).
# The ladder is a list of steps (geography, window), so a different order is a change of that list only (scope v6).
# Process flow v2: stop at the first step with at least x orders; if none, use the widest pool (state, 28 days) when
# it has more than 0 orders; use the ops config and TAT Adherence Master only when that pool has 0.

import csv
import glob
import sys
from datetime import datetime, date, timedelta

P = "archives/minimum-sample-size-courier-allocation/"
FMT = "%b %d, %Y, %I:%M %p"
WH, PIN = "37", "271604"
COURIER = sys.argv[1] if len(sys.argv) > 1 else "195"
D = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date(2026, 9, 21)
if not date(2026, 7, 29) <= D <= date(2026, 9, 30):
    sys.exit("Decision date must be between 2026-07-29 and 2026-09-30 (scope v5)")
XS = (10, 15, 20)
WINDOWS = (7, 14, 21, 28)
GEOS = ("pincode", "micro-cluster", "macro-cluster", "state")
LADDER = [(g, n) for g in GEOS for n in WINDOWS]  # time first, then geography


def main():
    gmap = {}
    with open(P + "outputs/goi-pincode-map.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            gmap[r["pincode"]] = (r["macro_cluster"], r["state"], r["district"], r["division"])
    me = gmap.get(PIN)
    if not me or not me[1]:
        sys.exit(f"Pincode {PIN} has no state, district and division in the GOI map")
    macro, state, district, division = me

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

    hist = []  # (pincode, attempt date) for WH x courier
    for fn in sorted(glob.glob(P + "raw-data/orders-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            if r["WAREHOUSE_ID"] != WH or r["DELIVERY_PARTNER"] != COURIER:
                continue
            try:
                a = datetime.strptime(r["DELIVERY_ATTEMPT_TIME"], FMT)
                p = datetime.strptime(r["PICKUP_TIME"], FMT)
            except ValueError:
                continue
            if a < p:
                continue
            hist.append((r["PINCODE"], a.date()))

    rows = []
    for geo, n in LADDER:
        lo, hi = D - timedelta(days=n), D - timedelta(days=1)
        cnt = sum(1 for pin, d in hist if lo <= d <= hi and in_geo(geo, pin))
        rows.append((geo, n, lo.isoformat(), hi.isoformat(), cnt))

    tag = f"{COURIER}-{D.isoformat()}"
    with open(P + f"outputs/example-v2-step2-ladder-counts-{tag}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["geography", "window_days", "attempts_from", "attempts_to", "orders"])
        w.writerows(rows)

    stops = []
    widest = rows[-1][4]
    for x in XS:
        hit = next((r for r in rows if r[4] >= x), None)
        if hit:
            stops.append([x, hit[0], hit[1], hit[4], "reached x"])
        elif widest > 0:
            stops.append([x, rows[-1][0], rows[-1][1], widest, "widest pool, below x"])
        else:
            stops.append([x, "ops config", "", 0, "no orders anywhere: ops config and TAT Adherence Master"])
    with open(P + f"outputs/example-v2-step2-ladder-stops-{tag}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["x", "geography", "window_days", "orders", "how"])
        w.writerows(stops)

    print(f"Warehouse {WH}, courier {COURIER}, order pincode {PIN}; decision date {D}")
    print(f"Pincode {PIN}: state {state}, district {district}, division {division}, macro-cluster {macro}")
    print(f"Orders for WH {WH} x courier {COURIER} in the shipment files (Jul-Sep, cleaned): {len(hist)}")
    print("geography, window, attempts from -> to, orders")
    for r in rows:
        print("  ", r[0], r[1], f"{r[2]} -> {r[3]}", r[4])
    print("Where the ladder stops:")
    for s in stops:
        print("  ", s)


if __name__ == "__main__":
    main()
