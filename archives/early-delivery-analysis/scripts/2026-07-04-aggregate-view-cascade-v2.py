"""View 1 (customer-experienced) and View 2 (ops-execution) leg outcomes.

v2 fix: View 1 cascade output changed from a Doctor x Warehouse x Dispatch cross-tab
to a per-leg marginal table -- one row per leg (Doctor/Warehouse/Dispatch/Delivery),
each with its own independent Early/On-Time/Late split. v1 wrongly nested Delivery
inside a 3-way cross-tab of the other legs instead of giving Delivery its own row.
View 2 cascade output is unchanged from v1 pending the same confirmation.

Leg rules:
  Doctor    (both views): promise vs actual call event, +/-60s buffer.
             View 1 actual = dr_confirm_ts. View 2 actual = actual_doctor_call_time.
  Warehouse (both views): digitised_dispatch_promise vs invoice_create_ts, matched to
             the minute (data has no seconds) -> less=Early, equal=On-Time, greater=Late.
             Deliberately benchmarked against the dispatch promise, not digitised_wh_promise.
  Dispatch  (both views): digitised_dispatch_promise vs pickup_time, calendar-date diff.
  Delivery  View 1: digitised_delivery_promise vs delivery_attempt_time, calendar-date diff.
  Delivery  View 2: promise_duration_days = date(delivery promise) - date(dispatch promise);
             actual_duration_days = date(delivery attempt) - date(pickup);
             compare the two integers -> less=Early, equal=On-Time, greater=Late.

Base: outputs/base-population.csv (digitised_ts > 8 May 2026, delivery_attempt_time not
null -- locked project-wide, see 2026-07-04-base-population-filter-v1.md). Each view
further drops rows missing its own required fields; final counts reported separately
per view (printed to console).

Emits per (view, cut): a leg-outcome summary CSV (outputs/viewN-cascade-<cut>.csv) and
an order-level detail CSV with all raw columns + computed leg labels
(outputs/viewN-orders-<cut>.csv) so any cohort can be pointed to directly.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "outputs" / "base-population.csv"
OUT = ROOT / "outputs"
TS_FMT = "%b %d, %Y, %I:%M %p"
BUF_S = 60
OUTCOMES = ["Early", "On-Time", "Late"]
LEGS = ["doctor", "warehouse", "dispatch", "delivery"]

CUTS: dict[str, tuple[str, str]] = {
    "all": ("any", "any"),
    "sdd-inventory": ("true", "true"),
    "sdd-noninventory": ("true", "false"),
    "nonsdd-inventory": ("false", "true"),
    "nonsdd-noninventory": ("false", "false"),
}

REQUIRED_COMMON = [
    "digitised_dr_promise",
    "invoice_create_ts",
    "digitised_dispatch_promise",
    "pickup_time",
    "digitised_delivery_promise",
    "delivery_attempt_time",
    "digitised_is_sdd",
    "digitised_is_inventory",
]


def parse_dt(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def cls_ts_buffered(actual: datetime, promised: datetime) -> str:
    diff = (actual - promised).total_seconds()
    return "Early" if diff < -BUF_S else "Late" if diff > BUF_S else "On-Time"


def cls_ts_exact(actual: datetime, promised: datetime) -> str:
    return "Early" if actual < promised else "Late" if actual > promised else "On-Time"


def cls_day(actual_date: date, promised_date: date) -> str:
    diff = (actual_date - promised_date).days
    return "Early" if diff < 0 else "Late" if diff > 0 else "On-Time"


def cls_duration(actual_days: int, promise_days: int) -> str:
    return "Early" if actual_days < promise_days else "Late" if actual_days > promise_days else "On-Time"


def pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def row_is_complete(row: dict, doctor_actual_col: str) -> bool:
    for col in REQUIRED_COMMON + [doctor_actual_col]:
        if not (row.get(col) or "").strip():
            return False
    sdd = row["digitised_is_sdd"].strip().lower()
    inv = row["digitised_is_inventory"].strip().lower()
    return sdd in ("true", "false") and inv in ("true", "false")


def classify_view1(row: dict) -> tuple[str, str, str, str]:
    dr_p, dr_a = parse_dt(row["digitised_dr_promise"]), parse_dt(row["dr_confirm_ts"])
    wh_p, wh_a = parse_dt(row["digitised_dispatch_promise"]), parse_dt(row["invoice_create_ts"])
    ds_p, ds_a = parse_dt(row["digitised_dispatch_promise"]), parse_dt(row["pickup_time"])
    dl_p, dl_a = parse_dt(row["digitised_delivery_promise"]), parse_dt(row["delivery_attempt_time"])
    doctor = cls_ts_buffered(dr_a, dr_p)
    warehouse = cls_ts_exact(wh_a, wh_p)
    dispatch = cls_day(ds_a.date(), ds_p.date())
    delivery = cls_day(dl_a.date(), dl_p.date())
    return doctor, warehouse, dispatch, delivery


def classify_view2(row: dict) -> tuple[str, str, str, str]:
    dr_p, dr_a = parse_dt(row["digitised_dr_promise"]), parse_dt(row["actual_doctor_call_time"])
    wh_p, wh_a = parse_dt(row["digitised_dispatch_promise"]), parse_dt(row["invoice_create_ts"])
    ds_p, ds_a = parse_dt(row["digitised_dispatch_promise"]), parse_dt(row["pickup_time"])
    dl_p, dl_a = parse_dt(row["digitised_delivery_promise"]), parse_dt(row["delivery_attempt_time"])
    doctor = cls_ts_buffered(dr_a, dr_p)
    warehouse = cls_ts_exact(wh_a, wh_p)
    dispatch = cls_day(ds_a.date(), ds_p.date())
    promise_days = (dl_p.date() - ds_p.date()).days
    actual_days = (dl_a.date() - ds_a.date()).days
    delivery = cls_duration(actual_days, promise_days)
    return doctor, warehouse, dispatch, delivery


def cut_key(row: dict) -> str:
    sdd = row["digitised_is_sdd"].strip().lower()
    inv = row["digitised_is_inventory"].strip().lower()
    for name, (want_sdd, want_inv) in CUTS.items():
        if name == "all":
            continue
        if sdd == want_sdd and inv == want_inv:
            return name
    raise ValueError(f"unmatched sdd/inventory combo: {sdd}, {inv}")


class MarginalCohort:
    """Per-leg independent Early/On-Time/Late distribution (no cross-tab)."""

    def __init__(self) -> None:
        self.marg: dict[str, dict[str, int]] = {leg: defaultdict(int) for leg in LEGS}
        self.n = 0

    def add(self, doctor: str, warehouse: str, dispatch: str, delivery: str) -> None:
        self.n += 1
        self.marg["doctor"][doctor] += 1
        self.marg["warehouse"][warehouse] += 1
        self.marg["dispatch"][dispatch] += 1
        self.marg["delivery"][delivery] += 1


def write_marginal_cascade(cohorts: dict[str, MarginalCohort], view_tag: str) -> None:
    for cut_name, co in cohorts.items():
        path = OUT / f"{view_tag}-cascade-{cut_name}.csv"
        with path.open("w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(
                ["leg", "count"]
                + ["early_n", "early_pct"]
                + ["ontime_n", "ontime_pct"]
                + ["late_n", "late_pct"]
            )
            for leg in LEGS:
                counts = co.marg[leg]
                row = [leg.capitalize(), co.n]
                for o in OUTCOMES:
                    row += [counts[o], pct(counts[o], co.n)]
                wr.writerow(row)


def main() -> None:
    seen: set[str] = set()

    cohorts_v1: dict[str, MarginalCohort] = {name: MarginalCohort() for name in CUTS}

    OUT.mkdir(parents=True, exist_ok=True)
    detail_writers_v1: dict[str, csv.DictWriter] = {}
    detail_files = []

    n_total = 0
    n_v1_complete = 0

    with open(BASE_PATH, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        detail_fields = fieldnames + ["doctor_leg", "warehouse_leg", "dispatch_leg", "delivery_leg"]

        for cut_name in CUTS:
            fh1 = open(OUT / f"view1-orders-{cut_name}.csv", "w", newline="")
            detail_files.append(fh1)
            w1 = csv.DictWriter(fh1, fieldnames=detail_fields)
            w1.writeheader()
            detail_writers_v1[cut_name] = w1

        for row in reader:
            oid = row["order_id"].strip()
            if oid in seen:
                continue
            seen.add(oid)
            n_total += 1

            if row_is_complete(row, "dr_confirm_ts"):
                n_v1_complete += 1
                d, w, dp, dl = classify_view1(row)
                cohorts_v1["all"].add(d, w, dp, dl)
                out_row = dict(row)
                out_row.update(doctor_leg=d, warehouse_leg=w, dispatch_leg=dp, delivery_leg=dl)
                detail_writers_v1["all"].writerow(out_row)
                ck = cut_key(row)
                cohorts_v1[ck].add(d, w, dp, dl)
                detail_writers_v1[ck].writerow(out_row)

    for fh in detail_files:
        fh.close()

    write_marginal_cascade(cohorts_v1, "view1")

    print(f"base population rows (deduped): {n_total}")
    print(f"View 1 final N (dr_confirm_ts leg): {n_v1_complete} ({n_v1_complete / n_total:.1%})")
    for name in CUTS:
        print(f"  view1 cut={name}: n={cohorts_v1[name].n}")
    print("NOTE: View 2 cascade files (view2-cascade-*.csv) untouched by this run -- still")
    print("the old cross-tab shape from v1, pending same confirmation for View 2.")


if __name__ == "__main__":
    main()
