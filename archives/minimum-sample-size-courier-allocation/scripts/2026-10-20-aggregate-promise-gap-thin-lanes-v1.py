# Purpose: on lanes where the replay falls back to the ops config (no order in the last 7 days on the shipper's pincode lane), what does the real promise look like?
# Serves: M4, M8 (supporting check for the replay baseline)
# Reads: the same inputs as aggregate-simulation-v2.py (imported as a module)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/promise-gap-thin-lanes-v1.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-promise-gap-thin-lanes-v1.py
#
# Orders placed 1 to 15 Sep 2026, the courier that shipped. Group by the number of orders on its own pincode lane in the 7 days before the order placed date (0, 1 to 4, 5 to 19, 20 or more).
# For each group: the replay's lane TAT (pincode 7 days when it has orders, otherwise the ops config), the ops config TAT, and the real promise: share equal, share longer, share shorter, mean real minus replay.
# For the group with no order, also: share where the real promise equals the ops config TAT, and the mean real minus ops config.

import csv
import importlib.util

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
    res, counts = L.evaluate(u)
    tat, adh, code = res["today"]
    n0 = counts[:, 0][inv]
    t = tat[inv]
    # ops config TAT for every order's own lane
    whe = sim.eff(wh)
    key_ops = (whe * sim.NC + c) * sim.M + pin
    p2 = np.minimum(np.searchsorted(data["cfg_keys"], key_ops), len(data["cfg_keys"]) - 1)
    found = data["cfg_keys"][p2] == key_ops
    ops = np.where(found, data["cfg_days"][p2], sim.DEFAULT_SUPPOSED_TAT)
    out = [["orders on the shipper's pincode lane in the 7 days", "orders", "replay TAT equals real %", "real longer %", "real shorter %", "mean real minus replay (days)", "ops config equals real %", "mean real minus ops config (days)"]]
    for name, m in (("0", n0 == 0), ("1 to 4", (n0 >= 1) & (n0 <= 4)), ("5 to 19", (n0 >= 5) & (n0 <= 19)), ("20 or more", n0 >= 20)):
        d = real[m] - t[m]
        o = real[m] - ops[m]
        out.append([name, int(m.sum()), round(100 * (d == 0).mean(), 2), round(100 * (d > 0).mean(), 2), round(100 * (d < 0).mean(), 2), round(float(d.mean()), 3),
                    round(100 * (o == 0).mean(), 2), round(float(o.mean()), 3)])
    with open(P + "outputs/promise-gap-thin-lanes-v1.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(out)
    for r in out:
        print(r)


if __name__ == "__main__":
    main()
