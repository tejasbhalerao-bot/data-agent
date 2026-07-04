"""Consistency checks for outputs of 2026-07-04-aggregate-view-cascade-v3.py.

Two invariants that must always hold, run after every regeneration:

1. Cascade summary CSVs must reconcile exactly with counts recomputed from the
   matching order-detail CSV -- the two output artifacts must never drift apart.
2. Warehouse and Dispatch legs are defined identically in View 1 and View 2, so any
   order present in both views' "all" cohort must get the same Warehouse/Dispatch
   label in both -- a mismatch would mean the two views silently diverged.

Run: python3 archives/early-delivery-analysis/tests/2026-07-04-test-aggregate-view-cascade-v1.py
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUTCOMES = ["Early", "On-Time", "Late"]
LEGS = ["doctor", "warehouse", "dispatch", "delivery"]
CUTS = ["all", "sdd-inventory", "sdd-noninventory", "nonsdd-inventory", "nonsdd-noninventory"]


def pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def load_cascade(path: Path) -> dict[str, dict[str, int]]:
    rows = {}
    with path.open(newline="") as f:
        for r in csv.DictReader(f):
            rows[r["leg"].lower()] = {
                "count": int(r["count"]),
                "Early": int(r["early_n"]),
                "On-Time": int(r["ontime_n"]),
                "Late": int(r["late_n"]),
            }
    return rows


def recompute_from_orders(path: Path) -> tuple[int, dict[str, Counter]]:
    counters = {leg: Counter() for leg in LEGS}
    n = 0
    with path.open(newline="") as f:
        for r in csv.DictReader(f):
            n += 1
            for leg in LEGS:
                counters[leg][r[f"{leg}_leg"]] += 1
    return n, counters


def check_cascade_matches_orders(view_tag: str, cut: str, failures: list[str]) -> None:
    cascade = load_cascade(OUT / f"{view_tag}-cascade-{cut}.csv")
    n, counters = recompute_from_orders(OUT / f"{view_tag}-orders-{cut}.csv")
    for leg in LEGS:
        expected = cascade[leg]
        if expected["count"] != n:
            failures.append(f"{view_tag}/{cut}/{leg}: count {expected['count']} != recomputed {n}")
        for outcome in OUTCOMES:
            if expected[outcome] != counters[leg][outcome]:
                failures.append(
                    f"{view_tag}/{cut}/{leg}/{outcome}: cascade says {expected[outcome]}, "
                    f"orders file has {counters[leg][outcome]}"
                )


def check_cross_view_leg_parity(failures: list[str]) -> None:
    v1 = {}
    with (OUT / "view1-orders-all.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            v1[r["order_id"]] = (r["warehouse_leg"], r["dispatch_leg"])
    v2 = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            v2[r["order_id"]] = (r["warehouse_leg"], r["dispatch_leg"])
    common = set(v1) & set(v2)
    if not common:
        failures.append("cross-view parity: no common orders found between view1 and view2 -- check inputs")
        return
    mismatches = [oid for oid in common if v1[oid] != v2[oid]]
    if mismatches:
        failures.append(
            f"cross-view parity: {len(mismatches)}/{len(common)} common orders have a "
            f"Warehouse/Dispatch label mismatch between View 1 and View 2 (should be 0, "
            f"same formula in both views) -- e.g. order {mismatches[0]}"
        )


def main() -> None:
    failures: list[str] = []
    for view_tag in ("view1", "view2"):
        for cut in CUTS:
            check_cascade_matches_orders(view_tag, cut, failures)
    check_cross_view_leg_parity(failures)

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- cascade/order-detail reconciliation and cross-view leg parity all hold "
          f"({len(CUTS)} cuts x 2 views).")


if __name__ == "__main__":
    main()
