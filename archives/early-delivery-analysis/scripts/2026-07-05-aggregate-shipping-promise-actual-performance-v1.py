"""True ops performance for rows 4 and 6 of courier-switch-promise-funnel-v2.csv --
the two "promise changed" cohorts (courier switched + promise changed, and courier
unchanged + promise changed).

Rationale: for these orders, the digitised-time promise was already known to be
wrong by shipping time (that's what "promise changed" means), so grading ops against
it -- like View 2 does elsewhere in this project -- measures against a stale target.
This grades ops against shipping_delivery_promise instead, the TAT actually given to
the shipping partner, which is the true, fair benchmark for what they were held to.

  actual_duration_days = date(delivery_attempt_time) - date(pickup_time)
  shipping_promise_days = shipping_delivery_promise (already an integer TAT in days)
  classification: actual < promise = Early, actual == promise = On-Time, actual > promise = Late

Population, drawn from the 230,923-order "not amazing" cohort (see
2026-07-05-aggregate-courier-switch-promise-funnel-v2.py):
  row 4 only : courier switched AND promise changed   (n=38,598)
  row 6 only : courier unchanged AND promise changed  (n=110,586)
  merged     : row 4 + row 6                          (n=149,184)

Emits outputs/shipping-promise-actual-performance.csv: one row per view
(row4, row6, merged), each with n and Early/On-Time/Late n + %.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "shipping-promise-actual-performance.csv"
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


def promise_changed(row: dict) -> bool | None:
    """None if indeterminate."""
    dispatch_promise = parse_date(row["digitised_dispatch_promise"])
    delivery_promise = parse_date(row["digitised_delivery_promise"])
    ship_promise_raw = row["shipping_delivery_promise"].strip()
    if dispatch_promise is None or delivery_promise is None or not ship_promise_raw:
        return None
    digitised_promise_days = (delivery_promise - dispatch_promise).days
    shipping_promise_days = int(ship_promise_raw)
    return shipping_promise_days != digitised_promise_days


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

    tallies: dict[str, dict[str, int]] = {
        "row4": defaultdict(int), "row6": defaultdict(int), "merged": defaultdict(int)
    }
    n_indeterminate = 0

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
            changed = promise_changed(row)
            if changed is not True:
                continue

            branch = "row4" if switched else "row6"
            outcome = classify_ops(row)
            if outcome is None:
                n_indeterminate += 1
                continue

            tallies[branch][outcome] += 1
            tallies[branch]["_n"] += 1
            tallies["merged"][outcome] += 1
            tallies["merged"]["_n"] += 1

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["view", "n"] + [f"{o.lower().replace('-', '')}_n" for o in OUTCOMES]
                    + [f"{o.lower().replace('-', '')}_pct" for o in OUTCOMES])
        for view in ("row4", "row6", "merged"):
            n = tallies[view]["_n"]
            counts = [tallies[view][o] for o in OUTCOMES]
            pcts = [pct(c, n) for c in counts]
            wr.writerow([view, n] + counts + pcts)

    for view in ("row4", "row6", "merged"):
        n = tallies[view]["_n"]
        parts = ", ".join(f"{o}={tallies[view][o]} ({pct(tallies[view][o], n)}%)" for o in OUTCOMES)
        print(f"{view}: n={n} -- {parts}")
    print(f"indeterminate (excluded, missing pickup/delivery_attempt/shipping_promise): {n_indeterminate}")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
