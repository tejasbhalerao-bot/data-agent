"""Sanity checks for late-magnitude-vs-promise-delta.csv.

Checks:
1. n_late for row4 (24,603) and row6 (82,450) match the already-validated Late
   counts from digitised-promise-actual-performance.csv exactly; merged = row4+row6
   (107,053).
2. late_1_day + late_2plus_days = n_late exactly for every view (exhaustive split).
3. promise_increased_1 + promise_increased_2plus + promise_decreased = n_late exactly
   for every view (exhaustive split).
4. promise_decreased = 0 for every view -- structural, since being Late against the
   (smaller) digitised promise while the promise also decreased would mean the order
   is even later against the (smaller still) shipping promise, which we already know
   is near-zero (shipping-promise-actual-performance.csv found Late <=0.4% everywhere).
5. Every count/pct matches an independent recount straight from the order-detail files.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-late-magnitude-vs-promise-delta-v1.py
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
EXPECTED_ROW4_N_LATE = 24_603
EXPECTED_ROW6_N_LATE = 82_450


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

    tallies: dict[str, dict[str, int]] = {
        "row4": defaultdict(int), "row6": defaultdict(int), "merged": defaultdict(int)
    }

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

            dispatch_promise = parse_date(row["digitised_dispatch_promise"])
            delivery_promise = parse_date(row["digitised_delivery_promise"])
            pickup = parse_date(row["pickup_time"])
            delivery_attempt = parse_date(row["delivery_attempt_time"])
            ship_promise_raw = row["shipping_delivery_promise"].strip()
            if dispatch_promise is None or delivery_promise is None or not ship_promise_raw:
                continue

            digitised_promise_days = (delivery_promise - dispatch_promise).days
            shipping_promise_days = int(ship_promise_raw)
            promise_delta = shipping_promise_days - digitised_promise_days
            if promise_delta == 0:
                continue

            actual_days = (delivery_attempt - pickup).days
            late_by_days = actual_days - digitised_promise_days
            if late_by_days <= 0:
                continue

            switched = dig_partner != ship_partner
            branch = "row4" if switched else "row6"

            late_bucket = "late_1_day" if late_by_days == 1 else "late_2plus_days"
            if promise_delta >= 2:
                delta_bucket = "promise_increased_2plus"
            elif promise_delta == 1:
                delta_bucket = "promise_increased_1"
            else:
                delta_bucket = "promise_decreased"

            for b in (branch, "merged"):
                tallies[b]["n_late"] += 1
                tallies[b][late_bucket] += 1
                tallies[b][delta_bucket] += 1

    if tallies["row4"]["n_late"] != EXPECTED_ROW4_N_LATE:
        failures.append(f"row4 n_late={tallies['row4']['n_late']}, expected {EXPECTED_ROW4_N_LATE}")
    if tallies["row6"]["n_late"] != EXPECTED_ROW6_N_LATE:
        failures.append(f"row6 n_late={tallies['row6']['n_late']}, expected {EXPECTED_ROW6_N_LATE}")
    merged_expected = tallies["row4"]["n_late"] + tallies["row6"]["n_late"]
    if tallies["merged"]["n_late"] != merged_expected:
        failures.append(f"merged n_late={tallies['merged']['n_late']}, expected row4+row6={merged_expected}")

    for view in ("row4", "row6", "merged"):
        t = tallies[view]
        n = t["n_late"]
        if t["late_1_day"] + t["late_2plus_days"] != n:
            failures.append(f"{view}: late_1_day+late_2plus_days != n_late")
        if t["promise_increased_1"] + t["promise_increased_2plus"] + t["promise_decreased"] != n:
            failures.append(f"{view}: promise buckets do not sum to n_late")
        if t["promise_decreased"] != 0:
            failures.append(f"{view}: promise_decreased={t['promise_decreased']}, expected 0 (structural)")

    csv_rows: dict[str, dict[str, str]] = {}
    with (OUT / "late-magnitude-vs-promise-delta.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            csv_rows[r["view"]] = r

    field_map = {
        "late_1_day": "late_1_day", "late_2plus_days": "late_2plus_days",
        "promise_increased_1": "promise_increased_1", "promise_increased_2plus": "promise_increased_2plus",
        "promise_decreased": "promise_decreased",
    }
    for view in ("row4", "row6", "merged"):
        r = csv_rows[view]
        t = tallies[view]
        n = t["n_late"]
        if int(r["n_late"]) != n:
            failures.append(f"{view}: CSV n_late={r['n_late']}, recount={n}")
        for key, col_prefix in field_map.items():
            expected_n = t[key]
            if int(r[f"{col_prefix}_n"]) != expected_n:
                failures.append(f"{view}/{key}: CSV n={r[f'{col_prefix}_n']}, recount={expected_n}")
            expected_pct = round(expected_n / n * 100, 1) if n else 0.0
            if abs(float(r[f"{col_prefix}_pct"]) - expected_pct) > 0.05:
                failures.append(f"{view}/{key}: CSV pct={r[f'{col_prefix}_pct']}, recompute={expected_pct}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- row4 n_late={tallies['row4']['n_late']} matches expected "
          f"{EXPECTED_ROW4_N_LATE}, row6 n_late={tallies['row6']['n_late']} matches "
          f"expected {EXPECTED_ROW6_N_LATE}, merged=row4+row6, both bucket splits are "
          f"exhaustive for every view, promise_decreased=0 as structurally required, "
          f"and all CSV values match an independent recount.")


if __name__ == "__main__":
    main()
