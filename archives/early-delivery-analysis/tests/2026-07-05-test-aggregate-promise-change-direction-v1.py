"""Sanity checks for promise-change-direction.csv.

Checks:
1. row4 n = 38,598 and row6 n = 110,586, matching the already-validated rows 4 and 6
   of courier-switch-promise-funnel-v2.csv exactly.
2. increased + decreased = n exactly for each row (no "unchanged" or indeterminate
   leakage -- these are by definition already-changed-promise orders).
3. Every count and pct matches an independent recount straight from the order-detail
   files.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-promise-change-direction-v1.py
"""

from __future__ import annotations

import csv
import sys
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
EXPECTED_ROW4_N = 38_598
EXPECTED_ROW6_N = 110_586


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


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


def main() -> None:
    failures: list[str] = []

    v2_delivery: dict[str, str] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    tallies: dict[str, dict[str, int]] = {
        "row4": {"n": 0, "increased": 0, "decreased": 0},
        "row6": {"n": 0, "increased": 0, "decreased": 0},
    }

    with (OUT / "view1-orders-all.csv").open(newline="") as f:
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
            tallies[branch]["n"] += 1
            tallies[branch][direction] += 1

    if tallies["row4"]["n"] != EXPECTED_ROW4_N:
        failures.append(f"row4 n={tallies['row4']['n']}, expected {EXPECTED_ROW4_N}")
    if tallies["row6"]["n"] != EXPECTED_ROW6_N:
        failures.append(f"row6 n={tallies['row6']['n']}, expected {EXPECTED_ROW6_N}")

    for branch in ("row4", "row6"):
        t = tallies[branch]
        if t["increased"] + t["decreased"] != t["n"]:
            failures.append(f"{branch}: increased({t['increased']}) + decreased({t['decreased']}) != n({t['n']})")

    csv_rows: dict[str, dict[str, str]] = {}
    with (OUT / "promise-change-direction.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            csv_rows[r["row"]] = r

    for branch in ("row4", "row6"):
        t = tallies[branch]
        r = csv_rows[branch]
        if int(r["n"]) != t["n"]:
            failures.append(f"{branch}: CSV n={r['n']}, recount={t['n']}")
        if int(r["increased_n"]) != t["increased"]:
            failures.append(f"{branch}: CSV increased_n={r['increased_n']}, recount={t['increased']}")
        if int(r["decreased_n"]) != t["decreased"]:
            failures.append(f"{branch}: CSV decreased_n={r['decreased_n']}, recount={t['decreased']}")
        exp_inc_pct = round(t["increased"] / t["n"] * 100, 1) if t["n"] else 0.0
        exp_dec_pct = round(t["decreased"] / t["n"] * 100, 1) if t["n"] else 0.0
        if abs(float(r["increased_pct"]) - exp_inc_pct) > 0.05:
            failures.append(f"{branch}: CSV increased_pct={r['increased_pct']}, recompute={exp_inc_pct}")
        if abs(float(r["decreased_pct"]) - exp_dec_pct) > 0.05:
            failures.append(f"{branch}: CSV decreased_pct={r['decreased_pct']}, recompute={exp_dec_pct}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- row4 n={tallies['row4']['n']} matches expected {EXPECTED_ROW4_N}, "
          f"row6 n={tallies['row6']['n']} matches expected {EXPECTED_ROW6_N}, increased+"
          f"decreased sums to n exactly for both rows, and all CSV values match an "
          f"independent recount.")


if __name__ == "__main__":
    main()
