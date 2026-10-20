# Purpose: list candidate warehouse x pincode x courier lanes for the one-pincode worked example
# Serves: worked example only (pre-brief); no metric
# Reads: archives/minimum-sample-size-courier-allocation/raw-data/orders-2026-07.csv .. orders-2026-10.csv (Tejas's Metabase exports)
#        archives/minimum-sample-size-courier-allocation/outputs/goi-pincode-map.csv (from structure-goi-pincode-map-v1.py)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/example-lane-candidates.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-example-lane-candidates-v1.py
#
# Decision date D = 2026-10-13. Orders to simulate: picked up on D. History: orders whose delivery
# attempt falls in the N days before D (D-N .. D-1), N = 7, 14, 21, 28, per scope v3.
# Candidate lane: 1 to 4 history orders in 7 days, at least 2 orders picked up on D, and a micro-cluster
# with at least 15 history orders in 7 days (so the ladder has something to widen to).
# Orders with a blank pickup time or an attempt before the pickup are excluded and counted.

import csv
import glob
import collections
from datetime import datetime, date, timedelta

P = "archives/minimum-sample-size-courier-allocation/"
FMT = "%b %d, %Y, %I:%M %p"
D = date(2026, 10, 13)
WINDOWS = (7, 14, 21, 28)


def main():
    gmap = {}
    with open(P + "outputs/goi-pincode-map.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            gmap[r["pincode"]] = (r["macro_cluster"], r["state"], r["district"], r["division"])

    lane = collections.defaultdict(collections.Counter)    # (wh, pin, dp) -> attempt date -> n
    micro = collections.defaultdict(collections.Counter)   # (wh, state, district, division, dp)
    macro = collections.defaultdict(collections.Counter)   # (wh, macro, dp)
    state = collections.defaultdict(collections.Counter)   # (wh, state, dp)
    picked = collections.Counter()                         # lane -> orders picked up on D
    excluded = 0
    rows = 0
    for fn in sorted(glob.glob(P + "raw-data/orders-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            rows += 1
            try:
                a = datetime.strptime(r["DELIVERY_ATTEMPT_TIME"], FMT)
                p = datetime.strptime(r["PICKUP_TIME"], FMT)
            except ValueError:
                excluded += 1
                continue
            if a < p:
                excluded += 1
                continue
            wh, pin, dp = r["WAREHOUSE_ID"], r["PINCODE"], r["DELIVERY_PARTNER"]
            ad = a.date()
            lane[(wh, pin, dp)][ad] += 1
            g = gmap.get(pin)
            if g and g[1]:
                micro[(wh, g[1], g[2], g[3], dp)][ad] += 1
                state[(wh, g[1], dp)][ad] += 1
            if g:
                macro[(wh, g[0], dp)][ad] += 1
            if p.date() == D:
                picked[(wh, pin, dp)] += 1

    def count(counter, n):
        lo = D - timedelta(days=n)
        hi = D - timedelta(days=1)
        return sum(v for d, v in counter.items() if lo <= d <= hi)

    out = []
    for key, npick in picked.items():
        if npick < 2:
            continue
        wh, pin, dp = key
        g = gmap.get(pin)
        if not g or not g[1]:
            continue
        l = [count(lane[key], n) for n in WINDOWS]
        if not 1 <= l[0] <= 4:
            continue
        mi = [count(micro[(wh, g[1], g[2], g[3], dp)], n) for n in WINDOWS]
        if mi[0] < 15:
            continue
        ma = [count(macro[(wh, g[0], dp)], n) for n in WINDOWS]
        st = [count(state[(wh, g[1], dp)], n) for n in WINDOWS]
        out.append([wh, pin, dp, npick, g[1], g[2], g[3], g[0]] + l + mi + ma + st)

    out.sort(key=lambda r: (-r[3], r[0], r[1], r[2]))
    head = ["warehouse_id", "pincode", "delivery_partner", "picked_up_on_D", "state", "district", "division", "macro"]
    for lvl in ("lane", "micro", "macro", "state"):
        head += [f"{lvl}_{n}d" for n in WINDOWS]
    with open(P + "outputs/example-lane-candidates.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(head)
        w.writerows(out)

    print("order rows read:", rows, "| excluded (blank pickup or attempt before pickup):", excluded)
    print("decision date D:", D)
    print("lanes with >=2 orders picked up on D:", sum(1 for v in picked.values() if v >= 2))
    print("candidate lanes:", len(out))
    for r in out[:12]:
        print(dict(zip(head, r)))


if __name__ == "__main__":
    main()
