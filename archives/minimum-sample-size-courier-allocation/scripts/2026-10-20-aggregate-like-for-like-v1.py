# Purpose: like-for-like check of M2: on the same orders, adherence under today's promise vs under the promise of each x
# Serves: M1, M2 (check that the M2 gain is not just a change in which orders are reported)
# Reads: archives/minimum-sample-size-courier-allocation/outputs/sim-v1-orders.csv (from aggregate-simulation-v1.py)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/like-for-like-v1.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-like-for-like-v1.py
#
# Complete dates only (placed up to 24 Sep 2026). For each x: S = orders where M2 is reported under x (the invoice winner under x shipped the order).
# On S: adherence under x's promise (= M2 of x) and adherence under today's promise (M1 of today on the same orders), with average promises.
# Also the same split by the courier that shipped, and for the orders NOT in S (courier would change): M1 under x and under today.

import csv
import collections
from datetime import datetime, timedelta

P = "archives/minimum-sample-size-courier-allocation/outputs/"
BASE = datetime(2026, 7, 1)
CUT = datetime(2026, 9, 24, 23, 59)
GOOD = ("Early", "On-Time")


def main():
    today = {}
    rest = collections.defaultdict(dict)
    for r in csv.DictReader(open(P + "sim-v1-orders.csv", encoding="utf-8")):
        if BASE + timedelta(minutes=int(r["placed_min"])) > CUT or r["promise_days"] == "":
            continue
        rec = (r["shipping_courier"], int(r["promise_days"]), r["M1"], r["M2"])
        (today if r["rule"] == "today" else rest[r["rule"]])[r["order_id"]] = rec
    out = [["rule", "group", "courier_that_shipped", "orders", "adherence_pct_under_x_promise", "adherence_pct_under_today_promise", "avg_promise_x", "avg_promise_today"]]
    for rule in ("x=10", "x=15", "x=20"):
        groups = collections.defaultdict(list)
        for o, (c, p, m1, m2) in rest[rule].items():
            if o not in today:
                continue
            g = "M2 reported (courier unchanged)" if m2 != "" else "M2 not reported (courier would change)"
            groups[(g, "all")].append((p, m1, today[o][1], today[o][2]))
            groups[(g, c)].append((p, m1, today[o][1], today[o][2]))
        for (g, c), v in sorted(groups.items()):
            n = len(v)
            out.append([rule, g, c, n, round(100 * sum(1 for p, a, tp, b in v if a in GOOD) / n, 2), round(100 * sum(1 for p, a, tp, b in v if b in GOOD) / n, 2),
                        round(sum(p for p, a, tp, b in v) / n, 3), round(sum(tp for p, a, tp, b in v) / n, 3)])
    with open(P + "like-for-like-v1.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(out)
    for r in out:
        if r[2] == "all" or r[0] == "rule":
            print(r)


if __name__ == "__main__":
    main()
