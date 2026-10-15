"""Share of non-SDD orders whose soft promise was served by PBA, and how many of those follow the CR formula.

Purpose: (1) % of non-SDD orders allocated through PBA at soft allocation (soft_served_candidate_type = COURIER_PBA);
         (2) of those, how many satisfy promised_delivery_time = promised_warehouse_processing_time + PBA soft TAT.
Serves: none (data check requested by Tejas; not one of M1-M5)
Reads:  archives/pba-cr/raw-data/<dump>.csv and outputs/<dump>-pba-formula-check.csv (local only)
Writes: stdout only
Run:    python3 archives/pba-cr/scripts/2026-10-15-aggregate-pba-allocation-share-v1.py fahad-raw-dump-3
"""
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DUMP = sys.argv[1] if len(sys.argv) > 1 else "fahad-raw-dump-3"
csv.field_size_limit(10**9)

rows = list(csv.DictReader(open(ROOT / "raw-data" / f"{DUMP}.csv", encoding="utf-8-sig")))
non_sdd = [r for r in rows if r["SDD_ENABLED"] == "false"]
with_soft = [r for r in non_sdd if r["HAS_SOFT_RECORD"] == "true"]
pba = [r for r in non_sdd if r["SOFT_SERVED_CANDIDATE_TYPE"] == "COURIER_PBA"]

print("1. Non-SDD orders allocated through PBA (soft_served_candidate_type = COURIER_PBA)")
print(f"   all non-SDD orders: {len(pba)} / {len(non_sdd)} = {100.0 * len(pba) / len(non_sdd):.2f}%")
print(f"   non-SDD orders with a soft record: {len(pba)} / {len(with_soft)} = {100.0 * len(pba) / len(with_soft):.2f}%")
print(f"   non-SDD orders without a soft record: {len(non_sdd) - len(with_soft)}")

chk = list(csv.DictReader(open(ROOT / "outputs" / f"{DUMP}-pba-formula-check.csv")))
res = Counter(r["result"] for r in chk)
print("2. PBA-served orders vs the formula promised_delivery_time = promised_warehouse_processing_time + PBA soft TAT")
for k, v in res.most_common():
    print(f"   {k}: {v} / {len(chk)} = {100.0 * v / len(chk):.2f}%")
