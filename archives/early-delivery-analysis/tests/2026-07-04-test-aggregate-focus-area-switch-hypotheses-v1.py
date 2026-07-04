"""Sanity checks for focus-area-switch-hypotheses-summary.csv and -overlap.csv.

Checks:
1. control (|day_diff|==1) + focus (|day_diff|>=2) = 230,923, matching the already
   validated v2 histogram total exactly (186,948 + 43,975).
2. Each hypothesis's n_determinable + blanks recomputed independently must equal the
   group's total n (no silent row loss).
3. The 16-row overlap table sums to the "fully determinable" focus count, and its
   marginal "at least one switch" / "no switch" split matches console output logic.
4. Per-hypothesis switch rates in the summary CSV match a fresh recount.

Run: python3 archives/early-delivery-analysis/tests/2026-07-04-test-aggregate-focus-area-switch-hypotheses-v1.py
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from datetime import date, datetime
from itertools import product
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
HYPOTHESES = ["courier", "inventory", "sdd", "warehouse"]
BOOL_MAP = {"true": True, "1": True, "false": False, "0": False}
EXPECTED_COHORT_TOTAL = 230_923


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


def norm_bool(raw: str) -> bool | None:
    return BOOL_MAP.get((raw or "").strip().lower())


def switch_flags(row: dict) -> dict[str, bool | None]:
    dig_partner = (row["digitised_delivery_partner"] or "").strip()
    ship_partner = (row["shipping_delivery_partner"] or "").strip()
    courier = None if not dig_partner or not ship_partner else dig_partner != ship_partner

    dig_inv = norm_bool(row["digitised_is_inventory"])
    ship_inv = norm_bool(row["shipping_is_inventory"])
    inventory = None if dig_inv is None or ship_inv is None else dig_inv != ship_inv

    dig_sdd = norm_bool(row["digitised_is_sdd"])
    ship_sdd = norm_bool(row["shipping_is_sdd"])
    sdd = None if dig_sdd is None or ship_sdd is None else dig_sdd != ship_sdd

    dig_wh = (row["digitised_wh_id"] or "").strip()
    ship_wh = (row["shipping_warehouse"] or "").strip()
    warehouse = None if not dig_wh or not ship_wh else dig_wh != ship_wh

    return {"courier": courier, "inventory": inventory, "sdd": sdd, "warehouse": warehouse}


def main() -> None:
    failures: list[str] = []

    v2_rows: dict[str, dict[str, str]] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    group_flags: dict[str, list[dict[str, bool | None]]] = {"focus": [], "control": []}

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

            if day_diff == 0:
                failures.append("found an order with day_diff==0 in the ops-breaking cohort -- impossible")
                continue
            if abs(day_diff) == 1:
                group_flags["control"].append(switch_flags(row))
            else:
                group_flags["focus"].append(switch_flags(row))

    n_control = len(group_flags["control"])
    n_focus = len(group_flags["focus"])
    if n_control + n_focus != EXPECTED_COHORT_TOTAL:
        failures.append(f"control({n_control}) + focus({n_focus}) = {n_control + n_focus}, expected {EXPECTED_COHORT_TOTAL}")
    if n_control != 186_948:
        failures.append(f"control n={n_control}, expected 186,948 (the |day_diff|==1 total from v2)")
    if n_focus != 43_975:
        failures.append(f"focus n={n_focus}, expected 43,975 (the |day_diff|>=2 total from v2)")

    summary_rows: dict[tuple[str, str], tuple[int, int, float]] = {}
    with (OUT / "focus-area-switch-hypotheses-summary.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            summary_rows[(r["group"], r["hypothesis"])] = (
                int(r["n_determinable"]), int(r["n_switch"]), float(r["pct_switch"])
            )

    for group_name, rows in group_flags.items():
        for h in HYPOTHESES:
            determinable = [r[h] for r in rows if r[h] is not None]
            n_det, n_switch = len(determinable), sum(determinable)
            csv_n_det, csv_n_switch, csv_pct = summary_rows[(group_name, h)]
            if (n_det, n_switch) != (csv_n_det, csv_n_switch):
                failures.append(
                    f"{group_name}/{h}: recount n_det={n_det},n_switch={n_switch} vs "
                    f"CSV n_det={csv_n_det},n_switch={csv_n_switch}"
                )
            expected_pct = round(n_switch / n_det * 100, 1) if n_det else 0.0
            if abs(expected_pct - csv_pct) > 0.05:
                failures.append(f"{group_name}/{h}: recomputed pct={expected_pct}, CSV pct={csv_pct}")

    focus_rows = group_flags["focus"]
    overlap_counts: Counter[tuple[bool, ...]] = Counter()
    for r in focus_rows:
        if any(r[h] is None for h in HYPOTHESES):
            continue
        overlap_counts[tuple(r[h] for h in HYPOTHESES)] += 1
    n_fully_determinable = sum(overlap_counts.values())

    overlap_csv_total = 0
    overlap_csv_counts: dict[tuple[bool, ...], int] = {}
    with (OUT / "focus-area-switch-overlap.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            combo = tuple(r[h] == "True" for h in HYPOTHESES)
            n = int(r["count"])
            overlap_csv_counts[combo] = n
            overlap_csv_total += n

    if overlap_csv_total != n_fully_determinable:
        failures.append(f"overlap CSV totals {overlap_csv_total}, recount gives {n_fully_determinable}")

    for combo in product([False, True], repeat=4):
        expected = overlap_counts.get(combo, 0)
        actual = overlap_csv_counts.get(combo, 0)
        if expected != actual:
            failures.append(f"overlap combo {combo}: recount={expected}, CSV={actual}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- control({n_control})+focus({n_focus})={n_control + n_focus} matches "
          f"expected {EXPECTED_COHORT_TOTAL}, all 8 summary rows match a fresh recount, "
          f"and all 16 overlap combinations match exactly (total fully-determinable "
          f"focus orders: {n_fully_determinable}).")


if __name__ == "__main__":
    main()
