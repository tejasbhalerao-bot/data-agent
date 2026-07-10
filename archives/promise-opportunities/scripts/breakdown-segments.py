import csv
from collections import defaultdict

INPUT = "/Users/tejasbhalerao/data-agent/archives/promise-opportunities/outputs/classified-eotl.csv"
TOTAL = 522839

def bool_field(val):
    v = val.strip().lower()
    if v in ("true", "1"): return True
    if v in ("false", "0"): return False
    return None  # null

SEGMENTS = {
    "SDD":                  lambda r: r["sdd"] is True,
    "Non-SDD":              lambda r: r["sdd"] is False,
    "Inventory":            lambda r: r["inv"] is True,
    "Non-Inventory":        lambda r: r["inv"] is False,
    "SDD + Inventory":      lambda r: r["sdd"] is True  and r["inv"] is True,
    "SDD + Non-Inventory":  lambda r: r["sdd"] is True  and r["inv"] is False,
    "Non-SDD + Inventory":  lambda r: r["sdd"] is False and r["inv"] is True,
    "Non-SDD + Non-Inventory": lambda r: r["sdd"] is False and r["inv"] is False,
}

STAGES = ["doctor", "warehouse", "dispatch", "delivery"]
LABELS = ["E", "OT", "L", "NULL"]

# accumulate
counts = {seg: {"n": 0, **{f"{s}_{l}": 0 for s in STAGES for l in LABELS}} for seg in SEGMENTS}

with open(INPUT) as f:
    for row in csv.DictReader(f):
        r = {
            "sdd": bool_field(row["digitised_is_sdd"]),
            "inv": bool_field(row["digitised_is_inventory"]),
        }
        for seg_name, fn in SEGMENTS.items():
            if fn(r):
                counts[seg_name]["n"] += 1
                for stage in STAGES:
                    val = row[f"{stage}_eotl"] or "NULL"
                    counts[seg_name][f"{stage}_{val}"] += 1

# print
def pct(n, d): return f"{n/d*100:.1f}%" if d else "—"

for seg_name in SEGMENTS:
    c = counts[seg_name]
    n = c["n"]
    print(f"\n{'='*60}")
    print(f"  {seg_name}")
    print(f"  Orders: {n:,}  ({pct(n, TOTAL)} of overall)")
    print(f"{'='*60}")
    print(f"  {'Stage':<12} {'E':>8} {'OT':>8} {'L':>8} {'NULL':>8}")
    print(f"  {'-'*48}")
    for stage in STAGES:
        row_n   = {l: c[f"{stage}_{l}"] for l in LABELS}
        stage_t = sum(row_n.values())
        def p(l): return f"{row_n[l]:,}({pct(row_n[l], stage_t)})"
        print(f"  {stage.capitalize():<12} {p('E'):>14} {p('OT'):>14} {p('L'):>14} {p('NULL'):>14}")

print(f"\n\nTOTAL working set: {TOTAL:,}")

# validation: sum of SDD + Non-SDD should cover all non-null sdd rows
sdd_check = counts["SDD"]["n"] + counts["Non-SDD"]["n"]
inv_check = counts["Inventory"]["n"] + counts["Non-Inventory"]["n"]
cross_check = counts["SDD + Inventory"]["n"] + counts["SDD + Non-Inventory"]["n"] + \
              counts["Non-SDD + Inventory"]["n"] + counts["Non-SDD + Non-Inventory"]["n"]
print(f"\n--- Validation ---")
print(f"SDD + Non-SDD = {sdd_check:,}")
print(f"Inv + Non-Inv = {inv_check:,}")
print(f"4-way cross   = {cross_check:,}")
print(f"Working set   = {TOTAL:,}")
