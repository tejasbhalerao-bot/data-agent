"""Day-over-day courier allocation share at digitisation, across ALL 515,465 View 1
orders, aggregated nationally (all geographies combined). Aggregating across every
pincode on a given day removes geography as a confound: if a courier's share still
moves day-to-day at this national level, that movement isn't explained by "today we
happened to get more orders from that courier's strongest city" -- it reflects a
real shift in courier standing/availability at the point of digitisation.

Supports the "Why Now?" case for reallocation: if the courier judged best at
digitisation keeps shifting day-to-day, holding a single courier fixed for up to
24 hours (through Payment Pending) means the original pick can already be stale by
the time the order actually ships.

Courier = digitised_delivery_partner. Top 8 couriers by overall volume are broken
out individually; the rest are grouped into "Other", and blank values into "(blank)".

Emits outputs/digitised-courier-share-by-day.csv: one row per calendar date
(digitised_ts.date()), with n and % share for each of the top 8 couriers + Other + blank.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
OUT_PATH = ROOT / "outputs" / "digitised-courier-share-by-day.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"
TOP_N = 8


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
    overall_courier_counts: Counter[str] = Counter()
    day_courier_counts: dict[date, Counter[str]] = defaultdict(Counter)
    day_totals: dict[date, int] = defaultdict(int)
    n_total = 0
    n_unparseable_date = 0

    with V1_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            n_total += 1
            digitised = parse_dt(row["digitised_ts"])
            if digitised is None:
                n_unparseable_date += 1
                continue

            courier = row["digitised_delivery_partner"].strip() or "(blank)"
            day = digitised.date()

            overall_courier_counts[courier] += 1
            day_courier_counts[day][courier] += 1
            day_totals[day] += 1

    top_couriers = [c for c, _ in overall_courier_counts.most_common(TOP_N) if c != "(blank)"]
    top_couriers = top_couriers[:TOP_N]

    with OUT_PATH.open("w", newline="") as f:
        wr = csv.writer(f)
        header = ["date", "n"]
        for c in top_couriers:
            header += [f"courier_{c}_n", f"courier_{c}_pct"]
        header += ["other_n", "other_pct", "blank_n", "blank_pct"]
        wr.writerow(header)

        for day in sorted(day_totals):
            n = day_totals[day]
            counts = day_courier_counts[day]
            row_out = [day.isoformat(), n]
            accounted = 0
            for c in top_couriers:
                cn = counts.get(c, 0)
                accounted += cn
                row_out += [cn, pct(cn, n)]
            blank_n = counts.get("(blank)", 0)
            other_n = n - accounted - blank_n
            row_out += [other_n, pct(other_n, n), blank_n, pct(blank_n, n)]
            wr.writerow(row_out)

    print(f"n_total: {n_total}, unparseable digitised_ts: {n_unparseable_date}")
    print(f"distinct dates: {len(day_totals)}")
    print(f"top {TOP_N} couriers by overall volume: {top_couriers}")
    print(f"wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
