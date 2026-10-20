# Purpose: why does today's replayed invoice winner differ from the courier that actually shipped (M8 mismatches)?
# Serves: M8 (replay match); supporting check for M3 under today's rule
# Reads: the same inputs as aggregate-simulation-v2.py (imported as a module; it loads the shipment, order-placed, config, adherence, cutoff, serviceability and GOI files)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/replay-mismatch-v1.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-replay-mismatch-v1.py
#
# Orders placed 29 Jul to 24 Sep (complete dates), today's rule, invoice stage. Each order is put in one group:
#   match: the replay picks the courier that shipped;
#   shipper not a candidate: the shipping courier does not serve the pincode in the serviceability file, or has no ops config for the warehouse, or no adherence master row;
#   tie lost on priority: the shipper ties on score with the winner but the agreed tie-break picks another courier;
#   shipper scores higher by < 0.25 / 0.25 to 1 / more than 1: the shipper is a candidate and loses on score by that margin.
# Also: for mismatches where the shipper is a candidate, the share of couriers (winner and shipper) that rest on the ops config instead of orders.

import csv
import importlib.util
import time
from collections import Counter

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
    pl, inv, whp = op["pl"][pos], op["inv"][pos], op["whp"][pos]
    Dp = pl // 1440
    Di = np.where(inv >= 0, inv // 1440, -1)
    keep = has_op & (Dp >= sim.FIRST_D) & (Dp <= 85) & (inv >= 0) & (Di >= sim.FIRST_D) & (Di <= sim.LAST_D) & (whp >= 0)
    od = dict(wh=ev["wh"][keep], cship=ev["c"][keep], pin=ev["pin"][keep], inv=inv[keep], Di=Di[keep])
    L = sim.Ladder(data)
    NC = sim.NC
    groups = Counter()
    ops_share = Counter()
    N = len(od["wh"])
    for s in range(0, N, 100000):
        sl = slice(s, min(N, s + 100000))
        wh, pin, cs = od["wh"][sl], od["pin"][sl], od["cship"][sl]
        n = len(wh)
        whe = sim.eff(wh)
        cand = np.zeros((n, NC), bool)
        for j in range(NC):
            cand[:, j] = data["serv"][j][pin] & data["cfg_pair"][whe, j] & ~np.isnan(data["master"][whe, j])
        D = od["Di"][sl]
        clock = od["inv"][sl] % 1440
        tat = np.full((n, NC), np.nan)
        adh = np.full((n, NC), np.nan)
        code = np.full((n, NC), -1)
        combos, ii_l, jj_l = [], [], []
        for j in range(NC):
            ii = np.nonzero(cand[:, j])[0]
            combos.append((((wh[ii] * NC + j) * sim.M + pin[ii]) * 128 + D[ii]))
            ii_l.append(ii)
            jj_l.append(np.full(len(ii), j))
        u, invx = np.unique(np.concatenate(combos), return_inverse=True)
        res, _ = L.evaluate(u)
        t, a, c = res["today"]
        ii, jj = np.concatenate(ii_l), np.concatenate(jj_l)
        tat[ii, jj], adh[ii, jj], code[ii, jj] = t[invx], a[invx], c[invx]
        cutm = data["cut"][whe[:, None], np.arange(NC)[None, :]]
        adj = sim.schedule_adjustment(clock[:, None], cutm)
        with np.errstate(divide="ignore", invalid="ignore"):
            sc = tat / (adh / 100) + adj
        sc = np.where(cand & np.isfinite(sc), sc, np.inf)
        w = sim.pick_winner(sc)
        rows = np.arange(n)
        best = np.round(sc, 9).min(axis=1)
        shipper_cand = cand[rows, cs]
        shipper_score = np.round(sc[rows, cs], 9)
        match = w == cs
        for i in range(n):
            if match[i]:
                g = "match"
            elif not shipper_cand[i]:
                g = "shipper not a candidate"
            elif shipper_score[i] == best[i]:
                g = "tie lost on priority"
            else:
                gap = shipper_score[i] - best[i]
                g = "shipper scores higher by less than 0.25" if gap < 0.25 else ("shipper scores higher by 0.25 to 1" if gap <= 1 else "shipper scores higher by more than 1")
                ops_share["mismatch rows with shipper candidate"] += 1
                ops_share["winner on ops config"] += code[i, w[i]] == sim.OPS if w[i] >= 0 else 0
                ops_share["shipper on ops config"] += code[i, cs[i]] == sim.OPS
            groups[g] += 1
    tot = sum(groups.values())
    out = [["group", "orders", "share_pct"]] + [[g, c, round(100 * c / tot, 2)] for g, c in groups.most_common()]
    out += [["(of mismatches where the shipper is a candidate and scores higher) winner rests on the ops config", ops_share["winner on ops config"], ""],
            ["(of mismatches where the shipper is a candidate and scores higher) shipper rests on the ops config", ops_share["shipper on ops config"], ""],
            ["(of mismatches where the shipper is a candidate and scores higher) rows", ops_share["mismatch rows with shipper candidate"], ""]]
    with open(P + "outputs/replay-mismatch-v1.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(out)
    for r in out:
        print(r)
    print("orders:", tot)


if __name__ == "__main__":
    main()
