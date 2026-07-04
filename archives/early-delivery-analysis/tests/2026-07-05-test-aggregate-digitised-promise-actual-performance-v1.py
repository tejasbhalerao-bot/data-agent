"""Sanity checks for digitised-promise-actual-performance.csv.

Checks:
1. row4 n = 38,598 and row6 n = 110,586, matching the already-validated funnel counts.
2. On-Time = 0 for every view -- structural, since rows 4/6 are drawn from the
   230,923-order cohort that excludes delivery_view2=On-Time by construction.
3. merged = row4 + row6 on every outcome.
4. Every count/pct matches an independent recount, and the outcome used matches
   view2-orders-all.csv's own delivery_leg for each order (not a re-derived value
   that could silently diverge from the already-validated View 2 classification).

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-digitised-promise-actual-performance-v1.py
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TS_FMT = "%b %d, %Y, %I:%M %p"
OUTCOMES = ["Early", "On-Time", "Late"]

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
EXPECTED_ROW4_N = 38_598
EXPECTED_ROW6_N = 110_586


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


def promise_changed(row: dict) -> bool | None:
    dispatch_promise = parse_date(row["digitised_dispatch_promise"])
    delivery_promise = parse_date(row["digitised_delivery_promise"])
    ship_promise_raw = row["shipping_delivery_promise"].strip()
    if dispatch_promise is None or delivery_promise is None or not ship_promise_raw:
        return None
    digitised_days = (delivery_promise - dispatch_promise).days
    shipping_days = int(ship_promise_raw)
    return shipping_days != digitised_days


def recompute_outcome(row: dict) -> str:
    """Independent recompute of the View 2 delivery formula, to cross-check against
    view2-orders-all.csv's own delivery_leg rather than trusting it blindly."""
    dispatch_promise = parse_date(row["digitised_dispatch_promise"])
    delivery_promise = parse_date(row["digitised_delivery_promise"])
    pickup = parse_date(row["pickup_time"])
    delivery_attempt = parse_date(row["delivery_attempt_time"])
    promise_days = (delivery_promise - dispatch_promise).days
    actual_days = (delivery_attempt - pickup).days
    diff = actual_days - promise_days
    return "Early" if diff < 0 else "Late" if diff > 0 else "On-Time"


def main() -> None:
    failures: list[str] = []

    v2_rows: dict[str, dict[str, str]] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    tallies: dict[str, dict[str, int]] = {
        "row4": defaultdict(int), "row6": defaultdict(int), "merged": defaultdict(int)
    }
    outcome_mismatches = 0

    with (OUT / "view1-orders-all.csv").open(newline="") as f:
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

            if promise_changed(row) is not True:
                continue

            switched = dig_partner != ship_partner
            branch = "row4" if switched else "row6"

            outcome = r2["delivery_leg"]
            if recompute_outcome(row) != outcome:
                outcome_mismatches += 1

            tallies[branch]["n"] += 1
            tallies[branch][outcome] += 1
            tallies["merged"]["n"] += 1
            tallies["merged"][outcome] += 1

    if outcome_mismatches:
        failures.append(f"{outcome_mismatches} orders: independent recompute of the View 2 "
                         f"formula disagrees with view2-orders-all.csv's own delivery_leg")

    if tallies["row4"]["n"] != EXPECTED_ROW4_N:
        failures.append(f"row4 n={tallies['row4']['n']}, expected {EXPECTED_ROW4_N}")
    if tallies["row6"]["n"] != EXPECTED_ROW6_N:
        failures.append(f"row6 n={tallies['row6']['n']}, expected {EXPECTED_ROW6_N}")

    for view in ("row4", "row6", "merged"):
        if tallies[view]["On-Time"] != 0:
            failures.append(f"{view}: On-Time={tallies[view]['On-Time']}, expected 0 (structural)")
        outcome_sum = sum(tallies[view][o] for o in OUTCOMES)
        if outcome_sum != tallies[view]["n"]:
            failures.append(f"{view}: Early+On-Time+Late={outcome_sum}, expected n={tallies[view]['n']}")

    for o in OUTCOMES:
        merged_expected = tallies["row4"][o] + tallies["row6"][o]
        if tallies["merged"][o] != merged_expected:
            failures.append(f"merged/{o}: {tallies['merged'][o]}, expected row4+row6={merged_expected}")

    csv_rows: dict[str, dict[str, str]] = {}
    with (OUT / "digitised-promise-actual-performance.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            csv_rows[r["view"]] = r

    for view in ("row4", "row6", "merged"):
        r = csv_rows[view]
        n = tallies[view]["n"]
        if int(r["n"]) != n:
            failures.append(f"{view}: CSV n={r['n']}, recount={n}")
        for o in OUTCOMES:
            col = o.lower().replace("-", "")
            expected_n = tallies[view][o]
            if int(r[f"{col}_n"]) != expected_n:
                failures.append(f"{view}/{o}: CSV n={r[f'{col}_n']}, recount={expected_n}")
            expected_pct = round(expected_n / n * 100, 1) if n else 0.0
            if abs(float(r[f"{col}_pct"]) - expected_pct) > 0.05:
                failures.append(f"{view}/{o}: CSV pct={r[f'{col}_pct']}, recompute={expected_pct}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- row4 n={tallies['row4']['n']} matches expected {EXPECTED_ROW4_N}, "
          f"row6 n={tallies['row6']['n']} matches expected {EXPECTED_ROW6_N}, On-Time=0 "
          f"in all 3 views as structurally required, merged=row4+row6 on every outcome, "
          f"the independent recompute of the View 2 formula agrees with "
          f"view2-orders-all.csv's own delivery_leg for every order, and all CSV values "
          f"match an independent recount.")


if __name__ == "__main__":
    main()
