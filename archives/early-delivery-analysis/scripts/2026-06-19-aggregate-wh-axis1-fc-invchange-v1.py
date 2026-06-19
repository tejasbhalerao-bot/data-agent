import csv
from collections import defaultdict
from datetime import datetime, date
RAW="archives/early-delivery-analysis/raw-data/early-delivery-raw-may-2026.csv"
FMT="%b %d, %Y, %I:%M %p"; CUT=date(2026,5,8)
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

cells=defaultdict(lambda:{"e4":0,"em":0,"o":0,"l":0})
seen=set()
for row in csv.DictReader(open(RAW,newline='',encoding='utf-8-sig')):
    oid=(row["order_id"] or "").replace(",","").strip()
    if oid in seen: continue
    seen.add(oid)
    dig=pdt(row["digitised_ts"])
    if dig is None or dig.date()<CUT: continue
    if pn(row["digitised_wh_process_mins"])==0: continue
    if tern(row["digitised_is_mfc"]) is not False: continue   # FC only (is_mfc == false)
    drp=pdt(row["digitised_dr_promise"]); whp=pdt(row["digitised_wh_promise"])
    st=pdt(row["processing_start_ts"]); inv=pdt(row["invoice_create_ts"])
    if None in (drp,whp,st,inv): continue
    promised=(whp-drp).total_seconds()/60; actual=(inv-st).total_seconds()/60
    if promised<0 or actual<0: continue
    diff=promised-actual
    c=cells[chg(row["digitised_is_inventory"],row["shipping_is_inventory"])]
    if diff>=240: c["e4"]+=1
    elif diff>1: c["em"]+=1
    elif diff<-1: c["l"]+=1
    else: c["o"]+=1

order=["Inv -> Inv","Inv -> Non-Inv","Non-Inv -> Non-Inv","Non-Inv -> Inv","unknown"]
print("FC orders only — E/OT/L by inventory-change bucket  (Early split into >4h and <=4h)\n")
print(f"{'change bucket':>20} {'n':>8} | {'Early':>7} {'>4h':>7} {'<=4h':>7} | {'OnTime':>7} | {'Late':>7}")
for k in order:
    if k not in cells: continue
    c=cells[k]; n=c["e4"]+c["em"]+c["o"]+c["l"]
    e=c["e4"]+c["em"]
    print(f"{k:>20} {n:>8d} | {e/n*100:6.1f}% {c['e4']/n*100:6.1f}% {c['em']/n*100:6.1f}% | "
          f"{c['o']/n*100:6.1f}% | {c['l']/n*100:6.1f}%")
    print(f"{'':>20} {'':>8} |  ({e:>6d}) ({c['e4']:>6d}) ({c['em']:>6d}) | ({c['o']:>6d}) | ({c['l']:>6d})")
