# Purpose: example step 1: the orders to simulate, and which couriers have history on this lane
# Serves: worked example only (pre-brief); no metric
# Reads: archives/minimum-sample-size-courier-allocation/raw-data/orders-2026-07.csv .. orders-2026-10.csv (Tejas's Metabase exports)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/example-step1-orders-2026-09-22.csv
#         archives/minimum-sample-size-courier-allocation/outputs/example-step1-lane-history-by-courier-2026-09-22.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-example-step1-orders-and-couriers-v1.py
#
# Example lane: warehouse 37 x pincode 271604. Decision date D = 2026-09-22 (scope v6).
# Couriers in the simulation: 185, 195, 225, 246, 247, 286 only (scope v4).
# Orders to simulate: orders on this warehouse x pincode picked up on D.
# Actual days = DATE(delivery_attempt_time) - DATE(pickup_time). No drop buffers (scope v3).
# History windows count orders whose delivery attempt falls in the N days before D (D-N .. D-1).

import csv
import glob
import collections
from datetime import datetime, date, timedelta

P = "archives/minimum-sample-size-courier-allocation/"
FMT = "%b %d, %Y, %I:%M %p"
D = date(2026, 9, 22)
WH, PIN = "37", "271604"
COURIERS = {"185", "195", "225", "246", "247", "286"}
WINDOWS = (7, 14, 21, 28)


def main():
    day_orders = []
    hist = collections.defaultdict(list)  # courier -> list of (attempt date, actual days)
    for fn in sorted(glob.glob(P + "raw-data/orders-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            if r["WAREHOUSE_ID"] != WH or r["PINCODE"] != PIN or r["DELIVERY_PARTNER"] not in COURIERS:
                continue
            try:
                a = datetime.strptime(r["DELIVERY_ATTEMPT_TIME"], FMT)
                p = datetime.strptime(r["PICKUP_TIME"], FMT)
            except ValueError:
                continue
            if a < p:
                continue
            days = (a.date() - p.date()).days
            if p.date() == D:
                day_orders.append([r["ORDER_ID"].replace(",", ""), r["DELIVERY_PARTNER"],
                                   p.strftime("%Y-%m-%d %H:%M"), a.strftime("%Y-%m-%d %H:%M"), days])
            hist[r["DELIVERY_PARTNER"]].append((a.date(), days))

    day_orders.sort(key=lambda x: x[2])
    with open(P + "outputs/example-step1-orders-2026-09-22.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "courier", "pickup_time", "delivery_attempt_time", "actual_days"])
        w.writerows(day_orders)

    rows = []
    for c in sorted(hist):
        counts = []
        for n in WINDOWS:
            lo, hi = D - timedelta(days=n), D - timedelta(days=1)
            counts.append(sum(1 for d, _ in hist[c] if lo <= d <= hi))
        rows.append([c] + counts)
    with open(P + "outputs/example-step1-lane-history-by-courier-2026-09-22.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["courier"] + [f"orders_{n}d" for n in WINDOWS])
        w.writerows(rows)

    print(f"Lane: warehouse {WH} x pincode {PIN}; decision date {D}")
    print(f"Orders picked up on {D} (six couriers): {len(day_orders)}")
    for o in day_orders:
        print("  ", o)
    print("History on this lane by courier (delivery attempts in the N days before D):")
    print("   courier", *[f"{n}d" for n in WINDOWS])
    for r in rows:
        print("  ", *r)


if __name__ == "__main__":
    main()
