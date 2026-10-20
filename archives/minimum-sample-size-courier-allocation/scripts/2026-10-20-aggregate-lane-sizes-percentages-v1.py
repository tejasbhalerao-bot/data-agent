# Purpose: the lane-size and rung counts as a percentage of the whole
# Serves: M5 (data used) and the sizing of x
# Reads: archives/minimum-sample-size-courier-allocation/outputs/lane-sizes-and-rungs-v1.csv (from aggregate-lane-sizes-and-rungs-v1.py)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/lane-sizes-percentages-v1.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-lane-sizes-percentages-v1.py
#
# Part A: each bin of orders in the last 7 days as a share of the combinations in its universe (average across the 58 decision dates).
# Part C: orders by the rung of the winning courier at order placed, as a share of the orders that have a winner under that rule.

import csv

P = "archives/minimum-sample-size-courier-allocation/outputs/"


def main():
    rows = list(csv.DictReader(open(P + "lane-sizes-and-rungs-v1.csv", encoding="utf-8")))
    out = [["part", "view", "item", "count", "percent of the whole"]]
    universe = {}
    for r in rows:
        if r["part"] == "A" and r["item"] == "combinations in the universe":
            universe[r["view"]] = float(r["value (average over dates in A)"])
    for r in rows:
        if r["part"] == "A" and r["item"] != "combinations in the universe":
            v = float(r["value (average over dates in A)"])
            out.append(["A", r["view"], r["item"], int(v), round(100 * v / universe[r["view"]], 2)])
    wr = [r for r in rows if r["part"] == "C" and r["view"].startswith("orders by the rung")]
    tot = {}
    for r in wr:
        rule = r["item"].split(": ")[0]
        tot[rule] = tot.get(rule, 0) + float(r["value (average over dates in A)"])
    for r in wr:
        rule = r["item"].split(": ")[0]
        v = float(r["value (average over dates in A)"])
        out.append(["C", f"orders by winner rung, {rule}", r["item"].split(": ")[1], int(v), round(100 * v / tot[rule], 2)])
    out.append(["C", "orders with a winner", "x=10", int(tot["x=10"]), ""])
    with open(P + "lane-sizes-percentages-v1.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(out)
    for r in out:
        print(r)


if __name__ == "__main__":
    main()
