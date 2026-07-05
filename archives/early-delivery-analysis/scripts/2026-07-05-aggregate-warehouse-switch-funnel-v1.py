"""Hypothesis 2: Warehouse switches between digitised and shipping, on the same
230,923-order "not amazing" cohort used for the courier-switch hypothesis.

  warehouse changed : digitised_wh_id != shipping_warehouse
  courier changed   : digitised_delivery_partner != shipping_delivery_partner
  promise changed   : shipping_delivery_promise != date(digitised_delivery_promise)
                        - date(digitised_dispatch_promise)  (days)

Note: as given, the requested funnel is asymmetric -- rows 12/13 split "warehouse
same AND courier changed" by promise, but there is no equivalent split for
"warehouse same AND courier unchanged" (row 11). Built exactly as specified (13
rows); flagging the gap rather than silently adding rows 14/15.

Emits outputs/warehouse-switch-funnel.csv. All % are of the 230,923-order cohort.
"""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "warehouse-switch-funnel.csv"
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


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


def pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def main() -> None:
    v2_delivery: dict[str, str] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    n_total = 0
    n_wh_changed = 0
    n_wh_same = 0
    n_wh_ch_courier_ch = 0
    n_wh_ch_courier_un = 0
    n_wh_ch_courier_ch_promise_ch = 0
    n_wh_ch_courier_ch_promise_un = 0
    n_wh_ch_courier_un_promise_ch = 0
    n_wh_ch_courier_un_promise_un = 0
    n_wh_un_courier_ch = 0
    n_wh_un_courier_un = 0
    n_wh_un_courier_ch_promise_ch = 0
    n_wh_un_courier_ch_promise_un = 0
    n_courier_indeterminate = 0
    n_promise_indeterminate = 0

    with V1_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            oid = row["order_id"]
            dl_v2 = v2_delivery.get(oid)
            if dl_v2 is None:
                continue
            triple = (row["dispatch_leg"], row["delivery_leg"], dl_v2)
            if triple not in TARGET_COHORTS:
                continue

            n_total += 1

            dig_wh = row["digitised_wh_id"].strip()
            ship_wh = row["shipping_warehouse"].strip()
            wh_changed = dig_wh != ship_wh  # both fields confirmed always populated

            if wh_changed:
                n_wh_changed += 1
            else:
                n_wh_same += 1

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            if not dig_partner or not ship_partner:
                n_courier_indeterminate += 1
                courier_known = False
                courier_changed = None
            else:
                courier_known = True
                courier_changed = dig_partner != ship_partner

            dispatch_promise = parse_date(row["digitised_dispatch_promise"])
            delivery_promise = parse_date(row["digitised_delivery_promise"])
            ship_promise_raw = row["shipping_delivery_promise"].strip()
            if dispatch_promise is None or delivery_promise is None or not ship_promise_raw:
                n_promise_indeterminate += 1
                promise_known = False
                promise_changed = None
            else:
                promise_known = True
                digitised_days = (delivery_promise - dispatch_promise).days
                shipping_days = int(ship_promise_raw)
                promise_changed = shipping_days != digitised_days

            if wh_changed and courier_known:
                if courier_changed:
                    n_wh_ch_courier_ch += 1
                    if promise_known:
                        if promise_changed:
                            n_wh_ch_courier_ch_promise_ch += 1
                        else:
                            n_wh_ch_courier_ch_promise_un += 1
                else:
                    n_wh_ch_courier_un += 1
                    if promise_known:
                        if promise_changed:
                            n_wh_ch_courier_un_promise_ch += 1
                        else:
                            n_wh_ch_courier_un_promise_un += 1
            elif not wh_changed and courier_known:
                if courier_changed:
                    n_wh_un_courier_ch += 1
                    if promise_known:
                        if promise_changed:
                            n_wh_un_courier_ch_promise_ch += 1
                        else:
                            n_wh_un_courier_ch_promise_un += 1
                else:
                    n_wh_un_courier_un += 1

    rows = [
        ("1. Total orders", n_total),
        ("2. Warehouse changed", n_wh_changed),
        ("3. Warehouse same", n_wh_same),
        ("4. Warehouse changed AND courier changed", n_wh_ch_courier_ch),
        ("5. Warehouse changed AND courier unchanged", n_wh_ch_courier_un),
        ("6. Warehouse changed AND courier changed AND promise changed", n_wh_ch_courier_ch_promise_ch),
        ("7. Warehouse changed AND courier changed AND promise unchanged", n_wh_ch_courier_ch_promise_un),
        ("8. Warehouse changed AND courier unchanged AND promise changed", n_wh_ch_courier_un_promise_ch),
        ("9. Warehouse changed AND courier unchanged AND promise unchanged", n_wh_ch_courier_un_promise_un),
        ("10. Warehouse same AND courier changed", n_wh_un_courier_ch),
        ("11. Warehouse same AND courier unchanged", n_wh_un_courier_un),
        ("12. Warehouse same AND courier changed AND promise changed", n_wh_un_courier_ch_promise_ch),
        ("13. Warehouse same AND courier changed AND promise unchanged", n_wh_un_courier_ch_promise_un),
    ]

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["step", "n", "pct_of_cohort"])
        for step, n in rows:
            wr.writerow([step, n, pct(n, n_total)])

    for step, n in rows:
        print(f"{step}: {n} ({pct(n, n_total)}%)")
    print(f"courier indeterminate (blank partner field): {n_courier_indeterminate} ({pct(n_courier_indeterminate, n_total)}%)")
    print(f"promise indeterminate (blank/unparseable): {n_promise_indeterminate} ({pct(n_promise_indeterminate, n_total)}%)")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
