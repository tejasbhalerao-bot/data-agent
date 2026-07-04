"""Sanity checks for exploded-cohorts-delivery-day-diff-{sdd,nonsdd}.csv.

Checks:
1. SDD total + Non-SDD total = 230,923 (the full ops-breaking cohort from
   2026-07-04-aggregate-exploded-cohort-day-diff-v2.py) with zero unclassified.
2. Zero orders at day_diff=0 in either group (same hard constraint as the unsplit
   histogram -- these cohorts exclude delivery_view2=On-Time regardless of SDD).
3. Per-group recount directly from the order-detail files matches the published CSVs.
4. Every order lands in exactly one of the two groups (no double counting).

Run: python3 archives/early-delivery-analysis/tests/2026-07-04-test-aggregate-exploded-cohort-day-diff-sdd-v1.py
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
EXPECTED_TOTAL = 230_923


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


def load_group_csv(path: Path) -> tuple[Counter[int], int]:
    hist: Counter[int] = Counter()
    with path.open(newline="") as f:
        for r in csv.DictReader(f):
            hist[int(r["day_diff"])] = int(r["count"])
    return hist, sum(hist.values())


def main() -> None:
    failures: list[str] = []

    v2_rows: dict[str, dict[str, str]] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    recount_sdd: Counter[int] = Counter()
    recount_nonsdd: Counter[int] = Counter()
    n_sdd = n_nonsdd = n_unclassified = 0

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
            day_diff = (delivery_attempt - pickup).days - (delivery_promise - dispatch_promise).days

            sdd = row["digitised_is_sdd"].strip().lower()
            if sdd == "true":
                recount_sdd[day_diff] += 1
                n_sdd += 1
            elif sdd == "false":
                recount_nonsdd[day_diff] += 1
                n_nonsdd += 1
            else:
                n_unclassified += 1

    if n_unclassified:
        failures.append(f"{n_unclassified} orders have unclassified digitised_is_sdd -- expected 0")

    if n_sdd + n_nonsdd != EXPECTED_TOTAL:
        failures.append(f"SDD({n_sdd}) + Non-SDD({n_nonsdd}) = {n_sdd + n_nonsdd}, expected {EXPECTED_TOTAL}")

    if recount_sdd.get(0, 0) != 0:
        failures.append(f"SDD group has {recount_sdd.get(0, 0)} orders at day_diff=0 -- should be 0")
    if recount_nonsdd.get(0, 0) != 0:
        failures.append(f"Non-SDD group has {recount_nonsdd.get(0, 0)} orders at day_diff=0 -- should be 0")

    csv_sdd_hist, csv_sdd_total = load_group_csv(OUT / "exploded-cohorts-delivery-day-diff-sdd.csv")
    csv_nonsdd_hist, csv_nonsdd_total = load_group_csv(OUT / "exploded-cohorts-delivery-day-diff-nonsdd.csv")

    if csv_sdd_total != n_sdd:
        failures.append(f"SDD CSV totals {csv_sdd_total}, recount gives {n_sdd}")
    if csv_nonsdd_total != n_nonsdd:
        failures.append(f"Non-SDD CSV totals {csv_nonsdd_total}, recount gives {n_nonsdd}")

    if dict(csv_sdd_hist) != dict(recount_sdd):
        failures.append("SDD histogram cells do not exactly match recount")
    if dict(csv_nonsdd_hist) != dict(recount_nonsdd):
        failures.append("Non-SDD histogram cells do not exactly match recount")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- SDD n={n_sdd}, Non-SDD n={n_nonsdd}, sum={n_sdd + n_nonsdd} matches "
          f"expected {EXPECTED_TOTAL}, zero unclassified, zero at day_diff=0 in either "
          f"group, and both CSVs exactly match a fresh recount.")


if __name__ == "__main__":
    main()
