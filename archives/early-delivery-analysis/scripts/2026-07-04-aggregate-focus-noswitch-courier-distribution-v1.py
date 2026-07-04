"""Courier partner distribution for the 22,858-order "no switch" remainder of the focus
tail, tested against Tejas's hypothesis that the courier allocated (digitised ==
shipping, since these orders have no courier switch by definition) explains the
unexplained 58.6% from 2026-07-04-aggregate-focus-area-switch-hypotheses-v1.py.

Population: within the focus group (|day_diff|>=2 in the 230,923-order ops-breaking
cohort), the subset with all 4 switch hypotheses = False (courier/inventory/sdd/
warehouse all unchanged digitise->shipping). For these orders, digitised_delivery_partner
== shipping_delivery_partner by construction, so "the courier" is unambiguous.

Also computes the same courier distribution for the equivalent "no switch" subset of
the control group (|day_diff|==1) as a baseline -- if a courier is genuinely a root
cause of the focus tail (not just high-volume everywhere), its share should be higher
in the focus "no switch" group than in the control "no switch" group. An index of
1.0 means the courier's share is identical in both groups (no signal); higher means
over-represented in the problem tail.

Emits outputs/focus-noswitch-courier-distribution.csv.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "focus-noswitch-courier-distribution.csv"
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


def is_no_switch(row: dict) -> bool | None:
    """None if any of the 4 hypothesis fields is blank/unclassifiable."""
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
    v2_rows: dict[str, dict[str, str]] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    focus_courier: Counter[str] = Counter()
    control_courier: Counter[str] = Counter()
    n_focus_noswitch = 0
    n_control_noswitch = 0

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

            no_switch = is_no_switch(row)
            if no_switch is not True:
                continue

            courier = row["digitised_delivery_partner"].strip()
            if abs(day_diff) >= 2:
                focus_courier[courier] += 1
                n_focus_noswitch += 1
            elif abs(day_diff) == 1:
                control_courier[courier] += 1
                n_control_noswitch += 1

    all_couriers = sorted(set(focus_courier) | set(control_courier), key=lambda c: -focus_courier[c])

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["courier", "focus_noswitch_n", "focus_noswitch_pct",
                     "control_noswitch_n", "control_noswitch_pct", "index_focus_vs_control"])
        for courier in all_couriers:
            fn = focus_courier[courier]
            cn = control_courier[courier]
            fp = pct(fn, n_focus_noswitch)
            cp = pct(cn, n_control_noswitch)
            index = round(fp / cp, 2) if cp else None
            wr.writerow([courier, fn, fp, cn, cp, index])

    print(f"focus 'no switch' n: {n_focus_noswitch}")
    print(f"control 'no switch' n: {n_control_noswitch}")
    print(f"distinct couriers: {len(all_couriers)}")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
