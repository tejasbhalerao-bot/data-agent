"""Cascade tree — Doctor -> Warehouse -> Dispatch -> Delivery, E/OT/L at each leg.

Each leg = actual handoff vs its digitised promise:
    Doctor   : dr_confirm_ts                vs digitised_dr_promise          (+/-1 min)
    Warehouse: actual_warehouse_processing  vs digitised_wh_promise          (+/-1 min)
    Dispatch : pickup_time                  vs digitised_dispatch_promise    (date-level)
    Delivery : delivery_attempt_time        vs digitised_delivery_promise    (date-level)

Early = actual before promise, Late = actual after, On-Time = within band.
Cohort: all 8 timestamps present, digitised_ts >= 2026-05-08, wh_processing_mins != 0.

Output: one row per tree node (3 + 9 + 27 + 81 = 120 rows), depth-first, with
order count, % of cohort, and % of parent (the conditional that shows cascade).
CSV is Google-Sheets-pasteable.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime, date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "raw-data" / "early-delivery-raw-may-2026.csv"
OUT_PATH = ROOT / "outputs" / "cascade-tree-v1.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"
CUTOVER = date(2026, 5, 8)
BUF_S = 60  # +/-1 min for sub-day legs
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


def main() -> None:
    seen: set[str] = set()
    leaves: Counter[tuple[str, str, str, str]] = Counter()
    n_missing = n_zero = n_pre = 0

    with open(RAW_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            oid = (row["order_id"] or "").replace(",", "").strip()
            if oid in seen:
                continue
            seen.add(oid)
            dig = parse_dt(row["digitised_ts"])
            if dig is None or dig.date() < CUTOVER:
                n_pre += 1
                continue
            if parse_num(row["digitised_wh_process_mins"]) == 0:
                n_zero += 1
                continue
            dr_p = parse_dt(row["digitised_dr_promise"]); dr_a = parse_dt(row["dr_confirm_ts"])
            wh_p = parse_dt(row["digitised_wh_promise"]); wh_a = parse_dt(row["actual_warehouse_processing"])
            ds_p = parse_dt(row["digitised_dispatch_promise"]); ds_a = parse_dt(row["pickup_time"])
            dl_p = parse_dt(row["digitised_delivery_promise"]); dl_a = parse_dt(row["delivery_attempt_time"])
            if None in (dr_p, dr_a, wh_p, wh_a, ds_p, ds_a, dl_p, dl_a):
                n_missing += 1
                continue
            leaves[(cls_ts(dr_a, dr_p), cls_ts(wh_a, wh_p),
                     cls_day(ds_a, ds_p), cls_day(dl_a, dl_p))] += 1  # dispatch & delivery: date-level

    cohort = sum(leaves.values())
    n_doc = Counter()
    n_dw = Counter()
    n_dwd = Counter()
    for (d, w, dp, dl), c in leaves.items():
        n_doc[d] += c
        n_dw[(d, w)] += c
        n_dwd[(d, w, dp)] += c

    print(f"cohort = {cohort}   (excluded: pre-May8={n_pre}, zero-SLA={n_zero}, missing-ts={n_missing})\n")

    rows = [["Doctor", "Warehouse", "Dispatch", "Delivery", "Orders", "Pct_Cohort", "Pct_Parent"]]

    def pct(a: int, b: int) -> str:
        return f"{a / b * 100:.2f}%" if b else "0.00%"

    for d in OUTS:
        nd = n_doc[d]
        rows.append([d, "", "", "", nd, pct(nd, cohort), pct(nd, cohort)])
        for w in OUTS:
            ndw = n_dw[(d, w)]
            rows.append([d, w, "", "", ndw, pct(ndw, cohort), pct(ndw, nd)])
            for dp in OUTS:
                ndwd = n_dwd[(d, w, dp)]
                rows.append([d, w, dp, "", ndwd, pct(ndwd, cohort), pct(ndwd, ndw)])
                for dl in OUTS:
                    c = leaves[(d, w, dp, dl)]
                    rows.append([d, w, dp, dl, c, pct(c, cohort), pct(c, ndwd)])

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)

    # echo CSV to stdout for paste
    for r in rows:
        print(",".join(str(x) for x in r))
    print(f"\nwrote -> {OUT_PATH}")


if __name__ == "__main__":
    main()
