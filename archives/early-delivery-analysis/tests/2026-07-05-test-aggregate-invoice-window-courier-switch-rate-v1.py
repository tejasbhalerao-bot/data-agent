"""Sanity checks for invoice-window-courier-switch-rate.csv.

Checks:
1. all_515465 n = 515,465; invoice_window_3to24h n = 263,117 (matches the
   already-validated step2 count from invoice-timing-performance.csv).
2. switch + same + indeterminate = n exactly for both populations.
3. Every count/pct matches an independent recount straight from the order-detail file.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-invoice-window-courier-switch-rate-v1.py
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TS_FMT = "%b %d, %Y, %I:%M %p"
EXPECTED_ALL_N = 515_465
EXPECTED_WINDOW_N = 263_117


def parse_dt(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def main() -> None:
    failures: list[str] = []

    n_all = 0
    n_all_switch = 0
    n_all_same = 0
    n_all_indeterminate = 0
    n_window = 0
    n_window_switch = 0
    n_window_same = 0
    n_window_indeterminate = 0

    with (OUT / "view1-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            n_all += 1

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            if not dig_partner or not ship_partner:
                switch = None
                n_all_indeterminate += 1
            else:
                switch = dig_partner != ship_partner
                if switch:
                    n_all_switch += 1
                else:
                    n_all_same += 1

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

    if n_all != EXPECTED_ALL_N:
        failures.append(f"all n={n_all}, expected {EXPECTED_ALL_N}")
    if n_window != EXPECTED_WINDOW_N:
        failures.append(f"window n={n_window}, expected {EXPECTED_WINDOW_N}")

    if n_all_switch + n_all_same + n_all_indeterminate != n_all:
        failures.append("all: switch+same+indeterminate != n")
    if n_window_switch + n_window_same + n_window_indeterminate != n_window:
        failures.append("window: switch+same+indeterminate != n")

    csv_rows = {}
    with (OUT / "invoice-window-courier-switch-rate.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            csv_rows[r["population"]] = r

    expected = {
        "all_515465": (n_all, n_all_switch, n_all_same, n_all_indeterminate),
        "invoice_window_3to24h": (n_window, n_window_switch, n_window_same, n_window_indeterminate),
    }
    for pop, (n, switch_n, same_n, indet_n) in expected.items():
        r = csv_rows[pop]
        if int(r["n"]) != n:
            failures.append(f"{pop}: CSV n={r['n']}, recount={n}")
        if int(r["switch_n"]) != switch_n:
            failures.append(f"{pop}: CSV switch_n={r['switch_n']}, recount={switch_n}")
        if int(r["same_n"]) != same_n:
            failures.append(f"{pop}: CSV same_n={r['same_n']}, recount={same_n}")
        if int(r["indeterminate_n"]) != indet_n:
            failures.append(f"{pop}: CSV indeterminate_n={r['indeterminate_n']}, recount={indet_n}")
        for field, val in [("switch_pct", switch_n), ("same_pct", same_n), ("indeterminate_pct", indet_n)]:
            exp_pct = round(val / n * 100, 1) if n else 0.0
            if abs(float(r[field]) - exp_pct) > 0.05:
                failures.append(f"{pop}/{field}: CSV={r[field]}, recompute={exp_pct}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- all n={n_all} matches expected {EXPECTED_ALL_N}, window n={n_window} "
          f"matches expected {EXPECTED_WINDOW_N}, switch+same+indeterminate sums "
          f"correctly for both populations, and all CSV values match an independent recount.")


if __name__ == "__main__":
    main()
