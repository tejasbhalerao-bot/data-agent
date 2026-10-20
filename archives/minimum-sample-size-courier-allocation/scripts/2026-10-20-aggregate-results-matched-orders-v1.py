# Purpose: the results of the simulation on matched orders: adherence and promise under x against today, on the same orders
# Serves: M1 adherence, M2 promise, M3 share of orders matched (results document)
# Reads: archives/minimum-sample-size-courier-allocation/outputs/sim-v2-orders.csv (from aggregate-simulation-v2.py)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/results-matched-orders-v1.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-results-matched-orders-v1.py
#
# A matched order is one where the courier the rule allocates at invoice is the courier that really shipped it.
# Today = reality: real promise (PROMISE_TAT) against actual days, on the same orders. x = the simulated promise (the courier allocated at order placed) against actual days.
# Date scopes: "complete dates" = orders placed 29 Jul to 24 Sep 2026 (headline); "all dates" = 29 Jul to 30 Sep.
# Groups: each x on its own matched orders; the common set (matched under all of x = 10, 15 and 20); by courier that shipped; by warehouse.

import csv
import collections
from datetime import datetime, timedelta

P = "archives/minimum-sample-size-courier-allocation/outputs/"
BASE = datetime(2026, 7, 1)
CUT = datetime(2026, 9, 24, 23, 59)
XS = ("x=10", "x=15", "x=20")
GOOD = ("Early", "On-Time")


def stats(recs):
    n = len(recs)
    if not n:
        return None
    ok_today = sum(1 for r in recs if r["actual"] <= r["real"])
    ok_x = sum(1 for r in recs if r["m2"] in GOOD)
    lo = sum(1 for r in recs if r["pp"] > r["real"])
    sh = sum(1 for r in recs if r["pp"] < r["real"])
    return [n, round(100 * ok_today / n, 2), round(100 * ok_x / n, 2), round(100 * (ok_x - ok_today) / n, 2),
            round(sum(r["real"] for r in recs) / n, 3), round(sum(r["pp"] for r in recs) / n, 3),
            round(sum(r["pp"] - r["real"] for r in recs) / n, 3), round(100 * lo / n, 2), round(100 * sh / n, 2), round(100 * (n - lo - sh) / n, 2)]


def main():
    data = {x: {} for x in XS}
    for r in csv.DictReader(open(P + "sim-v2-orders.csv", encoding="utf-8")):
        if r["rule"] not in XS or r["promise_days"] == "":
            continue
        placed = BASE + timedelta(minutes=int(r["placed_min"]))
        data[r["rule"]][r["order_id"]] = dict(complete=placed <= CUT, actual=int(r["actual_days"]), real=int(r["real_promise_days"]), pp=int(r["promise_days"]),
                                              courier=r["shipping_courier"], wh=r["warehouse"], m2=r["M2"])
    head = ["scope", "group", "cut", "orders in group", "matched orders", "matched share %", "adherence % today (same orders)", "adherence % under x", "adherence change (points)",
            "average promise today (days)", "average promise under x (days)", "promise change (days)", "x promise longer than today %", "x promise shorter than today %", "x promise equal to today %"]
    out = [head]
    for scope in ("complete dates", "all dates"):
        sel = {x: {o: v for o, v in data[x].items() if v["complete"] or scope == "all dates"} for x in XS}
        common = set(o for o, v in sel["x=10"].items() if v["m2"] != "")
        for x in XS[1:]:
            common &= set(o for o, v in sel[x].items() if v["m2"] != "")
        for x in XS:
            allo = sel[x]
            matched = [v for v in allo.values() if v["m2"] != ""]
            s = stats(matched)
            out.append([scope, x, "all", len(allo), s[0], round(100 * s[0] / len(allo), 2)] + s[1:])
            for key in ("courier", "wh"):
                for k in sorted({v[key] for v in matched}, key=lambda z: int(z)):
                    sub = [v for v in matched if v[key] == k]
                    allk = [v for v in allo.values() if v[key] == k]
                    ss = stats(sub)
                    out.append([scope, x, ("shipping courier " if key == "courier" else "warehouse ") + k, len(allk), ss[0], round(100 * ss[0] / len(allk), 2)] + ss[1:])
            cm = [sel[x][o] for o in common]
            s = stats(cm)
            out.append([scope, x, "common set (matched under all three x)", len(allo), s[0], round(100 * s[0] / len(allo), 2)] + s[1:])
    with open(P + "results-matched-orders-v1.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(out)
    for r in out:
        if r[0] == "complete dates" and (r[2] in ("all",) or r[2].startswith("common") or (r[1] == "x=20" and r[2].startswith("shipping courier"))):
            print(r)


if __name__ == "__main__":
    main()
