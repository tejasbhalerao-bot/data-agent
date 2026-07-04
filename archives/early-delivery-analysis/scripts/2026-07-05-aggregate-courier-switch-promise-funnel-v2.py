"""Courier-switch x promise-degradation funnel on the 230,923-order "not amazing"
cohort -- v2 adds the symmetric breakdown for the "courier unchanged" branch
(promise changed / unchanged), matching what was already done for "courier switched".

Definitions (confirmed with Tejas -- see "Discovered quirks & gotchas" in
data-sources.md for why digitised/shipping promise need different handling):
  courier switch   : digitised_delivery_partner != shipping_delivery_partner
  digitised_promise: date(digitised_delivery_promise) - date(digitised_dispatch_promise)  (days)
  shipping_promise : shipping_delivery_promise (already an integer TAT in days)
  promise changed  : shipping_promise != digitised_promise (any direction)

Full funnel:
  1. Total orders
  2. Courier switched
  2a. Courier switch indeterminate (blank partner field)
  3. Courier unchanged
  4. Courier switched AND promise changed
  5. Courier switched AND promise unchanged
  5a. Courier switched, promise indeterminate
  6. Courier unchanged AND promise changed
  7. Courier unchanged AND promise unchanged
  7a. Courier unchanged, promise indeterminate

Emits outputs/courier-switch-promise-funnel-v2.csv. All % are of the 230,923 total.
"""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "courier-switch-promise-funnel-v2.csv"
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


def promise_bucket(row: dict) -> str:
    """Returns 'changed', 'unchanged', or 'indeterminate'."""
    dispatch_promise = parse_date(row["digitised_dispatch_promise"])
    delivery_promise = parse_date(row["digitised_delivery_promise"])
    ship_promise_raw = row["shipping_delivery_promise"].strip()
    if dispatch_promise is None or delivery_promise is None or not ship_promise_raw:
        return "indeterminate"
    digitised_promise_days = (delivery_promise - dispatch_promise).days
    shipping_promise_days = int(ship_promise_raw)
    return "changed" if shipping_promise_days != digitised_promise_days else "unchanged"


def main() -> None:
    v2_delivery: dict[str, str] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    n_total = 0
    n_switch_indeterminate = 0
    n_switch = 0
    n_unchanged = 0
    counts = {
        ("switch", "changed"): 0, ("switch", "unchanged"): 0, ("switch", "indeterminate"): 0,
        ("unchanged", "changed"): 0, ("unchanged", "unchanged"): 0, ("unchanged", "indeterminate"): 0,
    }

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
            branch = "switch" if switched else "unchanged"
            if switched:
                n_switch += 1
            else:
                n_unchanged += 1

            counts[(branch, promise_bucket(row))] += 1

    rows = [
        ("1. Total orders", n_total),
        ("2. Courier switched", n_switch),
        ("2a. Courier switch indeterminate (blank partner field)", n_switch_indeterminate),
        ("3. Courier unchanged", n_unchanged),
        ("4. Courier switched AND promise changed", counts[("switch", "changed")]),
        ("5. Courier switched AND promise unchanged", counts[("switch", "unchanged")]),
        ("5a. Courier switched, promise indeterminate", counts[("switch", "indeterminate")]),
        ("6. Courier unchanged AND promise changed", counts[("unchanged", "changed")]),
        ("7. Courier unchanged AND promise unchanged", counts[("unchanged", "unchanged")]),
        ("7a. Courier unchanged, promise indeterminate", counts[("unchanged", "indeterminate")]),
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
