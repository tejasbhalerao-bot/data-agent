"""WH leg ops (v2) — TRUE processing window using pick-eligibility start.

v1 used (invoice - dr_confirm), which included WH non-working hours / queue / batch wait.
v2 uses processing_start_ts (the moment the order became eligible for picking, net of those),
so the window measures actual ops processing only.

Field 1 (promised) : digitised_wh_process_mins                          [minutes]
Field 2 (actual)   : actual_warehouse_processing - processing_start_ts  [minutes]
diff = Field1 - Field2
    Early   = diff >  +1 min   (ops faster than promised SLA)
    On-Time = -1 <= diff <= +1
    Late    = diff <  -1 min   (ops slower than promised SLA)

Scope: digitised_wh_process_mins numeric, processing_start_ts & actual_warehouse_processing non-null,
       digitised_ts >= 2026-05-08. All verticals.
Data anomaly: actual window < 0 -> excluded, counted.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "raw-data" / "early-delivery-raw-may-2026.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "outputs" / "wh-leg-ops-v2.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"
CUTOVER = date(2026, 5, 8)

BUCKETS = [
    ("Early >4h", None, -240), ("Early 2-4h", -240, -120), ("Early 1-2h", -120, -60),
    ("Early 30-60m", -60, -30), ("Early 10-30m", -30, -10), ("Early 1-10m", -10, -1),
    ("On-Time +/-1m", -1, 1),
    ("Late 1-10m", 1, 10), ("Late 10-30m", 10, 30), ("Late 30-60m", 30, 60),
    ("Late 1-2h", 60, 120), ("Late 2-4h", 120, 240), ("Late >4h", 240, None),
]
ORDER = [b[0] for b in BUCKETS]


def parse_dt(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def parse_num(raw: str) -> float | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def bucket_of(signed: float) -> str:  # signed = actual - promised (neg = early/faster)
    if -1 <= signed <= 1:
        return "On-Time +/-1m"
    for label, lo, hi in BUCKETS:
        if label == "On-Time +/-1m":
            continue
        if (lo is None or signed > lo) and (hi is None or signed <= hi):
            return label
    return "On-Time +/-1m"


def median(vals: list[float]) -> float:
    if not vals:
        return float("nan")
    vals = sorted(vals)
    n = len(vals)
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2


def main() -> None:
    seen: set[str] = set()
    n = 0
    n_missing = 0
    n_neg = 0
    eotl: dict[str, int] = defaultdict(int)
    dist: dict[str, int] = defaultdict(int)
    diffs: list[float] = []

    with open(RAW_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            oid = (row["order_id"] or "").replace(",", "").strip()
            if oid in seen:
                continue
            seen.add(oid)
            digitised = parse_dt(row["digitised_ts"])
            if digitised is None or digitised.date() < CUTOVER:
                continue
            promised = parse_num(row["digitised_wh_process_mins"])
            start = parse_dt(row["processing_start_ts"])
            end = parse_dt(row["actual_warehouse_processing"])
            if promised is None or start is None or end is None:
                n_missing += 1
                continue
            actual = (end - start).total_seconds() / 60.0
            if actual < 0:
                n_neg += 1
                continue
            n += 1
            diff = promised - actual
            signed = actual - promised
            if diff > 1:
                eotl["Early"] += 1
            elif diff < -1:
                eotl["Late"] += 1
            else:
                eotl["On-Time"] += 1
            dist[bucket_of(signed)] += 1
            diffs.append(diff)

    print(f"WH-leg ops v2 cohort = {n}   (excluded: missing={n_missing}, negative window={n_neg})\n")
    print("=== EARLY / ON-TIME / LATE (diff = promised - actual; eligible->finish) ===")
    for b in ["Early", "On-Time", "Late"]:
        print(f"  {b:8s} {eotl[b]:>9d}  {eotl[b]/n*100:5.1f}%")
    print(f"\n  median diff = {median(diffs):.1f} min   mean diff = {sum(diffs)/len(diffs):.1f} min")
    print(f"  (positive = ops faster than promised SLA)")

    print("\n=== MINUTE DISTRIBUTION ===")
    for b in ORDER:
        print(f"  {b:>16}  {dist[b]:>9d}  {dist[b]/n*100:5.1f}%")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["view", "bucket", "n", "pct"])
        for b in ["Early", "On-Time", "Late"]:
            wr.writerow(["eotl", b, eotl[b], round(eotl[b] / n * 100, 2)])
        for b in ORDER:
            wr.writerow(["minute_dist", b, dist[b], round(dist[b] / n * 100, 2)])
    print(f"\nwrote -> {OUT_PATH}")


if __name__ == "__main__":
    main()
