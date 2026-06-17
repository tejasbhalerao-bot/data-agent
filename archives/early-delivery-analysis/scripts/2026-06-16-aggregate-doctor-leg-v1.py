"""Doctor leg — Early / On-Time / Late, two comparisons + breakdown by order category.

Band: exact sign with +/-1 min buffer.
    offset = actual_event - promised_doctor_call_time   (minutes)
    Early   = offset <  -1 min   (event earlier than promise)
    On-Time = -1 min <= offset <= +1 min
    Late    = offset >  +1 min

Comparison 1 (OPS)         : promised_doctor_call_time vs actual_doctor_call_time
Comparison 2 (CONFIRMATION): promised_doctor_call_time vs doctor_confirmed_at

Scope: orders where actual_doctor_call_time AND doctor_confirmed_at are both non-null,
       AND digitised_ts >= 2026-05-08 (post instrumentation go-live). All verticals.
Null promised_doctor_call_time -> N/A bucket (reported, not classified).
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "raw-data" / "early-delivery-raw-may-2026.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "outputs" / "doctor-leg-v1.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"
CUTOVER = date(2026, 5, 8)
BUFFER_S = 60  # +/-1 minute


def parse_dt(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def classify(promised: datetime | None, event: datetime | None) -> str:
    if promised is None or event is None:
        return "N/A"
    diff = (event - promised).total_seconds()
    if diff < -BUFFER_S:
        return "Early"
    if diff > BUFFER_S:
        return "Late"
    return "On-Time"


def main() -> None:
    seen: set[str] = set()
    cohort = 0
    overall = {"ops": defaultdict(int), "conf": defaultdict(int)}
    by_cat = {"ops": defaultdict(lambda: defaultdict(int)), "conf": defaultdict(lambda: defaultdict(int))}
    wait_secs: list[float] = []

    with open(RAW_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            oid = (row["order_id"] or "").replace(",", "").strip()
            if oid in seen:
                continue
            seen.add(oid)
            call = parse_dt(row["actual_doctor_call_time"])
            confirm = parse_dt(row["dr_confirm_ts"])
            if call is None or confirm is None:  # scope: both actuals must be present
                continue
            digitised = parse_dt(row["digitised_ts"])
            if digitised is None or digitised.date() < CUTOVER:  # post May-8 only
                continue
            cohort += 1

            promised = parse_dt(row["digitised_dr_promise"])
            cat = (row["digitised_order_category"] or "").strip() or "(blank)"

            ops = classify(promised, call)
            conf = classify(promised, confirm)
            overall["ops"][ops] += 1
            overall["conf"][conf] += 1
            by_cat["ops"][cat][ops] += 1
            by_cat["conf"][cat][conf] += 1
            wait_secs.append((confirm - call).total_seconds())

    BK = ["Early", "On-Time", "Late", "N/A"]

    def pctline(label: str, d: dict[str, int]) -> None:
        n = sum(d.values())
        cls = n - d["N/A"]  # classifiable
        parts = []
        for b in ["Early", "On-Time", "Late"]:
            parts.append(f"{b} {d[b]:>7d} {d[b]/cls*100:5.1f}%" if cls else f"{b} 0")
        print(f"  {label:28s} n={n:>7d}  classifiable={cls:>7d}  " + "  ".join(parts)
              + f"   N/A={d['N/A']} ({d['N/A']/n*100:.1f}%)")

    print(f"cohort (call & confirm present, digitised >= May 8) = {cohort}\n")
    print("=== OVERALL (% of classifiable) ===")
    pctline("1. promised vs actual call", overall["ops"])
    pctline("2. promised vs confirmation", overall["conf"])

    if wait_secs:
        wait_secs.sort()
        med = wait_secs[len(wait_secs) // 2] / 60
        mean = sum(wait_secs) / len(wait_secs) / 60
        print(f"\ncustomer wait (confirm - call): median={med:.0f} min  mean={mean:.0f} min  n={len(wait_secs)}")

    cats = ["DOCTOR_AND_HA_CALL_REQUIRED", "DOCTOR_CALL_REQUIRED", "HA_CALL_REQUIRED",
            "AUTO_CONFIRM", "(blank)"]
    out_rows = []
    for comp, key in [("ops", "1 promised-vs-call"), ("conf", "2 promised-vs-confirm")]:
        print(f"\n=== BY ORDER CATEGORY — {key} (% of classifiable) ===")
        seen_cats = list(by_cat[comp].keys())
        ordered = [c for c in cats if c in seen_cats] + [c for c in seen_cats if c not in cats]
        for c in ordered:
            d = by_cat[comp][c]
            n = sum(d.values())
            cls = n - d["N/A"]
            e = d["Early"] / cls * 100 if cls else 0
            o = d["On-Time"] / cls * 100 if cls else 0
            l = d["Late"] / cls * 100 if cls else 0
            print(f"  {c:30s} n={n:>7d} cls={cls:>7d}  "
                  f"E {d['Early']:>6d} {e:4.1f}%  OT {d['On-Time']:>6d} {o:4.1f}%  "
                  f"L {d['Late']:>6d} {l:4.1f}%  N/A {d['N/A']:>6d}")
            out_rows.append([key, c, n, cls, d["Early"], d["On-Time"], d["Late"], d["N/A"],
                             round(e, 1), round(o, 1), round(l, 1)])

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["comparison", "order_category", "n", "classifiable",
                     "early_n", "ontime_n", "late_n", "na_n",
                     "early_pct", "ontime_pct", "late_pct"])
        wr.writerows(out_rows)
    print(f"\nwrote -> {OUT_PATH}")


if __name__ == "__main__":
    main()
