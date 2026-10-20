# Purpose: is the state-level step of the ladder needed? Run the simulation with and without it and compare
# Serves: the choice of ladder (scope v6: the order of the ladder and its steps are suggestions to evaluate)
# Reads: the same inputs as aggregate-simulation-v2.py (imported as a module)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/state-fallback-test-v1.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-state-fallback-test-v1.py
#
# Orders placed 29 Jul to 24 Sep 2026 (complete dates). Variant "with state": the ladder as in the simulation (pincode, micro, macro, state; widest pool = state over 28 days).
# Variant "without state": pincode, micro, macro only; the widest pool is then the macro-cluster over 28 days; the ops config only when that pool has no order.
# Everything else is identical. For each x: matched orders (the invoice courier is the courier that shipped), adherence under x and today's adherence on the same matched orders,
# average promise under x and today's on the same orders, and the share of courier evaluations that resolve on the ops config or on the widest pool below x.
# The comparison between the two variants is also made on the orders matched under both.

import csv
import importlib.util

import numpy as np

P = "archives/minimum-sample-size-courier-allocation/"
SPEC = importlib.util.spec_from_file_location("sim", P + "scripts/2026-10-20-aggregate-simulation-v2.py")
sim = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sim)
XS = ("x=10", "x=15", "x=20")


def patch(geos):
    sim.GEOS = tuple(geos)
    sim.STEPS = [(g, n) for g in sim.GEOS for n in sim.WINDOWS]
    sim.NSTEP = len(sim.STEPS)
    sim.OPS, sim.WIDEST = sim.NSTEP, sim.NSTEP + 1
    sim.CODE_LABEL = [f"{g} {n}d" for g, n in sim.STEPS] + ["ops config", "widest pool (below x)"]


def run(od, data):
    L = sim.Ladder(data)
    N = len(od["oid"])
    res = {r: {k: np.zeros(N, np.int64) for k in ("pw", "pp", "iw")} for r in sim.RULES}
    rung = {r: np.zeros(sim.NSTEP + 2, np.int64) for r in sim.RULES}
    for s in range(0, N, 100000):
        sl = slice(s, min(N, s + 100000))
        out, rc = sim.simulate_block(L, od, sl)
        for r in sim.RULES:
            for k in res[r]:
                res[r][k][sl] = out[r][k]
            rung[r] += rc[r]
    return res, rung


def main():
    data = sim.load_all()
    ev, op = data["ev"], data["op"]
    oo = np.argsort(op["id"], kind="stable")
    for k in op:
        op[k] = op[k][oo]
    pos = np.minimum(np.searchsorted(op["id"], ev["oid"]), len(op["id"]) - 1)
    has_op = op["id"][pos] == ev["oid"]
    pl, inv, whp = op["pl"][pos], op["inv"][pos], op["whp"][pos]
    Dp = pl // 1440
    Di = np.where(inv >= 0, inv // 1440, -1)
    keep = has_op & (Dp >= sim.FIRST_D) & (Dp <= 85) & (inv >= 0) & (Di >= sim.FIRST_D) & (Di <= sim.LAST_D) & (whp >= 0)
    od = dict(oid=ev["oid"][keep], wh=ev["wh"][keep], cship=ev["c"][keep], pin=ev["pin"][keep], actual=ev["actual"][keep], promise=ev["promise"][keep],
              pl=pl[keep], inv=inv[keep], whp=whp[keep], Dp=Dp[keep], Di=Di[keep])
    N = len(od["oid"])
    full, rung_full = run(od, data)
    labels_full = list(sim.CODE_LABEL)
    patch(("pincode", "micro-cluster", "macro-cluster"))
    nos, rung_nos = run(od, data)
    labels_nos = list(sim.CODE_LABEL)
    out = [["rule", "variant", "orders", "matched orders", "matched share %", "adherence % today (same orders)", "adherence % under x", "change (points)", "average promise today", "average promise under x",
            "promise change (days)", "evaluations on the ops config %", "evaluations on the widest pool below x %"]]
    ok_real = od["actual"] <= od["promise"]
    for r in XS:
        masks = {}
        for name, R in (("with state", full), ("without state", nos)):
            m = (R[r]["pw"] >= 0) & (R[r]["iw"] == od["cship"])
            masks[name] = m
        both = masks["with state"] & masks["without state"]
        for name, R, rung, lab in (("with state", full, rung_full, labels_full), ("without state", nos, rung_nos, labels_nos)):
            for scope, m in (("own matched orders", masks[name]), ("orders matched under both variants", both)):
                n = int(m.sum())
                ok_x = od["actual"][m] <= R[r]["pp"][m]
                tot = rung[r].sum()
                out.append([r, f"{name}, {scope}", N, n, round(100 * n / N, 2), round(100 * ok_real[m].mean(), 2), round(100 * ok_x.mean(), 2), round(100 * (ok_x.mean() - ok_real[m].mean()), 2),
                            round(float(od["promise"][m].mean()), 3), round(float(R[r]["pp"][m].mean()), 3), round(float(R[r]["pp"][m].mean() - od["promise"][m].mean()), 3),
                            round(100 * rung[r][len(lab) - 2] / tot, 2), round(100 * rung[r][len(lab) - 1] / tot, 2)])
    with open(P + "outputs/state-fallback-test-v1.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(out)
    for r in out:
        print(r)


if __name__ == "__main__":
    main()
