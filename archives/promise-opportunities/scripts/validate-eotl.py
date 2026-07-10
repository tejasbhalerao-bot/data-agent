import csv
from dateutil import parser as dtparser
from collections import defaultdict
import random

INPUT_RAW = "/Users/tejasbhalerao/Downloads/Early Deliveries Raw 8th May to 31st May.csv"
INPUT_CLASSIFIED = "/Users/tejasbhalerao/data-agent/archives/promise-opportunities/outputs/classified-eotl.csv"

_cache = {}
def parse(val):
    v = val.strip()
    if not v: return None
    if v in _cache: return _cache[v]
    dt = dtparser.parse(v)
    _cache[v] = dt
    return dt

def trunc_min(dt): return dt.replace(second=0, microsecond=0)

passes = []
fails  = []

def check(name, result, detail=""):
    if result:
        passes.append(name)
        print(f"  PASS  {name}")
    else:
        fails.append(name)
        print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))

print("=== Loading classified output ===")
rows = []
with open(INPUT_CLASSIFIED) as f:
    rows = list(csv.DictReader(f))

# 1. Row count
check("Row count == 522,839", len(rows) == 522839, f"got {len(rows):,}")

# 2. No unexpected values in eotl columns
valid_vals = {"E","OT","L",""}
for col in ["doctor_eotl","warehouse_eotl","dispatch_eotl","delivery_eotl"]:
    bad = [r["order_id"] for r in rows if r[col] not in valid_vals]
    check(f"No invalid values in {col}", len(bad)==0, f"{len(bad)} bad rows")

# 3. Spot-check known order 47,708,039
target = next((r for r in rows if r["order_id"].replace(",","") == "47708039"), None)
check("Spot-check order 47708039 exists", target is not None)
if target:
    check("Spot-check doctor=E",    target["doctor_eotl"]    == "E")
    check("Spot-check warehouse=E", target["warehouse_eotl"] == "E")
    check("Spot-check dispatch=OT", target["dispatch_eotl"]  == "OT")
    check("Spot-check delivery=OT", target["delivery_eotl"]  == "OT")

# 4. Doctor logic: delta = actual - promise; E<-1, -1<=OT<=1, L>1
print("\n--- Doctor boundary checks (sample 2000 non-null) ---")
doc_rows = [r for r in rows if r["doctor_eotl"] and r["dr_confirm_ts"].strip() and r["digitised_dr_promise"].strip()]
sample = random.sample(doc_rows, min(2000, len(doc_rows)))
doc_errors = 0
for r in sample:
    promise = parse(r["digitised_dr_promise"])
    actual  = parse(r["dr_confirm_ts"])
    delta   = (actual - promise).total_seconds() / 60
    label   = r["doctor_eotl"]
    expected = "E" if delta < -1 else ("OT" if delta <= 1 else "L")
    if label != expected:
        doc_errors += 1
check("Doctor classification correct (2000 sample)", doc_errors == 0, f"{doc_errors} mismatches")

# 5. Warehouse logic: trunc to minute, compare vs dispatch_promise
print("--- Warehouse boundary checks (sample 2000 non-null) ---")
wh_rows = [r for r in rows if r["warehouse_eotl"] and r["awb_print_ts"].strip() and r["digitised_dispatch_promise"].strip()]
sample = random.sample(wh_rows, min(2000, len(wh_rows)))
wh_errors = 0
for r in sample:
    promise = trunc_min(parse(r["digitised_dispatch_promise"]))
    actual  = trunc_min(parse(r["awb_print_ts"]))
    label   = r["warehouse_eotl"]
    expected = "E" if actual < promise else ("OT" if actual == promise else "L")
    if label != expected:
        wh_errors += 1
check("Warehouse classification correct (2000 sample)", wh_errors == 0, f"{wh_errors} mismatches")

# 6. Dispatch logic: date only
print("--- Dispatch boundary checks (sample 2000 non-null) ---")
disp_rows = [r for r in rows if r["dispatch_eotl"] and r["pickup_time"].strip() and r["digitised_dispatch_promise"].strip()]
sample = random.sample(disp_rows, min(2000, len(disp_rows)))
disp_errors = 0
for r in sample:
    pd = parse(r["digitised_dispatch_promise"]).date()
    ad = parse(r["pickup_time"]).date()
    label = r["dispatch_eotl"]
    expected = "E" if ad < pd else ("OT" if ad == pd else "L")
    if label != expected:
        disp_errors += 1
check("Dispatch classification correct (2000 sample)", disp_errors == 0, f"{disp_errors} mismatches")

# 7. Delivery logic: date only
print("--- Delivery boundary checks (sample 2000 non-null) ---")
delv_rows = [r for r in rows if r["delivery_eotl"] and r["delivery_attempt_time"].strip() and r["digitised_delivery_promise"].strip()]
sample = random.sample(delv_rows, min(2000, len(delv_rows)))
delv_errors = 0
for r in sample:
    pd = parse(r["digitised_delivery_promise"]).date()
    ad = parse(r["delivery_attempt_time"]).date()
    label = r["delivery_eotl"]
    expected = "E" if ad < pd else ("OT" if ad == pd else "L")
    if label != expected:
        delv_errors += 1
check("Delivery classification correct (2000 sample)", delv_errors == 0, f"{delv_errors} mismatches")

# 8. NULL consistency — eotl null iff source field(s) null
null_doc_errors = sum(
    1 for r in rows
    if (r["doctor_eotl"] == "") != (not r["dr_confirm_ts"].strip() or not r["digitised_dr_promise"].strip())
)
check("Doctor NULL iff source null", null_doc_errors == 0, f"{null_doc_errors} inconsistencies")

null_wh_errors = sum(
    1 for r in rows
    if (r["warehouse_eotl"] == "") != (not r["awb_print_ts"].strip() or not r["digitised_dispatch_promise"].strip())
)
check("Warehouse NULL iff source null", null_wh_errors == 0, f"{null_wh_errors} inconsistencies")

null_disp_errors = sum(
    1 for r in rows
    if (r["dispatch_eotl"] == "") != (not r["pickup_time"].strip() or not r["digitised_dispatch_promise"].strip())
)
check("Dispatch NULL iff source null", null_disp_errors == 0, f"{null_disp_errors} inconsistencies")

# 9. Delivery NULL should be 0 (delivery_attempt_time always set in working set, delivery_promise near-always set)
null_delv = sum(1 for r in rows if r["delivery_eotl"] == "")
check("Delivery NULLs minimal (<=100)", null_delv <= 100, f"{null_delv} nulls")

# 10. All rows in output have delivery_attempt_time set (working set guarantee)
no_attempt = sum(1 for r in rows if not r["delivery_attempt_time"].strip())
check("All output rows have delivery_attempt_time", no_attempt == 0, f"{no_attempt} rows missing it")

print(f"\n=== RESULT: {len(passes)} PASS / {len(fails)} FAIL ===")
if fails:
    print("FAILED checks:")
    for f in fails:
        print(f"  - {f}")
