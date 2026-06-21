"""Cascade — level-by-level conditional tables, Sheets-ready CSVs.

Each leg = actual handoff vs digitised promise.
Bands: Doctor & WH = +/-1 min (timestamp). Dispatch & Delivery = date-level (compare dates only).
Cohort: all 8 timestamps present, digitised_ts >= 2026-05-08, wh_processing_mins != 0.

Emits 4 CSVs (separate count + percent columns; percents are conditional within parent):
  cascade-step0-v1.csv  each leg's own E/OT/L  (denominator = cohort)
  cascade-step1-v1.csv  Doctor -> WH
  cascade-step2-v1.csv  Doctor, WH -> Dispatch
  cascade-step3-v1.csv  Doctor, WH, Dispatch -> Delivery
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "raw-data" / "early-delivery-raw-may-2026.csv"
OUT = ROOT / "outputs"
TS_FMT = "%b %d, %Y, %I:%M %p"
CUTOVER = date(2026, 5, 8)
BUF_S = 60
OUTS = ["Early", "On-Time", "Late"]


def parse_dt(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def parse_num(raw: str) -> float | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def cls_ts(actual: datetime, promised: datetime) -> str:
    d = (actual - promised).total_seconds()
    return "Early" if d < -BUF_S else "Late" if d > BUF_S else "On-Time"


def cls_day(actual: datetime, promised: datetime) -> str:
    diff = (actual.date() - promised.date()).days
    return "Early" if diff <= -1 else "Late" if diff >= 1 else "On-Time"


def pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def main() -> None:
    seen: set[str] = set()
    marg = {k: defaultdict(int) for k in ("Doctor", "Warehouse", "Dispatch", "Delivery")}
    l1: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    l2: dict[tuple, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    l3: dict[tuple, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    n = 0

    with open(RAW_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            oid = (row["order_id"] or "").replace(",", "").strip()
            if oid in seen:
                continue
            seen.add(oid)
            dig = parse_dt(row["digitised_ts"])
            if dig is None or dig.date() < CUTOVER:
                continue
            if parse_num(row["digitised_wh_process_mins"]) == 0:
                continue
            dr_p = parse_dt(row["digitised_dr_promise"]); dr_a = parse_dt(row["dr_confirm_ts"])
            wh_p = parse_dt(row["digitised_wh_promise"]); wh_a = parse_dt(row["actual_warehouse_processing"])
            ds_p = parse_dt(row["digitised_dispatch_promise"]); ds_a = parse_dt(row["pickup_time"])
            dl_p = parse_dt(row["digitised_delivery_promise"]); dl_a = parse_dt(row["delivery_attempt_time"])
            if None in (dr_p, dr_a, wh_p, wh_a, ds_p, ds_a, dl_p, dl_a):
                continue
            d = cls_ts(dr_a, dr_p); w = cls_ts(wh_a, wh_p)
            dp = cls_day(ds_a, ds_p); dl = cls_day(dl_a, dl_p)  # dispatch & delivery: date-level
            n += 1
            marg["Doctor"][d] += 1; marg["Warehouse"][w] += 1
            marg["Dispatch"][dp] += 1; marg["Delivery"][dl] += 1
            l1[d][w] += 1; l2[(d, w)][dp] += 1; l3[(d, w, dp)][dl] += 1

    OUT.mkdir(parents=True, exist_ok=True)

    def cols(prefix: str, d: dict[str, int], whole: int) -> list:
        out = []
        for o in OUTS:
            out += [d[o], pct(d[o], whole)]
        return out

    hdr_suffix = []
    for o in OUTS:
        tag = o.lower().replace("-", "")
        hdr_suffix += [f"{tag}_n", f"{tag}_pct"]

    # step 0
    with open(OUT / "cascade-step0-v1.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["leg", "total_n"] + hdr_suffix)
        for leg in ("Doctor", "Warehouse", "Dispatch", "Delivery"):
            wr.writerow([leg, n] + cols("", marg[leg], n))

    # step 1
    with open(OUT / "cascade-step1-v1.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["doctor", "parent_n"] + [f"wh_{s}" for s in hdr_suffix])
        for d in OUTS:
            pn = sum(l1[d].values())
            wr.writerow([d, pn] + cols("", l1[d], pn))

    # step 2
    with open(OUT / "cascade-step2-v1.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["doctor", "wh", "parent_n"] + [f"disp_{s}" for s in hdr_suffix])
        for d in OUTS:
            for w in OUTS:
                pn = sum(l2[(d, w)].values())
                if pn == 0:
                    continue
                wr.writerow([d, w, pn] + cols("", l2[(d, w)], pn))

    # step 3
    with open(OUT / "cascade-step3-v1.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["doctor", "wh", "dispatch", "parent_n"] + [f"del_{s}" for s in hdr_suffix])
        for d in OUTS:
            for w in OUTS:
                for dp in OUTS:
                    pn = sum(l3[(d, w, dp)].values())
                    if pn == 0:
                        continue
                    wr.writerow([d, w, dp, pn] + cols("", l3[(d, w, dp)], pn))

    print(f"cohort = {n}")
    for s in ("step0", "step1", "step2", "step3"):
        print(f"wrote -> {OUT / f'cascade-{s}-v1.csv'}")


if __name__ == "__main__":
    main()
