# Purpose: on the same orders, adherence under the real promise vs under the promise of each x, split by whether the courier would change
# Serves: M1, M2, M4 (reads the x rules against reality order by order)
# Reads: archives/minimum-sample-size-courier-allocation/outputs/sim-v2-orders.csv (from aggregate-simulation-v2.py)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/like-for-like-real-v2.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-like-for-like-real-v2.py
#
# Orders placed 29 Jul to 24 Sep. For each x and each group (invoice winner under x is the courier that shipped / is a different courier):
# adherence under the real promise (actual days vs PROMISE_TAT), adherence under x's promise (the simulated promise at order placed), and the average of both promises.
# In the "courier would change" group the outcome (actual days) belongs to the courier that really shipped, not to the courier that x picks.

import csv
import collections
from datetime import datetime, timedelta

P = "archives/minimum-sample-size-courier-allocation/outputs/"
BASE = datetime(2026, 7, 1)
CUT = datetime(2026, 9, 24, 23, 59)


def main():
    acc = collections.defaultdict(lambda: [0, 0, 0, 0, 0])  # orders, ok real, ok x, sum real promise, sum x promise
    for r in csv.DictReader(open(P + "sim-v2-orders.csv", encoding="utf-8")):
        if r["rule"] == "today" or r["promise_days"] == "" or BASE + timedelta(minutes=int(r["placed_min"])) > CUT:
            continue
        actual, real, sim = int(r["actual_days"]), int(r["real_promise_days"]), int(r["promise_days"])
        g = "courier unchanged" if r["invoice_winner"] == r["shipping_courier"] else "courier would change"
        for key in ((r["rule"], g), (r["rule"], "all")):
            a = acc[key]
            a[0] += 1
            a[1] += actual <= real
            a[2] += actual <= sim
            a[3] += real
            a[4] += sim
    out = [["rule", "group", "orders", "adherence % under the real promise", "adherence % under x's promise", "average real promise (days)", "average promise under x (days)", "adherence change, x minus real (points)", "promise change, x minus real (days)"]]
    for (rule, g), a in sorted(acc.items()):
        out.append([rule, g, a[0], round(100 * a[1] / a[0], 2), round(100 * a[2] / a[0], 2), round(a[3] / a[0], 3), round(a[4] / a[0], 3),
                    round(100 * (a[2] - a[1]) / a[0], 2), round((a[4] - a[3]) / a[0], 3)])
    with open(P + "like-for-like-real-v2.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(out)
    for r in out:
        print(r)


if __name__ == "__main__":
    main()
