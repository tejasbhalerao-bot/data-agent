"""Courier-switch x promise-degradation funnel on the 230,923-order "not amazing"
cohort (all rows of view1-dispatch-delivery-v1v2-crosstab.csv except the 3 where
delivery_view2=On-Time: On-Time/On-Time/On-Time, Early/Early/On-Time, Late/Late/On-Time).

Tests the hypothesis: courier switches between digitise and shipping, and whether
that switch comes with (a) the promise itself degrading, (b) just a different
courier at the same promise, or (c) a mix.

Definitions (confirmed with Tejas after the digitised/shipping promise units did not
match -- see "Discovered quirks & gotchas" in data-sources.md):
  courier switch   : digitised_delivery_partner != shipping_delivery_partner
  digitised_promise: date(digitised_delivery_promise) - date(digitised_dispatch_promise)  (days)
  shipping_promise : shipping_delivery_promise (already an integer TAT in days)
  promise degraded : shipping_promise != digitised_promise (any direction, not just worse)

Funnel:
  1. Total orders
  2. Courier switched (digitised_delivery_partner != shipping_delivery_partner)
  3. Courier unchanged (digitised_delivery_partner == shipping_delivery_partner)
  4. Courier switched AND promise changed
  5. Courier switched AND promise unchanged

Blank digitised_delivery_partner (~4.8% of the base population) makes the switch
undeterminable for that order -- reported separately, never folded into "unchanged."

Emits outputs/courier-switch-promise-funnel.csv. All % are of the 230,923 total.
"""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "courier-switch-promise-funnel.csv"
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
    n_switch_indeterminate = 0
    n_switch = 0
    n_unchanged = 0
    n_switch_promise_indeterminate = 0
    n_switch_promise_changed = 0
    n_switch_promise_unchanged = 0

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

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            if not dig_partner or not ship_partner:
                n_switch_indeterminate += 1
                continue

            switched = dig_partner != ship_partner
            if not switched:
                n_unchanged += 1
                continue

            n_switch += 1

            dispatch_promise = parse_date(row["digitised_dispatch_promise"])
            delivery_promise = parse_date(row["digitised_delivery_promise"])
            ship_promise_raw = row["shipping_delivery_promise"].strip()
            if dispatch_promise is None or delivery_promise is None or not ship_promise_raw:
                n_switch_promise_indeterminate += 1
                continue

            digitised_promise_days = (delivery_promise - dispatch_promise).days
            shipping_promise_days = int(ship_promise_raw)

            if shipping_promise_days != digitised_promise_days:
                n_switch_promise_changed += 1
            else:
                n_switch_promise_unchanged += 1

    rows = [
        ("1. Total orders", n_total),
        ("2. Courier switched", n_switch),
        ("2a. Courier switch indeterminate (blank partner field)", n_switch_indeterminate),
        ("3. Courier unchanged", n_unchanged),
        ("4. Courier switched AND promise changed", n_switch_promise_changed),
        ("5. Courier switched AND promise unchanged", n_switch_promise_unchanged),
        ("5a. Courier switched, promise indeterminate", n_switch_promise_indeterminate),
    ]

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["step", "n", "pct_of_all_orders"])
        for step, n in rows:
            wr.writerow([step, n, pct(n, n_total)])

    for step, n in rows:
        print(f"{step}: {n} ({pct(n, n_total)}%)")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
