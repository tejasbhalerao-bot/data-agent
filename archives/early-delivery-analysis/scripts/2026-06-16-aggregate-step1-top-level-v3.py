"""Step 1 (v3) — Top-level delivery outcome distribution.

Scope (locked 2026-06-16):
    - delivery_attempt_time IS NOT NULL  (delivered only)
    - digitised_ts >= 2026-05-08         (post instrumentation go-live; pre-May-8 lacks
                                          digitised SDD/MFC state -> 24% blind spot removed)

Outcomes (day-level): Early / On-Time / Late.
    Early   = delivered >= 1 full day before promise date
    On-Time = delivered on the same calendar date as promise
    Late    = delivered after the promise date

Cuts (each row reports n = orders under consideration):
    - All delivered
    - Vertical alone : Hyperlocal / Courier / Unknown   (digitised_is_sdd true/false/blank)
    - WH type alone  : FC / MFC / Unknown               (digitised_is_mfc false/true/blank)
    - Vertical x WH type

Hyperlocal = SDD construct (canonical); NOT necessarily same-day.
Every dropped order is counted by reason and reported as a funnel.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime, date
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "raw-data" / "early-delivery-raw-may-2026.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "outputs" / "step1-top-level-outcomes-v3.csv"

TS_FMT = "%b %d, %Y, %I:%M %p"  # e.g. "May 14, 2026, 6:37 AM"
CUTOVER = date(2026, 5, 8)
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
    n_not_delivered = 0
    n_attempt_unparseable = 0
    n_promise_blank = 0
    n_promise_unparseable = 0
    n_pre_cutover = 0            # digitised_ts < May 8 or unparseable -> out of scope

    seen: set[str] = set()
    cube: Counter[tuple[str, str, str]] = Counter()

    with open(RAW_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            n_rows += 1
            oid = (row["order_id"] or "").replace(",", "").strip()
            if oid in seen:
                n_dups += 1
                continue
            seen.add(oid)

            attempt = parse_dt(row["delivery_attempt_time"])
            if (row["delivery_attempt_time"] or "").strip() == "":
                n_not_delivered += 1
                continue
            if attempt is None:
                n_attempt_unparseable += 1
                continue

            digitised = parse_dt(row["digitised_ts"])
            if digitised is None or digitised.date() < CUTOVER:
                n_pre_cutover += 1
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

    print("=== FUNNEL (orders dropped, with reason) ===")
    print(f"  raw rows                          {n_rows:>8d}")
    print(f"  - duplicate order_id              {n_dups:>8d}")
    print(f"  - not delivered (attempt NULL)    {n_not_delivered:>8d}   [scope]")
    print(f"  - attempt unparseable             {n_attempt_unparseable:>8d}   [data issue]")
    print(f"  - digitised < May 8 (pre go-live) {n_pre_cutover:>8d}   [scope]")
    print(f"  - promise blank                   {n_promise_blank:>8d}   [data issue]")
    print(f"  - promise unparseable             {n_promise_unparseable:>8d}   [data issue]")
    print(f"  = ANALYSIS SET                    {n_analysis:>8d}")
    seg_unknown = sum(c for (v, w, _), c in cube.items() if v == "Unknown" or w == "Unknown")
    print(f"  (residual unsegmentable [blank flags post-cutover]: {seg_unknown}  "
          f"{seg_unknown / n_analysis * 100:.2f}%)\n")

    def cells(pred):
        by = {o: sum(c for (v, w, o2), c in cube.items() if o2 == o and pred(v, w)) for o in OUTCOMES}
        return sum(by.values()), by

    out_rows: list[list] = []

    def line(label: str, pred) -> None:
        n, by = cells(pred)
        if n == 0:
            return
        txt = "  ".join(f"{o[:4]} {by[o]:>6d} {by[o]/n*100:5.1f}%" for o in OUTCOMES)
        print(f"  {label:24s} n={n:>7d}   {txt}")
        out_rows.append([label, n] + [by[o] for o in OUTCOMES]
                        + [round(by[o] / n * 100, 1) for o in OUTCOMES])

    print("=== ALL DELIVERED (post May 8) ===")
    line("All delivered", lambda v, w: True)
    print("\n=== BY VERTICAL ===")
    for v in ["Hyperlocal", "Courier", "Unknown"]:
        line(v, lambda vv, ww, v=v: vv == v)
    print("\n=== BY WH TYPE ===")
    for w in ["FC", "MFC", "Unknown"]:
        line(w, lambda vv, ww, w=w: ww == w)
    print("\n=== VERTICAL x WH TYPE ===")
    for v in ["Hyperlocal", "Courier", "Unknown"]:
        for w in ["FC", "MFC", "Unknown"]:
            line(f"{v} x {w}", lambda vv, ww, v=v, w=w: vv == v and ww == w)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["segment", "orders", "early_n", "ontime_n", "late_n",
                     "early_pct", "ontime_pct", "late_pct"])
        wr.writerows(out_rows)
    print(f"\nwrote -> {OUT_PATH}")


if __name__ == "__main__":
    main()
