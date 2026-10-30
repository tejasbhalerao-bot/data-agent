# Purpose: explain the low % picked up (S1 M5): orders in the PBA and Internal bases by final order status
# Serves: Dashboard S1 M5-M6 diagnosis (2026-10-30)
# Reads: archives/pba-cr/raw-data/dashboard/pickup-gap-by-status-w2.json (Metabase, order_details joined to the S1 M5 trimmed base)
# Writes: archives/pba-cr/outputs/dashboard-pickup-gap-diagnosis-w2.txt
# Run with: python3 archives/pba-cr/scripts/2026-10-30-structure-dashboard-pickup-gap-diagnosis-v1.py
import json, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
R = json.load(open(f"{ROOT}/raw-data/dashboard/pickup-gap-by-status-w2.json")); N = R["status_names"]
lines = []
def say(t): print(t); lines.append(t)
NOT_PLACED = {49, 312, 174}          # incomplete, scrapped, discarded
for g, base_check in (("PBA", 8491), ("Internal", 161680)):
    rows = [r for r in R["non_sdd_rows"] if r[0] == g]
    tot = sum(r[2] for r in rows); pk = sum(r[3] for r in rows)
    assert tot == base_check and pk == {"PBA": 2814, "Internal": 54367}[g], (g, tot, pk)   # ties back to S1 M4 and S1 M5 v2
    np_ = sum(r[2] for r in rows if r[1] in NOT_PLACED)
    canc = sum(r[2] for r in rows if r[1] == 57); pk_canc = sum(r[3] for r in rows if r[1] == 57)
    say(f"{g} base {tot:,}: picked up {pk:,} ({pk/tot*100:.1f}%)")
    for r in sorted(rows, key=lambda r: -r[2])[:8]:
        say(f"   status {r[1]:>3} {N[str(r[1])]:<28} {r[2]:>7,} orders   picked up {r[3]:>7,}")
    say(f"   never real orders (incomplete + scrapped + discarded): {np_:,} ({np_/tot*100:.1f}% of the base), picked up 0")
    say(f"   excluding them: picked up {pk:,} of {tot-np_:,} = {pk/(tot-np_)*100:.1f}%")
    say(f"   also excluding cancelled ({canc:,}, of which {pk_canc} picked up): {pk-pk_canc:,} of {tot-np_-canc:,} = {(pk-pk_canc)/(tot-np_-canc)*100:.1f}%")
open(f"{ROOT}/outputs/dashboard-pickup-gap-diagnosis-w2.txt", "w").write("\n".join(lines) + "\n")
