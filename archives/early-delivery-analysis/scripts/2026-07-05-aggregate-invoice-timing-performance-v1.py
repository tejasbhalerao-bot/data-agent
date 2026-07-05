"""Data check: does the digitised_ts -> invoice_create_ts gap (3-24 hours) correlate
with Delivery/Dispatch outcome, and does it differ for couriers 246/247 vs others.

Population: all 515,465 View 1 orders (outputs/view1-orders-all.csv).

Assumption stated up front: "courier_id" for the #5 cut is shipping_delivery_partner
(the courier that actually executed the order), not digitised_delivery_partner --
chosen because #3/#4 measure actual execution outcomes (delivery_attempt_time,
pickup_time), so segmenting by the courier that actually ran the order is the more
meaningful cut. Flag if digitised-time courier was intended instead.

  #2 filter: 3 <= hours(invoice_create_ts - digitised_ts) <= 24 (inclusive both ends)
  #3 / #4: reuses the already-validated dispatch_leg / delivery_leg columns from
    view1-orders-all.csv directly (same formulas requested: digitised_delivery_promise
    vs delivery_attempt_time for #3; digitised_dispatch_promise vs pickup_time for #4)
    -- not recomputed, to avoid a second, possibly-diverging implementation.
  #5 cut: courier in {246, 247} vs courier not in {246, 247, 287} (287 excluded
    entirely from this comparison, per spec -- not its own group).

Emits outputs/invoice-timing-performance.csv.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "invoice-timing-performance.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"
OUTCOMES = ["Early", "On-Time", "Late"]
TARGET_COURIERS = {"246", "247"}
EXCLUDED_COURIER = "287"


def parse_dt(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def main() -> None:
    n_total = 0
    n_step2 = 0
    delivery_tally: dict[str, int] = defaultdict(int)
    dispatch_tally: dict[str, int] = defaultdict(int)
    cut_delivery: dict[str, dict[str, int]] = {"targeted": defaultdict(int), "others": defaultdict(int)}
    cut_dispatch: dict[str, dict[str, int]] = {"targeted": defaultdict(int), "others": defaultdict(int)}

    with V1_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            n_total += 1

            digitised = parse_dt(row["digitised_ts"])
            invoice_create = parse_dt(row["invoice_create_ts"])
            if digitised is None or invoice_create is None:
                continue

            gap_hours = (invoice_create - digitised).total_seconds() / 3600
            if not (3 <= gap_hours <= 24):
                continue

            n_step2 += 1
            delivery_outcome = row["delivery_leg"]
            dispatch_outcome = row["dispatch_leg"]
            delivery_tally[delivery_outcome] += 1
            dispatch_tally[dispatch_outcome] += 1

            courier = row["shipping_delivery_partner"].strip()
            if courier == EXCLUDED_COURIER:
                continue
            cut = "targeted" if courier in TARGET_COURIERS else "others"
            cut_delivery[cut][delivery_outcome] += 1
            cut_dispatch[cut][dispatch_outcome] += 1

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["section", "n"] + [f"{o.lower().replace('-', '')}_n" for o in OUTCOMES]
                    + [f"{o.lower().replace('-', '')}_pct" for o in OUTCOMES])

        wr.writerow(["1. Total orders", n_total] + [""] * 6)
        wr.writerow(["2. Digitised->invoice gap 3-24h", n_step2] + [""] * 6)

        counts = [delivery_tally[o] for o in OUTCOMES]
        wr.writerow(["3. Delivery E/OT/L (of step 2)", n_step2] + counts + [pct(c, n_step2) for c in counts])

        counts = [dispatch_tally[o] for o in OUTCOMES]
        wr.writerow(["4. Dispatch E/OT/L (of step 2)", n_step2] + counts + [pct(c, n_step2) for c in counts])

        for cut_name, label in [("targeted", "246/247"), ("others", "others excl. 287")]:
            n = sum(cut_delivery[cut_name].values())
            counts = [cut_delivery[cut_name][o] for o in OUTCOMES]
            wr.writerow([f"5. Delivery E/OT/L - {label}", n] + counts + [pct(c, n) for c in counts])
        for cut_name, label in [("targeted", "246/247"), ("others", "others excl. 287")]:
            n = sum(cut_dispatch[cut_name].values())
            counts = [cut_dispatch[cut_name][o] for o in OUTCOMES]
            wr.writerow([f"5. Dispatch E/OT/L - {label}", n] + counts + [pct(c, n) for c in counts])

    print(f"1. Total orders: {n_total}")
    print(f"2. Digitised->invoice gap 3-24h: {n_step2} ({pct(n_step2, n_total)}%)")
    print(f"3. Delivery E/OT/L: {dict(delivery_tally)}")
    print(f"4. Dispatch E/OT/L: {dict(dispatch_tally)}")
    for cut_name, label in [("targeted", "246/247"), ("others", "others excl. 287")]:
        print(f"5. Delivery [{label}]: n={sum(cut_delivery[cut_name].values())} {dict(cut_delivery[cut_name])}")
        print(f"5. Dispatch [{label}]: n={sum(cut_dispatch[cut_name].values())} {dict(cut_dispatch[cut_name])}")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
