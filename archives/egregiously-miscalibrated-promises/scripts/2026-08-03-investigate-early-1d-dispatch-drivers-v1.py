"""
Early 1d dispatch deviation — driver investigation.
Non-SDD Inventory egregious superset (n=57,688).
Cohort: dispatch_dev = +1 (pickup 1 calendar day before dispatch promise).

Known: 98.7% AWB 1d before dispatch promise; courier picks up same day as AWB.
Unknown: Is the D+1 gap structural (formula: dispatch_promise = wh_promise + 1)?
         Or does WH genuinely pack a full calendar day before wh_promise?

Parts:
  1. dispatch_promise - wh_promise gap in calendar days (Early 1d vs On-Time)
  2. awb_date vs wh_promise in calendar days (Early 1d vs On-Time)
  3. Counterfactual: if dispatch_promise = wh_promise (no D+1 buffer), how many
     Early 1d orders become On-Time?
  4. Residual early orders after formula fix -- what is their WH deviation?
  5. Couriers where D+1 pickup is genuine (pickup_date = awb_date + 1)
"""

import csv
import statistics
from datetime import datetime

CSV = 'archives/egregiously-miscalibrated-promises/raw-data/all-orders-july-2026.csv'


def to_date(s):
    if not s or not s.strip():
        return None
    s = s.strip()
    if len(s) < 10:
        return None
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        try:
            return datetime.strptime(s[:10], '%Y-%m-%d').date()
        except Exception:
            return None


def to_dt(s):
    if not s or not s.strip():
        return None
    s = s.strip()
    if len(s) < 10:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        try:
            return datetime.strptime(s[:19], '%Y-%m-%d %H:%M:%S')
        except Exception:
            return None


def is_true_str(s):
    if s is None:
        return None
    v = s.strip().lower()
    if v in ('true', '1', 'yes'):
        return True
    if v in ('false', '0', 'no'):
        return False
    return None


early1d = []
ontime  = []

with open(CSV, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        del_prom = to_date(row.get('digitised_delivery_promise', ''))
        del_att  = to_date(row.get('delivery_attempt_time', ''))
        if not del_prom or not del_att:
            continue
        if abs((del_prom - del_att).days) < 2:
            continue
        if is_true_str(row.get('digitised_is_sdd', '')) is not False:
            continue
        if is_true_str(row.get('digitised_is_inventory', '')) is not True:
            continue

        disp_prom = to_date(row.get('digitised_dispatch_promise', ''))
        pickup    = to_date(row.get('pickup_time', ''))
        if not disp_prom or not pickup:
            continue

        dev = (disp_prom - pickup).days
        if dev == 1:
            early1d.append(dict(row))
        elif dev == 0:
            ontime.append(dict(row))

print(f"Early 1d cohort : {len(early1d):,}")
print(f"On-Time cohort  : {len(ontime):,}")
print()


# -- Part 1: dispatch_promise - wh_promise gap ----------------------------
print("=" * 70)
print("PART 1 -- dispatch_promise - wh_promise gap (calendar days)")
print("  Positive = dispatch promise is N days AFTER WH promise")
print("=" * 70)

def dp_wh_gap(orders):
    d = {}
    missing = 0
    for r in orders:
        dp = to_date(r.get('digitised_dispatch_promise', ''))
        wh = to_date(r.get('digitised_wh_promise', ''))
        if not dp or not wh:
            missing += 1
            continue
        diff = (dp - wh).days
        k = str(diff) if -2 <= diff <= 5 else ('>5' if diff > 5 else '<-2')
        d[k] = d.get(k, 0) + 1
    return d, missing

e_gap, e_miss = dp_wh_gap(early1d)
o_gap, o_miss = dp_wh_gap(ontime)

all_keys = sorted(
    set(list(e_gap.keys()) + list(o_gap.keys())),
    key=lambda x: int(x) if x.lstrip('-').isdigit() else 99
)

hdr = f"{'Gap (days)':<12}  {'Early1d n':>9}  {'Early1d %':>10}  {'OnTime n':>9}  {'OnTime %':>10}"
print(hdr)
print('-' * len(hdr))
for k in all_keys:
    en = e_gap.get(k, 0)
    on = o_gap.get(k, 0)
    print(f"{k:<12}  {en:>9,}  {100*en/len(early1d):>9.1f}%  {on:>9,}  {100*on/len(ontime):>9.1f}%")
print(f"  Missing Early 1d: {e_miss}, Missing On-Time: {o_miss}")
print()


# -- Part 2: awb_date vs wh_promise (calendar days) -----------------------
print("=" * 70)
print("PART 2 -- awb_date vs wh_promise (calendar days)")
print("  wh_promise - awb_date: positive = AWB printed before wh promise (WH early)")
print("=" * 70)

def awb_wh_gap(orders):
    d = {}
    missing = 0
    for r in orders:
        wh  = to_date(r.get('digitised_wh_promise', ''))
        awb = to_dt(r.get('awb_sticker_printed_ts', ''))
        if not wh or not awb:
            missing += 1
            continue
        diff = (wh - awb.date()).days
        if diff >= 3:
            k = 'Early 3d+'
        elif diff == 2:
            k = 'Early 2d'
        elif diff == 1:
            k = 'Early 1d'
        elif diff == 0:
            k = 'On-Time'
        elif diff == -1:
            k = 'Late 1d'
        elif diff == -2:
            k = 'Late 2d'
        else:
            k = 'Late 3d+'
        d[k] = d.get(k, 0) + 1
    return d, missing

WH_ORDER = ['Early 3d+', 'Early 2d', 'Early 1d', 'On-Time', 'Late 1d', 'Late 2d', 'Late 3d+']
e_awb, e_awb_miss = awb_wh_gap(early1d)
o_awb, o_awb_miss = awb_wh_gap(ontime)

hdr2 = f"{'WH deviation':<14}  {'Early1d n':>9}  {'Early1d %':>10}  {'OnTime n':>9}  {'OnTime %':>10}"
print(hdr2)
print('-' * len(hdr2))
for k in WH_ORDER:
    en = e_awb.get(k, 0)
    on = o_awb.get(k, 0)
    if en == 0 and on == 0:
        continue
    print(f"{k:<14}  {en:>9,}  {100*en/len(early1d):>9.1f}%  {on:>9,}  {100*on/len(ontime):>9.1f}%")
print(f"  Missing Early 1d: {e_awb_miss}, Missing On-Time: {o_awb_miss}")
print()


# -- Part 3: Counterfactual -- dispatch_promise := wh_promise -------------
print("=" * 70)
print("PART 3 -- Counterfactual: simulated_dispatch_promise = wh_promise")
print("  sim_dispatch_dev = wh_promise - pickup_date")
print("=" * 70)

def sim_bucket(days):
    if days >= 2: return 'Early 2d+'
    if days == 1: return 'Early 1d'
    if days == 0: return 'On-Time'
    if days == -1: return 'Late 1d'
    return 'Late 2d+'

sim_dist = {}
missing_sim = 0
for r in early1d:
    wh     = to_date(r.get('digitised_wh_promise', ''))
    pickup = to_date(r.get('pickup_time', ''))
    if not wh or not pickup:
        missing_sim += 1
        continue
    sim_dev = (wh - pickup).days
    k = sim_bucket(sim_dev)
    sim_dist[k] = sim_dist.get(k, 0) + 1

SIM_ORDER = ['Early 2d+', 'Early 1d', 'On-Time', 'Late 1d', 'Late 2d+']
effective = len(early1d) - missing_sim

hdr3 = f"{'Simulated bucket':<16}  {'n':>8}  {'% of Early1d':>14}"
print(hdr3)
print('-' * len(hdr3))
for k in SIM_ORDER:
    n = sim_dist.get(k, 0)
    if n == 0:
        continue
    print(f"{k:<16}  {n:>8,}  {100*n/effective:>13.1f}%")
print(f"  Effective n: {effective:,}  Missing: {missing_sim}")
print()


# -- Part 4: Residual -- orders still early after formula fix -------------
print("=" * 70)
print("PART 4 -- Residual: Early 1d orders that stay early after formula fix")
print("  (sim_dev >= 1 means WH was also packed a full calendar day before pickup)")
print("=" * 70)

residual = []
for r in early1d:
    wh     = to_date(r.get('digitised_wh_promise', ''))
    pickup = to_date(r.get('pickup_time', ''))
    if not wh or not pickup:
        continue
    if (wh - pickup).days >= 1:
        residual.append(r)

print(f"Residual (sim_dev >= 1): {len(residual):,} of {effective:,} ({100*len(residual)/effective:.1f}%)")
print()

if residual:
    print("WH deviation for residual (awb_date vs wh_promise, calendar days):")
    r_awb, _ = awb_wh_gap(residual)
    hdr4 = f"{'WH deviation':<14}  {'n':>8}  {'%':>8}"
    print(hdr4)
    print('-' * len(hdr4))
    for k in WH_ORDER:
        n = r_awb.get(k, 0)
        if n == 0:
            continue
        print(f"{k:<14}  {n:>8,}  {100*n/len(residual):>7.1f}%")
    print()

    # For residual: what is dispatch_promise - wh_promise?
    print("dispatch_promise - wh_promise for residual:")
    r_gap, _ = dp_wh_gap(residual)
    hdr4b = f"{'Gap (days)':<12}  {'n':>8}  {'%':>8}"
    print(hdr4b)
    print('-' * len(hdr4b))
    for k in sorted(r_gap.keys(), key=lambda x: int(x) if x.lstrip('-').isdigit() else 99):
        n = r_gap.get(k, 0)
        print(f"{k:<12}  {n:>8,}  {100*n/len(residual):>7.1f}%")


# -- Part 5: Courier D+1 pickup rate (On-Time baseline) ------------------
print()
print("=" * 70)
print("PART 5 -- Courier pickup lag: % same-day vs D+1 vs D+2+ in On-Time cohort")
print("=" * 70)

courier_stats = {}
for r in ontime:
    awb    = to_dt(r.get('awb_sticker_printed_ts', ''))
    pickup = to_date(r.get('pickup_time', ''))
    if not awb or not pickup:
        continue
    lag = (pickup - awb.date()).days
    c = r.get('digitised_delivery_partner', '').strip() or 'UNKNOWN'
    if c not in courier_stats:
        courier_stats[c] = {'total': 0, 'same_day': 0, 'd1': 0, 'd2plus': 0}
    courier_stats[c]['total'] += 1
    if lag == 0:
        courier_stats[c]['same_day'] += 1
    elif lag == 1:
        courier_stats[c]['d1'] += 1
    else:
        courier_stats[c]['d2plus'] += 1

# Overall summary
total_ot = sum(s['total'] for s in courier_stats.values())
total_sd = sum(s['same_day'] for s in courier_stats.values())
total_d1 = sum(s['d1'] for s in courier_stats.values())
total_d2 = sum(s['d2plus'] for s in courier_stats.values())
print(f"Overall On-Time (n={total_ot:,}): same-day {100*total_sd/total_ot:.1f}%  "
      f"D+1 {100*total_d1/total_ot:.1f}%  D+2+ {100*total_d2/total_ot:.1f}%")
print()

couriers = sorted(
    [(c, s) for c, s in courier_stats.items() if s['total'] >= 100],
    key=lambda x: -x[1]['total']
)

hdr5 = f"{'Courier':<28}  {'n':>7}  {'Same-day':>9}  {'D+1':>7}  {'D+2+':>7}"
print(hdr5)
print('-' * len(hdr5))
for c, s in couriers[:20]:
    t = s['total']
    print(
        f"{c:<28}  {t:>7,}  {100*s['same_day']/t:>8.1f}%  "
        f"{100*s['d1']/t:>6.1f}%  {100*s['d2plus']/t:>6.1f}%"
    )
