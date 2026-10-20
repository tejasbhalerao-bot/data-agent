# Purpose: "today" taken from reality (the courier that shipped, the real promise) next to the replay of today's rule and the x rules
# Serves: M1, M2, M3, M4, M6
# Reads: archives/minimum-sample-size-courier-allocation/outputs/sim-v2-orders.csv (from aggregate-simulation-v2.py)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/today-real-baseline-v1.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-today-real-baseline-v1.py
#
# Orders placed 29 Jul to 24 Sep (complete dates). "Today (real)": the invoice courier is the courier that shipped the order and the promise is the real
# promise (PROMISE_TAT), so M2 equals M1 and M3 is 0 by construction. "Today (replay)" and the x rules are the simulation. All rows are computed on the same
# orders (those with a candidate courier under every rule) so that the rows are comparable.

import csv
import collections
from datetime import datetime, timedelta

P = "archives/minimum-sample-size-courier-allocation/outputs/"
BASE = datetime(2026, 7, 1)
CUT = datetime(2026, 9, 24, 23, 59)
GOOD = ("Early", "On-Time")
RULES = ("today", "x=10", "x=15", "x=20")


def main():
    rec = {r: {} for r in RULES}
    for r in csv.DictReader(open(P + "sim-v2-orders.csv", encoding="utf-8")):
        if BASE + timedelta(minutes=int(r["placed_min"])) > CUT or r["promise_days"] == "":
            continue
        rec[r["rule"]][r["order_id"]] = (int(r["actual_days"]), int(r["real_promise_days"]), int(r["promise_days"]), r["shipping_courier"], r["invoice_winner"], r["M1"], r["M2"])
    common = set(rec["today"])
    for r in RULES[1:]:
        common &= set(rec[r])
    n = len(common)
    out = [["row", "orders", "M1 adherence %", "M2 adherence %", "M3 orders not reported %", "M4 average promise (days)",
            "promise longer than real %", "promise shorter than real %", "promise equal to real %"]]
    real_ok = sum(1 for o in common if rec["today"][o][0] <= rec["today"][o][1])
    real_avg = sum(rec["today"][o][1] for o in common) / n
    out.append(["today (real)", n, round(100 * real_ok / n, 3), round(100 * real_ok / n, 3), 0.0, round(real_avg, 3), 0.0, 0.0, 100.0])
    for r in RULES:
        d = rec[r]
        m1 = sum(1 for o in common if d[o][5] in GOOD)
        rep = [o for o in common if d[o][6] != ""]
        m2 = sum(1 for o in rep if d[o][6] in GOOD)
        avg = sum(d[o][2] for o in common) / n
        lo = sum(1 for o in common if d[o][2] > d[o][1])
        sh = sum(1 for o in common if d[o][2] < d[o][1])
        eq = n - lo - sh
        name = "today (replay)" if r == "today" else r
        out.append([name, n, round(100 * m1 / n, 3), round(100 * m2 / len(rep), 3), round(100 * (n - len(rep)) / n, 3), round(avg, 3),
                    round(100 * lo / n, 2), round(100 * sh / n, 2), round(100 * eq / n, 2)])
    mix = collections.Counter(rec["today"][o][3] for o in common)
    out.append([])
    out.append(["courier that actually shipped (today, real) mix %"] + [f"{c}: {round(100 * v / n, 2)}" for c, v in sorted(mix.items())])
    with open(P + "today-real-baseline-v1.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(out)
    for r in out:
        print(r)


if __name__ == "__main__":
    main()
