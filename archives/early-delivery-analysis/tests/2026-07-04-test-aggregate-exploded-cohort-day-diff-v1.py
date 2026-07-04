"""Sanity checks for exploded-cohorts-delivery-day-diff-histogram.csv.

Checks:
1. Histogram total equals 230,923 (the verified sum of the 10 target cohorts, and the
   exact complement of the 3 "ops not breaking" rows out of the 515,396 common universe).
2. Per-cohort recount: for each of the 10 target (dispatch, delivery_view1, delivery_view2)
   triples, the number of orders selected here must exactly match the count already
   published (and separately validated) in view1-dispatch-delivery-v1v2-crosstab.csv.
3. Sign consistency: every order's day_diff sign must agree with its own delivery_leg
   (View 1) label -- negative/zero/positive must map to Early/On-Time/Late exactly,
   since that label was originally derived from this same day_diff.
4. Marginal check: sum of negative-day-diff buckets = sum of the 4 target cohorts with
   delivery_view1=Early (115,754); day_diff=0 bucket = sum of the 2 cohorts with
   delivery_view1=On-Time (52,220); sum of positive buckets = sum of the 4 cohorts with
   delivery_view1=Late (62,949).

Run: python3 archives/early-delivery-analysis/tests/2026-07-04-test-aggregate-exploded-cohort-day-diff-v1.py
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
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
EARLY_COHORTS = {("On-Time", "Early", "Early"), ("Early", "Early", "Early"),
                 ("Early", "Early", "Late"), ("Late", "Early", "Early")}
ONTIME_COHORTS = {("Early", "On-Time", "Late"), ("Late", "On-Time", "Early")}
LATE_COHORTS = {("On-Time", "Late", "Late"), ("Late", "Late", "Late"),
                 ("Early", "Late", "Late"), ("Late", "Late", "Early")}
EXPECTED_TOTAL = 230_923


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


def main() -> None:
    failures: list[str] = []

    v2_delivery: dict[str, str] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    per_cohort_recount: Counter[tuple[str, str, str]] = Counter()
    day_diff_histogram: Counter[int] = Counter()
    sign_mismatches = 0
    n_selected = 0

    with (OUT / "view1-orders-all.csv").open(newline="") as f:
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

            expected_sign_label = row["delivery_leg"]
            actual_sign_label = "Early" if day_diff < 0 else "Late" if day_diff > 0 else "On-Time"
            if expected_sign_label != actual_sign_label:
                sign_mismatches += 1

            per_cohort_recount[triple] += 1
            day_diff_histogram[day_diff] += 1
            n_selected += 1

    if n_selected != EXPECTED_TOTAL:
        failures.append(f"total selected={n_selected}, expected {EXPECTED_TOTAL}")

    if sign_mismatches:
        failures.append(f"{sign_mismatches} orders have day_diff sign inconsistent with their delivery_leg label")

    crosstab_counts: dict[tuple[str, str, str], int] = {}
    with (OUT / "view1-dispatch-delivery-v1v2-crosstab.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            crosstab_counts[(r["dispatch"], r["delivery_view1"], r["delivery_view2"])] = int(r["count"])

    for triple in TARGET_COHORTS:
        expected = crosstab_counts.get(triple, 0)
        actual = per_cohort_recount.get(triple, 0)
        if expected != actual:
            failures.append(f"cohort {triple}: crosstab says {expected}, histogram selection has {actual}")

    negative_sum = sum(n for d, n in day_diff_histogram.items() if d < 0)
    zero_sum = day_diff_histogram.get(0, 0)
    positive_sum = sum(n for d, n in day_diff_histogram.items() if d > 0)

    expected_negative = sum(crosstab_counts.get(t, 0) for t in EARLY_COHORTS)
    expected_zero = sum(crosstab_counts.get(t, 0) for t in ONTIME_COHORTS)
    expected_positive = sum(crosstab_counts.get(t, 0) for t in LATE_COHORTS)

    if negative_sum != expected_negative:
        failures.append(f"negative day_diff sum={negative_sum}, expected {expected_negative}")
    if zero_sum != expected_zero:
        failures.append(f"zero day_diff sum={zero_sum}, expected {expected_zero}")
    if positive_sum != expected_positive:
        failures.append(f"positive day_diff sum={positive_sum}, expected {expected_positive}")

    histogram_csv_total = 0
    with (OUT / "exploded-cohorts-delivery-day-diff-histogram.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            histogram_csv_total += int(r["count"])
    if histogram_csv_total != n_selected:
        failures.append(f"published histogram CSV totals {histogram_csv_total}, recount gives {n_selected}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- {n_selected} orders selected across the 10 target cohorts (matches "
          f"expected {EXPECTED_TOTAL}), every order's day_diff sign matches its own "
          f"delivery_leg label, per-cohort counts match the validated crosstab, and "
          f"Early/On-Time/Late marginal sums reconcile exactly.")


if __name__ == "__main__":
    main()
