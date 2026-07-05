"""Day-of-week concentration check: does the 230,923-order "not amazing" cohort
cluster on particular digitisation days relative to the overall order base?

Anchor date: digitised_ts (the day the order was digitised, i.e. when the promise
gets set) -- the natural anchor given the hypothesis is about digitisation-time
capacity/staleness effects, not shipping or delivery timing.

Overall population: all 515,465 View 1 orders (not the 515,396 common View1/View2
universe) -- matches the denominator Tejas specified.

index_vs_overall = cohort's % of that weekday / overall's % of that weekday.
  1.0 = no signal, >1 = over-represented in the cohort, <1 = under-represented.

Emits outputs/cohort-day-of-week-concentration.csv.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "cohort-day-of-week-concentration.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

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


def parse_dt(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 2) if whole else 0.0


def main() -> None:
    v2_delivery: dict[str, str] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    overall_counts: dict[str, int] = defaultdict(int)
    cohort_counts: dict[str, int] = defaultdict(int)
    n_overall = 0
    n_cohort = 0
    n_unparseable = 0

    with V1_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            digitised = parse_dt(row["digitised_ts"])
            if digitised is None:
                n_unparseable += 1
                continue

            weekday = WEEKDAYS[digitised.weekday()]
            overall_counts[weekday] += 1
            n_overall += 1

            oid = row["order_id"]
            dl_v2 = v2_delivery.get(oid)
            if dl_v2 is None:
                continue
            triple = (row["dispatch_leg"], row["delivery_leg"], dl_v2)
            if triple not in TARGET_COHORTS:
                continue

            cohort_counts[weekday] += 1
            n_cohort += 1

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["weekday", "cohort_n", "cohort_pct", "overall_n", "overall_pct", "index_vs_overall"])
        for day in WEEKDAYS:
            c_n = cohort_counts[day]
            o_n = overall_counts[day]
            c_pct = pct(c_n, n_cohort)
            o_pct = pct(o_n, n_overall)
            index = round(c_pct / o_pct, 2) if o_pct else None
            wr.writerow([day, c_n, c_pct, o_n, o_pct, index])

    print(f"overall n (all View 1 orders, parseable digitised_ts): {n_overall}")
    print(f"cohort n (230,923-order 'not amazing' cohort): {n_cohort}")
    print(f"unparseable digitised_ts: {n_unparseable}")
    for day in WEEKDAYS:
        c_n, o_n = cohort_counts[day], overall_counts[day]
        c_pct, o_pct = pct(c_n, n_cohort), pct(o_n, n_overall)
        index = round(c_pct / o_pct, 2) if o_pct else None
        print(f"  {day}: cohort={c_n} ({c_pct}%), overall={o_n} ({o_pct}%), index={index}")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
