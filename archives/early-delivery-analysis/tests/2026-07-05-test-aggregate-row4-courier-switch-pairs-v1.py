"""Sanity checks for row4-courier-switch-pairs.csv.

Checks:
1. Sum of all pair counts = 38,598, matching the already-validated row 4 total.
2. No pair has from_courier == to_courier (that would be a courier-unchanged row,
   i.e. row 6, not row 4).
3. Every count/pct/late-rate matches an independent recount straight from the
   order-detail files.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-row4-courier-switch-pairs-v1.py
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
EXPECTED_ROW4_N = 38_598

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


def main() -> None:
    failures: list[str] = []

    v2_rows: dict[str, dict[str, str]] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    pair_counts: dict[tuple[str, str], int] = defaultdict(int)
    pair_late_digitised: dict[tuple[str, str], int] = defaultdict(int)
    pair_late_shipping: dict[tuple[str, str], int] = defaultdict(int)
    n_row4 = 0

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
            if not dig_partner or not ship_partner or dig_partner == ship_partner:
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
            if shipping_promise_days == digitised_promise_days:
                continue

            n_row4 += 1
            pair = (dig_partner, ship_partner)
            pair_counts[pair] += 1

            actual_days = (delivery_attempt - pickup).days
            if actual_days - digitised_promise_days > 0:
                pair_late_digitised[pair] += 1
            if actual_days - shipping_promise_days > 0:
                pair_late_shipping[pair] += 1

    if n_row4 != EXPECTED_ROW4_N:
        failures.append(f"row4 n={n_row4}, expected {EXPECTED_ROW4_N}")

    csv_total = 0
    csv_rows = []
    with (OUT / "row4-courier-switch-pairs.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            csv_rows.append(r)
            csv_total += int(r["n"])
            if r["from_courier"] == r["to_courier"]:
                failures.append(f"pair {r['from_courier']}->{r['to_courier']}: from==to, should not exist in row4")

    if csv_total != n_row4:
        failures.append(f"CSV pair counts sum to {csv_total}, recount gives {n_row4}")

    for r in csv_rows:
        pair = (r["from_courier"], r["to_courier"])
        n = pair_counts.get(pair, 0)
        if int(r["n"]) != n:
            failures.append(f"pair {pair}: CSV n={r['n']}, recount={n}")
        exp_pct = round(n / n_row4 * 100, 1) if n_row4 else 0.0
        if abs(float(r["pct_of_row4"]) - exp_pct) > 0.05:
            failures.append(f"pair {pair}: CSV pct={r['pct_of_row4']}, recompute={exp_pct}")
        exp_late_dig = round(pair_late_digitised.get(pair, 0) / n * 100, 1) if n else 0.0
        if abs(float(r["late_vs_digitised_promise_pct"]) - exp_late_dig) > 0.05:
            failures.append(f"pair {pair}: CSV late_vs_digitised={r['late_vs_digitised_promise_pct']}, recompute={exp_late_dig}")
        exp_late_ship = round(pair_late_shipping.get(pair, 0) / n * 100, 1) if n else 0.0
        if abs(float(r["late_vs_shipping_promise_pct"]) - exp_late_ship) > 0.05:
            failures.append(f"pair {pair}: CSV late_vs_shipping={r['late_vs_shipping_promise_pct']}, recompute={exp_late_ship}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- {len(csv_rows)} pairs sum to {csv_total}, matches expected row4 "
          f"n={EXPECTED_ROW4_N}, no from==to pairs, and every count/pct/late-rate "
          f"matches an independent recount.")


if __name__ == "__main__":
    main()
