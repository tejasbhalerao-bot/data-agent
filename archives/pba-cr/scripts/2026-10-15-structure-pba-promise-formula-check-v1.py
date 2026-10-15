"""Check the CR promise formula on orders allocated through PBA at soft allocation.

Purpose: for every order whose soft promise was served by PBA, test
         promised_delivery_time = promised_warehouse_processing_time + pba_soft_selected_partner_tat_in_days
         and list the orders that break it.
Serves: none (data check for M1-M2; produces no metric figures)
Reads:  archives/pba-cr/raw-data/<dump>.csv (Q1 v2 output; local only), named on the command line
Writes: archives/pba-cr/outputs/<dump>-pba-formula-check.csv (one row per PBA-served order; local only)
Run:    python3 archives/pba-cr/scripts/2026-10-15-structure-pba-promise-formula-check-v1.py fahad-raw-dump-2
"""
import csv
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DUMP = sys.argv[1] if len(sys.argv) > 1 else "fahad-raw-dump-2"
SRC = ROOT / "raw-data" / f"{DUMP}.csv"
OUT = ROOT / "outputs" / f"{DUMP}-pba-formula-check.csv"
CR_SOFT_GO_LIVE = datetime(2026, 10, 14, 23, 5)  # LMS !359, per the Q1 v2 query header
TOLERANCE = timedelta(minutes=1)                  # Metabase export is at minute precision

csv.field_size_limit(10**9)


def ts(v):
    v = (v or "").strip()
    return datetime.strptime(v, "%b %d, %Y, %I:%M %p") if v else None


def num(v):
    v = (v or "").strip().replace(",", "")
    return float(v) if v else None


out, summary = [], Counter()
for r in csv.DictReader(open(SRC, encoding="utf-8-sig")):
    if r["SOFT_SERVED_CANDIDATE_TYPE"] != "COURIER_PBA":
        continue
    pt, dl, dp = ts(r["PROMISED_WAREHOUSE_PROCESSING_TIME"]), ts(r["PROMISED_DELIVERY_TIME"]), ts(r["PROMISED_DISPATCH_TIME"])
    tat, at = num(r["PBA_SOFT_SELECTED_PARTNER_TAT_IN_DAYS"]), ts(r["SOFT_PROMISE_AT"])
    period = "from 14 Oct 23:05" if at and at >= CR_SOFT_GO_LIVE else "before 14 Oct 23:05"
    if None in (pt, dl, tat):
        result, expected, gap = "MISSING_INPUT", None, None
    else:
        expected = pt + timedelta(minutes=round(tat * 1440))
        gap = (dl - expected).total_seconds() / 60
        if abs(dl - expected) <= TOLERANCE:
            result = "HOLDS"
        elif dp and abs(dl - (dp + timedelta(minutes=round(tat * 1440)))) <= TOLERANCE:
            result = "BREAKS_DISPATCH_PLUS_TAT"
        else:
            result = "BREAKS_OTHER"
    summary[(period, result)] += 1
    out.append({
        "order_id": r["ORDER_ID"], "soft_promise_at": at, "period": period, "result": result,
        "promised_warehouse_processing_time": pt, "promised_dispatch_time": dp, "promised_delivery_time": dl,
        "pba_soft_selected_partner_tat_in_days": tat, "expected_delivery_time": expected,
        "delivery_minus_expected_minutes": gap, "soft_served_partner": r["SOFT_SERVED_PARTNER"],
        "pba_soft_selected_delivery_partner": r["PBA_SOFT_SELECTED_DELIVERY_PARTNER"],
        "promised_delivery_partner": r["PROMISED_DELIVERY_PARTNER"],
    })

OUT.parent.mkdir(exist_ok=True)
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)

print("PBA-served orders:", len(out))
for period in ("before 14 Oct 23:05", "from 14 Oct 23:05"):
    n = sum(v for (p, _), v in summary.items() if p == period)
    print(f"  {period}: {n}")
    for (p, res), v in sorted(summary.items()):
        if p == period:
            print(f"    {res}: {v} ({100.0 * v / n:.1f}%)")
print("Orders that break the formula, from 14 Oct 23:05:")
for o in out:
    if o["period"] == "from 14 Oct 23:05" and o["result"] != "HOLDS":
        print("  ", o["order_id"], o["result"], "gap_min=", o["delivery_minus_expected_minutes"])
print("Wrote", OUT)
