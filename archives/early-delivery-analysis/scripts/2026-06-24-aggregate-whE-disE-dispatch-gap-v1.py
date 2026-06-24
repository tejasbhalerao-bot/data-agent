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
def tern(s):
    v=(s or "").strip().lower(); return True if v in("true","1") else False if v in("false","0") else None
def chg(d,s):
    di,si=tern(d),tern(s)
    if di is None or si is None: return "unknown"
    if di and si: return "Inv -> Inv"
    if not di and not si: return "Non-Inv -> Non-Inv"
    return "Inv -> Non-Inv" if di and not si else "Non-Inv -> Inv"
def cts(a,p): d=(a-p).total_seconds(); return "Early" if d<-BUF else "Late" if d>BUF else "On-Time"
def cday(a,p): d=(a.date()-p.date()).days; return "Early" if d<=-1 else "Late" if d>=1 else "On-Time"
def med(v): v=sorted(v); n=len(v); return v[n//2] if n else 0
def hd(m): return f"{m/60:.1f}h" if abs(m)<1440 else f"{m/1440:.1f}d"

seen=set()
B=defaultdict(lambda:{"pg":[],"ag":[],"wh_late":[],"pick_after_wh":[]})
for row in csv.DictReader(open(RAW,newline='',encoding='utf-8-sig')):
    oid=(row["order_id"] or "").replace(",","").strip()
    if oid in seen: continue
    seen.add(oid)
    dig=pdt(row["digitised_ts"])
    if dig is None or dig.date()<CUT: continue
    if pn(row["digitised_wh_process_mins"])==0: continue
    whp=pdt(row["digitised_wh_promise"]); wha=pdt(row["actual_warehouse_processing"])
    dsp=pdt(row["digitised_dispatch_promise"]); dsa=pdt(row["pickup_time"])
    if None in (whp,wha,dsp,dsa): continue
    if cts(wha,whp)!="Early" or cday(dsa,dsp)!="Early": continue
    k=chg(row["digitised_is_inventory"],row["shipping_is_inventory"]); b=B[k]
    b["pg"].append((dsp-whp).total_seconds()/60)        # promised WH->dispatch gap
    b["ag"].append((dsa-wha).total_seconds()/60)        # actual WH->pickup gap
    b["wh_late"].append((wha-whp).total_seconds()/60)   # WH vs its promise (neg=early)
    b["pick_after_wh"].append((dsa-wha).total_seconds()/60)

print(f"{'inv_change':>20} {'n':>7} | {'promised WH->disp gap':>21} | {'actual WH->pickup gap':>21} | {'dispatch leg ran early by':>26}")
for k in ["Inv -> Inv","Non-Inv -> Non-Inv","Non-Inv -> Inv"]:
    b=B[k]; n=len(b["pg"])
    pg=med(b["pg"]); ag=med(b["ag"])
    print(f"{k:>20} {n:>7d} | {hd(pg):>21} | {hd(ag):>21} | {hd(pg-ag):>26}")
