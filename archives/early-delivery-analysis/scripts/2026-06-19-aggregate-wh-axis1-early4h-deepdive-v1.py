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
    v=(s or "").strip().lower()
    return True if v in("true","1") else False if v in("false","0") else None
def whtype(s):
    m=tern(s); return "MFC" if m else "FC" if m is False else "Unknown"
def inv_d(s):
    di=tern(s); return "inventory" if di else "non-inventory" if di is False else "unknown"
def inv_chg(d,s):
    di,si=tern(d),tern(s)
    if di is None or si is None: return "unknown"
    if di and si: return "inv->inv"
    if not di and not si: return "non->non"
    return "inv->non-inv" if di and not si else "non-inv->inv"

seen=set()
coh=defaultdict(lambda: {"type":defaultdict(int),"inv":defaultdict(int),"chg":defaultdict(int),"n":0})
# coh["all"], coh["bucket"]
nested_invtype=defaultdict(int)   # bucket: (inv,type)
nested_chgtype=defaultdict(int)   # bucket: (chg,type)
N_all=N_bkt=0
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
    t=whtype(row["digitised_is_mfc"]); iv=inv_d(row["digitised_is_inventory"])
    cg=inv_chg(row["digitised_is_inventory"],row["shipping_is_inventory"])
    for key in ("all",):
        coh[key]["type"][t]+=1; coh[key]["inv"][iv]+=1; coh[key]["chg"][cg]+=1; coh[key]["n"]+=1
    N_all+=1
    if promised-actual>=240:   # Early >4h bucket
        N_bkt+=1
        coh["bucket"]["type"][t]+=1; coh["bucket"]["inv"][iv]+=1; coh["bucket"]["chg"][cg]+=1; coh["bucket"]["n"]+=1
        nested_invtype[(iv,t)]+=1
        nested_chgtype[(cg,t)]+=1

print(f"COHORT n={N_all} | Early>4h bucket n={N_bkt}  ({N_bkt/N_all*100:.1f}% of cohort)\n")

def comp(title, dim, keys):
    print(f"=== {title} — composition of the >4h-early bucket ===")
    print(f"  {'segment':>16} {'bkt_n':>8} {'%ofBkt':>7} {'%ofCohort':>10} {'index':>6}")
    tb=tc=0
    for k in keys:
        b=coh['bucket'][dim].get(k,0); c=coh['all'][dim].get(k,0)
        tb+=b; tc+=c
        bp=b/N_bkt*100; cp=c/N_all*100
        idx=bp/cp if cp else 0
        print(f"  {k:>16} {b:>8d} {bp:6.1f}% {cp:9.1f}% {idx:5.2f}x")
    print(f"  {'TOTAL':>16} {tb:>8d} {tb/N_bkt*100:6.1f}% {tc/N_all*100:9.1f}%   [n {'OK' if tb==N_bkt else 'BAD'}]")
    print()

comp("Q2  WH type (FC vs MFC)","type",["FC","MFC","Unknown"])
comp("Q3a Inventory @ digitisation","inv",["inventory","non-inventory","unknown"])

print("=== Q3b  inventory x WH type, WITHIN the >4h-early bucket ===")
print(f"  {'inv_state':>16} {'FC':>8} {'FC%':>6} {'MFC':>8} {'MFC%':>6} {'Unk':>6} {'row_n':>8}")
for iv in ["inventory","non-inventory","unknown"]:
    fc=nested_invtype.get((iv,"FC"),0); mfc=nested_invtype.get((iv,"MFC"),0); un=nested_invtype.get((iv,"Unknown"),0)
    rn=fc+mfc+un
    if rn==0: continue
    print(f"  {iv:>16} {fc:>8d} {fc/rn*100:5.1f}% {mfc:>8d} {mfc/rn*100:5.1f}% {un:>6d} {rn:>8d}")
print()

comp("Q4  Inventory change digi->ship","chg",["inv->inv","non->non","inv->non-inv","non-inv->inv","unknown"])

print("=== Q4b  inventory-change x WH type, WITHIN the >4h-early bucket ===")
print(f"  {'change':>16} {'FC':>8} {'FC%':>6} {'MFC':>8} {'MFC%':>6} {'Unk':>6} {'row_n':>8}")
for cg in ["inv->inv","non->non","inv->non-inv","non-inv->inv","unknown"]:
    fc=nested_chgtype.get((cg,"FC"),0); mfc=nested_chgtype.get((cg,"MFC"),0); un=nested_chgtype.get((cg,"Unknown"),0)
    rn=fc+mfc+un
    if rn==0: continue
    print(f"  {cg:>16} {fc:>8d} {fc/rn*100:5.1f}% {mfc:>8d} {mfc/rn*100:5.1f}% {un:>6d} {rn:>8d}")
