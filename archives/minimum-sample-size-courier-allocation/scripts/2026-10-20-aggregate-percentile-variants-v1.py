# Purpose: which percentile value and definition reproduces the real promise best on lanes with plenty of orders?
# Serves: M4, M8 (supporting check for the replay baseline)
# Reads: the same inputs as aggregate-simulation-v2.py (imported as a module)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/percentile-variants-v1.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-percentile-variants-v1.py
#
# Orders placed 1 to 15 Sep 2026. For the courier that actually shipped each order, take the orders on its own pincode lane with a first delivery attempt in the 7 days
# before the order placed date. Keep pools of at least 20 orders. Lane TAT = ROUNDUP of the percentile of actual days, for several percentile values and definitions
# (linear interpolation, nearest rank, lower, higher), and compare with the real promise (PROMISE_TAT): share equal, share where the real promise is longer, mean of real minus replay.

import csv
import importlib.util
import math

import numpy as np

P = "archives/minimum-sample-size-courier-allocation/"
SPEC = importlib.util.spec_from_file_location("sim", P + "scripts/2026-10-20-aggregate-simulation-v2.py")
sim = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sim)


def tat(vals, p, how):
    s = np.sort(vals)
    n = len(s)
    if how == "linear":
        pos = p * (n - 1)
        lo, hi = math.floor(pos), math.ceil(pos)
        return math.ceil(s[lo] + (s[hi] - s[lo]) * (pos - lo))
    if how == "nearest rank":
        return int(s[max(0, math.ceil(p * n) - 1)])
    if how == "lower":
        return int(s[math.floor(p * (n - 1))])
    return int(s[math.ceil(p * (n - 1))])


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
    base = u // 128
    Du = u % 128
    S, perm = L.S["pincode"], L.perm["pincode"]
    lo = np.searchsorted(S, base * 128 + (Du - 7), side="left")
    hi = np.searchsorted(S, base * 128 + (Du - 1), side="right")
    pools = []
    for i in range(len(u)):
        if hi[i] - lo[i] >= 20:
            pools.append((i, L.act[perm[lo[i]:hi[i]]]))
    ok = {i: k for k, (i, _) in enumerate(pools)}
    sel = np.array([inv_i in ok for inv_i in inv])
    realsel = real[sel]
    idx_in_pools = np.array([ok[i] for i in inv[sel]])
    out = [["definition", "percentile", "orders", "real promise equals replay %", "real longer %", "real shorter %", "mean real minus replay (days)"]]
    for how in ("linear", "nearest rank", "lower", "higher"):
        for p in (0.70, 0.75, 0.80, 0.85, 0.90):
            tv = np.array([tat(a, p, how) for _, a in pools])
            d = realsel - tv[idx_in_pools]
            out.append([how, p, int(sel.sum()), round(100 * (d == 0).mean(), 2), round(100 * (d > 0).mean(), 2), round(100 * (d < 0).mean(), 2), round(float(d.mean()), 3)])
    with open(P + "outputs/percentile-variants-v1.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(out)
    for r in out:
        print(r)


if __name__ == "__main__":
    main()
