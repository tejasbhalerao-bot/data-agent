# Purpose: where does the gap between the replayed promise and the real promise come from?
# Serves: M4, M8 (supporting check for the replay baseline)
# Reads: the same inputs as aggregate-simulation-v2.py (imported as a module)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/promise-gap-v1.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-promise-gap-v1.py
#
# Orders placed 1 to 15 Sep 2026. For the courier that actually shipped each order, take today's rule at the order placed date (its own pincode, 7 days).
# Keep orders whose pool holds at least 20 orders, so thin data is not the cause. Compare the lane TAT the replay gives with the real promise (PROMISE_TAT):
#   (1) for percentile values 0.80, 0.85, 0.90, 0.95: share equal, share where the real promise is longer, mean of real minus replay (days);
#   (2) at 0.85, by the weekday of the placed date: share where the real promise is longer and the mean difference.
# If a promise buffer (Sunday, holiday) is added in the real system, the real promise is longer on some weekdays and the difference concentrates there.

import csv
import importlib.util
from datetime import date, timedelta

import numpy as np

P = "archives/minimum-sample-size-courier-allocation/"
SPEC = importlib.util.spec_from_file_location("sim", P + "scripts/2026-10-20-aggregate-simulation-v2.py")
sim = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sim)


def main():
    data = sim.load_all()
    ev, op = data["ev"], data["op"]
    oo = np.argsort(op["id"], kind="stable")
    for k in op:
        op[k] = op[k][oo]
    pos = np.minimum(np.searchsorted(op["id"], ev["oid"]), len(op["id"]) - 1)
    has_op = op["id"][pos] == ev["oid"]
    Dp = op["pl"][pos] // 1440
    keep = has_op & (Dp >= 62) & (Dp <= 76)
    wh, c, pin, D, real = ev["wh"][keep], ev["c"][keep], ev["pin"][keep], Dp[keep], ev["promise"][keep]
    combo = ((wh * sim.NC + c) * sim.M + pin) * 128 + D
    u, inv = np.unique(combo, return_inverse=True)
    L = sim.Ladder(data)
    base = date(2026, 7, 1)
    wd = np.array([(base + timedelta(days=int(d))).weekday() for d in D])
    out = [["percentile", "orders with a pool of at least 20", "real promise equals replay %", "real longer than replay %", "real shorter than replay %", "mean real minus replay (days)"]]
    by_wd = None
    for pct in (0.80, 0.85, 0.90, 0.95):
        sim.PCT = pct
        res, counts = L.evaluate(u)
        tat, adh, code = res["today"]
        big = (counts[:, 0] >= 20)[inv]
        t = tat[inv]
        d = real[big] - t[big]
        n = int(big.sum())
        out.append([pct, n, round(100 * (d == 0).mean(), 2), round(100 * (d > 0).mean(), 2), round(100 * (d < 0).mean(), 2), round(float(d.mean()), 3)])
        if pct == 0.85:
            by_wd = []
            for k, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
                m = big & (wd == k)
                dd = real[m] - t[m]
                by_wd.append([name, int(m.sum()), round(100 * (dd > 0).mean(), 2), round(float(dd.mean()), 3)])
    out.append([])
    out.append(["weekday of placed date (percentile 0.85)", "orders", "real longer than replay %", "mean real minus replay (days)"])
    out += by_wd
    with open(P + "outputs/promise-gap-v1.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(out)
    for r in out:
        print(r)


if __name__ == "__main__":
    main()
