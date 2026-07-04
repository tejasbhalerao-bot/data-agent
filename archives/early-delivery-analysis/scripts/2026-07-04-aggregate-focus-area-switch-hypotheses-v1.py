"""Tests 4 digitise-to-shipping "switch" hypotheses against the ops day-diff distribution.

Population: the 230,923-order "ops breaking" cohort from
2026-07-04-aggregate-exploded-cohort-day-diff-v2.py (delivery_view2 != On-Time),
split into:
  focus   = |day_diff| >= 2  (the tail Tejas wants explained)
  control = |day_diff| == 1  (the near-miss band, used as a baseline)
day_diff is the same View 2 ops duration-diff as v2: actual_duration_days - promise_duration_days.

4 switch hypotheses (digitised_* value at digitise time vs shipping_* value at
shipping time):
  1. courier  : digitised_delivery_partner != shipping_delivery_partner
  2. inventory: digitised_is_inventory != shipping_is_inventory
  3. sdd      : digitised_is_sdd != shipping_is_sdd (digitised uses true/false,
                shipping uses 1/0 -- normalized to bool before comparing)
  4. warehouse: digitised_wh_id != shipping_warehouse

Blank/unclassifiable values (digitised_delivery_partner has ~4.8% blanks in the base
population, shipping_is_inventory has a small number of blanks) are excluded from
that specific hypothesis's denominator and counted separately -- never silently
treated as "no switch."

For each group (focus, control) x hypothesis: switch rate, to see whether a switch is
enriched in the focus tail relative to the near-miss baseline (evidence of causality)
or occurs at a similar background rate in both (not explanatory).

Also computes, within the focus group only, the full 16-way overlap across the 4
hypotheses (2^4 combinations, including "no switch at all") to answer the overlap
and "is anything left unexplained" questions directly.

Emits:
  outputs/focus-area-switch-hypotheses-summary.csv
  outputs/focus-area-switch-overlap.csv
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import date, datetime
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_SUMMARY = ROOT / "outputs" / "focus-area-switch-hypotheses-summary.csv"
OUT_OVERLAP = ROOT / "outputs" / "focus-area-switch-overlap.csv"
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


def pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


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
    v2_rows: dict[str, dict[str, str]] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    group_flags: dict[str, list[dict[str, bool | None]]] = {"focus": [], "control": []}

    with V1_PATH.open(newline="") as f:
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

            if abs(day_diff) == 1:
                group_flags["control"].append(switch_flags(row))
            elif abs(day_diff) >= 2:
                group_flags["focus"].append(switch_flags(row))
            # day_diff == 0 cannot occur in this cohort by construction (see v2)

    with OUT_SUMMARY.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["group", "hypothesis", "n_determinable", "n_switch", "pct_switch"])
        for group_name, rows in group_flags.items():
            for h in HYPOTHESES:
                determinable = [r[h] for r in rows if r[h] is not None]
                n_det = len(determinable)
                n_switch = sum(determinable)
                wr.writerow([group_name, h, n_det, n_switch, pct(n_switch, n_det)])

    focus_rows = group_flags["focus"]
    n_focus = len(focus_rows)
    overlap_counts: Counter[tuple[bool, ...]] = Counter()
    n_any_unknown = 0
    for r in focus_rows:
        if any(r[h] is None for h in HYPOTHESES):
            n_any_unknown += 1
            continue
        key = tuple(r[h] for h in HYPOTHESES)
        overlap_counts[key] += 1
    n_fully_determinable = sum(overlap_counts.values())

    with OUT_OVERLAP.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(HYPOTHESES + ["count", "pct_of_focus_fully_determinable"])
        for combo in product([False, True], repeat=4):
            n = overlap_counts.get(combo, 0)
            wr.writerow(list(combo) + [n, pct(n, n_fully_determinable)])

    n_no_switch = overlap_counts.get((False, False, False, False), 0)
    n_at_least_one = n_fully_determinable - n_no_switch

    print(f"control group (|day_diff|==1) n: {len(group_flags['control'])}")
    print(f"focus group (|day_diff|>=2) n: {n_focus}")
    print(f"focus orders with at least one hypothesis field blank/unclassifiable: {n_any_unknown}")
    print(f"focus orders fully determinable across all 4 hypotheses: {n_fully_determinable}")
    print(f"  -> at least one switch present: {n_at_least_one} ({pct(n_at_least_one, n_fully_determinable)}%)")
    print(f"  -> no switch on any of the 4 hypotheses: {n_no_switch} ({pct(n_no_switch, n_fully_determinable)}%)")
    print(f"wrote: {OUT_SUMMARY}")
    print(f"wrote: {OUT_OVERLAP}")


if __name__ == "__main__":
    main()
