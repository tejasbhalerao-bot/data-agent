"""Consistency checks for outputs/view1-dispatch-delivery-crosstab.csv.

Invariants that must always hold:

1. Every (dispatch, delivery) cell count must exactly match a fresh recount straight
   from view1-orders-all.csv -- the crosstab must never drift from the order-detail file.
2. The 9 cells must sum to the full View 1 "all" population (n=515,465) and pct_of_all
   values must sum to ~100%.
3. Each cell's dispatch_leg/delivery_leg marginal totals (summed across the crosstab)
   must match the Dispatch/Delivery rows already reported in view1-cascade-all.csv --
   this new cut of the data cannot silently disagree with the already-validated
   per-leg marginals.

Run: python3 archives/early-delivery-analysis/tests/2026-07-04-test-aggregate-dispatch-delivery-crosstab-v1.py
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUTCOMES = ["Early", "On-Time", "Late"]


def load_crosstab(path: Path) -> dict[tuple[str, str], tuple[int, float]]:
    cells = {}
    with path.open(newline="") as f:
        for r in csv.DictReader(f):
            cells[(r["dispatch"], r["delivery"])] = (int(r["count"]), float(r["pct_of_all"]))
    return cells


def load_cascade_leg(path: Path, leg: str) -> dict[str, int]:
    with path.open(newline="") as f:
        for r in csv.DictReader(f):
            if r["leg"].lower() == leg:
                return {"Early": int(r["early_n"]), "On-Time": int(r["ontime_n"]), "Late": int(r["late_n"])}
    raise ValueError(f"leg {leg} not found in {path}")


def main() -> None:
    failures: list[str] = []

    crosstab = load_crosstab(OUT / "view1-dispatch-delivery-crosstab.csv")

    recount: Counter[tuple[str, str]] = Counter()
    n_total = 0
    with (OUT / "view1-orders-all.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            n_total += 1
            recount[(r["dispatch_leg"], r["delivery_leg"])] += 1

    for dp in OUTCOMES:
        for dl in OUTCOMES:
            expected_n, expected_pct = crosstab[(dp, dl)]
            actual_n = recount[(dp, dl)]
            if expected_n != actual_n:
                failures.append(f"cell ({dp},{dl}): crosstab n={expected_n}, recount from orders file={actual_n}")
            actual_pct = round(actual_n / n_total * 100, 1) if n_total else 0.0
            if abs(expected_pct - actual_pct) > 0.05:
                failures.append(f"cell ({dp},{dl}): crosstab pct={expected_pct}, recomputed pct={actual_pct}")

    n_sum = sum(n for n, _ in crosstab.values())
    if n_sum != n_total:
        failures.append(f"crosstab cells sum to {n_sum}, expected {n_total}")

    pct_sum = sum(p for _, p in crosstab.values())
    if abs(pct_sum - 100.0) > 0.5:
        failures.append(f"pct_of_all sums to {pct_sum}, expected ~100.0")

    dispatch_marg = {o: sum(n for (dp, dl), (n, _) in crosstab.items() if dp == o) for o in OUTCOMES}
    delivery_marg = {o: sum(n for (dp, dl), (n, _) in crosstab.items() if dl == o) for o in OUTCOMES}
    cascade_dispatch = load_cascade_leg(OUT / "view1-cascade-all.csv", "dispatch")
    cascade_delivery = load_cascade_leg(OUT / "view1-cascade-all.csv", "delivery")

    for o in OUTCOMES:
        if dispatch_marg[o] != cascade_dispatch[o]:
            failures.append(
                f"dispatch={o}: crosstab marginal={dispatch_marg[o]}, "
                f"view1-cascade-all.csv dispatch row={cascade_dispatch[o]}"
            )
        if delivery_marg[o] != cascade_delivery[o]:
            failures.append(
                f"delivery={o}: crosstab marginal={delivery_marg[o]}, "
                f"view1-cascade-all.csv delivery row={cascade_delivery[o]}"
            )

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print("PASS -- crosstab reconciles with order-detail recount, sums to full population, "
          "and marginals match the already-validated view1-cascade-all.csv leg rows.")


if __name__ == "__main__":
    main()
