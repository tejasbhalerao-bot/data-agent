"""Delivery E/OT/L for two cohorts within the digitised->invoice 3-24h window
(n=263,117, from 2026-07-05-aggregate-invoice-timing-performance-v1.py):

  Cohort 1: courier switched (digitised_delivery_partner != shipping_delivery_partner)
  Cohort 2: courier not switched

Delivery definition (as specified): date(delivery_attempt_time) vs
date(digitised_delivery_promise) -- this is exactly view1-orders-all.csv's own
delivery_leg field, reused directly rather than recomputed.

Blank digitised_delivery_partner (indeterminate switch status) is excluded from
both cohorts, not folded into either.

Emits outputs/invoice-window-courier-switch-delivery.csv.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "invoice-window-courier-switch-delivery.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"
OUTCOMES = ["Early", "On-Time", "Late"]


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
    tallies: dict[str, dict[str, int]] = {"switched": defaultdict(int), "not_switched": defaultdict(int)}
    n_indeterminate = 0
    n_window = 0

    with V1_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            digitised = parse_dt(row["digitised_ts"])
            invoice_create = parse_dt(row["invoice_create_ts"])
            if digitised is None or invoice_create is None:
                continue
            gap_hours = (invoice_create - digitised).total_seconds() / 3600
            if not (3 <= gap_hours <= 24):
                continue

            n_window += 1

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            if not dig_partner or not ship_partner:
                n_indeterminate += 1
                continue

            cohort = "switched" if dig_partner != ship_partner else "not_switched"
            tallies[cohort][row["delivery_leg"]] += 1

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["cohort", "n"] + [f"{o.lower().replace('-', '')}_n" for o in OUTCOMES]
                    + [f"{o.lower().replace('-', '')}_pct" for o in OUTCOMES])
        for cohort, label in [("switched", "Cohort 1: Courier switched"), ("not_switched", "Cohort 2: Courier not switched")]:
            n = sum(tallies[cohort].values())
            counts = [tallies[cohort][o] for o in OUTCOMES]
            wr.writerow([label, n] + counts + [pct(c, n) for c in counts])

    print(f"invoice window (3-24h) n: {n_window}")
    print(f"indeterminate (blank courier field): {n_indeterminate} ({pct(n_indeterminate, n_window)}%)")
    for cohort, label in [("switched", "Cohort 1: Courier switched"), ("not_switched", "Cohort 2: Courier not switched")]:
        n = sum(tallies[cohort].values())
        parts = ", ".join(f"{o}={tallies[cohort][o]} ({pct(tallies[cohort][o], n)}%)" for o in OUTCOMES)
        print(f"{label}: n={n} -- {parts}")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
