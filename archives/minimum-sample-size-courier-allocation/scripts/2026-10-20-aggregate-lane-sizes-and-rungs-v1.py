# Purpose: how thin are the lanes, and at which rung do orders resolve? (questions about the data built during the simulation)
# Serves: M5 (data used), and the sizing of x
# Reads: the same inputs as aggregate-simulation-v2.py (imported as a module)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/lane-sizes-and-rungs-v1.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-lane-sizes-and-rungs-v1.py
#
# Decision dates 29 Jul to 24 Sep 2026 (complete dates). "Last 7 days" = delivery attempts in the 7 days before the decision date.
# A. Universe view. Lanes = warehouse x pincode x courier combinations in the ops config for the six couriers where the courier serves the pincode.
#    WH x pincode = the distinct warehouse x pincode pairs among those lanes (orders of any of the six couriers count). For every decision date, how many have
#    0, 1-4, 5-9, 10-14, 15-19, 20+ orders in the last 7 days; reported as the average over the 58 dates, the minimum and maximum, and as of 24 Sep.
# B. Evaluation view. Every courier evaluation at order placed in the simulation (order x candidate courier): the number of orders on the pincode lane in the last 7 days.
# C. Rungs. Courier evaluations at order placed that resolve at each ladder step (time x geography), per value of x; and orders by the step their winning courier's TAT resolved at.

import csv
import importlib.util

import numpy as np

P = "archives/minimum-sample-size-courier-allocation/"
SPEC = importlib.util.spec_from_file_location("sim", P + "scripts/2026-10-20-aggregate-simulation-v2.py")
sim = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sim)
BINS = [(0, 0, "0"), (1, 4, "1 to 4"), (5, 9, "5 to 9"), (10, 14, "10 to 14"), (15, 19, "15 to 19"), (20, 10 ** 9, "20 or more")]


def binned(counts):
    return [int(((counts >= lo) & (counts <= hi)).sum()) for lo, hi, _ in BINS]


def main():
    data = sim.load_all()
    L = sim.Ladder(data)
    M, NC = sim.M, sim.NC
    out = []

    # A. universe
    keys = data["cfg_keys"]
    pin = keys % M
    wc = keys // M
    wh = wc // NC
    c = wc % NC
    serviceable = data["serv"][c, pin]
    lane = keys[serviceable]
    wp = np.unique((lane // M // NC) * M + (lane % M))
    S_lane = L.S["pincode"]
    wp_ev = np.sort((L.wh * M + L.pin) * 128 + L.dd)
    rows_lane, rows_wp = [], []
    for D in range(sim.FIRST_D, 86):
        lo = np.searchsorted(S_lane, lane * 128 + (D - 7), side="left")
        hi = np.searchsorted(S_lane, lane * 128 + (D - 1), side="right")
        rows_lane.append(binned(hi - lo))
        lo = np.searchsorted(wp_ev, wp * 128 + (D - 7), side="left")
        hi = np.searchsorted(wp_ev, wp * 128 + (D - 1), side="right")
        rows_wp.append(binned(hi - lo))
    for name, rows, total in (("lane: warehouse x pincode x courier", rows_lane, len(lane)), ("warehouse x pincode (any of the six couriers)", rows_wp, len(wp))):
        arr = np.array(rows)
        out.append(["A", name, "combinations in the universe", total, "", "", ""])
        for j, (_, _, lab) in enumerate(BINS):
            out.append(["A", name, f"orders in the last 7 days: {lab}", round(float(arr[:, j].mean())), int(arr[:, j].min()), int(arr[:, j].max()), int(arr[-1, j])])
        less = {k: arr[:, :j].sum(axis=1) for k, j in (("less than 5", 2), ("less than 10", 3), ("less than 15", 4), ("less than 20", 5))}
        for k, v in less.items():
            out.append(["A", name, f"orders in the last 7 days: {k}", round(float(v.mean())), int(v.min()), int(v.max()), int(v[-1])])

    # orders in scope (placed up to 24 Sep)
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
    hist_eval = np.zeros(len(BINS), np.int64)
    rung = {r: np.zeros(sim.NSTEP + 2, np.int64) for r in sim.RULES}
    win_rung = {r: np.zeros(sim.NSTEP + 2, np.int64) for r in sim.RULES}
    n_orders_with_winner = {r: 0 for r in sim.RULES}
    for s in range(0, N, 100000):
        sl = slice(s, min(N, s + 100000))
        res, rc = sim.simulate_block(L, od, sl)
        for r in sim.RULES:
            rung[r] += rc[r]
            pc = res[r]["pcode"]
            pc = pc[res[r]["pw"] >= 0]
            win_rung[r] += np.bincount(pc, minlength=sim.NSTEP + 2)
            n_orders_with_winner[r] += len(pc)
        # B. pincode-7d count of each candidate evaluation at order placed
        w, p_ = od["wh"][sl], od["pin"][sl]
        whe = sim.eff(w)
        cand = np.zeros((len(w), NC), bool)
        for j in range(NC):
            cand[:, j] = data["serv"][j][p_] & data["cfg_pair"][whe, j] & ~np.isnan(data["master"][whe, j])
        Dd = od["Dp"][sl]
        combos, owner = [], []
        for j in range(NC):
            ii = np.nonzero(cand[:, j])[0]
            combos.append((((w[ii] * NC + j) * M + p_[ii]) * 128 + Dd[ii]))
        allc = np.concatenate(combos)
        u, invx = np.unique(allc, return_inverse=True)
        _, counts = L.evaluate(u)
        hist_eval += np.array(binned(counts[:, 0][invx]), np.int64)
    tot = int(hist_eval.sum())
    for j, (_, _, lab) in enumerate(BINS):
        out.append(["B", "courier evaluations at order placed", f"orders on the pincode lane in the last 7 days: {lab}", int(hist_eval[j]), round(100 * hist_eval[j] / tot, 2), "", ""])
    out.append(["B", "courier evaluations at order placed", "total evaluations", tot, "", "", ""])
    for r in sim.RULES:
        for cd in range(sim.NSTEP + 2):
            out.append(["C", "courier evaluations by rung", f"{r}: {sim.CODE_LABEL[cd]}", int(rung[r][cd]), round(100 * rung[r][cd] / rung[r].sum(), 2), "", ""])
        for cd in range(sim.NSTEP + 2):
            out.append(["C", "orders by the rung of the winning courier at order placed", f"{r}: {sim.CODE_LABEL[cd]}", int(win_rung[r][cd]), round(100 * win_rung[r][cd] / max(1, n_orders_with_winner[r]), 2), "", ""])
    with open(P + "outputs/lane-sizes-and-rungs-v1.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["part", "view", "item", "value (average over dates in A)", "min over dates / share %", "max over dates", "as of 24 Sep"])
        w.writerows(out)
    print("orders in scope:", N)
    for r in out:
        print(r)


if __name__ == "__main__":
    main()
