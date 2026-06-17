"""Doctor leg — MINUTE-level offset distribution, both comparisons, overall + by category.

offset_min = (event - promised_doctor_call_time) in minutes.   negative = early, positive = late.
On-Time band = within +/-1 min.
Comparison 1 (call)   : event = actual_doctor_call_time
Comparison 2 (confirm): event = doctor_confirmed_at

Scope: actual_doctor_call_time AND doctor_confirmed_at non-null, digitised_ts >= 2026-05-08. All verticals.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "raw-data" / "early-delivery-raw-may-2026.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "outputs" / "doctor-leg-minute-dist-v1.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"
CUTOVER = date(2026, 5, 8)

# ordered buckets (label, lo, hi]  in minutes; On-Time is the +/-1 band
BUCKETS = [
    ("Early >4h",     None, -240),
    ("Early 2-4h",    -240, -120),
    ("Early 1-2h",    -120, -60),
    ("Early 30-60m",  -60,  -30),
    ("Early 10-30m",  -30,  -10),
    ("Early 1-10m",   -10,  -1),
    ("On-Time +/-1m", -1,   1),
    ("Late 1-10m",    1,    10),
    ("Late 10-30m",   10,   30),
    ("Late 30-60m",   30,   60),
    ("Late 1-2h",     60,   120),
    ("Late 2-4h",     120,  240),
    ("Late >4h",      240,  None),
]
ORDER = [b[0] for b in BUCKETS]
CATS = ["DOCTOR_AND_HA_CALL_REQUIRED", "DOCTOR_CALL_REQUIRED", "HA_CALL_REQUIRED",
        "AUTO_CONFIRM", "(blank)"]


def parse_dt(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def bucket_of(o: float) -> str:
    if -1 <= o <= 1:
        return "On-Time +/-1m"
    for label, lo, hi in BUCKETS:
        if label == "On-Time +/-1m":
            continue
        lo_ok = lo is None or o > lo
        hi_ok = hi is None or o <= hi
        if lo_ok and hi_ok:
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
    overall = {"call": defaultdict(int), "confirm": defaultdict(int)}
    by_cat = {"call": defaultdict(lambda: defaultdict(int)), "confirm": defaultdict(lambda: defaultdict(int))}
    offs = {"call": [], "confirm": []}
    offs_cat = {"call": defaultdict(list), "confirm": defaultdict(list)}
    n = 0

    with open(RAW_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            oid = (row["order_id"] or "").replace(",", "").strip()
            if oid in seen:
                continue
            seen.add(oid)
            call = parse_dt(row["actual_doctor_call_time"])
            confirm = parse_dt(row["dr_confirm_ts"])
            promised = parse_dt(row["digitised_dr_promise"])
            if call is None or confirm is None or promised is None:
                continue
            digitised = parse_dt(row["digitised_ts"])
            if digitised is None or digitised.date() < CUTOVER:
                continue
            n += 1
            cat = (row["digitised_order_category"] or "").strip() or "(blank)"
            for key, event in (("call", call), ("confirm", confirm)):
                o = (event - promised).total_seconds() / 60.0
                b = bucket_of(o)
                overall[key][b] += 1
                by_cat[key][cat][b] += 1
                offs[key].append(o)
                offs_cat[key][cat].append(o)

    def show_overall() -> None:
        print(f"cohort = {n}\n")
        print(f"{'bucket':>16} | {'CALL n':>9} {'CALL %':>7} | {'CONFIRM n':>10} {'CONFIRM %':>9}")
        for b in ORDER:
            cn, fn = overall["call"][b], overall["confirm"][b]
            print(f"{b:>16} | {cn:>9d} {cn/n*100:6.1f}% | {fn:>10d} {fn/n*100:8.1f}%")
        for key in ("call", "confirm"):
            v = offs[key]
            print(f"  {key:8s} median={median(v):7.1f} min  mean={sum(v)/len(v):7.1f} min")

    def show_cat(key: str) -> None:
        label = "promised vs actual call" if key == "call" else "promised vs confirmation"
        cats = [c for c in CATS if c in by_cat[key]]
        print(f"\n=== BY CATEGORY ({label}) — % within category ===")
        print(f"{'bucket':>16} | " + " | ".join(f"{c[:14]:>14}" for c in cats))
        tot = {c: sum(by_cat[key][c].values()) for c in cats}
        for b in ORDER:
            cells = [f"{by_cat[key][c][b]/tot[c]*100:5.1f}%" if tot[c] else "  -  " for c in cats]
            print(f"{b:>16} | " + " | ".join(f"{x:>14}" for x in cells))
        print(f"{'median min':>16} | " + " | ".join(f"{median(offs_cat[key][c]):>14.1f}" for c in cats))
        print(f"{'n':>16} | " + " | ".join(f"{tot[c]:>14d}" for c in cats))

    show_overall()
    show_cat("call")
    show_cat("confirm")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["comparison", "scope", "bucket", "n", "pct_within_scope"])
        for key in ("call", "confirm"):
            for b in ORDER:
                wr.writerow([key, "ALL", b, overall[key][b], round(overall[key][b] / n * 100, 2)])
            for c in by_cat[key]:
                tot = sum(by_cat[key][c].values())
                for b in ORDER:
                    wr.writerow([key, c, b, by_cat[key][c][b],
                                 round(by_cat[key][c][b] / tot * 100, 2) if tot else 0])
    print(f"\nwrote -> {OUT_PATH}")


if __name__ == "__main__":
    main()
