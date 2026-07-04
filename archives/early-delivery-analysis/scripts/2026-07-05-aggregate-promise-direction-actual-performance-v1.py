"""Marries promise-change-direction.csv with shipping-promise-actual-performance.csv:
for each (row4/row6) x (increased/decreased) cell, classifies actual ops performance
against the shipping-time promise.

  digitised_promise_days: date(digitised_delivery_promise) - date(digitised_dispatch_promise)
  shipping_promise_days : shipping_delivery_promise (already an integer TAT in days)
  direction              : increased if shipping > digitised, decreased if shipping < digitised
  actual_duration_days   : date(delivery_attempt_time) - date(pickup_time)
  ops outcome            : actual < shipping_promise = Early, == = On-Time, > = Late

Population: rows 4 and 6 of courier-switch-promise-funnel-v2.csv (courier
switched/unchanged x promise changed), split further by direction of that change.

Emits outputs/promise-direction-actual-performance.csv: 4 rows
(row4-increased, row4-decreased, row6-increased, row6-decreased), each with n and
Early/On-Time/Late n + % (of that cell's own n).
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "promise-direction-actual-performance.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"
OUTCOMES = ["Early", "On-Time", "Late"]

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


def promise_direction(row: dict) -> str | None:
    dispatch_promise = parse_date(row["digitised_dispatch_promise"])
    delivery_promise = parse_date(row["digitised_delivery_promise"])
    ship_promise_raw = row["shipping_delivery_promise"].strip()
    if dispatch_promise is None or delivery_promise is None or not ship_promise_raw:
        return None
    digitised_days = (delivery_promise - dispatch_promise).days
    shipping_days = int(ship_promise_raw)
    if shipping_days > digitised_days:
        return "increased"
    if shipping_days < digitised_days:
        return "decreased"
    return "unchanged"


def classify_ops(row: dict) -> str | None:
    pickup = parse_date(row["pickup_time"])
    delivery_attempt = parse_date(row["delivery_attempt_time"])
    ship_promise_raw = row["shipping_delivery_promise"].strip()
    if pickup is None or delivery_attempt is None or not ship_promise_raw:
        return None
    actual_duration = (delivery_attempt - pickup).days
    shipping_promise = int(ship_promise_raw)
    diff = actual_duration - shipping_promise
    return "Early" if diff < 0 else "Late" if diff > 0 else "On-Time"


def main() -> None:
    v2_delivery: dict[str, str] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    cells = ["row4-increased", "row4-decreased", "row6-increased", "row6-decreased"]
    tallies: dict[str, dict[str, int]] = {c: defaultdict(int) for c in cells}

    with V1_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            oid = row["order_id"]
            dl_v2 = v2_delivery.get(oid)
            if dl_v2 is None:
                continue
            triple = (row["dispatch_leg"], row["delivery_leg"], dl_v2)
            if triple not in TARGET_COHORTS:
                continue

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            if not dig_partner or not ship_partner:
                continue

            switched = dig_partner != ship_partner
            direction = promise_direction(row)
            if direction is None or direction == "unchanged":
                continue

            branch = "row4" if switched else "row6"
            cell = f"{branch}-{direction}"

            outcome = classify_ops(row)
            if outcome is None:
                continue

            tallies[cell]["n"] += 1
            tallies[cell][outcome] += 1

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["cell", "n"] + [f"{o.lower().replace('-', '')}_n" for o in OUTCOMES]
                    + [f"{o.lower().replace('-', '')}_pct" for o in OUTCOMES])
        for cell in cells:
            n = tallies[cell]["n"]
            counts = [tallies[cell][o] for o in OUTCOMES]
            pcts = [pct(c, n) for c in counts]
            wr.writerow([cell, n] + counts + pcts)

    for cell in cells:
        n = tallies[cell]["n"]
        parts = ", ".join(f"{o}={tallies[cell][o]} ({pct(tallies[cell][o], n)}%)" for o in OUTCOMES)
        print(f"{cell}: n={n} -- {parts}")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
