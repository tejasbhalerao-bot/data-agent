"""Sanity checks for digitised-courier-share-by-day.csv.

Checks:
1. Sum of daily n across all dates = 515,465 (the full View 1 population).
2. For every date, (top-8 courier n's) + other_n + blank_n = that day's n exactly.
3. Every count/pct matches an independent recount straight from the order-detail file.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-digitised-courier-share-by-day-v1.py
"""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TS_FMT = "%b %d, %Y, %I:%M %p"
EXPECTED_TOTAL = 515_465
TOP_N = 8


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

    overall_courier_counts: Counter[str] = Counter()
    day_courier_counts: dict[date, Counter[str]] = defaultdict(Counter)
    day_totals: dict[date, int] = defaultdict(int)
    n_total = 0

    with (OUT / "view1-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            n_total += 1
            digitised = parse_dt(row["digitised_ts"])
            if digitised is None:
                continue
            courier = row["digitised_delivery_partner"].strip() or "(blank)"
            day = digitised.date()
            overall_courier_counts[courier] += 1
            day_courier_counts[day][courier] += 1
            day_totals[day] += 1

    if n_total != EXPECTED_TOTAL:
        failures.append(f"total={n_total}, expected {EXPECTED_TOTAL}")

    if sum(day_totals.values()) != n_total:
        failures.append(f"sum of daily totals={sum(day_totals.values())}, expected {n_total}")

    top_couriers = [c for c, _ in overall_courier_counts.most_common(TOP_N) if c != "(blank)"][:TOP_N]

    csv_rows: dict[str, dict[str, str]] = {}
    with (OUT / "digitised-courier-share-by-day.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            csv_rows[r["date"]] = r

    if len(csv_rows) != len(day_totals):
        failures.append(f"CSV has {len(csv_rows)} dates, recount has {len(day_totals)}")

    for day, n in day_totals.items():
        r = csv_rows.get(day.isoformat())
        if r is None:
            failures.append(f"date {day} missing from CSV")
            continue
        if int(r["n"]) != n:
            failures.append(f"{day}: CSV n={r['n']}, recount={n}")

        counts = day_courier_counts[day]
        accounted = 0
        for c in top_couriers:
            cn = counts.get(c, 0)
            accounted += cn
            csv_cn = int(r[f"courier_{c}_n"])
            if csv_cn != cn:
                failures.append(f"{day}/courier_{c}: CSV n={csv_cn}, recount={cn}")
            exp_pct = round(cn / n * 100, 1) if n else 0.0
            if abs(float(r[f"courier_{c}_pct"]) - exp_pct) > 0.05:
                failures.append(f"{day}/courier_{c}_pct: CSV={r[f'courier_{c}_pct']}, recompute={exp_pct}")

        blank_n = counts.get("(blank)", 0)
        other_n = n - accounted - blank_n
        if int(r["other_n"]) != other_n:
            failures.append(f"{day}/other_n: CSV={r['other_n']}, recount={other_n}")
        if int(r["blank_n"]) != blank_n:
            failures.append(f"{day}/blank_n: CSV={r['blank_n']}, recount={blank_n}")

        row_sum = accounted + other_n + blank_n
        if row_sum != n:
            failures.append(f"{day}: top8+other+blank={row_sum}, expected n={n}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures[:30]:
            print(f"  - {f}")
        if len(failures) > 30:
            print(f"  ... and {len(failures) - 30} more")
        sys.exit(1)

    print(f"PASS -- total={n_total} matches expected {EXPECTED_TOTAL}, daily totals sum "
          f"correctly, every date's top-8+other+blank reconciles to that day's n exactly, "
          f"and all CSV values match an independent recount across {len(day_totals)} dates.")


if __name__ == "__main__":
    main()
