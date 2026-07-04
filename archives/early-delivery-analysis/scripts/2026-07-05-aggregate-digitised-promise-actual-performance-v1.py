"""Digitised-promise-graded performance for rows 4 and 6, individually and merged.

  digitised_promise_days: date(digitised_delivery_promise) - date(digitised_dispatch_promise)
  actual_duration_days  : date(delivery_attempt_time) - date(pickup_time)
  outcome               : actual < digitised_promise = Early, == = On-Time, > = Late

This is exactly the View 2 Delivery-leg formula already computed and validated
throughout this project (see view2-orders-all.csv's delivery_leg column) -- reused
directly here rather than recomputed, to avoid a second, possibly-diverging
implementation of the same classification.

IMPORTANT, stated up front to avoid the day_diff=0 confusion from earlier in this
session: rows 4 and 6 are drawn from the 230,923-order "not amazing" cohort, which by
construction excludes every (dispatch, delivery_view1, delivery_view2) combination
where delivery_view2=On-Time. So On-Time will be exactly 0% in every view below --
that is expected and structural, not a bug. This is the mirror image of
shipping-promise-actual-performance.csv (which grades the SAME orders against
shipping_delivery_promise instead and found Late near-zero) -- the point of this
script is the "before" picture: how bad performance looks graded against the promise
that was already known to be stale by shipping time.

Emits outputs/digitised-promise-actual-performance.csv: one row per view
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
OUT_PATH = ROOT / "outputs" / "digitised-promise-actual-performance.csv"
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
    dispatch_promise = parse_date(row["digitised_dispatch_promise"])
    delivery_promise = parse_date(row["digitised_delivery_promise"])
    ship_promise_raw = row["shipping_delivery_promise"].strip()
    if dispatch_promise is None or delivery_promise is None or not ship_promise_raw:
        return None
    digitised_days = (delivery_promise - dispatch_promise).days
    shipping_days = int(ship_promise_raw)
    return shipping_days != digitised_days


def main() -> None:
    v2_rows: dict[str, dict[str, str]] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    tallies: dict[str, dict[str, int]] = {
        "row4": defaultdict(int), "row6": defaultdict(int), "merged": defaultdict(int)
    }

    with V1_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            oid = row["order_id"]
            r2 = v2_rows.get(oid)
            if r2 is None:
                continue
            triple = (row["dispatch_leg"], row["delivery_leg"], r2["delivery_leg"])
            if triple not in TARGET_COHORTS:
                continue

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            if not dig_partner or not ship_partner:
                continue

            changed = promise_changed(row)
            if changed is not True:
                continue

            switched = dig_partner != ship_partner
            branch = "row4" if switched else "row6"

            # digitised-promise-graded outcome = View 2's already-validated delivery_leg
            # (same formula: actual_duration vs digitised-derived promise_duration).
            outcome = r2["delivery_leg"]

            tallies[branch]["n"] += 1
            tallies[branch][outcome] += 1
            tallies["merged"]["n"] += 1
            tallies["merged"][outcome] += 1

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["view", "n"] + [f"{o.lower().replace('-', '')}_n" for o in OUTCOMES]
                    + [f"{o.lower().replace('-', '')}_pct" for o in OUTCOMES])
        for view in ("row4", "row6", "merged"):
            n = tallies[view]["n"]
            counts = [tallies[view][o] for o in OUTCOMES]
            pcts = [pct(c, n) for c in counts]
            wr.writerow([view, n] + counts + pcts)

    for view in ("row4", "row6", "merged"):
        n = tallies[view]["n"]
        parts = ", ".join(f"{o}={tallies[view][o]} ({pct(tallies[view][o], n)}%)" for o in OUTCOMES)
        print(f"{view}: n={n} -- {parts}")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
