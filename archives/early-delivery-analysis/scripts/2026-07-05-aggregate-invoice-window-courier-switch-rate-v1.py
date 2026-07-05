"""Courier switch rate (digitised_delivery_partner != shipping_delivery_partner) for
the 263,117-order digitised->invoice 3-24h window vs the full 515,465-order View 1
population.

Same courier-switch definition as courier-switch-promise-funnel-v2.csv, applied to
the step-2 population from 2026-07-05-aggregate-invoice-timing-performance-v1.py.

Emits outputs/invoice-window-courier-switch-rate.csv.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "invoice-window-courier-switch-rate.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"


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
    n_all = 0
    n_all_switch = 0
    n_all_same = 0
    n_all_indeterminate = 0

    n_window = 0
    n_window_switch = 0
    n_window_same = 0
    n_window_indeterminate = 0

    with V1_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            n_all += 1

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            if not dig_partner or not ship_partner:
                switch = None
                n_all_indeterminate += 1
            else:
                switch = dig_partner != ship_partner
                n_all_switch += 1 if switch else 0
                n_all_same += 0 if switch else 1

            digitised = parse_dt(row["digitised_ts"])
            invoice_create = parse_dt(row["invoice_create_ts"])
            if digitised is None or invoice_create is None:
                continue
            gap_hours = (invoice_create - digitised).total_seconds() / 3600
            if not (3 <= gap_hours <= 24):
                continue

            n_window += 1
            if switch is None:
                n_window_indeterminate += 1
            elif switch:
                n_window_switch += 1
            else:
                n_window_same += 1

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["population", "n", "switch_n", "switch_pct", "same_n", "same_pct",
                     "indeterminate_n", "indeterminate_pct"])
        wr.writerow(["all_515465", n_all, n_all_switch, pct(n_all_switch, n_all),
                     n_all_same, pct(n_all_same, n_all), n_all_indeterminate, pct(n_all_indeterminate, n_all)])
        wr.writerow(["invoice_window_3to24h", n_window, n_window_switch, pct(n_window_switch, n_window),
                     n_window_same, pct(n_window_same, n_window), n_window_indeterminate, pct(n_window_indeterminate, n_window)])

    print(f"ALL (n={n_all}): switch={n_all_switch} ({pct(n_all_switch, n_all)}%), "
          f"same={n_all_same} ({pct(n_all_same, n_all)}%), indeterminate={n_all_indeterminate} ({pct(n_all_indeterminate, n_all)}%)")
    print(f"WINDOW 3-24h (n={n_window}): switch={n_window_switch} ({pct(n_window_switch, n_window)}%), "
          f"same={n_window_same} ({pct(n_window_same, n_window)}%), indeterminate={n_window_indeterminate} ({pct(n_window_indeterminate, n_window)}%)")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
