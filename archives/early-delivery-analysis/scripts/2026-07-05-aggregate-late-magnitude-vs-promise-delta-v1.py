"""Magnitude of "Late" for rows 4/6, graded against the digitised (stale) promise --
i.e. the Late subset of digitised-promise-actual-performance.csv -- broken down by
how many days late, and in parallel by how much the promise increased.

  digitised_promise_days: date(digitised_delivery_promise) - date(digitised_dispatch_promise)
  actual_duration_days  : date(delivery_attempt_time) - date(pickup_time)
  late_by_days          : actual_duration_days - digitised_promise_days (only >0 orders selected)
  promise_delta         : shipping_delivery_promise - digitised_promise_days
                           (positive = promise increased, negative = decreased;
                           0 impossible here since row 4/6 selection requires promise changed)

Two parallel breakdowns of the same Late population, all % of that view's own Late n:
  late by 1 day / late by >=2 days                         (exhaustive, sums to 100%)
  promise increased by 1 day / by >=2 days / decreased (any amount)  (exhaustive, sums to 100%)

Population: Late orders from row4, row6, and merged (row4+row6), all drawn from the
already-validated digitised-promise-actual-performance.csv.

Emits outputs/late-magnitude-vs-promise-delta.csv.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "late-magnitude-vs-promise-delta.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"

TARGET_COHORTS = {
    ("On-Time", "Early", "Early"),
    ("On-Time", "Late", "Late"),
    ("Early", "On-Time", "Late"),
    ("Early", "Early", "Early"),
    ("Late", "On-Time", "Early"),
    ("Early", "Early", "Late"),
    ("Late", "Late", "Late"),
    ("Early", "Late", "Late"),
    ("Late", "Early", "Early"),
    ("Late", "Late", "Early"),
}


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


def pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def main() -> None:
    v2_rows: dict[str, dict[str, str]] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    tallies: dict[str, dict[str, int]] = {
        "row4": defaultdict(int), "row6": defaultdict(int), "merged": defaultdict(int)
    }

    with V1_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            oid = row["order_id"]
            r2 = v2_rows.get(oid)
            if r2 is None:
                continue
            triple = (row["dispatch_leg"], row["delivery_leg"], r2["delivery_leg"])
            if triple not in TARGET_COHORTS:
                continue

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            if not dig_partner or not ship_partner:
                continue

            dispatch_promise = parse_date(row["digitised_dispatch_promise"])
            delivery_promise = parse_date(row["digitised_delivery_promise"])
            pickup = parse_date(row["pickup_time"])
            delivery_attempt = parse_date(row["delivery_attempt_time"])
            ship_promise_raw = row["shipping_delivery_promise"].strip()
            if dispatch_promise is None or delivery_promise is None or not ship_promise_raw:
                continue

            digitised_promise_days = (delivery_promise - dispatch_promise).days
            shipping_promise_days = int(ship_promise_raw)
            promise_delta = shipping_promise_days - digitised_promise_days
            if promise_delta == 0:
                continue  # not row 4/6 -- promise didn't change

            actual_days = (delivery_attempt - pickup).days
            late_by_days = actual_days - digitised_promise_days
            if late_by_days <= 0:
                continue  # not Late against the digitised promise

            switched = dig_partner != ship_partner
            branch = "row4" if switched else "row6"

            late_bucket = "late_1_day" if late_by_days == 1 else "late_2plus_days"
            if promise_delta >= 2:
                delta_bucket = "promise_increased_2plus"
            elif promise_delta == 1:
                delta_bucket = "promise_increased_1"
            else:
                delta_bucket = "promise_decreased"

            for b in (branch, "merged"):
                tallies[b]["n_late"] += 1
                tallies[b][late_bucket] += 1
                tallies[b][delta_bucket] += 1

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow([
            "view", "n_late",
            "late_1_day_n", "late_1_day_pct",
            "late_2plus_days_n", "late_2plus_days_pct",
            "promise_increased_1_n", "promise_increased_1_pct",
            "promise_increased_2plus_n", "promise_increased_2plus_pct",
            "promise_decreased_n", "promise_decreased_pct",
        ])
        for view in ("row4", "row6", "merged"):
            t = tallies[view]
            n = t["n_late"]
            wr.writerow([
                view, n,
                t["late_1_day"], pct(t["late_1_day"], n),
                t["late_2plus_days"], pct(t["late_2plus_days"], n),
                t["promise_increased_1"], pct(t["promise_increased_1"], n),
                t["promise_increased_2plus"], pct(t["promise_increased_2plus"], n),
                t["promise_decreased"], pct(t["promise_decreased"], n),
            ])

    for view in ("row4", "row6", "merged"):
        t = tallies[view]
        n = t["n_late"]
        print(f"{view}: n_late={n} -- "
              f"late_1d={t['late_1_day']} ({pct(t['late_1_day'], n)}%), "
              f"late_2plus={t['late_2plus_days']} ({pct(t['late_2plus_days'], n)}%) | "
              f"promise_inc_1={t['promise_increased_1']} ({pct(t['promise_increased_1'], n)}%), "
              f"promise_inc_2plus={t['promise_increased_2plus']} ({pct(t['promise_increased_2plus'], n)}%), "
              f"promise_decreased={t['promise_decreased']} ({pct(t['promise_decreased'], n)}%)")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
