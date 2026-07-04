"""Sanity checks for promise-direction-actual-performance.csv.

Checks:
1. Cell n's match the already-validated promise-change-direction.csv counts exactly:
   row4-increased=29,569, row4-decreased=9,029, row6-increased=86,203, row6-decreased=24,383.
2. row4-increased + row4-decreased = row4 total (38,598); row6-increased + row6-decreased
   = row6 total (110,586).
3. Early+On-Time+Late = n for every cell.
4. Every count and pct matches an independent recount straight from the order-detail files.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-promise-direction-actual-performance-v1.py
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
EXPECTED_N = {
    "row4-increased": 29_569, "row4-decreased": 9_029,
    "row6-increased": 86_203, "row6-decreased": 24_383,
}


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


def promise_direction(row: dict) -> str | None:
    dispatch_promise = parse_date(row["digitised_dispatch_promise"])
    delivery_promise = parse_date(row["digitised_delivery_promise"])
    ship_promise_raw = row["shipping_delivery_promise"].strip()
    if dispatch_promise is None or delivery_promise is None or not ship_promise_raw:
        return None
    digitised_days = (delivery_promise - dispatch_promise).days
    shipping_days = int(ship_promise_raw)
    if shipping_days > digitised_days:
        return "increased"
    if shipping_days < digitised_days:
        return "decreased"
    return "unchanged"


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

    cells = ["row4-increased", "row4-decreased", "row6-increased", "row6-decreased"]
    tallies: dict[str, dict[str, int]] = {c: defaultdict(int) for c in cells}

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
            direction = promise_direction(row)
            if direction is None or direction == "unchanged":
                continue

            branch = "row4" if switched else "row6"
            cell = f"{branch}-{direction}"
            outcome = classify_ops(row)
            if outcome is None:
                continue

            tallies[cell]["n"] += 1
            tallies[cell][outcome] += 1

    for cell in cells:
        if tallies[cell]["n"] != EXPECTED_N[cell]:
            failures.append(f"{cell}: n={tallies[cell]['n']}, expected {EXPECTED_N[cell]}")
        outcome_sum = sum(tallies[cell][o] for o in OUTCOMES)
        if outcome_sum != tallies[cell]["n"]:
            failures.append(f"{cell}: Early+On-Time+Late={outcome_sum}, expected n={tallies[cell]['n']}")

    row4_total = tallies["row4-increased"]["n"] + tallies["row4-decreased"]["n"]
    row6_total = tallies["row6-increased"]["n"] + tallies["row6-decreased"]["n"]
    if row4_total != 38_598:
        failures.append(f"row4-increased + row4-decreased = {row4_total}, expected 38,598")
    if row6_total != 110_586:
        failures.append(f"row6-increased + row6-decreased = {row6_total}, expected 110,586")

    csv_rows: dict[str, dict[str, str]] = {}
    with (OUT / "promise-direction-actual-performance.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            csv_rows[r["cell"]] = r

    for cell in cells:
        r = csv_rows[cell]
        n = tallies[cell]["n"]
        if int(r["n"]) != n:
            failures.append(f"{cell}: CSV n={r['n']}, recount={n}")
        for o in OUTCOMES:
            col = o.lower().replace("-", "")
            expected_n = tallies[cell][o]
            if int(r[f"{col}_n"]) != expected_n:
                failures.append(f"{cell}/{o}: CSV n={r[f'{col}_n']}, recount={expected_n}")
            expected_pct = round(expected_n / n * 100, 1) if n else 0.0
            if abs(float(r[f"{col}_pct"]) - expected_pct) > 0.05:
                failures.append(f"{cell}/{o}: CSV pct={r[f'{col}_pct']}, recompute={expected_pct}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- all 4 cell counts match promise-change-direction.csv exactly, "
          f"row4/row6 sub-totals reconcile (38,598 / 110,586), Early+On-Time+Late=n "
          f"for every cell, and all CSV values match an independent recount.")


if __name__ == "__main__":
    main()
