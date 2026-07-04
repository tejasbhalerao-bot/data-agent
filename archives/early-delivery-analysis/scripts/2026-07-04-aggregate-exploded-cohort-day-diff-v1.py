"""Day-level temporal histogram for the 10 "operations breaking" cohorts.

Cohorts (Dispatch, Delivery-View1, Delivery-View2) selected -- the complement of the
3 "ops not breaking" rows from view1-dispatch-delivery-v1v2-crosstab.csv:
  (On-Time,Early,Early) (On-Time,Late,Late) (Early,On-Time,Late) (Early,Early,Early)
  (Late,On-Time,Early) (Early,Early,Late) (Late,Late,Late) (Early,Late,Late)
  (Late,Early,Early) (Late,Late,Early)
Total: 230,923 orders (common View1/View2 universe of 515,396, minus the 284,473 in
On-Time/On-Time/On-Time + Early/Early/On-Time + Late/Late/On-Time).

For every order in these 10 cohorts, computes the exact day-diff already underlying
the View 1 Delivery leg label: date(delivery_attempt_time) - date(digitised_delivery_promise).
Negative = N days early, 0 = on-time, positive = N days late. This is the calendar,
customer-facing measure (not View 2's duration-diff).

Emits outputs/exploded-cohorts-delivery-day-diff-histogram.csv: one row per day-diff
value, with order count and % of the 230,923-order cohort total.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "exploded-cohorts-delivery-day-diff-histogram.csv"
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
        return f"{-day_diff} day(s) early"
    if day_diff > 0:
        return f"{day_diff} day(s) late"
    return "On-Time (0 days)"


def main() -> None:
    v2_delivery: dict[str, str] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    histogram: Counter[int] = Counter()
    n_selected = 0

    with V1_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            oid = row["order_id"]
            dl_v2 = v2_delivery.get(oid)
            if dl_v2 is None:
                continue
            triple = (row["dispatch_leg"], row["delivery_leg"], dl_v2)
            if triple not in TARGET_COHORTS:
                continue

            promise = parse_date(row["digitised_delivery_promise"])
            actual = parse_date(row["delivery_attempt_time"])
            day_diff = (actual - promise).days

            histogram[day_diff] += 1
            n_selected += 1

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["day_diff", "label", "count", "pct_of_cohort"])
        for day_diff in sorted(histogram):
            n = histogram[day_diff]
            wr.writerow([day_diff, label(day_diff), n, pct(n, n_selected)])

    print(f"n_selected (10-cohort total): {n_selected}")
    print(f"distinct day_diff values: {len(histogram)}")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
