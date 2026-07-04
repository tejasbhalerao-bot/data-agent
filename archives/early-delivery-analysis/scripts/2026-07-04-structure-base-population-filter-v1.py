"""Locks base population for early-delivery-analysis: digitised_ts > 8 May 2026 AND delivery_attempt_time not null."""

import csv
from datetime import datetime
from pathlib import Path

RAW_PATH = Path(__file__).parents[1] / "raw-data" / "early-delivery-raw-may-2026.csv"
OUTPUT_PATH = Path(__file__).parents[1] / "outputs" / "base-population.csv"
CUTOFF = datetime(2026, 5, 8)
TS_FORMAT = "%b %d, %Y, %I:%M %p"


def passes_filters(row: dict[str, str]) -> bool:
    digitised_ts = row["digitised_ts"].strip()
    delivery_attempt_time = row["delivery_attempt_time"].strip()
    if not digitised_ts or not delivery_attempt_time:
        return False
    return datetime.strptime(digitised_ts, TS_FORMAT) > CUTOFF


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    kept = 0
    with RAW_PATH.open(newline="") as infile, OUTPUT_PATH.open("w", newline="") as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            total += 1
            if passes_filters(row):
                kept += 1
                writer.writerow(row)

    print(f"total rows: {total}")
    print(f"base population rows: {kept} ({kept / total:.1%})")
    print(f"written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
