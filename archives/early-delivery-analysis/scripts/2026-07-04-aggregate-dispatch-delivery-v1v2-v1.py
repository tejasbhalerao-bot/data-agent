"""Dispatch x Delivery(View 1) x Delivery(View 2): customer experience vs ops execution.

Marries the View 1 Dispatch->Delivery crosstab with View 2's Delivery outcome for the
same order, to separate "customer saw X" from "ops actually did Y" on the same order.

Universe: orders present in BOTH view1-orders-all.csv and view2-orders-all.csv (515,396
of them -- View 1 and View 2 differ by 69/4 orders respectively due to differing
Doctor-actual-column completeness requirements, see 2026-07-04-view1-view2-cascade-
definitions-v1.md). "% of all orders" below is % of this common universe, NOT of the
515,465-order View 1 population or the 515,400-order View 2 population -- those totals
include a handful of orders the other view can't classify. This is flagged explicitly
so the denominator is never a silent assumption.

Dispatch is read from View 1's file only: Dispatch is defined identically in both views
(same digitised_dispatch_promise vs pickup_time formula), so it must be identical for
every common order. This script asserts that and fails loudly if not -- if it ever
fires, something upstream has silently diverged.

Emits outputs/view1-dispatch-delivery-v1v2-crosstab.csv: 27 rows
(Dispatch x Delivery-View1 x Delivery-View2), each with order count and % of the
common universe.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "view1-dispatch-delivery-v1v2-crosstab.csv"
OUTCOMES = ["Early", "On-Time", "Late"]


def pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def main() -> None:
    v1: dict[str, tuple[str, str]] = {}
    with V1_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v1[row["order_id"]] = (row["dispatch_leg"], row["delivery_leg"])

    v2: dict[str, tuple[str, str]] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2[row["order_id"]] = (row["dispatch_leg"], row["delivery_leg"])

    common = set(v1) & set(v2)
    n_common = len(common)

    dispatch_mismatches = 0
    counts: Counter[tuple[str, str, str]] = Counter()
    for oid in common:
        dispatch_v1, delivery_v1 = v1[oid]
        dispatch_v2, delivery_v2 = v2[oid]
        if dispatch_v1 != dispatch_v2:
            dispatch_mismatches += 1
            continue
        counts[(dispatch_v1, delivery_v1, delivery_v2)] += 1

    if dispatch_mismatches:
        print(f"ABORT: {dispatch_mismatches} common orders have mismatched Dispatch "
              f"label between View 1 and View 2 -- should be 0, same formula in both "
              f"views. Investigate before trusting this output.")
        sys.exit(1)

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["dispatch", "delivery_view1", "delivery_view2", "count", "pct_of_all"])
        for dp in OUTCOMES:
            for dl1 in OUTCOMES:
                for dl2 in OUTCOMES:
                    n = counts[(dp, dl1, dl2)]
                    wr.writerow([dp, dl1, dl2, n, pct(n, n_common)])

    print(f"common universe (in both View 1 and View 2): {n_common}")
    print(f"dispatch label mismatches found: {dispatch_mismatches} (expected 0)")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
