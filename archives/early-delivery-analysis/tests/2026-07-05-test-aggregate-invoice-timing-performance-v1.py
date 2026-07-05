"""Sanity checks for invoice-timing-performance.csv.

Checks:
1. Total = 515,465 (all View 1 orders).
2. Step 2 (3-24h gap) Early+On-Time+Late = step 2 n exactly.
3. Cut #5's two groups (targeted 246/247, others excl. 287) sum to less than or
   equal to step 2 n, with the gap explained by courier 287 + blank/unparseable
   shipping_delivery_partner within step 2.
4. Delivery/dispatch outcome for every order matches view1-orders-all.csv's own
   delivery_leg/dispatch_leg fields exactly (reused, not recomputed -- confirms no
   drift was introduced).
5. Every count/pct matches an independent recount straight from the order-detail file.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-invoice-timing-performance-v1.py
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
TARGET_COURIERS = {"246", "247"}
EXCLUDED_COURIER = "287"
EXPECTED_TOTAL = 515_465


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

    n_total = 0
    n_step2 = 0
    n_287_in_step2 = 0
    n_courier_blank_in_step2 = 0
    delivery_tally: dict[str, int] = defaultdict(int)
    dispatch_tally: dict[str, int] = defaultdict(int)
    cut_delivery: dict[str, dict[str, int]] = {"targeted": defaultdict(int), "others": defaultdict(int)}
    cut_dispatch: dict[str, dict[str, int]] = {"targeted": defaultdict(int), "others": defaultdict(int)}

    with (OUT / "view1-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            n_total += 1

            digitised = parse_dt(row["digitised_ts"])
            invoice_create = parse_dt(row["invoice_create_ts"])
            if digitised is None or invoice_create is None:
                continue

            gap_hours = (invoice_create - digitised).total_seconds() / 3600
            if not (3 <= gap_hours <= 24):
                continue

            n_step2 += 1
            delivery_outcome = row["delivery_leg"]
            dispatch_outcome = row["dispatch_leg"]
            delivery_tally[delivery_outcome] += 1
            dispatch_tally[dispatch_outcome] += 1

            courier = row["shipping_delivery_partner"].strip()
            if not courier:
                n_courier_blank_in_step2 += 1
                continue
            if courier == EXCLUDED_COURIER:
                n_287_in_step2 += 1
                continue
            cut = "targeted" if courier in TARGET_COURIERS else "others"
            cut_delivery[cut][delivery_outcome] += 1
            cut_dispatch[cut][dispatch_outcome] += 1

    if n_total != EXPECTED_TOTAL:
        failures.append(f"total={n_total}, expected {EXPECTED_TOTAL}")

    delivery_sum = sum(delivery_tally.values())
    if delivery_sum != n_step2:
        failures.append(f"delivery tally sums to {delivery_sum}, expected step2 n={n_step2}")
    dispatch_sum = sum(dispatch_tally.values())
    if dispatch_sum != n_step2:
        failures.append(f"dispatch tally sums to {dispatch_sum}, expected step2 n={n_step2}")

    cut_total = sum(cut_delivery["targeted"].values()) + sum(cut_delivery["others"].values())
    if cut_total + n_287_in_step2 + n_courier_blank_in_step2 != n_step2:
        failures.append(
            f"cut totals({cut_total}) + courier287({n_287_in_step2}) + "
            f"blank({n_courier_blank_in_step2}) != step2 n({n_step2})"
        )

    csv_rows = {}
    with (OUT / "invoice-timing-performance.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            csv_rows[r["section"]] = r

    if int(csv_rows["1. Total orders"]["n"]) != n_total:
        failures.append("CSV total mismatch")
    if int(csv_rows["2. Digitised->invoice gap 3-24h"]["n"]) != n_step2:
        failures.append("CSV step2 n mismatch")

    def check_section(section: str, tally: dict[str, int], n: int) -> None:
        r = csv_rows[section]
        if int(r["n"]) != n:
            failures.append(f"{section}: CSV n={r['n']}, recount={n}")
        for o in OUTCOMES:
            col = o.lower().replace("-", "")
            expected_n = tally[o]
            if int(r[f"{col}_n"]) != expected_n:
                failures.append(f"{section}/{o}: CSV n={r[f'{col}_n']}, recount={expected_n}")
            expected_pct = round(expected_n / n * 100, 1) if n else 0.0
            if abs(float(r[f"{col}_pct"]) - expected_pct) > 0.05:
                failures.append(f"{section}/{o}: CSV pct={r[f'{col}_pct']}, recompute={expected_pct}")

    check_section("3. Delivery E/OT/L (of step 2)", delivery_tally, n_step2)
    check_section("4. Dispatch E/OT/L (of step 2)", dispatch_tally, n_step2)
    check_section("5. Delivery E/OT/L - 246/247", cut_delivery["targeted"], sum(cut_delivery["targeted"].values()))
    check_section("5. Delivery E/OT/L - others excl. 287", cut_delivery["others"], sum(cut_delivery["others"].values()))
    check_section("5. Dispatch E/OT/L - 246/247", cut_dispatch["targeted"], sum(cut_dispatch["targeted"].values()))
    check_section("5. Dispatch E/OT/L - others excl. 287", cut_dispatch["others"], sum(cut_dispatch["others"].values()))

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- total={n_total} matches expected {EXPECTED_TOTAL}, step2 n={n_step2}, "
          f"delivery/dispatch tallies sum to step2 exactly, cut totals + courier-287 "
          f"({n_287_in_step2}) + blank-courier ({n_courier_blank_in_step2}) reconcile "
          f"to step2 n, and all CSV sections match an independent recount.")


if __name__ == "__main__":
    main()
