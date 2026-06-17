"""Courier early/on-time/late distribution by delivery partner at digitisation.

Metric (day-level): offset = date(delivery_attempt_time) - date(digitised_delivery_promise)
    <= -1 Early | 0 On-Time | >= +1 Late
Scope: delivered (attempt not null), digitised_ts >= 2026-05-08, Courier (digitised_is_sdd == false).
Group: digitised_delivery_partner (raw SVM id; not name-decoded here).
Output: per partner n, early/ontime/late counts + %, and % of all courier early.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "raw-data" / "early-delivery-raw-may-2026.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "outputs" / "courier-partner-distribution-v1.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"
CUTOVER = date(2026, 5, 8)


def parse_dt(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def main() -> None:
    part: dict[str, dict[str, int]] = defaultdict(lambda: {"early": 0, "ontime": 0, "late": 0})
    seen: set[str] = set()
    total = 0
    total_early = 0

    with open(RAW_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            oid = (row["order_id"] or "").replace(",", "").strip()
            if oid in seen:
                continue
            seen.add(oid)
            attempt = parse_dt(row["delivery_attempt_time"])
            if attempt is None:
                continue
            digitised = parse_dt(row["digitised_ts"])
            if digitised is None or digitised.date() < CUTOVER:
                continue
            promise = parse_dt(row["digitised_delivery_promise"])
            if promise is None:
                continue
            if (row["digitised_is_sdd"] or "").strip().lower() != "false":  # courier only
                continue

            p = (row["digitised_delivery_partner"] or "").strip() or "(blank)"
            offset = (attempt.date() - promise.date()).days
            bucket = "early" if offset <= -1 else "ontime" if offset == 0 else "late"
            part[p][bucket] += 1
            total += 1
            if offset <= -1:
                total_early += 1

    rows = []
    for p, d in part.items():
        n = d["early"] + d["ontime"] + d["late"]
        rows.append((p, n, d["early"], d["ontime"], d["late"]))
    rows.sort(key=lambda r: -r[2])  # by early count

    print(f"courier total={total}  total_early={total_early}  partners={len(rows)}\n")
    hd = f"{'partner':>8} {'n':>8} {'early_n':>8} {'early%':>7} {'ontime%':>8} {'late%':>6} {'%ofAllEarly':>11}"
    print(hd)
    for p, n, e, o, l in rows:
        print(f"{p:>8} {n:>8d} {e:>8d} {e/n*100:6.1f}% {o/n*100:7.1f}% {l/n*100:5.1f}% {e/total_early*100:10.1f}%")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["partner_id", "n", "early_n", "ontime_n", "late_n",
                     "early_pct", "ontime_pct", "late_pct", "pct_of_all_courier_early"])
        for p, n, e, o, l in rows:
            wr.writerow([p, n, e, o, l, round(e / n * 100, 1), round(o / n * 100, 1),
                         round(l / n * 100, 1), round(e / total_early * 100, 1)])
    print(f"\nwrote -> {OUT_PATH}")


if __name__ == "__main__":
    main()
