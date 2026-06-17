"""Step 1 (v2) — Top-level delivery outcome distribution, DELIVERED orders only.

Scope: delivery_attempt_time IS NOT NULL only.
Outcomes (day-level): Early / On-Time / Late.
    Early   = delivered >= 1 full day before promise date
    On-Time = delivered on the same calendar date as promise
    Late    = delivered after the promise date

Cuts (each row reports n = orders under consideration):
    - All delivered
    - Vertical alone : Hyperlocal / Courier / Unknown   (digitised_is_sdd true/false/blank)
    - WH type alone  : FC / MFC / Unknown               (digitised_is_mfc false/true/blank)
    - Vertical x WH type

Hyperlocal = SDD construct (canonical); NOT necessarily same-day. Multi-day SDD promise is valid.

Data-issue accounting: every dropped order is counted by reason and reported as a funnel.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "raw-data" / "early-delivery-raw-may-2026.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "outputs" / "step1-top-level-outcomes-v2.csv"

TS_FMT = "%b %d, %Y, %I:%M %p"  # e.g. "May 14, 2026, 6:37 AM"
OUTCOMES = ["Early", "On-Time", "Late"]


def parse_dt(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def vertical_of(raw: str) -> str:
    return {"true": "Hyperlocal", "false": "Courier"}.get((raw or "").strip().lower(), "Unknown")


def whtype_of(raw: str) -> str:
    return {"true": "MFC", "false": "FC"}.get((raw or "").strip().lower(), "Unknown")


def main() -> None:
    n_rows = 0
    n_dups = 0
    n_not_delivered = 0          # attempt blank -> out of scope
    n_attempt_unparseable = 0    # attempt present but unparseable -> dropped
    n_promise_blank = 0          # delivered but promise empty -> can't classify -> dropped
    n_promise_unparseable = 0    # delivered but promise unparseable -> dropped

    seen: set[str] = set()
    cube: Counter[tuple[str, str, str]] = Counter()  # (vertical, whtype, outcome)

    with open(RAW_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            n_rows += 1
            oid = (row["order_id"] or "").replace(",", "").strip()
            if oid in seen:
                n_dups += 1
                continue
            seen.add(oid)

            attempt_raw = (row["delivery_attempt_time"] or "").strip()
            if not attempt_raw:
                n_not_delivered += 1
                continue
            attempt = parse_dt(attempt_raw)
            if attempt is None:
                n_attempt_unparseable += 1
                continue

            promise_raw = (row["digitised_delivery_promise"] or "").strip()
            if not promise_raw:
                n_promise_blank += 1
                continue
            promise = parse_dt(promise_raw)
            if promise is None:
                n_promise_unparseable += 1
                continue

            diff = (promise.date() - attempt.date()).days
            outcome = "Early" if diff >= 1 else "On-Time" if diff == 0 else "Late"
            cube[(vertical_of(row["digitised_is_sdd"]), whtype_of(row["digitised_is_mfc"]), outcome)] += 1

    n_analysis = sum(cube.values())

    # ---------- data-issue funnel ----------
    print("=== FUNNEL (orders dropped, with reason) ===")
    print(f"  raw rows                         {n_rows:>8d}")
    print(f"  - duplicate order_id             {n_dups:>8d}")
    print(f"  = unique orders                  {n_rows - n_dups:>8d}")
    print(f"  - not delivered (attempt NULL)   {n_not_delivered:>8d}   [scope filter]")
    print(f"  - delivered, attempt unparseable {n_attempt_unparseable:>8d}   [DATA ISSUE]")
    print(f"  - delivered, promise blank       {n_promise_blank:>8d}   [DATA ISSUE]")
    print(f"  - delivered, promise unparseable {n_promise_unparseable:>8d}   [DATA ISSUE]")
    print(f"  = ANALYSIS SET                   {n_analysis:>8d}")
    seg_unknown = sum(c for (v, w, _), c in cube.items() if v == "Unknown" or w == "Unknown")
    print(f"  (within analysis set, UNsegmentable [blank digitised flags]: {seg_unknown}  "
          f"{seg_unknown / n_analysis * 100:.1f}%)\n")

    # ---------- report + tidy output ----------
    def cells(pred) -> tuple[int, dict[str, int]]:
        by = {o: sum(c for (v, w, o2), c in cube.items() if o2 == o and pred(v, w)) for o in OUTCOMES}
        return sum(by.values()), by

    def line(label: str, pred) -> list:
        n, by = cells(pred)
        if n == 0:
            return []
        txt = "  ".join(f"{o[:4]} {by[o]:>6d} {by[o]/n*100:5.1f}%" for o in OUTCOMES)
        print(f"  {label:24s} n={n:>7d}   {txt}")
        return [label, n] + [by[o] for o in OUTCOMES] + [round(by[o] / n * 100, 1) for o in OUTCOMES]

    out_rows: list[list] = []

    print("=== ALL DELIVERED ===")
    out_rows.append(line("All delivered", lambda v, w: True))

    print("\n=== BY VERTICAL (no WH cut) ===")
    for v in ["Hyperlocal", "Courier", "Unknown"]:
        r = line(v, lambda vv, ww, v=v: vv == v)
        if r:
            out_rows.append(r)

    print("\n=== BY WH TYPE (no vertical cut) ===")
    for w in ["FC", "MFC", "Unknown"]:
        r = line(w, lambda vv, ww, w=w: ww == w)
        if r:
            out_rows.append(r)

    print("\n=== VERTICAL x WH TYPE ===")
    for v in ["Hyperlocal", "Courier", "Unknown"]:
        for w in ["FC", "MFC", "Unknown"]:
            r = line(f"{v} x {w}", lambda vv, ww, v=v, w=w: vv == v and ww == w)
            if r:
                out_rows.append(r)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["segment", "orders", "early_n", "ontime_n", "late_n",
                     "early_pct", "ontime_pct", "late_pct"])
        wr.writerows(out_rows)
    print(f"\nwrote -> {OUT_PATH}")


if __name__ == "__main__":
    main()
