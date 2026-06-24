"""Cascade levels v3 — v2 + exclude blank digitised state (no instrumentation blanks).

Same as v2 (Doctor = actual_doctor_call_time vs promise; WH +/-1 min; Dispatch & Delivery date)
but adds: digitised_is_sdd must be populated (true/false) — drops the ~7k post-May-8 residual
blank-state orders, so every order has a real SDD / inventory / MFC value.

Cohorts (both: delivery attempt present, digitised_ts >= 2026-05-08, all 4 legs' timestamps
present, wh_processing_mins != 0, digitised_is_sdd in {true,false}):
    ALL      — every order with populated state
    COURIER  — digitised_is_sdd == false

Emits 8 Sheets-ready CSVs: cascade-{all,courier}-step{0,1,2,3}-v3.csv
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


class Cohort:
    def __init__(self) -> None:
        self.marg = {k: defaultdict(int) for k in ("Doctor", "Warehouse", "Dispatch", "Delivery")}
        self.l1: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.l2: dict[tuple, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.l3: dict[tuple, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.n = 0

    def add(self, d: str, w: str, dp: str, dl: str) -> None:
        self.n += 1
        self.marg["Doctor"][d] += 1; self.marg["Warehouse"][w] += 1
        self.marg["Dispatch"][dp] += 1; self.marg["Delivery"][dl] += 1
        self.l1[d][w] += 1; self.l2[(d, w)][dp] += 1; self.l3[(d, w, dp)][dl] += 1


def cols(d: dict[str, int], whole: int) -> list:
    out = []
    for o in OUTS:
        out += [d[o], pct(d[o], whole)]
    return out


def write_cohort(co: Cohort, tag: str) -> None:
    suffix = []
    for o in OUTS:
        t = o.lower().replace("-", "")
        suffix += [f"{t}_n", f"{t}_pct"]

    with open(OUT / f"cascade-{tag}-step0-v3.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["leg", "total_n"] + suffix)
        for leg in ("Doctor", "Warehouse", "Dispatch", "Delivery"):
            wr.writerow([leg, co.n] + cols(co.marg[leg], co.n))

    with open(OUT / f"cascade-{tag}-step1-v3.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["doctor", "parent_n"] + [f"wh_{s}" for s in suffix])
        for d in OUTS:
            pn = sum(co.l1[d].values())
            wr.writerow([d, pn] + cols(co.l1[d], pn))

    with open(OUT / f"cascade-{tag}-step2-v3.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["doctor", "wh", "parent_n"] + [f"disp_{s}" for s in suffix])
        for d in OUTS:
            for w in OUTS:
                pn = sum(co.l2[(d, w)].values())
                if pn:
                    wr.writerow([d, w, pn] + cols(co.l2[(d, w)], pn))

    with open(OUT / f"cascade-{tag}-step3-v3.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["doctor", "wh", "dispatch", "parent_n"] + [f"del_{s}" for s in suffix])
        for d in OUTS:
            for w in OUTS:
                for dp in OUTS:
                    pn = sum(co.l3[(d, w, dp)].values())
                    if pn:
                        wr.writerow([d, w, dp, pn] + cols(co.l3[(d, w, dp)], pn))


def main() -> None:
    seen: set[str] = set()
    co_all, co_cour = Cohort(), Cohort()
    n_blank_state = 0

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
            sdd = (row["digitised_is_sdd"] or "").strip().lower()
            if sdd not in ("true", "false"):   # exclude blank digitised state
                n_blank_state += 1
                continue
            dr_p = parse_dt(row["digitised_dr_promise"]); dr_a = parse_dt(row["actual_doctor_call_time"])
            wh_p = parse_dt(row["digitised_wh_promise"]); wh_a = parse_dt(row["actual_warehouse_processing"])
            ds_p = parse_dt(row["digitised_dispatch_promise"]); ds_a = parse_dt(row["pickup_time"])
            dl_p = parse_dt(row["digitised_delivery_promise"]); dl_a = parse_dt(row["delivery_attempt_time"])
            if None in (dr_p, dr_a, wh_p, wh_a, ds_p, ds_a, dl_p, dl_a):
                continue
            d = cls_ts(dr_a, dr_p); w = cls_ts(wh_a, wh_p)
            dp = cls_day(ds_a, ds_p); dl = cls_day(dl_a, dl_p)
            co_all.add(d, w, dp, dl)
            if sdd == "false":
                co_cour.add(d, w, dp, dl)

    OUT.mkdir(parents=True, exist_ok=True)
    write_cohort(co_all, "all")
    write_cohort(co_cour, "courier")
    print(f"excluded blank digitised state: {n_blank_state}")
    print(f"ALL cohort     = {co_all.n}")
    print(f"COURIER cohort = {co_cour.n}")
    print("wrote 8 CSVs: cascade-{all,courier}-step{0..3}-v3.csv")


if __name__ == "__main__":
    main()
