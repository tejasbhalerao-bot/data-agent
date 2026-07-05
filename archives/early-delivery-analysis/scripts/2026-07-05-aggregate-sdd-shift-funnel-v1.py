"""Hypothesis 3: SDD state shifts between digitised and shipping, on the same
230,923-order "not amazing" cohort used for the courier/warehouse hypotheses.

  digitised_is_sdd uses true/false; shipping_is_sdd uses 1/0 -- normalized before
  comparing (see "Discovered quirks & gotchas" in data-sources.md).

Emits outputs/sdd-shift-funnel.csv. All % are of the 230,923-order cohort.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "sdd-shift-funnel.csv"
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


def pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def main() -> None:
    v2_delivery: dict[str, str] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    n_total = 0
    n_sdd_to_nonsdd = 0
    n_nonsdd_to_sdd = 0
    n_no_shift = 0
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

    rows = [
        ("1. Total orders", n_total),
        ("2. SDD -> Non-SDD shift", n_sdd_to_nonsdd),
        ("3. Non-SDD -> SDD shift", n_nonsdd_to_sdd),
        ("4. No shift", n_no_shift),
    ]

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["step", "n", "pct_of_cohort"])
        for step, n in rows:
            wr.writerow([step, n, pct(n, n_total)])

    for step, n in rows:
        print(f"{step}: {n} ({pct(n, n_total)}%)")
    print(f"indeterminate (blank/unparseable digitised_is_sdd or shipping_is_sdd): {n_indeterminate} ({pct(n_indeterminate, n_total)}%)")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
