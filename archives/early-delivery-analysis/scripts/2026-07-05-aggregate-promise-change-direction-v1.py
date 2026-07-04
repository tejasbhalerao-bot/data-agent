"""Direction of the promise change for rows 4 and 6 of courier-switch-promise-funnel-v2.csv
(courier switched + promise changed, and courier unchanged + promise changed).

  digitised_promise_days: date(digitised_delivery_promise) - date(digitised_dispatch_promise)
  shipping_promise_days : shipping_delivery_promise (already an integer TAT in days)
  increased : shipping_promise_days > digitised_promise_days  (more time given at shipping)
  decreased : shipping_promise_days < digitised_promise_days  (less time given at shipping)

Both rows already exclude "unchanged" (shipping == digitised) and indeterminate cases
by construction (0 indeterminate confirmed in courier-switch-promise-funnel-v2.csv),
so increased + decreased should equal 100% of each row's n.

Emits outputs/promise-change-direction.csv: one row per (row4, row6), with n, increased n/%,
decreased n/%. % is of that row's own n.
"""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "promise-change-direction.csv"
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


def promise_direction(row: dict) -> str | None:
    """Returns 'increased', 'decreased', 'unchanged', or None (indeterminate/unchanged not expected here)."""
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


def main() -> None:
    v2_delivery: dict[str, str] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    tallies: dict[str, dict[str, int]] = {
        "row4": {"n": 0, "increased": 0, "decreased": 0, "unchanged": 0, "indeterminate": 0},
        "row6": {"n": 0, "increased": 0, "decreased": 0, "unchanged": 0, "indeterminate": 0},
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

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            if not dig_partner or not ship_partner:
                continue

            switched = dig_partner != ship_partner
            direction = promise_direction(row)
            if direction is None or direction == "unchanged":
                continue  # not a "promise changed" order -- not row 4 or row 6

            branch = "row4" if switched else "row6"
            tallies[branch]["n"] += 1
            tallies[branch][direction] += 1

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["row", "n", "increased_n", "increased_pct", "decreased_n", "decreased_pct"])
        for branch in ("row4", "row6"):
            t = tallies[branch]
            wr.writerow([branch, t["n"], t["increased"], pct(t["increased"], t["n"]),
                         t["decreased"], pct(t["decreased"], t["n"])])

    for branch in ("row4", "row6"):
        t = tallies[branch]
        print(f"{branch}: n={t['n']} -- increased={t['increased']} ({pct(t['increased'], t['n'])}%), "
              f"decreased={t['decreased']} ({pct(t['decreased'], t['n'])}%)")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
