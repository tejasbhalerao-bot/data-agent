import csv
from collections import defaultdict
from datetime import datetime, date
RAW="archives/early-delivery-analysis/raw-data/early-delivery-raw-may-2026.csv"
FMT="%b %d, %Y, %I:%M %p"; CUT=date(2026,5,8)
NAME={"195":"Delhivery Surface","185":"Xpressbees Surface","225":"Delhivery Express",
"247":"Bluedart Express","246":"Bluedart","286":"Xpressbees Express","686":"Delhivery NDD",
"697":"Shiprocket NDD","608":"Shiprocket","639":"Shadowfax Surface","685":"Shiprocket Courier",
"638":"Shadowfax Express","":"(blank)"}
EARLY_RED={"195","185","225"}; LATE_RED={"247","246","286"}
def pdt(s):
    s=(s or "").strip()
    if not s: return None
    try: return datetime.strptime(s,FMT)
    except: return None
seen=set()
vol=defaultdict(int); b_neg1=defaultdict(int); b_pos1=defaultdict(int); tneg=tpos=tvol=0
for row in csv.DictReader(open(RAW,newline='',encoding='utf-8-sig')):
    oid=(row["order_id"] or "").replace(",","").strip()
    if oid in seen: continue
    seen.add(oid)
    att=pdt(row["delivery_attempt_time"])
    if att is None: continue
    dig=pdt(row["digitised_ts"])
    if dig is None or dig.date()<CUT: continue
    pr=pdt(row["digitised_delivery_promise"])
    if pr is None: continue
    if (row["digitised_is_sdd"] or "").strip().lower()!="false": continue  # courier
    p=(row["digitised_delivery_partner"] or "").strip()
    vol[p]+=1; tvol+=1
    off=(att.date()-pr.date()).days
    if off==-1: b_neg1[p]+=1; tneg+=1
    elif off==1: b_pos1[p]+=1; tpos+=1

def show(title, bucket, tot):
    print(f"\n=== {title}  (bucket n={tot}) ===")
    print(f"{'partner':>20} {'n':>7} {'%ofBucket':>10} {'%ofVolume':>10}")
    for p,_ in sorted(bucket.items(), key=lambda kv:-kv[1]):
        nm=NAME.get(p,p)
        print(f"{nm:>20} {bucket[p]:>7d} {bucket[p]/tot*100:9.1f}% {vol[p]/tvol*100:9.1f}%")

print(f"courier cohort={tvol} | -1 bucket={tneg} | +1 bucket={tpos}")
show("-1 bucket (1 day EARLY)", b_neg1, tneg)
show("+1 bucket (1 day LATE)", b_pos1, tpos)

er_neg=sum(b_neg1[p] for p in EARLY_RED); lr_neg=sum(b_neg1[p] for p in LATE_RED)
er_pos=sum(b_pos1[p] for p in EARLY_RED); lr_pos=sum(b_pos1[p] for p in LATE_RED)
er_vol=sum(vol[p] for p in EARLY_RED); lr_vol=sum(vol[p] for p in LATE_RED)
print(f"\n=== TRIO SUMMARY ===")
print(f"early-red trio (195,185,225): {er_vol/tvol*100:.1f}% of volume | {er_neg/tneg*100:.1f}% of -1 bucket | {er_pos/tpos*100:.1f}% of +1 bucket")
print(f"late-red  trio (247,246,286): {lr_vol/tvol*100:.1f}% of volume | {lr_neg/tneg*100:.1f}% of -1 bucket | {lr_pos/tpos*100:.1f}% of +1 bucket")
