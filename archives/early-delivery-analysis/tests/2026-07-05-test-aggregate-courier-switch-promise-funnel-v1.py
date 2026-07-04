"""Sanity checks for courier-switch-promise-funnel.csv.

Checks:
1. Total = 230,923 (the already-validated "not amazing" cohort -- all rows of
   view1-dispatch-delivery-v1v2-crosstab.csv except On-Time/On-Time/On-Time,
   Early/Early/On-Time, Late/Late/On-Time).
2. Switched + Unchanged + switch-indeterminate = Total exactly.
3. (Switched AND promise changed) + (Switched AND promise unchanged) +
   (Switched, promise indeterminate) = Switched exactly.
4. Every row's pct_of_all_orders in the CSV matches a fresh recompute against Total.
5. Every count matches an independent recount straight from the order-detail files.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-courier-switch-promise-funnel-v1.py
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
EXPECTED_TOTAL = 230_923


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


def main() -> None:
    failures: list[str] = []

    v2_delivery: dict[str, str] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    n_total = 0
    n_switch_indeterminate = 0
    n_switch = 0
    n_unchanged = 0
    n_switch_promise_indeterminate = 0
    n_switch_promise_changed = 0
    n_switch_promise_unchanged = 0

    with (OUT / "view1-orders-all.csv").open(newline="") as f:
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

    if n_total != EXPECTED_TOTAL:
        failures.append(f"total={n_total}, expected {EXPECTED_TOTAL}")

    if n_switch + n_unchanged + n_switch_indeterminate != n_total:
        failures.append(
            f"switch({n_switch}) + unchanged({n_unchanged}) + indeterminate({n_switch_indeterminate}) "
            f"= {n_switch + n_unchanged + n_switch_indeterminate}, expected total {n_total}"
        )

    if n_switch_promise_changed + n_switch_promise_unchanged + n_switch_promise_indeterminate != n_switch:
        failures.append(
            f"promise-changed({n_switch_promise_changed}) + promise-unchanged({n_switch_promise_unchanged}) "
            f"+ promise-indeterminate({n_switch_promise_indeterminate}) = "
            f"{n_switch_promise_changed + n_switch_promise_unchanged + n_switch_promise_indeterminate}, "
            f"expected switched total {n_switch}"
        )

    expected_rows = {
        "1. Total orders": n_total,
        "2. Courier switched": n_switch,
        "2a. Courier switch indeterminate (blank partner field)": n_switch_indeterminate,
        "3. Courier unchanged": n_unchanged,
        "4. Courier switched AND promise changed": n_switch_promise_changed,
        "5. Courier switched AND promise unchanged": n_switch_promise_unchanged,
        "5a. Courier switched, promise indeterminate": n_switch_promise_indeterminate,
    }

    with (OUT / "courier-switch-promise-funnel.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            step, n, csv_pct = r["step"], int(r["n"]), float(r["pct_of_all_orders"])
            if step not in expected_rows:
                failures.append(f"unexpected step in CSV: {step}")
                continue
            if n != expected_rows[step]:
                failures.append(f"{step}: CSV n={n}, recount={expected_rows[step]}")
            expected_pct = round(expected_rows[step] / n_total * 100, 1) if n_total else 0.0
            if abs(csv_pct - expected_pct) > 0.05:
                failures.append(f"{step}: CSV pct={csv_pct}, recompute={expected_pct}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- total={n_total} matches expected {EXPECTED_TOTAL}, funnel steps sum "
          f"correctly at both levels (switch/unchanged/indeterminate, and within-switch "
          f"promise-changed/unchanged/indeterminate), and every CSV row matches an "
          f"independent recount.")


if __name__ == "__main__":
    main()
