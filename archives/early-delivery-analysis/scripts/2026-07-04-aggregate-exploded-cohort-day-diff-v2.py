"""Day-level temporal histogram for the 10 "operations breaking" cohorts -- v2 fix.

v1 wrongly used the View 1 (customer, calendar-date) delivery diff. Since all 10
target cohorts are defined by delivery_view2 != On-Time, the ops-based diff can
never legitimately be 0 for any of these orders -- v1 showed 22.6% at 0 days
because it was measuring the wrong leg's diff entirely. Fixed here to use the
View 2 (ops) duration-diff instead:

  actual_duration_days  = date(delivery_attempt_time) - date(pickup_time)
  promise_duration_days = date(digitised_delivery_promise) - date(digitised_dispatch_promise)
  day_diff = actual_duration_days - promise_duration_days

Negative = ops beat its own duration target by N days, 0 = ops hit it exactly
(should never appear here by construction), positive = ops missed its own duration
target by N days.

Cohorts (Dispatch, Delivery-View1, Delivery-View2), complement of the 3 "ops not
breaking" rows out of the 515,396 common View1/View2 universe. Total: 230,923 orders.

Emits outputs/exploded-cohorts-delivery-day-diff-histogram-v2.csv: one row per
day-diff value, with order count and % of the 230,923-order cohort total.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "exploded-cohorts-delivery-day-diff-histogram-v2.csv"
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


def label(day_diff: int) -> str:
    if day_diff < 0:
        return f"{-day_diff} day(s) ahead of ops target"
    if day_diff > 0:
        return f"{day_diff} day(s) over ops target"
    return "ops On-Time (0 days) -- should not occur in this cohort"


def main() -> None:
    v2_rows: dict[str, dict[str, str]] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    histogram: Counter[int] = Counter()
    n_selected = 0

    with V1_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            oid = row["order_id"]
            r2 = v2_rows.get(oid)
            if r2 is None:
                continue
            triple = (row["dispatch_leg"], row["delivery_leg"], r2["delivery_leg"])
            if triple not in TARGET_COHORTS:
                continue

            dispatch_promise = parse_date(row["digitised_dispatch_promise"])
            pickup = parse_date(row["pickup_time"])
            delivery_promise = parse_date(row["digitised_delivery_promise"])
            delivery_attempt = parse_date(row["delivery_attempt_time"])

            actual_duration = (delivery_attempt - pickup).days
            promise_duration = (delivery_promise - dispatch_promise).days
            day_diff = actual_duration - promise_duration

            histogram[day_diff] += 1
            n_selected += 1

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["day_diff", "label", "count", "pct_of_cohort"])
        for day_diff in sorted(histogram):
            n = histogram[day_diff]
            wr.writerow([day_diff, label(day_diff), n, pct(n, n_selected)])

    n_zero = histogram.get(0, 0)
    print(f"n_selected (10-cohort total): {n_selected}")
    print(f"distinct day_diff values: {len(histogram)}")
    print(f"orders at day_diff=0: {n_zero} (must be 0 by construction)")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
