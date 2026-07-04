"""Sanity checks for shipping-promise-actual-performance.csv.

Checks:
1. row4 n = 38,598 and row6 n = 110,586, matching the already-validated rows 4 and 6
   of courier-switch-promise-funnel-v2.csv exactly.
2. merged n = row4 n + row6 n, and merged Early/On-Time/Late = row4 + row6 per outcome.
3. Every row's Early+On-Time+Late = n exactly.
4. Every count and pct matches an independent recount straight from the order-detail
   files, using the same shipping_delivery_promise-based classification.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-shipping-promise-actual-performance-v1.py
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
    digitised_promise_days = (delivery_promise - dispatch_promise).days
    shipping_promise_days = int(ship_promise_raw)
    return shipping_promise_days != digitised_promise_days


def classify_ops(row: dict) -> str | None:
    pickup = parse_date(row["pickup_time"])
    delivery_attempt = parse_date(row["delivery_attempt_time"])
    ship_promise_raw = row["shipping_delivery_promise"].strip()
    if pickup is None or delivery_attempt is None or not ship_promise_raw:
        return None
    actual_duration = (delivery_attempt - pickup).days
    shipping_promise = int(ship_promise_raw)
    diff = actual_duration - shipping_promise
    return "Early" if diff < 0 else "Late" if diff > 0 else "On-Time"


def main() -> None:
    failures: list[str] = []

    v2_delivery: dict[str, str] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    tallies: dict[str, dict[str, int]] = {
        "row4": defaultdict(int), "row6": defaultdict(int), "merged": defaultdict(int)
    }

    with (OUT / "view1-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            oid = row["order_id"]
            dl_v2 = v2_delivery.get(oid)
            if dl_v2 is None:
                continue
            triple = (row["dispatch_leg"], row["delivery_leg"], dl_v2)
            if triple not in TARGET_COHORTS:
                continue

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            if not dig_partner or not ship_partner:
                continue

            switched = dig_partner != ship_partner
            if promise_changed(row) is not True:
                continue

            branch = "row4" if switched else "row6"
            outcome = classify_ops(row)
            if outcome is None:
                continue

            tallies[branch][outcome] += 1
            tallies[branch]["_n"] += 1
            tallies["merged"][outcome] += 1
            tallies["merged"]["_n"] += 1

    if tallies["row4"]["_n"] != EXPECTED_ROW4_N:
        failures.append(f"row4 n={tallies['row4']['_n']}, expected {EXPECTED_ROW4_N}")
    if tallies["row6"]["_n"] != EXPECTED_ROW6_N:
        failures.append(f"row6 n={tallies['row6']['_n']}, expected {EXPECTED_ROW6_N}")

    for view in ("row4", "row6", "merged"):
        n = tallies[view]["_n"]
        outcome_sum = sum(tallies[view][o] for o in OUTCOMES)
        if outcome_sum != n:
            failures.append(f"{view}: Early+On-Time+Late={outcome_sum}, expected n={n}")

    for o in OUTCOMES:
        merged_expected = tallies["row4"][o] + tallies["row6"][o]
        if tallies["merged"][o] != merged_expected:
            failures.append(f"merged/{o}: {tallies['merged'][o]}, expected row4+row6={merged_expected}")
    merged_n_expected = tallies["row4"]["_n"] + tallies["row6"]["_n"]
    if tallies["merged"]["_n"] != merged_n_expected:
        failures.append(f"merged n={tallies['merged']['_n']}, expected row4+row6={merged_n_expected}")

    csv_rows: dict[str, dict[str, float]] = {}
    with (OUT / "shipping-promise-actual-performance.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            csv_rows[r["view"]] = r

    for view in ("row4", "row6", "merged"):
        r = csv_rows[view]
        n = tallies[view]["_n"]
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

    print(f"PASS -- row4 n={tallies['row4']['_n']} matches expected {EXPECTED_ROW4_N}, "
          f"row6 n={tallies['row6']['_n']} matches expected {EXPECTED_ROW6_N}, merged "
          f"reconciles as row4+row6 on every outcome, and all CSV values match an "
          f"independent recount.")


if __name__ == "__main__":
    main()
