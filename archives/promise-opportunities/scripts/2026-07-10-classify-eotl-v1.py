import csv
from dateutil import parser as dtparser
from collections import defaultdict

INPUT = "/Users/tejasbhalerao/Downloads/Early Deliveries Raw 8th May to 31st May.csv"
OUTPUT = "/Users/tejasbhalerao/data-agent/archives/promise-opportunities/outputs/classified-eotl.csv"

_cache = {}

def parse(val):
    v = val.strip()
    if not v:
        return None
    if v in _cache:
        return _cache[v]
    dt = dtparser.parse(v)
    _cache[v] = dt
    return dt

def trunc_minute(dt):
    return dt.replace(second=0, microsecond=0)

def classify_doctor(promise, actual):
    if promise is None or actual is None:
        return None
    delta = (actual - promise).total_seconds() / 60
    if delta < -1:
        return "E"
    elif delta <= 1:
        return "OT"
    else:
        return "L"

def classify_wh(dispatch_promise, awb_print):
    if dispatch_promise is None or awb_print is None:
        return None
    p = trunc_minute(dispatch_promise)
    a = trunc_minute(awb_print)
    if a < p:
        return "E"
    elif a == p:
        return "OT"
    else:
        return "L"

def classify_date(promise, actual):
    if promise is None or actual is None:
        return None
    if actual.date() < promise.date():
        return "E"
    elif actual.date() == promise.date():
        return "OT"
    else:
        return "L"

stage_counts = {s: defaultdict(int) for s in ["doctor", "warehouse", "dispatch", "delivery"]}
working_set = 0

with open(INPUT) as f:
    reader = csv.DictReader(f)
    out_fields = reader.fieldnames + ["doctor_eotl", "warehouse_eotl", "dispatch_eotl", "delivery_eotl"]

    with open(OUTPUT, "w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=out_fields)
        writer.writeheader()

        for i, row in enumerate(reader):
            if not row["delivery_attempt_time"].strip():
                continue
            working_set += 1

            dr_promise   = parse(row["digitised_dr_promise"])
            dr_confirm   = parse(row["dr_confirm_ts"])
            disp_promise = parse(row["digitised_dispatch_promise"])
            awb_print    = parse(row["awb_print_ts"])
            pickup       = parse(row["pickup_time"])
            del_promise  = parse(row["digitised_delivery_promise"])
            del_attempt  = parse(row["delivery_attempt_time"])

            doc  = classify_doctor(dr_promise, dr_confirm)
            wh   = classify_wh(disp_promise, awb_print)
            disp = classify_date(disp_promise, pickup)
            delv = classify_date(del_promise, del_attempt)

            row["doctor_eotl"]    = doc  or ""
            row["warehouse_eotl"] = wh   or ""
            row["dispatch_eotl"]  = disp or ""
            row["delivery_eotl"]  = delv or ""

            writer.writerow(row)

            for label, val in [("doctor", doc), ("warehouse", wh), ("dispatch", disp), ("delivery", delv)]:
                stage_counts[label][val if val else "NULL"] += 1

            if working_set % 50000 == 0:
                print(f"  processed {working_set:,}...")

print(f"\nWorking set: {working_set:,}\n")
for stage in ["doctor", "warehouse", "dispatch", "delivery"]:
    counts = stage_counts[stage]
    total = sum(counts.values())
    print(f"--- {stage.upper()} ---")
    for label in ["E", "OT", "L", "NULL"]:
        n = counts.get(label, 0)
        print(f"  {label:4s}: {n:>7,}  ({n/total*100:.1f}%)")
    print()

print(f"Output written: {OUTPUT}")
