"""Sanity checks for invoice-window-courier-switch-delivery.csv.

Checks:
1. Cohort 1 n (43,081) + Cohort 2 n (211,000) + indeterminate (9,036) = 263,117,
   matching the already-validated invoice window total and switch rate exactly
   (invoice-window-courier-switch-rate.csv: window switch_n=43,081, same_n=211,000).
2. Early+On-Time+Late = n exactly for each cohort.
3. Delivery outcome for every order matches view1-orders-all.csv's own delivery_leg
   field exactly (reused, not recomputed).
4. Every count/pct matches an independent recount straight from the order-detail file.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-invoice-window-courier-switch-delivery-v1.py
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TS_FMT = "%b %d, %Y, %I:%M %p"
OUTCOMES = ["Early", "On-Time", "Late"]
EXPECTED_SWITCHED_N = 43_081
EXPECTED_NOT_SWITCHED_N = 211_000
EXPECTED_WINDOW_N = 263_117


def parse_dt(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def main() -> None:
    failures: list[str] = []

    tallies: dict[str, dict[str, int]] = {"switched": defaultdict(int), "not_switched": defaultdict(int)}
    n_indeterminate = 0
    n_window = 0

    with (OUT / "view1-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            digitised = parse_dt(row["digitised_ts"])
            invoice_create = parse_dt(row["invoice_create_ts"])
            if digitised is None or invoice_create is None:
                continue
            gap_hours = (invoice_create - digitised).total_seconds() / 3600
            if not (3 <= gap_hours <= 24):
                continue

            n_window += 1

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            if not dig_partner or not ship_partner:
                n_indeterminate += 1
                continue

            cohort = "switched" if dig_partner != ship_partner else "not_switched"
            tallies[cohort][row["delivery_leg"]] += 1

    n_switched = sum(tallies["switched"].values())
    n_not_switched = sum(tallies["not_switched"].values())

    if n_window != EXPECTED_WINDOW_N:
        failures.append(f"window n={n_window}, expected {EXPECTED_WINDOW_N}")
    if n_switched != EXPECTED_SWITCHED_N:
        failures.append(f"switched n={n_switched}, expected {EXPECTED_SWITCHED_N}")
    if n_not_switched != EXPECTED_NOT_SWITCHED_N:
        failures.append(f"not_switched n={n_not_switched}, expected {EXPECTED_NOT_SWITCHED_N}")
    if n_switched + n_not_switched + n_indeterminate != n_window:
        failures.append("switched + not_switched + indeterminate != window n")

    for cohort in ("switched", "not_switched"):
        n = sum(tallies[cohort].values())
        outcome_sum = sum(tallies[cohort][o] for o in OUTCOMES)
        if outcome_sum != n:
            failures.append(f"{cohort}: Early+On-Time+Late={outcome_sum}, expected n={n}")

    csv_rows = {}
    with (OUT / "invoice-window-courier-switch-delivery.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            csv_rows[r["cohort"]] = r

    label_map = {"switched": "Cohort 1: Courier switched", "not_switched": "Cohort 2: Courier not switched"}
    for cohort, label in label_map.items():
        r = csv_rows[label]
        n = sum(tallies[cohort].values())
        if int(r["n"]) != n:
            failures.append(f"{label}: CSV n={r['n']}, recount={n}")
        for o in OUTCOMES:
            col = o.lower().replace("-", "")
            expected_n = tallies[cohort][o]
            if int(r[f"{col}_n"]) != expected_n:
                failures.append(f"{label}/{o}: CSV n={r[f'{col}_n']}, recount={expected_n}")
            expected_pct = round(expected_n / n * 100, 1) if n else 0.0
            if abs(float(r[f"{col}_pct"]) - expected_pct) > 0.05:
                failures.append(f"{label}/{o}: CSV pct={r[f'{col}_pct']}, recompute={expected_pct}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- window n={n_window} matches expected {EXPECTED_WINDOW_N}, "
          f"Cohort 1 n={n_switched} matches expected {EXPECTED_SWITCHED_N}, Cohort 2 "
          f"n={n_not_switched} matches expected {EXPECTED_NOT_SWITCHED_N}, Early+On-"
          f"Time+Late=n for both cohorts, and all CSV values match an independent recount.")


if __name__ == "__main__":
    main()
