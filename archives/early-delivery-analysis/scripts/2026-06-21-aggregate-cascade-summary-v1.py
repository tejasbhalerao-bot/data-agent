"""Cascade — simplified, readable views (companion to the full 120-node tree).

Same cohort + leg definitions as aggregate-cascade-tree-v1.
Bands: Doctor & WH = +/-1 min (timestamp). Dispatch & Delivery = date-level.

Outputs:
  1. MARGINAL  — delivery E/OT/L split conditioned on each leg alone (Doctor / WH / Dispatch).
  2. PIVOT     — 27 upstream paths (Doctor x WH x Dispatch), each with its delivery split. No blanks.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "raw-data" / "early-delivery-raw-may-2026.csv"
OUT_PIVOT = ROOT / "outputs" / "cascade-pivot-v1.csv"
OUT_MARG = ROOT / "outputs" / "cascade-marginal-v1.csv"
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


def main() -> None:
    seen: set[str] = set()
    marg = {leg: defaultdict(lambda: defaultdict(int)) for leg in ("Doctor", "Warehouse", "Dispatch")}
    pivot: dict[tuple[str, str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    cohort = 0

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
            doc = cls_ts(dr_a, dr_p); wh = cls_ts(wh_a, wh_p)
            disp = cls_day(ds_a, ds_p); dele = cls_day(dl_a, dl_p)  # dispatch & delivery: date-level
            cohort += 1
            marg["Doctor"][doc][dele] += 1
            marg["Warehouse"][wh][dele] += 1
            marg["Dispatch"][disp][dele] += 1
            pivot[(doc, wh, disp)][dele] += 1

    print(f"cohort = {cohort}\n")

    # ---- marginals ----
    marg_rows = [["leg", "leg_outcome", "orders", "delivery_early_pct", "delivery_ontime_pct", "delivery_late_pct"]]
    for leg in ("Doctor", "Warehouse", "Dispatch"):
        print(f"=== Delivery outcome when {leg.upper()} is... ===")
        print(f"  {'leg':>9} {'orders':>8} | {'Del Early':>9} {'Del OnTime':>10} {'Del Late':>9}")
        for o in OUTS:
            d = marg[leg][o]
            n = sum(d.values())
            if n == 0:
                continue
            e, ot, lt = d["Early"] / n * 100, d["On-Time"] / n * 100, d["Late"] / n * 100
            print(f"  {o:>9} {n:>8d} | {e:8.1f}% {ot:9.1f}% {lt:8.1f}%")
            marg_rows.append([leg, o, n, round(e, 1), round(ot, 1), round(lt, 1)])
        print()

    # ---- pivot (27 rows, sorted by volume) ----
    piv_rows = [["Doctor", "Warehouse", "Dispatch", "Orders", "Pct_Cohort",
                 "Del_Early_pct", "Del_OnTime_pct", "Del_Late_pct"]]
    items = []
    for key, d in pivot.items():
        n = sum(d.values())
        items.append((key, n, d))
    items.sort(key=lambda x: -x[1])
    print("=== PIVOT: upstream path -> delivery split (sorted by volume) ===")
    print(f"  {'Doctor':>8} {'WH':>8} {'Dispatch':>8} {'Orders':>8} {'Coh%':>6} | "
          f"{'DelE%':>6} {'DelOT%':>6} {'DelL%':>6}")
    for (doc, wh, disp), n, d in items:
        e, ot, lt = d["Early"] / n * 100, d["On-Time"] / n * 100, d["Late"] / n * 100
        print(f"  {doc:>8} {wh:>8} {disp:>8} {n:>8d} {n/cohort*100:5.1f}% | "
              f"{e:5.1f}% {ot:5.1f}% {lt:5.1f}%")
        piv_rows.append([doc, wh, disp, n, round(n / cohort * 100, 2),
                         round(e, 1), round(ot, 1), round(lt, 1)])

    OUT_PIVOT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PIVOT, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(piv_rows)
    with open(OUT_MARG, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(marg_rows)
    print(f"\nwrote -> {OUT_PIVOT}\nwrote -> {OUT_MARG}")


if __name__ == "__main__":
    main()
