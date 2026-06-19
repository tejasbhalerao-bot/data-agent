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
def ptm(s):
    s=(s or "").strip()
    try: return datetime.strptime(s,"%I:%M %p").time()
    except: return None
def tern(s):
    v=(s or "").strip().lower(); return True if v in("true","1") else False if v in("false","0") else None
H={}
for r in csv.DictReader(open("archives/early-delivery-analysis/context/warehouse-working-hours.csv",encoding='utf-8-sig')):
    H[r['id'].strip()]=(ptm(r['work_start']),ptm(r['work_end']))

def grp():
    return {"n":0,"inv_inside":0,"inv_before":0,"inv_after":0,"ps_outside":0,"nohrs":0}
G={"early_inv":grp(),"ctrl_inv":grp()}
seen=set()
for row in csv.DictReader(open(RAW,newline='',encoding='utf-8-sig')):
    oid=(row["order_id"] or "").replace(",","").strip()
    if oid in seen: continue
    seen.add(oid)
    dig=pdt(row["digitised_ts"])
    if dig is None or dig.date()<CUT: continue
    if pn(row["digitised_wh_process_mins"])==0: continue
    drp=pdt(row["digitised_dr_promise"]); whp=pdt(row["digitised_wh_promise"])
    st=pdt(row["processing_start_ts"]); inv=pdt(row["invoice_create_ts"])
    if None in (drp,whp,st,inv): continue
    promised=(whp-drp).total_seconds()/60; actual=(inv-st).total_seconds()/60
    if promised<0 or actual<0: continue
    if tern(row["digitised_is_inventory"]) is not True: continue   # inventory only
    early = (promised-actual)>=240
    g=G["early_inv"] if early else G["ctrl_inv"]
    g["n"]+=1
    o,c=H.get((row["digitised_wh_id"] or "").strip(),(None,None))
    if not o or not c:
        g["nohrs"]+=1; continue
    it=inv.time()
    if it<o: g["inv_before"]+=1
    elif it>c: g["inv_after"]+=1
    else: g["inv_inside"]+=1
    if st.time()<o or st.time()>c: g["ps_outside"]+=1

for name,g in G.items():
    wh=g["n"]-g["nohrs"]
    outside=g["inv_before"]+g["inv_after"]
    print(f"=== {name}  (inventory orders, n={g['n']}, with-hours={wh}) ===")
    print(f"  invoice INSIDE working hours : {g['inv_inside']:>8d}  ({g['inv_inside']/wh*100:5.1f}%)")
    print(f"  invoice OUTSIDE hours        : {outside:>8d}  ({outside/wh*100:5.1f}%)")
    print(f"     - before open            : {g['inv_before']:>8d}  ({g['inv_before']/wh*100:5.1f}%)")
    print(f"     - after close            : {g['inv_after']:>8d}  ({g['inv_after']/wh*100:5.1f}%)")
    print(f"  processing_start outside hrs : {g['ps_outside']:>8d}  ({g['ps_outside']/wh*100:5.1f}%)")
    print()
