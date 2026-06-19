"""WH Axis 1 — Is WH ops accurate?

Field 1 (promised) : digitised_wh_process_mins                       [minutes]
Field 2 (actual)   : invoice_create_ts - processing_start_ts         [minutes]
diff = Field1 - Field2
    Early   = diff >  +1 min   (ops faster than promised SLA)
    On-Time = -1 <= diff <= +1
    Late    = diff <  -1 min   (ops slower than promised SLA)

Outputs: overall E/OT/L + minute-bucket distribution, then breakdown by
    - warehouse (with working hours from context/warehouse-working-hours.csv)
    - inventory state at digitisation (digitised_is_inventory)
    - inventory change digitisation -> shipping (digitised_is_inventory vs shipping_is_inventory)
    - WH type FC vs MFC (digitised_is_mfc)

Scope: digitised_wh_process_mins numeric, processing_start_ts & invoice_create_ts non-null,
       digitised_ts >= 2026-05-08. All verticals.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "raw-data" / "early-delivery-raw-may-2026.csv"
HOURS_PATH = ROOT / "context" / "warehouse-working-hours.csv"
OUT_PATH = ROOT / "outputs" / "wh-axis1-ops-accuracy-v1.csv"
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


def bucket_of(signed: float) -> str:  # signed = actual - promised (neg = early)
    if -1 <= signed <= 1:
        return "On-Time +/-1m"
    for label, lo, hi in BUCKETS:
        if label == "On-Time +/-1m":
            continue
        if (lo is None or signed > lo) and (hi is None or signed <= hi):
            return label
    return "On-Time +/-1m"


def load_hours() -> dict[str, str]:
    h: dict[str, str] = {}
    with open(HOURS_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            ws, we = (row["work_start"] or "").strip(), (row["work_end"] or "").strip()
            h[row["id"].strip()] = f"{ws}-{we}" if ws and we else "(no hours)"
    return h


def tern(raw: str) -> bool | None:
    v = (raw or "").strip().lower()
    if v in ("true", "1"):
        return True
    if v in ("false", "0"):
        return False
    return None


def inv_change(d: str, s: str) -> str:
    di, si = tern(d), tern(s)
    if di is None or si is None:
        return "unknown"
    if di and si:
        return "inv -> inv"
    if not di and not si:
        return "non -> non"
    if di and not si:
        return "inv -> non-inv"
    return "non-inv -> inv"


class Cell:
    __slots__ = ("e", "o", "l")

    def __init__(self) -> None:
        self.e = self.o = self.l = 0

    def add(self, k: str) -> None:
        setattr(self, k, getattr(self, k) + 1)

    @property
    def n(self) -> int:
        return self.e + self.o + self.l


def main() -> None:
    hours = load_hours()
    seen: set[str] = set()
    n = 0
    n_missing = 0
    n_neg = 0
    eotl = Cell()
    dist: dict[str, int] = defaultdict(int)
    by_wh: dict[str, Cell] = defaultdict(Cell)
    by_inv: dict[str, Cell] = defaultdict(Cell)
    by_chg: dict[str, Cell] = defaultdict(Cell)
    by_type: dict[str, Cell] = defaultdict(Cell)
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
            invoice = parse_dt(row["invoice_create_ts"])
            if promised is None or start is None or invoice is None:
                n_missing += 1
                continue
            actual = (invoice - start).total_seconds() / 60.0
            if actual < 0:
                n_neg += 1
                continue
            n += 1
            diff = promised - actual
            k = "e" if diff > 1 else "l" if diff < -1 else "o"
            eotl.add(k)
            dist[bucket_of(actual - promised)] += 1
            diffs.append(diff)
            by_wh[(row["digitised_wh_id"] or "").strip() or "(blank)"].add(k)
            di = tern(row["digitised_is_inventory"])
            by_inv["inventory" if di else "non-inventory" if di is False else "unknown"].add(k)
            by_chg[inv_change(row["digitised_is_inventory"], row["shipping_is_inventory"])].add(k)
            mfc = tern(row["digitised_is_mfc"])
            by_type["MFC" if mfc else "FC" if mfc is False else "Unknown"].add(k)

    diffs.sort()
    med = diffs[len(diffs) // 2]
    print(f"AXIS 1 — Is WH ops accurate?  cohort = {n}   "
          f"(excluded: missing={n_missing}, negative window={n_neg})\n")
    print("=== OVERALL E/OT/L (diff = promised - actual; eligible -> invoice) ===")
    print(f"  Early   {eotl.e:>9d}  {eotl.e/n*100:5.1f}%")
    print(f"  On-Time {eotl.o:>9d}  {eotl.o/n*100:5.1f}%")
    print(f"  Late    {eotl.l:>9d}  {eotl.l/n*100:5.1f}%")
    print(f"  median diff = {med:.1f} min  mean = {sum(diffs)/len(diffs):.1f} min  "
          f"(positive = faster than promised)\n")

    print("=== TIME-BUCKET DISTRIBUTION ===")
    for b in ORDER:
        print(f"  {b:>16}  {dist[b]:>9d}  {dist[b]/n*100:5.1f}%")

    def show(title: str, d: dict[str, Cell], keys=None, wh_hours=False) -> None:
        print(f"\n=== BREAKDOWN — {title} (% within row) ===")
        hdr = f"  {'segment':>20} {'n':>9} {'Early%':>7} {'OnTime%':>8} {'Late%':>7}"
        if wh_hours:
            hdr += "   working_hours"
        print(hdr)
        items = [(kk, d[kk]) for kk in keys if kk in d] if keys else \
            sorted(d.items(), key=lambda kv: -kv[1].l / kv[1].n if kv[1].n else 0)
        for key, c in items:
            line = (f"  {key:>20} {c.n:>9d} {c.e/c.n*100:6.1f}% {c.o/c.n*100:7.1f}% {c.l/c.n*100:6.1f}%")
            if wh_hours:
                line += f"   {hours.get(key, '?')}"
            print(line)

    show("WH type (FC vs MFC)", by_type, keys=["FC", "MFC", "Unknown"])
    show("Inventory @ digitisation", by_inv, keys=["inventory", "non-inventory", "unknown"])
    show("Inventory change digi -> ship", by_chg,
         keys=["inv -> inv", "non -> non", "inv -> non-inv", "non-inv -> inv", "unknown"])
    show("Warehouse (sorted by Late%)", by_wh, wh_hours=True)

    # ---- write tidy CSV ----
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["view", "segment", "n", "early_n", "ontime_n", "late_n",
                     "early_pct", "ontime_pct", "late_pct", "extra"])
        wr.writerow(["overall", "ALL", eotl.n, eotl.e, eotl.o, eotl.l,
                     round(eotl.e/n*100, 2), round(eotl.o/n*100, 2), round(eotl.l/n*100, 2), ""])
        for b in ORDER:
            wr.writerow(["minute_bucket", b, dist[b], "", "", "", round(dist[b]/n*100, 2), "", "", ""])
        for title, d in [("type", by_type), ("inv_digi", by_inv), ("inv_change", by_chg), ("warehouse", by_wh)]:
            for key, c in d.items():
                extra = hours.get(key, "") if title == "warehouse" else ""
                wr.writerow([title, key, c.n, c.e, c.o, c.l,
                             round(c.e/c.n*100, 2), round(c.o/c.n*100, 2), round(c.l/c.n*100, 2), extra])
    print(f"\nwrote -> {OUT_PATH}")


if __name__ == "__main__":
    main()
