import csv
from collections import defaultdict
from datetime import datetime, date
RAW="archives/early-delivery-analysis/raw-data/early-delivery-raw-may-2026.csv"
FMT="%b %d, %Y, %I:%M %p"; CUT=date(2026,5,8); BUF=60
def pdt(s):
    s=(s or "").strip()
    if not s: return None
    try: return datetime.strptime(s,FMT)
    except: return None
def pn(s):
    s=(s or "").strip()
    try: return float(s)
    except: return None
def ptm(s):
    s=(s or "").strip()
    try: return datetime.strptime(s,"%I:%M %p").time()
    except: return None
def tern(s):
    v=(s or "").strip().lower(); return True if v in("true","1") else False if v in("false","0") else None
def chg(d,s):
    di,si=tern(d),tern(s)
    if di is None or si is None: return "unknown"
    if di and si: return "Inv -> Inv"
    if not di and not si: return "Non-Inv -> Non-Inv"
    return "Inv -> Non-Inv" if di and not si else "Non-Inv -> Inv"
H={}
for r in csv.DictReader(open("archives/early-delivery-analysis/context/warehouse-working-hours.csv",encoding='utf-8-sig')):
    H[r['id'].strip()]=(ptm(r['work_start']),ptm(r['work_end']))

def cts(a,p): d=(a-p).total_seconds(); return "Early" if d<-BUF else "Late" if d>BUF else "On-Time"
def cday(a,p): d=(a.date()-p.date()).days; return "Early" if d<=-1 else "Late" if d>=1 else "On-Time"
def med(v): v=sorted(v); n=len(v); return v[n//2] if n else 0

seen=set()
B=defaultdict(lambda:{"n":0,"de":0,"do":0,"dl":0,"wearly":[],"outside":0})
N=0
for row in csv.DictReader(open(RAW,newline='',encoding='utf-8-sig')):
    oid=(row["order_id"] or "").replace(",","").strip()
    if oid in seen: continue
    seen.add(oid)
    dig=pdt(row["digitised_ts"])
    if dig is None or dig.date()<CUT: continue
    if pn(row["digitised_wh_process_mins"])==0: continue
    drp=pdt(row["digitised_dr_promise"]); dra=pdt(row["dr_confirm_ts"])
    whp=pdt(row["digitised_wh_promise"]); wha=pdt(row["actual_warehouse_processing"])
    dsp=pdt(row["digitised_dispatch_promise"]); dsa=pdt(row["pickup_time"])
    dlp=pdt(row["digitised_delivery_promise"]); dla=pdt(row["delivery_attempt_time"])
    if None in (drp,dra,whp,wha,dsp,dsa,dlp,dla): continue
    if cts(wha,whp)!="Early": continue          # WH Early
    if cday(dsa,dsp)!="Early": continue          # Dispatch Early (date)
    N+=1
    k=chg(row["digitised_is_inventory"],row["shipping_is_inventory"])
    b=B[k]; b["n"]+=1
    dl=cday(dla,dlp); b["de"]+=dl=="Early"; b["do"]+=dl=="On-Time"; b["dl"]+=dl=="Late"
    b["wearly"].append((whp-wha).total_seconds()/60)   # how early WH finished (min)
    o,c=H.get((row["digitised_wh_id"] or "").strip(),(None,None))
    if o and c and not (o<=wha.time()<=c): b["outside"]+=1

print(f"WH-Early & Dispatch-Early cohort = {N}\n")
print(f"{'inv_change':>20} {'n':>8} {'%coh':>6} | {'delE%':>6} {'delOT%':>7} {'delL%':>6} | {'WHearly_med':>11} {'finish_outside_hrs%':>19}")
for k in ["Non-Inv -> Non-Inv","Inv -> Inv","Non-Inv -> Inv","Inv -> Non-Inv","unknown"]:
    if k not in B: continue
    b=B[k]; n=b["n"]; me=med(b["wearly"])
    mestr=f"{me/60:.1f}h" if abs(me)<1440 else f"{me/1440:.1f}d"
    print(f"{k:>20} {n:>8d} {n/N*100:5.1f}% | {b['de']/n*100:5.1f}% {b['do']/n*100:6.1f}% {b['dl']/n*100:5.1f}% | "
          f"{mestr:>11} {b['outside']/n*100:18.1f}%")
