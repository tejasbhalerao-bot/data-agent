"""
Impact simulation for every root cause across all four segments.

For each identified problem, answers: "If this were fixed, how many orders
would exit the egregious set (|delivery deviation| drops below 2 days)?"

Mechanics per simulation:
  WH fix      : new_del_prom = date(invoice_create_ts + 0.4h) + TAT_days
                TAT_days = ceil(digitised_delivery_tat_mins / 1440) if available,
                else (digitised_delivery_promise - digitised_dispatch_promise).days
  TAT fix     : new_del_prom = actual_pickup + actual_TAT (shows max potential)
  Pmt pending : AWB_sim = invoice_create_ts + 0.4h for pmt-pending orders;
                pickup_sim = date(AWB_sim); delivery_sim = pickup_sim + actual_TAT
  Dr SLA      : AWB_sim = digitised_wh_promise + 25 min; same chain
  SDD elig.   : new_del_prom = actual_pickup + 2d (min non-SDD TAT)

Sections
  A  Non-SDD Non-Inventory  — WH fix;  WH+TAT combined fix
  B  SDD Non-Inventory      — WH fix   (single lever, no TAT layer)
  C  Non-SDD Inventory      — Doctor SLA fix;  HA call SLA fix;  TAT fix
  D  SDD Inventory          — Payment pending fix; Doctor confirm fix; SDD elig fix
"""

import csv
import math
import statistics
from datetime import datetime, timedelta
from collections import Counter

CSV = 'archives/egregiously-miscalibrated-promises/raw-data/all-orders-july-2026.csv'
PMT_NON_BASELINE_H = 0.4   # non-pmt invoice→AWB gap (from analysis #31)
DR_PIPELINE_H      = 25/60 # dr_confirm→invoice→AWB pipeline (~25 min)

# ── helpers ──────────────────────────────────────────────────────────────────

def to_date(s):
    if not s or not s.strip(): return None
    s = s.strip()
    try:    return datetime.fromisoformat(s).date()
    except Exception:
        try: return datetime.strptime(s[:10], '%Y-%m-%d').date()
        except: return None

def to_dt(s):
    if not s or not s.strip(): return None
    s = s.strip()
    try:    return datetime.fromisoformat(s)
    except Exception:
        try: return datetime.strptime(s[:19], '%Y-%m-%d %H:%M:%S')
        except: return None

def is_true(s):
    if s is None: return None
    v = s.strip().lower()
    if v in ('true','1','yes'): return True
    if v in ('false','0','no'): return False
    return None

def tat_days(row):
    """Promised TAT in calendar days from dispatch to delivery."""
    try:
        m = float(row.get('digitised_delivery_tat_mins','') or '')
        if m > 0: return math.ceil(m / 1440)
    except: pass
    dp  = to_date(row.get('digitised_dispatch_promise',''))
    dlp = to_date(row.get('digitised_delivery_promise',''))
    if dp and dlp: return max(0, (dlp - dp).days)
    return None

def del_dev(row):
    """Current delivery deviation in days. Positive = early (del < promise)."""
    dp  = to_date(row.get('digitised_delivery_promise',''))
    da  = to_date(row.get('delivery_attempt_time',''))
    if not dp or not da: return None
    return (dp - da).days

def actual_tat(row):
    pk = to_date(row.get('pickup_time',''))
    da = to_date(row.get('delivery_attempt_time',''))
    if pk and da: return (da - pk).days
    return None

def dev_bucket(d):
    if d is None: return '?'
    if d >= 5:  return 'Early 5d+'
    if d == 4:  return 'Early 4d'
    if d == 3:  return 'Early 3d'
    if d == 2:  return 'Early 2d'
    if d == 1:  return 'Early 1d'
    if d == 0:  return 'On-Time'
    if d == -1: return 'Late 1d'
    if d == -2: return 'Late 2d'
    if d == -3: return 'Late 3d'
    if d == -4: return 'Late 4d'
    return 'Late 5d+'

BUCKET_ORDER = ['Early 5d+','Early 4d','Early 3d','Early 2d','Early 1d',
                'On-Time','Late 1d','Late 2d','Late 3d','Late 4d','Late 5d+','?']


def print_sim(label, base_devs, sim_devs, n_total):
    """Print before/after delivery deviation distributions + rescued count."""
    rescued = sum(1 for d in sim_devs if d is not None and abs(d) < 2)
    currently_egregious = sum(1 for d in base_devs if d is not None and abs(d) >= 2)
    print(f"  → {label}")
    print(f"     Orders in scope            : {len(base_devs):,}")
    print(f"     Currently egregious (≥2d)  : {currently_egregious:,}")
    if currently_egregious == 0:
        print(f"     No egregious orders in scope — skipping")
        print()
        return
    print(f"     Rescued (exit egregious)   : {rescued:,}  ({100*rescued/currently_egregious:.1f}% of in-scope egregious, "
          f"{100*rescued/n_total:.1f}% of all egregious)")
    # before/after distribution
    before = Counter(dev_bucket(d) for d in base_devs)
    after  = Counter(dev_bucket(d) for d in sim_devs)
    print(f"     {'Bucket':<14} {'Before':>8}  {'After':>8}  {'Δ':>6}")
    for b in BUCKET_ORDER:
        bef = before.get(b, 0)
        aft = after.get(b, 0)
        if bef == 0 and aft == 0: continue
        print(f"     {b:<14} {bef:>8,}  {aft:>8,}  {aft-bef:>+6,}")
    print()


# ── Load all rows once ────────────────────────────────────────────────────────
print("Loading data …")
rows_all = []
with open(CSV, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dp  = to_date(row.get('digitised_delivery_promise',''))
        da  = to_date(row.get('delivery_attempt_time',''))
        if not dp or not da: continue
        if abs((dp - da).days) < 2: continue
        rows_all.append(row)

n_all_egregious = len(rows_all)
print(f"Total egregious: {n_all_egregious:,}\n")


# ── Segment rows ─────────────────────────────────────────────────────────────
non_sdd_non_inv = [r for r in rows_all
                   if is_true(r.get('digitised_is_sdd',''))    is False
                   and is_true(r.get('digitised_is_inventory','')) is False]
sdd_non_inv     = [r for r in rows_all
                   if is_true(r.get('digitised_is_sdd',''))    is True
                   and is_true(r.get('digitised_is_inventory','')) is False]
non_sdd_inv     = [r for r in rows_all
                   if is_true(r.get('digitised_is_sdd',''))    is False
                   and is_true(r.get('digitised_is_inventory','')) is True]
sdd_inv         = [r for r in rows_all
                   if is_true(r.get('digitised_is_sdd',''))    is True
                   and is_true(r.get('digitised_is_inventory','')) is True]

print(f"Segments: Non-SDD Non-Inv {len(non_sdd_non_inv):,} | SDD Non-Inv {len(sdd_non_inv):,} | "
      f"Non-SDD Inv {len(non_sdd_inv):,} | SDD Inv {len(sdd_inv):,}\n")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION A — Non-SDD Non-Inventory
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("SECTION A — Non-SDD Non-Inventory (n={:,})".format(len(non_sdd_non_inv)))
print("=" * 70)

# ── A.1  WH promise fix ───────────────────────────────────────────────────────
# Mechanic: dispatch_promise_sim = date(invoice_create_ts + 0.4h)
#           delivery_promise_sim = dispatch_promise_sim + TAT_days
#           new_dev = (delivery_promise_sim - actual_delivery).days
print("A.1 — Simulation: WH promise fix")
print("      dispatch_sim = date(invoice_create_ts + 0.4h)")
print("      delivery_sim = dispatch_sim + TAT_days")

base_A = []; sim_A = []
n_no_inv = 0
for r in non_sdd_non_inv:
    inv = to_dt(r.get('invoice_create_ts',''))
    da  = to_date(r.get('delivery_attempt_time',''))
    td  = tat_days(r)
    cur_dev = del_dev(r)
    if not inv or not da or td is None:
        n_no_inv += 1
        continue
    base_A.append(cur_dev)
    inv_plus = inv + timedelta(hours=PMT_NON_BASELINE_H)
    dispatch_sim = inv_plus.date()
    delivery_sim = dispatch_sim + timedelta(days=td)
    new_dev = (delivery_sim - da).days
    sim_A.append(new_dev)

print(f"  (skipped {n_no_inv} rows with missing invoice/delivery/TAT)")
print_sim("WH promise fix", base_A, sim_A, n_all_egregious)

# ── A.2  WH + TAT combined fix ────────────────────────────────────────────────
# Mechanic: delivery_sim = actual_pickup + actual_TAT → new_dev = 0 for all
# Shows max potential (upper bound)
print("A.2 — Simulation: WH fix + TAT recalibration (combined, max potential)")
print("      delivery_sim = actual_pickup + actual_TAT")

base_A2 = []; sim_A2 = []
for r in non_sdd_non_inv:
    pk  = to_date(r.get('pickup_time',''))
    da  = to_date(r.get('delivery_attempt_time',''))
    at  = actual_tat(r)
    cur_dev = del_dev(r)
    if not pk or not da or at is None: continue
    base_A2.append(cur_dev)
    delivery_sim = pk + timedelta(days=at)
    sim_A2.append((delivery_sim - da).days)   # = 0

print_sim("WH + TAT combined fix", base_A2, sim_A2, n_all_egregious)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION B — SDD Non-Inventory
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("SECTION B — SDD Non-Inventory (n={:,})".format(len(sdd_non_inv)))
print("=" * 70)

# ── B.1  WH promise fix (single lever — no TAT layer) ─────────────────────────
print("B.1 — Simulation: WH promise fix (single lever)")
print("      dispatch_sim = date(invoice_create_ts + 0.4h)")
print("      delivery_sim = dispatch_sim + TAT_days")
print("      (SDD TAT = 0-1d; actual TAT = 0-1d; no stale TAT layer)")

base_B = []; sim_B = []
n_no_inv_B = 0
for r in sdd_non_inv:
    inv = to_dt(r.get('invoice_create_ts',''))
    da  = to_date(r.get('delivery_attempt_time',''))
    td  = tat_days(r)
    cur_dev = del_dev(r)
    if not inv or not da or td is None:
        n_no_inv_B += 1
        continue
    base_B.append(cur_dev)
    dispatch_sim = (inv + timedelta(hours=PMT_NON_BASELINE_H)).date()
    delivery_sim = dispatch_sim + timedelta(days=td)
    sim_B.append((delivery_sim - da).days)

print(f"  (skipped {n_no_inv_B} rows missing invoice/delivery/TAT)")
print_sim("WH promise fix", base_B, sim_B, n_all_egregious)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION C — Non-SDD Inventory
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("SECTION C — Non-SDD Inventory (n={:,})".format(len(non_sdd_inv)))
print("=" * 70)

# Pre-classify Late dispatch orders
late_disp_inv = []
for r in non_sdd_inv:
    dp  = to_date(r.get('digitised_dispatch_promise',''))
    pk  = to_date(r.get('pickup_time',''))
    if dp and pk and pk > dp:
        late_disp_inv.append(r)

late_3plus_inv = []
for r in non_sdd_inv:
    dp  = to_date(r.get('digitised_dispatch_promise',''))
    pk  = to_date(r.get('pickup_time',''))
    if dp and pk and (pk - dp).days >= 3:
        late_3plus_inv.append(r)

print(f"  Late dispatch orders : {len(late_disp_inv):,}")
print(f"  Late 3d+ dispatch    : {len(late_3plus_inv):,}")
print()


# ── C.1  Doctor SLA fix — corrected mechanic (chain-delta preserved) ──────────
# Baseline: digitised_dr_promise (promised doctor call time)
# dr_lag   = dr_confirm_ts − digitised_dr_promise  (how late doctor was)
# delivery_sim = delivery_attempt_time − dr_lag    (shift entire chain back)
# All downstream deltas (awb→pickup→delivery) preserved exactly.
# Only orders with dr_lag > 0 are in scope (on-time confirmations unaffected).
print("C.1 — Simulation: Doctor SLA fix (chain-delta preserved, v2)")
print("      dr_lag = dr_confirm_ts − digitised_dr_promise")
print("      delivery_sim = delivery_attempt_time − dr_lag")

base_C1 = []; sim_C1 = []; n_scope_C1 = 0
for r in late_disp_inv:
    cat = r.get('digitised_order_category','').strip()
    if 'DOCTOR_AND_HA_CALL' not in cat and 'HA_CALL_REQUIRED' not in cat:
        continue
    dr_p  = to_dt(r.get('digitised_dr_promise',''))
    conf  = to_dt(r.get('dr_confirm_ts',''))
    if not conf or not dr_p or conf <= dr_p:
        continue   # doctor confirmed on time — unaffected
    da_dt = to_dt(r.get('delivery_attempt_time',''))
    dlp   = to_date(r.get('digitised_delivery_promise',''))
    if not da_dt or not dlp:
        continue
    n_scope_C1 += 1
    cur_dev = del_dev(r)
    base_C1.append(cur_dev)
    dr_lag = conf - dr_p                        # timedelta (hours/minutes)
    delivery_sim_dt = da_dt - dr_lag            # shift whole chain back
    sim_C1.append((dlp - delivery_sim_dt.date()).days)

print(f"  Scope: {n_scope_C1:,} call-required late-dispatch orders with late dr_confirm")
print_sim("Doctor SLA fix", base_C1, sim_C1, n_all_egregious)


# ── C.2  HA call SLA fix — corrected mechanic (chain-delta preserved) ─────────
# Baseline: HA call completes on same calendar day as dr_confirm_ts.
# ha_excess = DATE(invoice_create_ts) − DATE(dr_confirm_ts)  (days bled over)
# delivery_sim = delivery_attempt_time − ha_excess days
# Orders where ha_excess = 0 (same-day HA call) are already at baseline — excluded.
print("C.2 — Simulation: HA call SLA fix (same-day completion, chain-delta preserved, v2)")
print("      ha_excess = DATE(invoice_create_ts) − DATE(dr_confirm_ts) in days")
print("      delivery_sim = delivery_attempt_time − ha_excess days")

base_C2 = []; sim_C2 = []; n_scope_C2 = 0
for r in late_3plus_inv:
    cat = r.get('digitised_order_category','').strip()
    if 'DOCTOR_AND_HA_CALL' not in cat and 'HA_CALL' not in cat:
        continue
    conf_d  = to_date(r.get('dr_confirm_ts',''))
    inv_d   = to_date(r.get('invoice_create_ts',''))
    da_dt   = to_dt(r.get('delivery_attempt_time',''))
    dlp     = to_date(r.get('digitised_delivery_promise',''))
    if not conf_d or not inv_d or not da_dt or not dlp:
        continue
    ha_excess = (inv_d - conf_d).days
    if ha_excess <= 0:
        continue  # HA call completed same day — already at baseline
    n_scope_C2 += 1
    cur_dev = del_dev(r)
    base_C2.append(cur_dev)
    delivery_sim_dt = da_dt - timedelta(days=ha_excess)
    sim_C2.append((dlp - delivery_sim_dt.date()).days)

print(f"  Scope: {n_scope_C2:,} Late 3d+ HA-involved orders with HA call crossing a day boundary")
print_sim("HA call SLA fix", base_C2, sim_C2, n_all_egregious)


# ── C.3  TAT recalibration (all Non-SDD Inv egregious) ───────────────────────
# Option 1: use shipping_delivery_promise as TAT from actual_pickup
# Option 2: perfect recalibration (delivery_sim = actual_pickup + actual_TAT → dev = 0)
print("C.3 — Simulation: TAT recalibration")

# Option 1: Shipping-based promise
print("  C.3a — Using shipping_delivery_promise as new TAT anchor")
print("         delivery_sim = actual_pickup + shipping_delivery_promise (in days)")
base_C3a = []; sim_C3a = []
for r in non_sdd_inv:
    pk  = to_date(r.get('pickup_time',''))
    da  = to_date(r.get('delivery_attempt_time',''))
    dlp = to_date(r.get('digitised_delivery_promise',''))
    try:
        ship_days = int(float(r.get('shipping_delivery_promise','') or ''))
    except:
        ship_days = None
    if not pk or not da or not dlp or ship_days is None:
        continue
    base_C3a.append((dlp - da).days)
    delivery_sim = pk + timedelta(days=ship_days)
    sim_C3a.append((delivery_sim - da).days)

print_sim("TAT recalibration (shipping-based)", base_C3a, sim_C3a, n_all_egregious)

# Option 2: Perfect recalibration
print("  C.3b — Perfect recalibration (delivery_sim = actual_pickup + actual_TAT)")
base_C3b = []; sim_C3b = []
for r in non_sdd_inv:
    pk  = to_date(r.get('pickup_time',''))
    da  = to_date(r.get('delivery_attempt_time',''))
    dlp = to_date(r.get('digitised_delivery_promise',''))
    at  = actual_tat(r)
    if not pk or not da or not dlp or at is None:
        continue
    base_C3b.append((dlp - da).days)
    delivery_sim = pk + timedelta(days=at)
    sim_C3b.append((delivery_sim - da).days)  # = 0

print_sim("TAT recalibration (perfect)", base_C3b, sim_C3b, n_all_egregious)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION D — SDD Inventory
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("SECTION D — SDD Inventory (n={:,})".format(len(sdd_inv)))
print("=" * 70)

# Classify subgroups
late_wh_late_del  = []
early_wh_late_del = []
for r in sdd_inv:
    wh  = to_dt(r.get('digitised_wh_promise',''))
    awb = to_dt(r.get('awb_sticker_printed_ts',''))
    dlp = to_date(r.get('digitised_delivery_promise',''))
    da  = to_date(r.get('delivery_attempt_time',''))
    if not wh or not awb or not dlp or not da: continue
    wh_late  = awb > wh
    del_late = da > dlp
    if wh_late and del_late:
        late_wh_late_del.append(r)
    elif not wh_late and del_late:
        early_wh_late_del.append(r)

print(f"  Mode 1 (Late WH + Late Del) : {len(late_wh_late_del):,}")
print(f"  Mode 2 (Early WH + Late Del): {len(early_wh_late_del):,}")
print()


# ── D.1  Payment pending fix (Mode 1) ─────────────────────────────────────────
print("D.1 — Simulation: Payment pending fix (Mode 1 — Late WH Late Delivery)")
print("      For pmt-pending orders: AWB_sim = invoice + 0.4h")
print("      pickup_sim = date(AWB_sim); delivery_sim = pickup_sim + actual_TAT")

base_D1 = []; sim_D1 = []
n_pmt = 0
for r in late_wh_late_del:
    dlp = to_date(r.get('digitised_delivery_promise',''))
    da  = to_date(r.get('delivery_attempt_time',''))
    at  = actual_tat(r)
    cur_dev = del_dev(r)
    if not dlp or not da or at is None: continue
    base_D1.append(cur_dev)
    pmt_ts = r.get('payment_pending_ts','').strip()
    inv = to_dt(r.get('invoice_create_ts',''))
    if pmt_ts and inv:
        n_pmt += 1
        awb_sim = inv + timedelta(hours=PMT_NON_BASELINE_H)
        pk_sim  = awb_sim.date()
        del_sim = pk_sim + timedelta(days=at)
        sim_D1.append((dlp - del_sim).days)
    else:
        sim_D1.append(cur_dev)   # unchanged

print(f"  Payment-pending orders in scope: {n_pmt:,}")
print_sim("Payment pending fix (Mode 1)", base_D1, sim_D1, n_all_egregious)


# ── D.2  Doctor confirmation fix (Mode 1) ─────────────────────────────────────
print("D.2 — Simulation: Doctor confirmation fix (Mode 1 — Late WH Late Delivery)")
print("      For late-dr-confirm orders: AWB_sim = digitised_wh_promise + 25min")
print("      pickup_sim = date(AWB_sim); delivery_sim = pickup_sim + actual_TAT")

base_D2 = []; sim_D2 = []
n_late_conf = 0
for r in late_wh_late_del:
    wh  = to_dt(r.get('digitised_wh_promise',''))
    conf = to_dt(r.get('dr_confirm_ts',''))
    dlp = to_date(r.get('digitised_delivery_promise',''))
    da  = to_date(r.get('delivery_attempt_time',''))
    at  = actual_tat(r)
    cur_dev = del_dev(r)
    if not dlp or not da or at is None: continue
    base_D2.append(cur_dev)
    if wh and conf and conf > wh:
        n_late_conf += 1
        awb_sim = wh + timedelta(hours=DR_PIPELINE_H)
        pk_sim  = awb_sim.date()
        del_sim = pk_sim + timedelta(days=at)
        sim_D2.append((dlp - del_sim).days)
    else:
        sim_D2.append(cur_dev)

print(f"  Late-confirmation orders in scope: {n_late_conf:,}")
print_sim("Doctor confirmation fix (Mode 1)", base_D2, sim_D2, n_all_egregious)


# ── D.3  Combined Mode 1 fix (pmt pending + doctor confirmation) ──────────────
print("D.3 — Simulation: Combined Mode 1 fix (payment pending AND doctor confirmation)")
print("      Apply both: whichever applies first, then the other")

base_D3 = []; sim_D3 = []
for r in late_wh_late_del:
    wh  = to_dt(r.get('digitised_wh_promise',''))
    conf = to_dt(r.get('dr_confirm_ts',''))
    dlp = to_date(r.get('digitised_delivery_promise',''))
    da  = to_date(r.get('delivery_attempt_time',''))
    at  = actual_tat(r)
    cur_dev = del_dev(r)
    inv = to_dt(r.get('invoice_create_ts',''))
    pmt_ts = r.get('payment_pending_ts','').strip()
    if not dlp or not da or at is None: continue
    base_D3.append(cur_dev)

    # Determine simulated AWB
    awb_sim = None
    if pmt_ts and inv:
        awb_sim = inv + timedelta(hours=PMT_NON_BASELINE_H)
    elif wh and conf and conf > wh:
        awb_sim = wh + timedelta(hours=DR_PIPELINE_H)

    if awb_sim:
        pk_sim  = awb_sim.date()
        del_sim = pk_sim + timedelta(days=at)
        sim_D3.append((dlp - del_sim).days)
    else:
        sim_D3.append(cur_dev)

print_sim("Combined Mode 1 fix", base_D3, sim_D3, n_all_egregious)


# ── D.4  SDD eligibility fix (Mode 2) ────────────────────────────────────────
print("D.4 — Simulation: SDD eligibility fix (Mode 2 — Early WH + Late Delivery)")
print("      Reconfigure these orders to 2-day non-SDD TAT promise:")
print("      delivery_promise_sim = actual_pickup + 2d")

base_D4 = []; sim_D4 = []
for r in early_wh_late_del:
    pk  = to_date(r.get('pickup_time',''))
    da  = to_date(r.get('delivery_attempt_time',''))
    dlp = to_date(r.get('digitised_delivery_promise',''))
    cur_dev = del_dev(r)
    if not pk or not da or not dlp: continue
    base_D4.append(cur_dev)
    delivery_promise_sim = pk + timedelta(days=2)
    sim_D4.append((delivery_promise_sim - da).days)

print_sim("SDD eligibility fix (Mode 2)", base_D4, sim_D4, n_all_egregious)


# ── D.5  Full SDD Inventory fix (Modes 1+2 combined) ─────────────────────────
print("D.5 — Simulation: Full fix — Mode 1 (combined) + Mode 2 (SDD eligibility)")

base_D5 = []; sim_D5 = []

for r in late_wh_late_del:
    wh  = to_dt(r.get('digitised_wh_promise',''))
    conf = to_dt(r.get('dr_confirm_ts',''))
    dlp = to_date(r.get('digitised_delivery_promise',''))
    da  = to_date(r.get('delivery_attempt_time',''))
    at  = actual_tat(r)
    inv = to_dt(r.get('invoice_create_ts',''))
    pmt_ts = r.get('payment_pending_ts','').strip()
    cur_dev = del_dev(r)
    if not dlp or not da or at is None: continue
    base_D5.append(cur_dev)
    awb_sim = None
    if pmt_ts and inv:
        awb_sim = inv + timedelta(hours=PMT_NON_BASELINE_H)
    elif wh and conf and conf > wh:
        awb_sim = wh + timedelta(hours=DR_PIPELINE_H)
    if awb_sim:
        pk_sim  = awb_sim.date()
        sim_D5.append((dlp - (pk_sim + timedelta(days=at))).days)
    else:
        sim_D5.append(cur_dev)

for r in early_wh_late_del:
    pk  = to_date(r.get('pickup_time',''))
    da  = to_date(r.get('delivery_attempt_time',''))
    dlp = to_date(r.get('digitised_delivery_promise',''))
    cur_dev = del_dev(r)
    if not pk or not da or not dlp: continue
    base_D5.append(cur_dev)
    sim_D5.append(((pk + timedelta(days=2)) - da).days)

print_sim("Full SDD Inventory fix (Mode 1 + Mode 2)", base_D5, sim_D5, n_all_egregious)

print("=" * 70)
print("Done.")
