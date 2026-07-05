"""Sanity checks for warehouse-switch-funnel.csv.

Checks:
1. Total = 230,923.
2. Warehouse changed + Warehouse same = Total exactly.
3. Every count matches an independent recount straight from the order-detail files.
4. Cross-file consistency against the already-validated courier-switch-promise-funnel-v2.csv:
   row6 (wh changed & courier changed & promise changed) + row12 (wh same & courier
   changed & promise changed) = 38,598 (the original row 4 total, courier switched
   AND promise changed, regardless of warehouse). Same logic for promise-unchanged
   (row7 + row13 = 10,158, the original row 5 total).

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-warehouse-switch-funnel-v1.py
"""

from __future__ import annotations

import csv
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TS_FMT = "%b %d, %Y, %I:%M %p"
EXPECTED_TOTAL = 230_923

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


def main() -> None:
    failures: list[str] = []

    v2_delivery: dict[str, str] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    counts = {
        "n_total": 0, "n_wh_changed": 0, "n_wh_same": 0,
        "n_wh_ch_courier_ch": 0, "n_wh_ch_courier_un": 0,
        "n_wh_ch_courier_ch_promise_ch": 0, "n_wh_ch_courier_ch_promise_un": 0,
        "n_wh_ch_courier_un_promise_ch": 0, "n_wh_ch_courier_un_promise_un": 0,
        "n_wh_un_courier_ch": 0, "n_wh_un_courier_un": 0,
        "n_wh_un_courier_ch_promise_ch": 0, "n_wh_un_courier_ch_promise_un": 0,
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

            counts["n_total"] += 1

            dig_wh = row["digitised_wh_id"].strip()
            ship_wh = row["shipping_warehouse"].strip()
            wh_changed = dig_wh != ship_wh
            counts["n_wh_changed" if wh_changed else "n_wh_same"] += 1

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            courier_known = bool(dig_partner) and bool(ship_partner)
            courier_changed = (dig_partner != ship_partner) if courier_known else None

            dispatch_promise = parse_date(row["digitised_dispatch_promise"])
            delivery_promise = parse_date(row["digitised_delivery_promise"])
            ship_promise_raw = row["shipping_delivery_promise"].strip()
            promise_known = dispatch_promise is not None and delivery_promise is not None and bool(ship_promise_raw)
            promise_changed = None
            if promise_known:
                digitised_days = (delivery_promise - dispatch_promise).days
                shipping_days = int(ship_promise_raw)
                promise_changed = shipping_days != digitised_days

            if wh_changed and courier_known:
                if courier_changed:
                    counts["n_wh_ch_courier_ch"] += 1
                    if promise_known:
                        counts["n_wh_ch_courier_ch_promise_ch" if promise_changed else "n_wh_ch_courier_ch_promise_un"] += 1
                else:
                    counts["n_wh_ch_courier_un"] += 1
                    if promise_known:
                        counts["n_wh_ch_courier_un_promise_ch" if promise_changed else "n_wh_ch_courier_un_promise_un"] += 1
            elif not wh_changed and courier_known:
                if courier_changed:
                    counts["n_wh_un_courier_ch"] += 1
                    if promise_known:
                        counts["n_wh_un_courier_ch_promise_ch" if promise_changed else "n_wh_un_courier_ch_promise_un"] += 1
                else:
                    counts["n_wh_un_courier_un"] += 1

    if counts["n_total"] != EXPECTED_TOTAL:
        failures.append(f"total={counts['n_total']}, expected {EXPECTED_TOTAL}")
    if counts["n_wh_changed"] + counts["n_wh_same"] != counts["n_total"]:
        failures.append("warehouse changed + same != total")

    step_to_key = {
        "1. Total orders": "n_total",
        "2. Warehouse changed": "n_wh_changed",
        "3. Warehouse same": "n_wh_same",
        "4. Warehouse changed AND courier changed": "n_wh_ch_courier_ch",
        "5. Warehouse changed AND courier unchanged": "n_wh_ch_courier_un",
        "6. Warehouse changed AND courier changed AND promise changed": "n_wh_ch_courier_ch_promise_ch",
        "7. Warehouse changed AND courier changed AND promise unchanged": "n_wh_ch_courier_ch_promise_un",
        "8. Warehouse changed AND courier unchanged AND promise changed": "n_wh_ch_courier_un_promise_ch",
        "9. Warehouse changed AND courier unchanged AND promise unchanged": "n_wh_ch_courier_un_promise_un",
        "10. Warehouse same AND courier changed": "n_wh_un_courier_ch",
        "11. Warehouse same AND courier unchanged": "n_wh_un_courier_un",
        "12. Warehouse same AND courier changed AND promise changed": "n_wh_un_courier_ch_promise_ch",
        "13. Warehouse same AND courier changed AND promise unchanged": "n_wh_un_courier_ch_promise_un",
    }

    csv_values: dict[str, int] = {}
    with (OUT / "warehouse-switch-funnel.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            csv_values[r["step"]] = int(r["n"])
            key = step_to_key.get(r["step"])
            if key is None:
                failures.append(f"unexpected step in CSV: {r['step']}")
                continue
            if int(r["n"]) != counts[key]:
                failures.append(f"{r['step']}: CSV n={r['n']}, recount={counts[key]}")
            expected_pct = round(counts[key] / counts["n_total"] * 100, 1) if counts["n_total"] else 0.0
            if abs(float(r["pct_of_cohort"]) - expected_pct) > 0.05:
                failures.append(f"{r['step']}: CSV pct={r['pct_of_cohort']}, recompute={expected_pct}")

    for step in step_to_key:
        if step not in csv_values:
            failures.append(f"missing step in CSV: {step}")

    row4_expected = 38_598
    row5_expected = 10_158
    row6_plus_12 = counts["n_wh_ch_courier_ch_promise_ch"] + counts["n_wh_un_courier_ch_promise_ch"]
    row7_plus_13 = counts["n_wh_ch_courier_ch_promise_un"] + counts["n_wh_un_courier_ch_promise_un"]
    if row6_plus_12 != row4_expected:
        failures.append(f"row6+row12={row6_plus_12}, expected original row4 total={row4_expected}")
    if row7_plus_13 != row5_expected:
        failures.append(f"row7+row13={row7_plus_13}, expected original row5 total={row5_expected}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- total={counts['n_total']} matches expected {EXPECTED_TOTAL}, "
          f"warehouse changed+same=total, all 13 CSV rows match an independent "
          f"recount, and cross-file consistency holds: (wh changed + wh same, "
          f"courier changed, promise changed)={row6_plus_12} matches the original "
          f"row4 total ({row4_expected}), and promise-unchanged equivalent "
          f"({row7_plus_13}) matches the original row5 total ({row5_expected}).")


if __name__ == "__main__":
    main()
