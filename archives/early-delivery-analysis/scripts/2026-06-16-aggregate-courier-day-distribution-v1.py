"""Courier day-level offset distribution (Step 1 drill-down).

offset_days = date(delivery_attempt_time) - date(digitised_delivery_promise)
    negative = EARLY (delivered before promise)
    0        = ON-TIME
    positive = LATE

Scope: delivered (attempt not null), digitised_ts >= 2026-05-08, vertical = Courier
       (digitised_is_sdd == false).
Cuts : Courier (all) | Courier x FC (is_mfc false) | Courier x MFC (is_mfc true).

Output: per-offset counts and within-cut % for each cut.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime, date
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "raw-data" / "early-delivery-raw-may-2026.csv"
OUT_PATH = Path(__file__).resolve().parents[1] / "outputs" / "courier-day-distribution-v1.csv"

TS_FMT = "%b %d, %Y, %I:%M %p"
CUTOVER = date(2026, 5, 8)
CLAMP = 10  # display tails as <=-CLAMP-1 and >=CLAMP+1


def parse_dt(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def main() -> None:
    cuts: dict[str, Counter[int]] = {"Courier": Counter(), "Courier x FC": Counter(),
                                     "Courier x MFC": Counter()}
    seen: set[str] = set()

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
            if (row["digitised_is_sdd"] or "").strip().lower() != "false":  # Courier only
                continue

            offset = (attempt.date() - promise.date()).days
            cuts["Courier"][offset] += 1
            mfc = (row["digitised_is_mfc"] or "").strip().lower()
            if mfc == "false":
                cuts["Courier x FC"][offset] += 1
            elif mfc == "true":
                cuts["Courier x MFC"][offset] += 1

    totals = {k: sum(c.values()) for k, c in cuts.items()}
    lo = min(min(c) for c in cuts.values() if c)
    hi = max(max(c) for c in cuts.values() if c)

    def clamp(o: int) -> int:
        return max(-CLAMP - 1, min(CLAMP + 1, o))

    # collapse to clamped display bins
    disp = {k: Counter() for k in cuts}
    for k, c in cuts.items():
        for o, n in c.items():
            disp[k][clamp(o)] += n

    def lbl(b: int) -> str:
        if b == -CLAMP - 1:
            return f"<=-{CLAMP + 1}"
        if b == CLAMP + 1:
            return f">=+{CLAMP + 1}"
        return f"{b:+d}" if b != 0 else "0"

    order = list(range(-CLAMP - 1, CLAMP + 2))

    # ---- console ----
    print(f"raw offset range: {lo} .. {hi}    totals: "
          + "  ".join(f"{k}={v}" for k, v in totals.items()) + "\n")
    head = f"{'offset':>7s} | " + " | ".join(f"{k:>16s}" for k in cuts)
    print(head)
    print("-" * len(head))
    for b in order:
        cells = []
        for k in cuts:
            n = disp[k][b]
            t = totals[k]
            cells.append(f"{n:>7d} {n/t*100:5.1f}%" if t else " " * 13)
        marker = "  <-- on-time" if b == 0 else ""
        print(f"{lbl(b):>7s} | " + " | ".join(f"{c:>16s}" for c in cells) + marker)

    # summary E/OT/L + median
    print("\nsummary:")
    for k, c in cuts.items():
        t = totals[k]
        early = sum(n for o, n in c.items() if o <= -1)
        ontime = c[0]
        late = sum(n for o, n in c.items() if o >= 1)
        # median offset
        vals = sorted(o for o, n in c.items() for _ in range(n)) if t else []
        med = vals[t // 2] if t else None
        print(f"  {k:16s} n={t:>7d}  early(<=-1)={early/t*100:4.1f}%  "
              f"on-time(0)={ontime/t*100:4.1f}%  late(>=1)={late/t*100:4.1f}%  median_offset={med}")

    # ---- tidy output ----
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["offset_bin"] + [f"{k}_n" for k in cuts] + [f"{k}_pct" for k in cuts])
        for b in order:
            wr.writerow([lbl(b)]
                        + [disp[k][b] for k in cuts]
                        + [round(disp[k][b] / totals[k] * 100, 2) if totals[k] else 0 for k in cuts])
    print(f"\nwrote -> {OUT_PATH}")


if __name__ == "__main__":
    main()
