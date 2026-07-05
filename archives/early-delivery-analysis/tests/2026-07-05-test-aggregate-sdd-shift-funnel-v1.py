"""Sanity checks for sdd-shift-funnel.csv.

Checks:
1. Total = 230,923.
2. SDD->Non-SDD + Non-SDD->SDD + No shift + indeterminate = Total exactly.
3. Every count/pct matches an independent recount straight from the order-detail files.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-sdd-shift-funnel-v1.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
EXPECTED_TOTAL = 230_923
BOOL_MAP = {"true": True, "1": True, "false": False, "0": False}

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


def norm_bool(raw: str) -> bool | None:
    return BOOL_MAP.get((raw or "").strip().lower())


def main() -> None:
    failures: list[str] = []

    v2_delivery: dict[str, str] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    n_total = 0
    n_sdd_to_nonsdd = 0
    n_nonsdd_to_sdd = 0
    n_no_shift = 0
    n_indeterminate = 0

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

            dig_sdd = norm_bool(row["digitised_is_sdd"])
            ship_sdd = norm_bool(row["shipping_is_sdd"])
            if dig_sdd is None or ship_sdd is None:
                n_indeterminate += 1
                continue

            if dig_sdd and not ship_sdd:
                n_sdd_to_nonsdd += 1
            elif not dig_sdd and ship_sdd:
                n_nonsdd_to_sdd += 1
            else:
                n_no_shift += 1

    if n_total != EXPECTED_TOTAL:
        failures.append(f"total={n_total}, expected {EXPECTED_TOTAL}")

    if n_sdd_to_nonsdd + n_nonsdd_to_sdd + n_no_shift + n_indeterminate != n_total:
        failures.append("funnel components do not sum to total")

    expected_rows = {
        "1. Total orders": n_total,
        "2. SDD -> Non-SDD shift": n_sdd_to_nonsdd,
        "3. Non-SDD -> SDD shift": n_nonsdd_to_sdd,
        "4. No shift": n_no_shift,
    }

    with (OUT / "sdd-shift-funnel.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            step, n, csv_pct = r["step"], int(r["n"]), float(r["pct_of_cohort"])
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

    print(f"PASS -- total={n_total} matches expected {EXPECTED_TOTAL}, funnel "
          f"components sum correctly (indeterminate={n_indeterminate}), and all "
          f"CSV rows match an independent recount.")


if __name__ == "__main__":
    main()
