"""Dominant courier switch pairs (digitised_delivery_partner -> shipping_delivery_partner)
within row 4 (courier switched AND promise changed, n=38,598) of
courier-switch-promise-funnel-v2.csv.

For each pair, also reports its Late rate against the digitised promise (reusing
View 2's already-validated delivery_leg) and against the shipping promise, so the
pair breakdown connects directly to the performance-gap story already established.

Emits outputs/row4-courier-switch-pairs.csv: one row per (from, to) pair, sorted by
n descending, with n, % of row4, and both Late rates.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "row4-courier-switch-pairs.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"

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


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


def pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def main() -> None:
    v2_rows: dict[str, dict[str, str]] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    pair_counts: dict[tuple[str, str], int] = defaultdict(int)
    pair_late_digitised: dict[tuple[str, str], int] = defaultdict(int)
    pair_late_shipping: dict[tuple[str, str], int] = defaultdict(int)
    n_row4 = 0

    with V1_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            oid = row["order_id"]
            r2 = v2_rows.get(oid)
            if r2 is None:
                continue
            triple = (row["dispatch_leg"], row["delivery_leg"], r2["delivery_leg"])
            if triple not in TARGET_COHORTS:
                continue

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            if not dig_partner or not ship_partner or dig_partner == ship_partner:
                continue

            dispatch_promise = parse_date(row["digitised_dispatch_promise"])
            delivery_promise = parse_date(row["digitised_delivery_promise"])
            pickup = parse_date(row["pickup_time"])
            delivery_attempt = parse_date(row["delivery_attempt_time"])
            ship_promise_raw = row["shipping_delivery_promise"].strip()
            if dispatch_promise is None or delivery_promise is None or not ship_promise_raw:
                continue

            digitised_promise_days = (delivery_promise - dispatch_promise).days
            shipping_promise_days = int(ship_promise_raw)
            if shipping_promise_days == digitised_promise_days:
                continue  # not row 4 -- promise unchanged

            n_row4 += 1
            pair = (dig_partner, ship_partner)
            pair_counts[pair] += 1

            actual_days = (delivery_attempt - pickup).days
            if actual_days - digitised_promise_days > 0:
                pair_late_digitised[pair] += 1
            if actual_days - shipping_promise_days > 0:
                pair_late_shipping[pair] += 1

    ranked_pairs = sorted(pair_counts, key=lambda p: -pair_counts[p])

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["from_courier", "to_courier", "n", "pct_of_row4",
                     "late_vs_digitised_promise_pct", "late_vs_shipping_promise_pct"])
        for pair in ranked_pairs:
            n = pair_counts[pair]
            wr.writerow([
                pair[0], pair[1], n, pct(n, n_row4),
                pct(pair_late_digitised[pair], n), pct(pair_late_shipping[pair], n),
            ])

    print(f"row4 n (courier switched AND promise changed): {n_row4}")
    print(f"distinct courier pairs: {len(ranked_pairs)}")
    print("top 10 pairs:")
    for pair in ranked_pairs[:10]:
        n = pair_counts[pair]
        print(f"  {pair[0]} -> {pair[1]}: n={n} ({pct(n, n_row4)}%), "
              f"late_vs_digitised={pct(pair_late_digitised[pair], n)}%, "
              f"late_vs_shipping={pct(pair_late_shipping[pair], n)}%")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
