"""Sanity checks for exploded-cohorts-delivery-day-diff-histogram-v2.csv.

v1's test would not have caught v1's bug (it checked sign against delivery_leg from
View 1, which was consistent with v1's own -- wrong -- diff by construction). This
version checks against View 2's delivery_leg instead, and adds the hard structural
check that should have existed from the start: zero orders at day_diff=0, since all
10 target cohorts are defined by delivery_view2 != On-Time.

Checks:
1. Histogram total equals 230,923.
2. Zero orders at day_diff=0 (hard constraint given cohort selection).
3. Per-cohort recount matches the already-validated view1-dispatch-delivery-v1v2-crosstab.csv.
4. Sign consistency: every order's day_diff sign must agree with its own View 2
   delivery_leg label (not View 1's).
5. Marginal check: negative-diff sum = sum of the 5 cohorts with delivery_view2=Early
   (117,907); positive-diff sum = sum of the 5 cohorts with delivery_view2=Late (113,016).

Run: python3 archives/early-delivery-analysis/tests/2026-07-04-test-aggregate-exploded-cohort-day-diff-v2.py
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
VIEW2_EARLY_COHORTS = {("On-Time", "Early", "Early"), ("Early", "Early", "Early"),
                        ("Late", "On-Time", "Early"), ("Late", "Early", "Early"),
                        ("Late", "Late", "Early")}
VIEW2_LATE_COHORTS = {("On-Time", "Late", "Late"), ("Early", "On-Time", "Late"),
                       ("Early", "Early", "Late"), ("Late", "Late", "Late"),
                       ("Early", "Late", "Late")}
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

    v2_rows: dict[str, dict[str, str]] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    per_cohort_recount: Counter[tuple[str, str, str]] = Counter()
    day_diff_histogram: Counter[int] = Counter()
    sign_mismatches = 0
    n_selected = 0

    with (OUT / "view1-orders-all.csv").open(newline="") as f:
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

            expected_sign_label = r2["delivery_leg"]
            actual_sign_label = "Early" if day_diff < 0 else "Late" if day_diff > 0 else "On-Time"
            if expected_sign_label != actual_sign_label:
                sign_mismatches += 1

            per_cohort_recount[triple] += 1
            day_diff_histogram[day_diff] += 1
            n_selected += 1

    if n_selected != EXPECTED_TOTAL:
        failures.append(f"total selected={n_selected}, expected {EXPECTED_TOTAL}")

    if day_diff_histogram.get(0, 0) != 0:
        failures.append(
            f"{day_diff_histogram.get(0, 0)} orders at day_diff=0 -- should be 0, "
            f"all 10 target cohorts exclude delivery_view2=On-Time"
        )

    if sign_mismatches:
        failures.append(f"{sign_mismatches} orders have day_diff sign inconsistent with their View 2 delivery_leg label")

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
    positive_sum = sum(n for d, n in day_diff_histogram.items() if d > 0)
    expected_negative = sum(crosstab_counts.get(t, 0) for t in VIEW2_EARLY_COHORTS)
    expected_positive = sum(crosstab_counts.get(t, 0) for t in VIEW2_LATE_COHORTS)

    if negative_sum != expected_negative:
        failures.append(f"negative day_diff sum={negative_sum}, expected {expected_negative}")
    if positive_sum != expected_positive:
        failures.append(f"positive day_diff sum={positive_sum}, expected {expected_positive}")

    histogram_csv_total = 0
    with (OUT / "exploded-cohorts-delivery-day-diff-histogram-v2.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            histogram_csv_total += int(r["count"])
    if histogram_csv_total != n_selected:
        failures.append(f"published histogram CSV totals {histogram_csv_total}, recount gives {n_selected}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- {n_selected} orders selected (matches expected {EXPECTED_TOTAL}), "
          f"zero orders at day_diff=0 as required, every order's day_diff sign matches "
          f"its own View 2 delivery_leg label, per-cohort counts match the validated "
          f"crosstab, and Early({expected_negative})/Late({expected_positive}) marginal "
          f"sums reconcile exactly.")


if __name__ == "__main__":
    main()
