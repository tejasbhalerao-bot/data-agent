"""Step 1 — Top-level delivery outcome distribution.

Early / On-Time / Late / Not-Delivered, split by FC|MFC x Hyperlocal|Courier.

Locked definitions (Tejas, 2026-06-16):
- Outcome is DAY-LEVEL: compare date(delivery_attempt_time) vs date(digitised_delivery_promise).
    Early       = delivered >= 1 full day before promise date
    On-Time     = delivered on the same calendar date as promise
    Late        = delivered after the promise date
    NotDelivered= delivery_attempt_time is empty
    PromiseMissing = promise empty but order delivered (cannot classify)
- Vertical  from digitised_is_sdd : true->Hyperlocal, false->Courier, blank->Unknown
- WH type   from digitised_is_mfc : true->MFC,        false->FC,      blank->Unknown
- Grain: one row per order_id; 15 duplicate order_ids deduped keep-first.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "raw-data" / "early-delivery-raw-may-2026.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "outputs" / "step1-top-level-outcomes-v1.csv"

TS_FMT = "%b %d, %Y, %I:%M %p"  # e.g. "May 14, 2026, 6:37 AM"

OUTCOMES = ["Early", "On-Time", "Late", "Not-Delivered", "Promise-Missing"]


def parse_date(raw: str) -> datetime | None:
    """Parse the Metabase timestamp string; return None if blank/unparseable."""
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def vertical_of(raw: str) -> str:
    v = (raw or "").strip().lower()
    return {"true": "Hyperlocal", "false": "Courier"}.get(v, "Unknown")


def whtype_of(raw: str) -> str:
    v = (raw or "").strip().lower()
    return {"true": "MFC", "false": "FC"}.get(v, "Unknown")


def outcome_of(promise_raw: str, attempt_raw: str) -> str:
    """Day-level outcome classification."""
    attempt = parse_date(attempt_raw)
    if attempt is None:
        return "Not-Delivered"
    promise = parse_date(promise_raw)
    if promise is None:
        return "Promise-Missing"
    diff_days = (promise.date() - attempt.date()).days
    if diff_days >= 1:
        return "Early"
    if diff_days == 0:
        return "On-Time"
    return "Late"


def main() -> None:
    seen: set[str] = set()
    dups = 0
    total = 0
    # (vertical, whtype, outcome) -> count
    cube: Counter[tuple[str, str, str]] = Counter()

    with open(RAW_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            total += 1
            oid = (row["order_id"] or "").replace(",", "").strip()
            if oid in seen:
                dups += 1
                continue
            seen.add(oid)
            v = vertical_of(row["digitised_is_sdd"])
            w = whtype_of(row["digitised_is_mfc"])
            o = outcome_of(row["digitised_delivery_promise"], row["delivery_attempt_time"])
            cube[(v, w, o)] += 1

    n = total - dups

    # ---- write tidy long output ----
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["vertical", "wh_type", "outcome", "orders"])
        for (v, w, o), c in sorted(cube.items()):
            wr.writerow([v, w, o, c])

    # ---- console report ----
    def pct(part: int, whole: int) -> str:
        return f"{(part / whole * 100):5.1f}%" if whole else "  n/a"

    print(f"rows={total}  dups_dropped={dups}  orders={n}\n")

    overall = Counter()
    for (v, w, o), c in cube.items():
        overall[o] += c
    print("=== OVERALL OUTCOME ===")
    for o in OUTCOMES:
        print(f"  {o:16s} {overall[o]:>8d}  {pct(overall[o], n)}")

    print("\n=== BY VERTICAL (row % within vertical) ===")
    verts = ["Hyperlocal", "Courier", "Unknown"]
    print(f"  {'vertical':12s} " + " ".join(f"{o:>14s}" for o in OUTCOMES) + f" {'total':>10s}")
    for v in verts:
        vt = sum(c for (vv, _, _), c in cube.items() if vv == v)
        cells = []
        for o in OUTCOMES:
            cc = sum(c for (vv, _, oo), c in cube.items() if vv == v and oo == o)
            cells.append(f"{cc:>6d} {pct(cc, vt)}")
        print(f"  {v:12s} " + " ".join(f"{c:>14s}" for c in cells) + f" {vt:>10d}")

    print("\n=== BY WH TYPE (row % within wh_type) ===")
    whs = ["FC", "MFC", "Unknown"]
    print(f"  {'wh_type':12s} " + " ".join(f"{o:>14s}" for o in OUTCOMES) + f" {'total':>10s}")
    for w in whs:
        wt = sum(c for (_, ww, _), c in cube.items() if ww == w)
        cells = []
        for o in OUTCOMES:
            cc = sum(c for (_, ww, oo), c in cube.items() if ww == w and oo == o)
            cells.append(f"{cc:>6d} {pct(cc, wt)}")
        print(f"  {w:12s} " + " ".join(f"{c:>14s}" for c in cells) + f" {wt:>10d}")

    print("\n=== VERTICAL x WH TYPE x OUTCOME (row % within cell-segment) ===")
    print(f"  {'segment':22s} " + " ".join(f"{o:>14s}" for o in OUTCOMES) + f" {'total':>10s}")
    for v in verts:
        for w in whs:
            seg_total = sum(c for (vv, ww, _), c in cube.items() if vv == v and ww == w)
            if seg_total == 0:
                continue
            cells = []
            for o in OUTCOMES:
                cc = cube[(v, w, o)]
                cells.append(f"{cc:>6d} {pct(cc, seg_total)}")
            print(f"  {v+' x '+w:22s} " + " ".join(f"{c:>14s}" for c in cells) + f" {seg_total:>10d}")

    print(f"\nwrote -> {OUT_PATH}")


if __name__ == "__main__":
    main()
