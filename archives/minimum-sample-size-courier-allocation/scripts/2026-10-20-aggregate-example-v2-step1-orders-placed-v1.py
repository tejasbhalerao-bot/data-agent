# Purpose: example step 1 (process flow v2): the orders placed on the decision date on the example lane
# Serves: worked example only (pre-brief); no metric
# Reads: archives/minimum-sample-size-courier-allocation/raw-data/op-2026-07.csv .. op-2026-09.csv (order placed files)
#        archives/minimum-sample-size-courier-allocation/raw-data/orders-2026-07.csv .. orders-2026-09.csv (shipment files)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/example-v2-step1-orders-2026-09-22.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-example-v2-step1-orders-placed-v1.py
#
# Example lane: warehouse 37 x pincode 271604. Decision date D = 2026-09-22 (order placed date).
# An order is "placed on D" when its digitised timestamp falls on D (process flow v2).
# Orders with no order-placed row are excluded (Tejas). Only couriers 185, 195, 225, 246, 247, 286 are kept (scope v4).
# Actual days = DATE(first delivery attempt) - DATE(pickup). The invoice date is the invoice-create timestamp.

import csv
import glob
from datetime import datetime, date

P = "archives/minimum-sample-size-courier-allocation/"
FMT = "%b %d, %Y, %I:%M %p"
D = date(2026, 9, 22)
WH, PIN = "37", "271604"
SIX = {"185", "195", "225", "246", "247", "286"}


def ts(v):
    try:
        return datetime.strptime(v, FMT)
    except (ValueError, TypeError):
        return None


def oid(v):
    return v.replace(",", "")


def main():
    placed = {}
    for fn in sorted(glob.glob(P + "raw-data/op-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            d = ts(r["DIGITISED_TS"])
            if d and d.date() == D:
                placed[oid(r["ORDER_ID"])] = (d, ts(r["INVOICE_CREATE_TS"]))

    rows = []
    in_lane = 0
    no_op = 0
    other_courier = 0
    for fn in sorted(glob.glob(P + "raw-data/orders-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            if r["WAREHOUSE_ID"] != WH or r["PINCODE"] != PIN:
                continue
            o = oid(r["ORDER_ID"])
            if o not in placed:
                continue
            in_lane += 1
            if r["DELIVERY_PARTNER"] not in SIX:
                other_courier += 1
                continue
            d, inv = placed[o]
            pk, at = ts(r["PICKUP_TIME"]), ts(r["DELIVERY_ATTEMPT_TIME"])
            days = (at.date() - pk.date()).days if pk and at else ""
            rows.append([o, d.strftime("%Y-%m-%d %H:%M"), inv.strftime("%Y-%m-%d %H:%M") if inv else "",
                         r["DELIVERY_PARTNER"], pk.strftime("%Y-%m-%d %H:%M") if pk else "",
                         at.strftime("%Y-%m-%d %H:%M") if at else "", days, r["PROMISE_TAT"]])

    rows.sort(key=lambda x: x[1])
    with open(P + "outputs/example-v2-step1-orders-2026-09-22.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "placed_at", "invoice_at", "shipping_courier", "pickup_at",
                    "first_attempt_at", "actual_days", "promise_days"])
        w.writerows(rows)

    print(f"Order-placed rows with digitised date {D}: {len(placed)}")
    print(f"Of those, shipped from WH {WH} to pincode {PIN} (and found in the shipment files): {in_lane}")
    print(f"  dropped because the shipping courier is outside the six: {other_courier}")
    print(f"  kept: {len(rows)}")
    for r in rows:
        print("  ", r)


if __name__ == "__main__":
    main()
