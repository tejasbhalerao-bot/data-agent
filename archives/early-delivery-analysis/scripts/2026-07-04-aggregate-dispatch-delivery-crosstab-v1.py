"""View 1 Dispatch x Delivery cross-tab: how much of Delivery's outcome traces to Dispatch.

Deliberately reads dispatch_leg/delivery_leg off outputs/view1-orders-all.csv rather
than re-deriving from raw data -- those labels were already computed and validated by
2026-07-04-aggregate-view-cascade-v3.py (see its consistency test). Re-implementing the
classification here would risk a second, possibly-diverging definition of the same leg.

Emits outputs/view1-dispatch-delivery-crosstab.csv: 9 rows (Dispatch x Delivery), each
with order count and % of all View 1 orders (not % within Dispatch bucket).
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDERS_PATH = ROOT / "outputs" / "view1-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "view1-dispatch-delivery-crosstab.csv"
OUTCOMES = ["Early", "On-Time", "Late"]


def pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def main() -> None:
    counts: Counter[tuple[str, str]] = Counter()
    n_total = 0
    with ORDERS_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            n_total += 1
            counts[(row["dispatch_leg"], row["delivery_leg"])] += 1

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["dispatch", "delivery", "count", "pct_of_all"])
        for dp in OUTCOMES:
            for dl in OUTCOMES:
                n = counts[(dp, dl)]
                wr.writerow([dp, dl, n, pct(n, n_total)])

    print(f"n_total (View 1, ALL cut): {n_total}")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
