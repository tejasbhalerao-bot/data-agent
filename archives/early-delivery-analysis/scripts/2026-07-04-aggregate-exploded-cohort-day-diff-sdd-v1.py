"""SDD vs Non-SDD split of the ops (View 2) day-diff histogram for the 10 "ops
breaking" cohorts (same 230,923-order population as
2026-07-04-aggregate-exploded-cohort-day-diff-v2.py, sliced by digitised_is_sdd
at time of digitisation -- not the shipping-time value).

Same day_diff definition as v2: actual_duration_days - promise_duration_days, where
  actual_duration_days  = date(delivery_attempt_time) - date(pickup_time)
  promise_duration_days = date(digitised_delivery_promise) - date(digitised_dispatch_promise)

Emits two files, each with % relative to that group's own total (not the combined
230,923), consistent with how the View 1/View 2 SDD cuts were reported earlier:
  outputs/exploded-cohorts-delivery-day-diff-sdd.csv
  outputs/exploded-cohorts-delivery-day-diff-nonsdd.csv
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_SDD = ROOT / "outputs" / "exploded-cohorts-delivery-day-diff-sdd.csv"
OUT_NONSDD = ROOT / "outputs" / "exploded-cohorts-delivery-day-diff-nonsdd.csv"
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


def write_group(path: Path, histogram: Counter[int], n: int) -> None:
    with path.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["day_diff", "label", "count", "pct_of_group"])
        for day_diff in sorted(histogram):
            c = histogram[day_diff]
            wr.writerow([day_diff, label(day_diff), c, pct(c, n)])


def main() -> None:
    v2_rows: dict[str, dict[str, str]] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    hist_sdd: Counter[int] = Counter()
    hist_nonsdd: Counter[int] = Counter()
    n_sdd = 0
    n_nonsdd = 0
    n_unclassified_sdd = 0

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

            sdd = row["digitised_is_sdd"].strip().lower()
            if sdd == "true":
                hist_sdd[day_diff] += 1
                n_sdd += 1
            elif sdd == "false":
                hist_nonsdd[day_diff] += 1
                n_nonsdd += 1
            else:
                n_unclassified_sdd += 1

    write_group(OUT_SDD, hist_sdd, n_sdd)
    write_group(OUT_NONSDD, hist_nonsdd, n_nonsdd)

    print(f"SDD n: {n_sdd}")
    print(f"Non-SDD n: {n_nonsdd}")
    print(f"unclassified digitised_is_sdd (excluded, should be 0 -- required field for this cohort): {n_unclassified_sdd}")
    print(f"SDD + Non-SDD = {n_sdd + n_nonsdd} (expected 230,923)")
    print(f"wrote: {OUT_SDD}")
    print(f"wrote: {OUT_NONSDD}")


if __name__ == "__main__":
    main()
