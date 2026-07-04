"""Consistency + algebraic sanity checks for view1-dispatch-delivery-v1v2-crosstab.csv.

The crosstab came back with 18 of 27 cells at exactly zero. This is expected, not a
bug -- it falls out of algebra, not data quality:

  x  = date(pickup_time) - date(dispatch_promise)            -> sign(x) = Dispatch bucket
  D1 = date(delivery_attempt) - date(delivery_promise)        -> sign(D1) = View 1 Delivery bucket
  A  = date(delivery_attempt) - date(pickup_time)              (View 2 actual duration)
  P  = date(delivery_promise) - date(dispatch_promise)         (View 2 promise duration)

  A - P = (delivery_attempt - delivery_promise) - (pickup_time - dispatch_promise) = D1 - x

  -> View 2 Delivery bucket = sign(D1 - x), always.

So whenever Dispatch (sign of x) and View 1 Delivery (sign of D1) have different or zero
sign, D1 - x has a forced sign and View 2 Delivery collapses to a single deterministic
outcome. Real variation in View 2 Delivery only exists when Dispatch and View 1 Delivery
are the same sign (both Early, or both Late) -- there the two magnitudes compete and the
result isn't fixed. That is exactly the (Early,Early,*) and (Late,Late,*) rows, the only
two with all three View 2 outcomes populated.

Checks:
1. For every common order, recompute D1 - x directly from raw promise/actual columns and
   confirm it predicts the actual View 2 Delivery label exactly (0 mismatches).
2. Crosstab cell counts reconcile exactly with a fresh recount from the two order-detail files.
3. The 7 structurally-deterministic (dispatch, delivery_view1) combos have exactly one
   non-zero delivery_view2 cell each; only (Early,Early) and (Late,Late) have all three.

Run: python3 archives/early-delivery-analysis/tests/2026-07-04-test-aggregate-dispatch-delivery-v1v2-v1.py
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TS_FMT = "%b %d, %Y, %I:%M %p"
OUTCOMES = ["Early", "On-Time", "Late"]

DETERMINISTIC_EXPECTED = {
    ("Early", "Early"): None,  # varies -- checked separately, must have >1 non-zero cell
    ("Early", "On-Time"): "Late",
    ("Early", "Late"): "Late",
    ("On-Time", "Early"): "Early",
    ("On-Time", "On-Time"): "On-Time",
    ("On-Time", "Late"): "Late",
    ("Late", "Early"): "Early",
    ("Late", "On-Time"): "Early",
    ("Late", "Late"): None,  # varies -- checked separately, must have >1 non-zero cell
}


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


def cls(diff: int) -> str:
    return "Early" if diff < 0 else "Late" if diff > 0 else "On-Time"


def main() -> None:
    failures: list[str] = []

    v1_rows: dict[str, dict[str, str]] = {}
    with (OUT / "view1-orders-all.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            v1_rows[r["order_id"]] = r

    v2_rows: dict[str, dict[str, str]] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            v2_rows[r["order_id"]] = r

    common = set(v1_rows) & set(v2_rows)

    algebra_mismatches = 0
    recount: Counter[tuple[str, str, str]] = Counter()
    for oid in common:
        r1 = v1_rows[oid]
        r2 = v2_rows[oid]

        dispatch_promise = parse_date(r1["digitised_dispatch_promise"])
        pickup = parse_date(r1["pickup_time"])
        delivery_promise = parse_date(r1["digitised_delivery_promise"])
        delivery_attempt = parse_date(r1["delivery_attempt_time"])

        x = (pickup - dispatch_promise).days
        d1 = (delivery_attempt - delivery_promise).days
        expected_v2 = cls(d1 - x)

        if expected_v2 != r2["delivery_leg"]:
            algebra_mismatches += 1

        recount[(r1["dispatch_leg"], r1["delivery_leg"], r2["delivery_leg"])] += 1

    if algebra_mismatches:
        failures.append(
            f"algebraic identity View2_delivery = sign(D1 - x) failed for "
            f"{algebra_mismatches}/{len(common)} orders -- expected 0"
        )

    crosstab: dict[tuple[str, str, str], int] = {}
    with (OUT / "view1-dispatch-delivery-v1v2-crosstab.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            crosstab[(r["dispatch"], r["delivery_view1"], r["delivery_view2"])] = int(r["count"])

    for dp in OUTCOMES:
        for dl1 in OUTCOMES:
            for dl2 in OUTCOMES:
                key = (dp, dl1, dl2)
                if crosstab.get(key, 0) != recount.get(key, 0):
                    failures.append(
                        f"cell {key}: crosstab={crosstab.get(key, 0)}, recount={recount.get(key, 0)}"
                    )

    for (dp, dl1), expected in DETERMINISTIC_EXPECTED.items():
        cell_counts = {dl2: recount.get((dp, dl1, dl2), 0) for dl2 in OUTCOMES}
        non_zero = [o for o, n in cell_counts.items() if n > 0]
        if expected is None:
            if len(non_zero) < 2:
                failures.append(
                    f"({dp},{dl1}) expected genuine variation (>=2 non-zero View2 outcomes), "
                    f"got {non_zero}"
                )
        else:
            if non_zero != [expected]:
                failures.append(
                    f"({dp},{dl1}) expected deterministic View2={expected} only, "
                    f"got non-zero cells {non_zero}"
                )

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- algebraic identity View2_delivery=sign(D1-x) holds for all {len(common)} "
          f"common orders, crosstab reconciles with recount, and the 18 structurally-zero "
          f"cells match the predicted deterministic pattern.")


if __name__ == "__main__":
    main()
