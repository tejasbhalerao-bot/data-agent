import csv
from dateutil import parser as dtparser
from collections import defaultdict
import random

INPUT_CLASSIFIED = "/Users/tejasbhalerao/data-agent/archives/promise-opportunities/outputs/classified-eotl-v2.csv"

_cache = {}
def parse(val):
    v = val.strip()
    if not v: return None
    if v in _cache: return _cache[v]
    dt = dtparser.parse(v)
    _cache[v] = dt
    return dt

def trunc_min(dt): return dt.replace(second=0, microsecond=0)

passes, fails = [], []
def check(name, result, detail=""):
    if result:
        passes.append(name)
        print(f"  PASS  {name}")
    else:
        fails.append(name)
        print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))

print("=== Loading classified output ===")
rows = list(csv.DictReader(open(INPUT_CLASSIFIED)))

# 1. Row count
check("Row count == 522,839", len(rows) == 522839, f"got {len(rows):,}")

# 2. Valid enum values
valid = {"E","OT","L",""}
for col in ["doctor_eotl","warehouse_eotl","dispatch_eotl","delivery_tat_eotl","delivery_ops_eotl"]:
    bad = [r["order_id"] for r in rows if r[col] not in valid]
    check(f"No invalid values in {col}", len(bad)==0, f"{len(bad)} bad rows")

# 3. Spot-check order 47,708,039
t = next((r for r in rows if r["order_id"].replace(",","") == "47708039"), None)
check("Spot-check order exists", t is not None)
if t:
    check("Spot-check doctor=E",       t["doctor_eotl"]       == "E")
    check("Spot-check warehouse=E",    t["warehouse_eotl"]    == "E")
    check("Spot-check dispatch=OT",    t["dispatch_eotl"]     == "OT")
    check("Spot-check delivery_tat=OT",t["delivery_tat_eotl"] == "OT")
    check("Spot-check delivery_ops=E", t["delivery_ops_eotl"] == "E")

# 4. Doctor boundary (2000 sample)
doc_rows = [r for r in rows if r["doctor_eotl"] and r["actual_doctor_call_time"].strip()]
sample = random.sample(doc_rows, min(2000, len(doc_rows)))
errors = 0
for r in sample:
    promise = parse(r["digitised_dr_promise"])
    actual  = parse(r["actual_doctor_call_time"])
    delta   = (actual - promise).total_seconds() / 60
    expected = "E" if delta < -1 else ("OT" if delta <= 1 else "L")
    if r["doctor_eotl"] != expected: errors += 1
check("Doctor logic correct (2000 sample)", errors==0, f"{errors} mismatches")

# 5. Warehouse boundary (2000 sample)
wh_rows = [r for r in rows if r["warehouse_eotl"] and r["awb_print_ts"].strip()]
sample = random.sample(wh_rows, min(2000, len(wh_rows)))
errors = 0
for r in sample:
    p = trunc_min(parse(r["digitised_dispatch_promise"]))
    a = trunc_min(parse(r["awb_print_ts"]))
    expected = "E" if a < p else ("OT" if a == p else "L")
    if r["warehouse_eotl"] != expected: errors += 1
check("Warehouse logic correct (2000 sample)", errors==0, f"{errors} mismatches")

# 6. Dispatch boundary (2000 sample)
disp_rows = [r for r in rows if r["dispatch_eotl"] and r["pickup_time"].strip()]
sample = random.sample(disp_rows, min(2000, len(disp_rows)))
errors = 0
for r in sample:
    pd = parse(r["digitised_dispatch_promise"]).date()
    ad = parse(r["pickup_time"]).date()
    expected = "E" if ad < pd else ("OT" if ad == pd else "L")
    if r["dispatch_eotl"] != expected: errors += 1
check("Dispatch logic correct (2000 sample)", errors==0, f"{errors} mismatches")

# 7. Delivery TAT boundary (2000 sample)
tat_rows = [r for r in rows if r["delivery_tat_eotl"] and r["pickup_time"].strip()]
sample = random.sample(tat_rows, min(2000, len(tat_rows)))
errors = 0
for r in sample:
    promised = (parse(r["digitised_delivery_promise"]).date() - parse(r["digitised_dispatch_promise"]).date()).days
    actual   = (parse(r["delivery_attempt_time"]).date() - parse(r["pickup_time"]).date()).days
    expected = "E" if actual < promised else ("OT" if actual == promised else "L")
    if r["delivery_tat_eotl"] != expected: errors += 1
check("Delivery TAT logic correct (2000 sample)", errors==0, f"{errors} mismatches")

# 8. Delivery Ops boundary (2000 sample)
ops_rows = [r for r in rows if r["delivery_ops_eotl"] and r["shipping_delivery_promise"].strip()]
sample = random.sample(ops_rows, min(2000, len(ops_rows)))
errors = 0
for r in sample:
    promised = int(r["shipping_delivery_promise"].strip())
    actual   = (parse(r["delivery_attempt_time"]).date() - parse(r["pickup_time"]).date()).days
    expected = "E" if actual < promised else ("OT" if actual == promised else "L")
    if r["delivery_ops_eotl"] != expected: errors += 1
check("Delivery Ops logic correct (2000 sample)", errors==0, f"{errors} mismatches")

# 9. All rows have delivery_attempt_time
no_attempt = sum(1 for r in rows if not r["delivery_attempt_time"].strip())
check("All rows have delivery_attempt_time", no_attempt==0, f"{no_attempt} missing")

print(f"\n=== RESULT: {len(passes)} PASS / {len(fails)} FAIL ===")
if fails:
    for f in fails: print(f"  FAILED: {f}")
