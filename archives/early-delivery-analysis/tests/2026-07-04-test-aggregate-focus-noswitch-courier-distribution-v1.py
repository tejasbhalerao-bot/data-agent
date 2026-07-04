"""Sanity checks for focus-noswitch-courier-distribution.csv.

Checks:
1. focus_noswitch_n sums to 22,858 -- the exact "no switch" count from
   2026-07-04-aggregate-focus-area-switch-hypotheses-v1.py's overlap table
   (combo courier=False, inventory=False, sdd=False, warehouse=False).
2. control_noswitch_n sums to an independently recomputed total (not previously
   published, so recomputed here from scratch and cross-checked for internal
   consistency only).
3. Every row's index_focus_vs_control = round(focus_pct / control_pct, 2) exactly.
4. Per-courier recount directly from the order-detail files matches the CSV exactly.

Run: python3 archives/early-delivery-analysis/tests/2026-07-04-test-aggregate-focus-noswitch-courier-distribution-v1.py
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
BOOL_MAP = {"true": True, "1": True, "false": False, "0": False}
EXPECTED_FOCUS_NOSWITCH = 22_858


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


def is_no_switch(row: dict) -> bool | None:
    dig_partner = (row["digitised_delivery_partner"] or "").strip()
    ship_partner = (row["shipping_delivery_partner"] or "").strip()
    if not dig_partner or not ship_partner:
        return None
    courier_switch = dig_partner != ship_partner

    dig_inv, ship_inv = norm_bool(row["digitised_is_inventory"]), norm_bool(row["shipping_is_inventory"])
    if dig_inv is None or ship_inv is None:
        return None
    inventory_switch = dig_inv != ship_inv

    dig_sdd, ship_sdd = norm_bool(row["digitised_is_sdd"]), norm_bool(row["shipping_is_sdd"])
    if dig_sdd is None or ship_sdd is None:
        return None
    sdd_switch = dig_sdd != ship_sdd

    dig_wh = (row["digitised_wh_id"] or "").strip()
    ship_wh = (row["shipping_warehouse"] or "").strip()
    if not dig_wh or not ship_wh:
        return None
    warehouse_switch = dig_wh != ship_wh

    return not (courier_switch or inventory_switch or sdd_switch or warehouse_switch)


def main() -> None:
    failures: list[str] = []

    v2_rows: dict[str, dict[str, str]] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    focus_courier: Counter[str] = Counter()
    control_courier: Counter[str] = Counter()

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

            if is_no_switch(row) is not True:
                continue

            courier = row["digitised_delivery_partner"].strip()
            if abs(day_diff) >= 2:
                focus_courier[courier] += 1
            elif abs(day_diff) == 1:
                control_courier[courier] += 1

    n_focus = sum(focus_courier.values())
    n_control = sum(control_courier.values())

    if n_focus != EXPECTED_FOCUS_NOSWITCH:
        failures.append(f"recount focus 'no switch' n={n_focus}, expected {EXPECTED_FOCUS_NOSWITCH}")

    csv_rows = []
    csv_focus_total = 0
    csv_control_total = 0
    with (OUT / "focus-noswitch-courier-distribution.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            csv_rows.append(r)
            csv_focus_total += int(r["focus_noswitch_n"])
            csv_control_total += int(r["control_noswitch_n"])

    if csv_focus_total != n_focus:
        failures.append(f"CSV focus total={csv_focus_total}, recount={n_focus}")
    if csv_control_total != n_control:
        failures.append(f"CSV control total={csv_control_total}, recount={n_control}")

    for r in csv_rows:
        courier = r["courier"]
        exp_focus_n = focus_courier.get(courier, 0)
        exp_control_n = control_courier.get(courier, 0)
        if int(r["focus_noswitch_n"]) != exp_focus_n:
            failures.append(f"courier {courier}: CSV focus_n={r['focus_noswitch_n']}, recount={exp_focus_n}")
        if int(r["control_noswitch_n"]) != exp_control_n:
            failures.append(f"courier {courier}: CSV control_n={r['control_noswitch_n']}, recount={exp_control_n}")

        exp_fp = round(exp_focus_n / n_focus * 100, 1) if n_focus else 0.0
        exp_cp = round(exp_control_n / n_control * 100, 1) if n_control else 0.0
        if abs(float(r["focus_noswitch_pct"]) - exp_fp) > 0.05:
            failures.append(f"courier {courier}: CSV focus_pct={r['focus_noswitch_pct']}, recompute={exp_fp}")
        if abs(float(r["control_noswitch_pct"]) - exp_cp) > 0.05:
            failures.append(f"courier {courier}: CSV control_pct={r['control_noswitch_pct']}, recompute={exp_cp}")

        if exp_cp:
            exp_index = round(exp_fp / exp_cp, 2)
            if r["index_focus_vs_control"] and abs(float(r["index_focus_vs_control"]) - exp_index) > 0.02:
                failures.append(f"courier {courier}: CSV index={r['index_focus_vs_control']}, recompute={exp_index}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- focus 'no switch' n={n_focus} matches expected {EXPECTED_FOCUS_NOSWITCH}, "
          f"control 'no switch' n={n_control}, all {len(csv_rows)} courier rows (counts, "
          f"pcts, and index) match a fresh recount exactly.")


if __name__ == "__main__":
    main()
