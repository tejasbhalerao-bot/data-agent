# Purpose: full simulation: for every order placed 29 Jul to 30 Sep 2026, allocate the courier at order placed and at invoice under today's rule and under x = 10, 15, 20, and report M1 to M8
# Serves: M1, M2, M3, M4, M5, M6, M7, M8 (approved brief, insights/2026-10-20-minimum-sample-size-courier-allocation-v1.md)
# Reads: archives/minimum-sample-size-courier-allocation/raw-data/orders-2026-07.csv .. orders-2026-09.csv (shipment files; no query saved)
#        archives/minimum-sample-size-courier-allocation/raw-data/op-2026-07.csv .. op-2026-09.csv (order placed files; no query saved)
#        archives/minimum-sample-size-courier-allocation/raw-data/ops-speed-config-wh<NN>.csv (ops-configured delivery days, 19 warehouses)
#        archives/minimum-sample-size-courier-allocation/raw-data/tat-adherence-master.csv
#        archives/minimum-sample-size-courier-allocation/raw-data/courier-partner-schedules.csv
#        archives/minimum-sample-size-courier-allocation/raw-data/serviceability-<courier>.csv
#        archives/minimum-sample-size-courier-allocation/outputs/goi-pincode-map.csv (from structure-goi-pincode-map-v1.py)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/sim-v2-orders.csv (one row per order x rule)
#         archives/minimum-sample-size-courier-allocation/outputs/sim-v2-summary.csv (one row per metric x rule x cut)
#         archives/minimum-sample-size-courier-allocation/outputs/sim-v2-matchrate.csv (order placed rows found in the shipment files, by placed date)
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-simulation-v2.py
#
# Method: context/2026-10-20-process-flow-v5.md and simulation-scope-v7.md (same steps as the 9-order example, scripts step 1 to 7).
#   Decision dates: order placed stage = digitised date; invoice stage = invoice-create date. Both must be 29 Jul .. 30 Sep (October is never used).
#   History for a lane = orders with a first delivery attempt in the N days before the decision date (7, 14, 21, 28), keyed warehouse x courier x
#   (pincode | micro-cluster | macro-cluster | state). Micro-cluster = same state, district and division in the GOI map; macro-cluster = same first 3 digits.
#   Ladder (time first, then geography): pincode 7,14,21,28; micro 7..28; macro 7..28; state 7..28. Stop at the first step with at least x orders;
#   if none, the widest pool (state, 28 days) when it has orders; otherwise ops config + TAT Adherence Master. "Today" = pincode 7 days when it has any order, else ops config.
#   Lane TAT = ROUNDUP(85th percentile, linear) of actual days; adherence = running share of delay-day buckets until it first reaches 0.85. No drop or pickup buffers.
#   Candidates: the six couriers (185, 195, 225, 246, 247, 286) serviceable on the order's pincode, with ops config rows for the warehouse and a TAT Adherence Master row.
#   Warehouse 19 uses warehouse 40's ops config, adherence master and cutoffs. A lane with no ops config row gets the default 3 days.
#   Score = lane TAT / (adherence / 100) + schedule adjustment (+1 when the time of day of the stage's clock is after the courier's cutoff; no cutoff = no adjustment).
#   Clock: order placed stage = promised warehouse processing time (DIGITISED_WH_PROMISE); invoice stage = invoice-create time. Lowest score wins; tie-break 195 > 185 > 225 > 246 > 286 > 247.
#   Promise = lane TAT of the order placed stage winner. M1: actual days vs that promise (any couriers). M2: same, only when the invoice stage winner is the courier that shipped.
# Outcomes (actual days, first delivery attempt) exist only for orders in the shipment files, which stop at 30 Sep: see sim-v2-matchrate.csv for how complete the late dates are.

import csv
import glob
import math
import sys
import time
from datetime import datetime, date

import numpy as np

P = "archives/minimum-sample-size-courier-allocation/"
FMT = "%b %d, %Y, %I:%M %p"
BASE = datetime(2026, 7, 1)
PRIORITY = ["195", "185", "225", "246", "286", "247"]  # also the tie-break order and the column order
NC = 6
CIDX = {c: i for i, c in enumerate(PRIORITY)}
PCT = 0.85
XS = (10, 15, 20)
WINDOWS = (7, 14, 21, 28)
GEOS = ("pincode", "micro-cluster", "macro-cluster", "state")
STEPS = [(g, n) for g in GEOS for n in WINDOWS]  # the ladder as an ordered list (time first, then geography)
NSTEP = len(STEPS)
RULES = ["today", "x=10", "x=15", "x=20"]
OPS, WIDEST = NSTEP, NSTEP + 1
CODE_LABEL = [f"{g} {n}d" for g, n in STEPS] + ["ops config", "widest pool (below x)"]
DEFAULT_SUPPOSED_TAT = 3
FIRST_D, LAST_D = 28, 91  # day index from 1 Jul: 29 Jul .. 30 Sep
CLASS_NAME = ["Early", "On-Time", "Late"]
M = 10 ** 6


# ---------- calculation core (tested in tests/2026-10-20-test-aggregate-simulation-v1.py) ----------

def bucket_of(delay):
    """Delay-day bucket: 0 Early 4+, 1 Early 3, 2 Early 2, 3 Early 1, 4 On-Time, 5 Late 1, 6 Late 2, 7 Late 3, 8 Late 4+."""
    if delay <= -4:
        return 0
    if delay < 0:
        return 4 + delay
    if delay == 0:
        return 4
    return min(4 + delay, 8)


def percentile_from_hist(hist, n, p):
    """Linear-interpolation percentile of the n values described by hist (hist[v] = count of value v)."""
    cum = np.cumsum(hist)
    pos = p * (n - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    slo = int(np.searchsorted(cum, lo, side="right"))
    shi = int(np.searchsorted(cum, hi, side="right"))
    return slo + (shi - slo) * (pos - lo)


def tat_adh_from_hists(act_hist, bkt_hist):
    """Lane TAT (days, rounded up) and adherence (%) from the actual-days histogram and the delay-bucket histogram of a pool."""
    n = int(np.sum(act_hist))
    lane_tat = math.ceil(percentile_from_hist(act_hist, n, PCT))
    cum = 0
    for c in bkt_hist:
        cum += int(c)
        if cum / n >= PCT:
            return lane_tat, 100 * cum / n
    return lane_tat, 100.0


def stop_for_rule(counts, x):
    """counts: (N, 16) orders per ladder step. Returns (stop, code) per row. x=None is today's rule."""
    n = counts.shape[0]
    if x is None:
        ok = counts[:, 0] > 0
        stop = np.where(ok, 0, OPS)
        return stop, stop.copy()
    ge = counts >= x
    anyok = ge.any(axis=1)
    first = np.argmax(ge, axis=1)
    widest = counts[:, NSTEP - 1] > 0
    stop = np.where(anyok, first, np.where(widest, NSTEP - 1, OPS))
    code = np.where(anyok, first, np.where(widest, WIDEST, OPS))
    return stop, code


def pick_winner(score):
    """score: (N, 6) in tie-break order, inf = not a candidate. Returns winner index or -1. Ties go to the lowest column."""
    s = np.round(score, 9)
    w = np.argmin(s, axis=1)
    return np.where(np.isfinite(s.min(axis=1)), w, -1)


def class_of(delay):
    """0 Early, 1 On-Time, 2 Late from delay days = actual days - promise."""
    return np.where(delay < 0, 0, np.where(delay == 0, 1, 2))


def schedule_adjustment(clock_min, cutoff_min):
    """+1 when the time of day is after the cutoff; no cutoff (-1) = 0."""
    return ((cutoff_min >= 0) & (clock_min > cutoff_min)).astype(np.int64)


# ---------- loading ----------

def minutes(s):
    return int((datetime.strptime(s, FMT) - BASE).total_seconds() // 60)


def load_all():
    t0 = time.time()
    # GOI map
    micro_id = np.full(M, -1, np.int32)
    macro_id = np.full(M, -1, np.int32)
    state_id = np.full(M, -1, np.int32)
    micro_ids, state_ids = {}, {}
    with open(P + "outputs/goi-pincode-map.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            pin = int(r["pincode"])
            macro_id[pin] = int(r["macro_cluster"])
            if r["state"] and r["district"] and r["division"]:
                micro_id[pin] = micro_ids.setdefault((r["state"], r["district"], r["division"]), len(micro_ids))
                state_id[pin] = state_ids.setdefault(r["state"], len(state_ids))
    gid = {"micro-cluster": micro_id, "macro-cluster": macro_id, "state": state_id}

    # serviceability
    serv = np.zeros((NC, M), bool)
    for c in PRIORITY:
        with open(P + f"raw-data/serviceability-{c}.csv", encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                serv[CIDX[c], int(r["pincode"])] = True

    # ops config
    keys, days = [], []
    cfg_pair = np.zeros((41, NC), bool)
    for fn in sorted(glob.glob(P + "raw-data/ops-speed-config-wh*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            c = r["delivery_partner"]
            if c not in CIDX:
                continue
            wh = int(r["warehouse_id"])
            keys.append((wh * NC + CIDX[c]) * M + int(r["pincode"]))
            days.append(int(r["delivery_days"]))
            cfg_pair[wh, CIDX[c]] = True
    keys, days = np.array(keys, np.int64), np.array(days, np.int64)
    order = np.argsort(keys, kind="stable")
    keys, days = keys[order], days[order]
    keys, first = np.unique(keys, return_index=True)  # repeated rows carry identical values
    days = days[first]

    # adherence master and cutoffs
    master = np.full((41, NC), np.nan)
    for r in csv.DictReader(open(P + "raw-data/tat-adherence-master.csv", encoding="utf-8-sig", newline="")):
        if r["Delivery Partner"] in CIDX:
            master[int(r["Warehouse ID"]), CIDX[r["Delivery Partner"]]] = float(r["Adherence Percentage"])
    cut = np.full((41, NC), -1, np.int64)
    for r in csv.DictReader(open(P + "raw-data/courier-partner-schedules.csv", encoding="utf-8-sig", newline="")):
        if r["Courier Partner ID"] in CIDX:
            h, m, _ = r["Courier Partner Schedule Time"][:8].split(":")
            cut[int(r["Warehouse ID"]), CIDX[r["Courier Partner ID"]]] = int(h) * 60 + int(m)

    # shipments
    ev = {k: [] for k in ("oid", "wh", "c", "pin", "d", "actual", "promise")}
    all_ids = []
    bad = 0
    for fn in sorted(glob.glob(P + "raw-data/orders-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            oid = int(r["ORDER_ID"].replace(",", ""))
            all_ids.append(oid)
            c = r["DELIVERY_PARTNER"]
            if c not in CIDX:
                continue
            try:
                a = datetime.strptime(r["DELIVERY_ATTEMPT_TIME"], FMT)
                p = datetime.strptime(r["PICKUP_TIME"], FMT)
            except ValueError:
                bad += 1
                continue
            if a < p:
                bad += 1
                continue
            ev["oid"].append(oid)
            ev["wh"].append(int(r["WAREHOUSE_ID"]))
            ev["c"].append(CIDX[c])
            ev["pin"].append(int(r["PINCODE"]))
            ev["d"].append((a.date() - BASE.date()).days)
            ev["actual"].append((a.date() - p.date()).days)
            ev["promise"].append(int(r["PROMISE_TAT"]))
    ev = {k: np.array(v, np.int64) for k, v in ev.items()}
    all_ids = np.array(all_ids, np.int64)

    # order placed rows
    o_id, o_pl, o_inv, o_whp = [], [], [], []
    for fn in sorted(glob.glob(P + "raw-data/op-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            o_id.append(int(r["ORDER_ID"].replace(",", "")))
            o_pl.append(minutes(r["DIGITISED_TS"]))
            o_inv.append(minutes(r["INVOICE_CREATE_TS"]) if r["INVOICE_CREATE_TS"] else -1)
            o_whp.append(minutes(r["DIGITISED_WH_PROMISE"]) if r["DIGITISED_WH_PROMISE"] else -1)
    op = {k: np.array(v, np.int64) for k, v in (("id", o_id), ("pl", o_pl), ("inv", o_inv), ("whp", o_whp))}
    print(f"loaded in {time.time() - t0:.0f}s: {len(ev['oid']):,} six-courier shipment rows ({bad} unusable), {len(op['id']):,} order placed rows")
    return dict(gid=gid, micro_id=micro_id, macro_id=macro_id, state_id=state_id, serv=serv, cfg_keys=keys, cfg_days=days,
                cfg_pair=cfg_pair, master=master, cut=cut, ev=ev, all_ids=all_ids, op=op, bad=bad)


def eff(wh):
    """Warehouse 19 takes warehouse 40's config, adherence master and cutoffs."""
    return np.where(wh == 19, 40, wh)


# ---------- the ladder on a set of (warehouse, courier, pincode, decision date) combinations ----------

class Ladder:
    def __init__(self, data):
        self.d = data
        ev = data["ev"]
        keep = (ev["d"] >= 0) & (ev["d"] <= LAST_D)
        self.wh = ev["wh"][keep]
        self.c = ev["c"][keep]
        self.pin = ev["pin"][keep]
        self.dd = ev["d"][keep]
        self.act = ev["actual"][keep]
        delay = self.act - ev["promise"][keep]
        self.bkt = np.where(delay <= -4, 0, np.where(delay < 0, 4 + delay, np.where(delay == 0, 4, np.minimum(4 + delay, 8))))
        self.maxa = int(self.act.max()) + 1
        wc = self.wh * NC + self.c
        self.S, self.perm = {}, {}
        for g in GEOS:
            if g == "pincode":
                comp = wc * M + self.pin
                valid = np.ones(len(comp), bool)
            else:
                gi = data["gid"][g][self.pin]
                valid = gi >= 0
                comp = wc * 4096 + gi
            idx = np.nonzero(valid)[0]
            keys = comp[idx] * 128 + self.dd[idx]
            o = np.argsort(keys, kind="stable")
            self.S[g] = keys[o]
            self.perm[g] = idx[o]

    def evaluate(self, combo):
        """combo: unique int64 keys ((wh*6+c)*1e6+pin)*128+D. Returns per rule: tat, adh, code arrays aligned to combo, and counts."""
        d = self.d
        D = combo % 128
        base = combo // 128
        pin = base % M
        wc = base // M
        n = len(combo)
        counts = np.zeros((n, NSTEP), np.int64)
        LO = np.zeros((n, NSTEP), np.int64)
        HI = np.zeros((n, NSTEP), np.int64)
        for gi_, g in enumerate(GEOS):
            if g == "pincode":
                comp, valid = base, np.ones(n, bool)
            else:
                gid = d["gid"][g][pin]
                valid = gid >= 0
                comp = wc * 4096 + np.where(valid, gid, 0)
            for wi, w in enumerate(WINDOWS):
                lo = np.searchsorted(self.S[g], comp * 128 + (D - w), side="left")
                hi = np.searchsorted(self.S[g], comp * 128 + (D - 1), side="right")
                col = gi_ * 4 + wi
                counts[:, col] = np.where(valid, hi - lo, 0)
                LO[:, col], HI[:, col] = lo, hi
        wh = wc // NC
        cc = wc % NC
        whe = eff(wh)
        key_ops = (whe * NC + cc) * M + pin
        pos = np.searchsorted(d["cfg_keys"], key_ops)
        pos = np.minimum(pos, len(d["cfg_keys"]) - 1)
        found = d["cfg_keys"][pos] == key_ops
        ops_tat = np.where(found, d["cfg_days"][pos], DEFAULT_SUPPOSED_TAT).astype(float)
        ops_adh = d["master"][whe, cc]
        out = {}
        pool_cache = {}
        rows = np.arange(n)
        for rule in RULES:
            stop, code = stop_for_rule(counts, None if rule == "today" else int(rule[2:]))
            tat = ops_tat.copy()
            adh = ops_adh.copy()
            has = stop < OPS
            if has.any():
                sel = np.nonzero(has)[0]
                st = stop[sel]
                lo, hi = LO[sel, st], HI[sel, st]
                lvl = st // 4
                pk = (lvl * (1 << 23) + lo) * (1 << 23) + hi
                upk, inv = np.unique(pk, return_inverse=True)
                res = np.zeros((len(upk), 2))
                for i, k in enumerate(upk):
                    if k in pool_cache:
                        res[i] = pool_cache[k]
                        continue
                    hi_ = int(k % (1 << 23))
                    lo_ = int((k // (1 << 23)) % (1 << 23))
                    lv = int(k // (1 << 46))
                    idx = self.perm[GEOS[lv]][lo_:hi_]
                    ah = np.bincount(self.act[idx], minlength=self.maxa)
                    bh = np.bincount(self.bkt[idx], minlength=9)
                    r2 = tat_adh_from_hists(ah, bh)
                    pool_cache[k] = r2
                    res[i] = r2
                tat[sel] = res[inv, 0]
                adh[sel] = res[inv, 1]
            out[rule] = (tat, adh, code)
        return out, counts


# ---------- simulation of a block of orders ----------

def simulate_block(L, od, sl):
    """od: order arrays; sl: slice or index array of orders in the block. Returns per-rule result arrays and rung counts."""
    d = L.d
    wh = od["wh"][sl]
    pin = od["pin"][sl]
    n = len(wh)
    whe = eff(wh)
    cand = np.zeros((n, NC), bool)
    for j in range(NC):
        cand[:, j] = d["serv"][j][pin] & d["cfg_pair"][whe, j] & ~np.isnan(d["master"][whe, j])
    stage_res = {}
    rung_counts = {r: np.zeros(NSTEP + 2, np.int64) for r in RULES}
    for stage, dkey, clockkey in (("placed", "Dp", "whp"), ("invoice", "Di", "inv")):
        D = od[dkey][sl]
        clock = od[clockkey][sl] % 1440
        tat = {r: np.full((n, NC), np.nan) for r in RULES}
        adh = {r: np.full((n, NC), np.nan) for r in RULES}
        code = {r: np.full((n, NC), -1, np.int64) for r in RULES}
        combos, owner = [], []
        for j in range(NC):
            ii = np.nonzero(cand[:, j])[0]
            combos.append((((wh[ii] * NC + j) * M + pin[ii]) * 128 + D[ii]))
            owner.append((ii, np.full(len(ii), j)))
        allc = np.concatenate(combos)
        ucombo, inv = np.unique(allc, return_inverse=True)
        res, _ = L.evaluate(ucombo)
        ii = np.concatenate([o[0] for o in owner])
        jj = np.concatenate([o[1] for o in owner])
        for r in RULES:
            t, a, c = res[r]
            tat[r][ii, jj] = t[inv]
            adh[r][ii, jj] = a[inv]
            code[r][ii, jj] = c[inv]
        cutm = d["cut"][whe[:, None], np.arange(NC)[None, :]]
        adj = schedule_adjustment(clock[:, None], cutm)
        score, winner = {}, {}
        for r in RULES:
            with np.errstate(divide="ignore", invalid="ignore"):
                sc = tat[r] / (adh[r] / 100) + adj
            sc = np.where(cand & np.isfinite(sc), sc, np.inf)
            score[r] = sc
            winner[r] = pick_winner(sc)
        stage_res[stage] = dict(tat=tat, adh=adh, code=code, winner=winner)
        if stage == "placed":
            for r in RULES:
                cc = code[r][cand]
                rung_counts[r] += np.bincount(cc, minlength=NSTEP + 2)
    out = {}
    cs = od["cship"][sl]
    actual = od["actual"][sl]
    rows = np.arange(n)
    for r in RULES:
        pw = stage_res["placed"]["winner"][r]
        iw = stage_res["invoice"]["winner"][r]
        has = pw >= 0
        pp = np.where(has, stage_res["placed"]["tat"][r][rows, np.maximum(pw, 0)], np.nan)
        pcode = np.where(has, stage_res["placed"]["code"][r][rows, np.maximum(pw, 0)], -1)
        proj = stage_res["placed"]["tat"][r][rows, cs]
        m1 = np.where(has, class_of(actual - np.nan_to_num(pp)), -1)
        m2 = np.where(has & (iw == cs), m1, -1)
        out[r] = dict(pw=pw, pp=np.nan_to_num(pp, nan=-1).astype(np.int64), pcode=pcode, iw=iw,
                      proj=np.nan_to_num(proj, nan=-1).astype(np.int64), m1=m1, m2=m2)
    return out, rung_counts


# ---------- main ----------

def main():
    T0 = time.time()
    data = load_all()
    ev, op = data["ev"], data["op"]
    oo = np.argsort(op["id"], kind="stable")
    for k in op:
        op[k] = op[k][oo]

    # orders in scope: six-courier shipments with an order placed row, placed and invoiced 29 Jul .. 30 Sep, with a promised warehouse time
    pos = np.searchsorted(op["id"], ev["oid"])
    pos = np.minimum(pos, len(op["id"]) - 1)
    has_op = op["id"][pos] == ev["oid"]
    pl, inv, whp = op["pl"][pos], op["inv"][pos], op["whp"][pos]
    Dp = pl // 1440
    Di = np.where(inv >= 0, inv // 1440, -1)
    in_win = has_op & (Dp >= FIRST_D) & (Dp <= LAST_D)
    inv_ok = in_win & (inv >= 0) & (Di >= FIRST_D) & (Di <= LAST_D)
    keep = inv_ok & (whp >= 0)
    print(f"six-courier shipment rows: {len(ev['oid']):,}; with an order placed row: {int(has_op.sum()):,}; placed 29 Jul to 30 Sep: {int(in_win.sum()):,}; "
          f"invoiced 29 Jul to 30 Sep: {int(inv_ok.sum()):,}; with a promised warehouse time: {int(keep.sum()):,}")
    od = dict(oid=ev["oid"][keep], wh=ev["wh"][keep], cship=ev["c"][keep], pin=ev["pin"][keep], actual=ev["actual"][keep],
              promise=ev["promise"][keep], pl=pl[keep], inv=inv[keep], whp=whp[keep], Dp=Dp[keep], Di=Di[keep])
    srt = np.lexsort((od["oid"], od["pl"]))
    od = {k: v[srt] for k, v in od.items()}
    if "--smoke" in sys.argv:  # quick check on the first orders by placed time
        n_smoke = int(sys.argv[sys.argv.index("--smoke") + 1])
        od = {k: v[:n_smoke] for k, v in od.items()}
    N = len(od["oid"])

    # share of order placed rows (any courier) found in the shipment files, by placed date
    inwin_rows = (op["pl"] // 1440 >= FIRST_D) & (op["pl"] // 1440 <= LAST_D)
    found = np.isin(op["id"][inwin_rows], data["all_ids"])
    pdate = (op["pl"][inwin_rows] // 1440)
    mr = []
    for dd in range(FIRST_D, LAST_D + 1):
        m = pdate == dd
        mr.append((dd, int(m.sum()), int(found[m].sum())))
    with open(P + "outputs/sim-v2-matchrate.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["placed_date", "order_placed_rows", "found_in_shipment_files", "share_pct"])
        for dd, a, b in mr:
            w.writerow([(BASE.date().fromordinal(BASE.date().toordinal() + dd)).isoformat(), a, b, round(100 * b / a, 2)])
    ref = [b / a for dd, a, b in mr if dd <= 61]  # 29 Jul .. 31 Aug
    thr = float(np.mean(ref)) - 0.02
    cut_day = LAST_D
    for dd, a, b in mr:
        if b / a < thr:
            cut_day = dd - 1
            break
    print(f"order placed rows found in shipment files: 29 Jul to 31 Aug mean {100 * np.mean(ref):.1f}%; complete dates = placed up to day index {cut_day} "
          f"({BASE.date().fromordinal(BASE.date().toordinal() + cut_day).isoformat()}), threshold {100 * thr:.1f}%")

    L = Ladder(data)
    res = {r: {k: np.zeros(N, np.int64) for k in ("pw", "pp", "pcode", "iw", "proj", "m1", "m2")} for r in RULES}
    rung = {r: np.zeros(NSTEP + 2, np.int64) for r in RULES}
    CH = 100000
    for s in range(0, N, CH):
        sl = slice(s, min(N, s + CH))
        t = time.time()
        out, rc = simulate_block(L, od, sl)
        for r in RULES:
            for k in res[r]:
                res[r][k][sl] = out[r][k]
            rung[r] += rc[r]
        print(f"  block {s // CH + 1}/{math.ceil(N / CH)} done in {time.time() - t:.0f}s")

    write_outputs(od, res, rung, cut_day)
    print(f"total {time.time() - T0:.0f}s")


def write_outputs(od, res, rung, cut_day):
    N = len(od["oid"])
    cs = od["cship"]
    cname = np.array(PRIORITY)
    with open(P + "outputs/sim-v2-orders.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "warehouse", "pincode", "shipping_courier", "actual_days", "real_promise_days", "placed_min", "invoice_min", "rule",
                    "placed_winner", "promise_days", "placed_winner_data_used", "invoice_winner", "shipping_courier_projected_tat", "M1", "M2"])
        for r in RULES:
            R = res[r]
            for i in range(N):
                w.writerow([od["oid"][i], od["wh"][i], od["pin"][i], PRIORITY[cs[i]], od["actual"][i], od["promise"][i], od["pl"][i], od["inv"][i], r,
                            PRIORITY[R["pw"][i]] if R["pw"][i] >= 0 else "", R["pp"][i] if R["pw"][i] >= 0 else "",
                            CODE_LABEL[R["pcode"][i]] if R["pw"][i] >= 0 else "", PRIORITY[R["iw"][i]] if R["iw"][i] >= 0 else "",
                            R["proj"][i] if R["proj"][i] >= 0 else "", CLASS_NAME[R["m1"][i]] if R["m1"][i] >= 0 else "",
                            CLASS_NAME[R["m2"][i]] if R["m2"][i] >= 0 else ""])
    rows = []

    def add(metric, rule, scope, cut, val, num, den):
        rows.append([metric, rule, scope, cut, "" if val is None else round(val, 4), num, den])

    base = {}

    def add_with_delta(metric, rule, scope, val, num, den, unit):
        """Adds the metric and, for x rules, its change against today's rule."""
        add(metric, rule, scope, "all", val, num, den)
        if rule == "today":
            base[(scope, metric)] = val
        else:
            add(f"{metric} change vs today ({unit})", rule, scope, "all", val - base[(scope, metric)], "", den)

    for scope, mask in (("all dates", np.ones(N, bool)), ("complete dates", od["Dp"] <= cut_day)):
        n = int(mask.sum())
        ontime_real = int(((od["actual"] <= od["promise"]) & mask).sum())
        add("real adherence (actual vs real promise)", "real", scope, "all", 100 * ontime_real / n, ontime_real, n)
        for r in RULES:
            R = res[r]
            has = (R["pw"] >= 0) & mask
            ok1 = (R["m1"] <= 1) & has
            add_with_delta("M1 adherence %", r, scope, 100 * ok1.sum() / has.sum(), int(ok1.sum()), int(has.sum()), "percentage points")
            rep = (R["m2"] >= 0) & mask
            ok2 = (R["m2"] >= 0) & (R["m2"] <= 1) & mask
            add_with_delta("M2 adherence % (reported only if invoice courier shipped it)", r, scope, 100 * ok2.sum() / max(1, rep.sum()), int(ok2.sum()), int(rep.sum()), "percentage points")
            add_with_delta("M3 orders not reported in M2 %", r, scope, 100 * (has.sum() - rep.sum()) / has.sum(), int(has.sum() - rep.sum()), int(has.sum()), "percentage points")
            add_with_delta("M4 average promise (days)", r, scope, float(R["pp"][has].mean()), "", int(has.sum()), "days")
            T = res["today"]
            both = has & (T["pw"] >= 0)
            for lab, cond in (("longer than today", R["pp"] > T["pp"]), ("shorter than today", R["pp"] < T["pp"]), ("equal to today", R["pp"] == T["pp"])):
                add(f"M4 share of orders with promise {lab} %", r, scope, "all", 100 * (cond & both).sum() / both.sum(), int((cond & both).sum()), int(both.sum()))
            for cut_name, key in (("courier", cs), ("warehouse", od["wh"])):
                for v in np.unique(key[mask]):
                    mv = mask & (key == v)
                    hv = (R["pw"] >= 0) & mv
                    if hv.sum():
                        a1 = ((R["m1"] <= 1) & hv).sum()
                        lab = PRIORITY[v] if cut_name == "courier" else int(v)
                        add("M1 adherence % by " + cut_name + " of shipping", r, scope, lab, 100 * a1 / hv.sum(), int(a1), int(hv.sum()))
                        rv = (R["m2"] >= 0) & mv
                        if rv.sum():
                            a2 = ((R["m2"] <= 1) & rv).sum()
                            add("M2 adherence % by " + cut_name + " of shipping", r, scope, lab, 100 * a2 / rv.sum(), int(a2), int(rv.sum()))
            for cd in np.unique(R["pcode"][has]):
                mv = has & (R["pcode"] == cd)
                a1 = ((R["m1"] <= 1) & mv).sum()
                add("M1 adherence % by data used by the order placed winner", r, scope, CODE_LABEL[cd], 100 * a1 / mv.sum(), int(a1), int(mv.sum()))
            for j in range(NC):
                cp = ((R["pw"] == j) & mask).sum()
                ci = ((R["iw"] == j) & mask).sum()
                tp = ((T["pw"] == j) & mask).sum()
                ti = ((T["iw"] == j) & mask).sum()
                add("M5 courier mix at order placed %", r, scope, PRIORITY[j], 100 * cp / n, int(cp), n)
                add("M5 change vs today (percentage points)", r, scope, PRIORITY[j], 100 * (cp - tp) / n, int(cp - tp), n)
                add("M6 courier mix at invoice %", r, scope, PRIORITY[j], 100 * ci / n, int(ci), n)
                add("M6 change vs today (percentage points)", r, scope, PRIORITY[j], 100 * (ci - ti) / n, int(ci - ti), n)
        for j in range(NC):
            c = ((cs == j) & mask).sum()
            add("M6 courier that actually shipped %", "actual", scope, PRIORITY[j], 100 * c / n, int(c), n)
        T = res["today"]
        mt = ((T["iw"] == cs) & mask).sum()
        add("M8 replay match (today's invoice winner = shipping courier) %", "today", scope, "all", 100 * mt / n, int(mt), n)
    for r in RULES:
        tot = int(rung[r].sum())
        for cd in range(NSTEP + 2):
            if rung[r][cd]:
                add("M7 share of courier evaluations at order placed resolved at", r, "all dates", CODE_LABEL[cd], 100 * rung[r][cd] / tot, int(rung[r][cd]), tot)
    with open(P + "outputs/sim-v2-summary.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["metric", "rule", "date_scope", "cut", "value", "numerator", "denominator"])
        w.writerows(rows)
    print(f"wrote sim-v2-orders.csv ({N * len(RULES):,} rows) and sim-v2-summary.csv ({len(rows)} rows)")


if __name__ == "__main__":
    main()
