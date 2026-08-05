"""
Simulation: impact of payment-pending fix on DELIVERY deviation for Non-SDD Non-Inventory.

Segment: Non-SDD, Non-Inventory, |delivery deviation| >= 2 days (n ≈ 29,813).

Mechanic:
  1. Compute baseline_gap = median(DATE(pickup_time) - DATE(invoice_create_ts))
     for non-payment-pending orders in this segment.
     (AWB print date = pickup date for Non-Inventory, so this is the AWB-invoice gap.)
  2. For each payment-pending order:
       sim_pickup           = DATE(invoice_create_ts) + baseline_gap
       actual_courier_tat   = (DATE(delivery_attempt_time) - DATE(pickup_time)).days
       new_delivery_attempt = sim_pickup + actual_courier_tat days
       new_dev              = DATE(digitised_delivery_promise) - new_delivery_attempt
  3. Classify new_dev; exits egregious if |new_dev| < 2.

All percentages expressed as % of full segment N.
Reports rescued (exits egregious) and worsened (larger |dev|) separately.
"""

import csv
import statistics
from datetime import date, datetime, timedelta

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


def dev_bucket(d):
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


BUCKET_ORDER = [
    'Early 5d+', 'Early 4d', 'Early 3d', 'Early 2d',
    'Early 1d', 'On-Time', 'Late 1d',
    'Late 2d', 'Late 3d', 'Late 4d', 'Late 5d+',
]

# ── Pass 1: load segment, compute baseline gap ────────────────────────────────
baseline_gaps = []
segment_rows  = []

with open(CSV, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        sdd = row.get('digitised_is_sdd', '').strip().lower()
        inv = row.get('digitised_is_inventory', '').strip().lower()
        if sdd not in ('false', '0', 'no'):
            continue
        if inv not in ('false', '0', 'no'):
            continue

        dlp = to_date(row.get('digitised_delivery_promise', ''))
        da  = to_date(row.get('delivery_attempt_time', ''))
        if not dlp or not da:
            continue
        dev = (dlp - da).days
        if abs(dev) < 2:
            continue

        pk       = to_date(row.get('pickup_time', ''))
        inv_date = to_date(row.get('invoice_create_ts', ''))
        pmt      = row.get('payment_pending_ts', '').strip()

        segment_rows.append({
            'dlp': dlp, 'da': da, 'dev': dev,
            'pk': pk, 'inv_date': inv_date, 'pmt': pmt,
        })

        if not pmt and pk and inv_date:
            baseline_gaps.append((pk - inv_date).days)

N               = len(segment_rows)
baseline_median = int(statistics.median(baseline_gaps)) if baseline_gaps else 0
baseline_mean   = statistics.mean(baseline_gaps) if baseline_gaps else 0

print(f"Non-SDD Non-Inventory egregious n      : {N:,}")
print(f"Non-pmt baseline computed from         : {len(baseline_gaps):,} orders")
print(f"Baseline gap  median                   : {baseline_median} day(s)")
print(f"Baseline gap  mean                     : {baseline_mean:.2f} day(s)")
print()

# ── Pass 2: simulate ──────────────────────────────────────────────────────────
before_full = {b: 0 for b in BUCKET_ORDER}
after_full  = {b: 0 for b in BUCKET_ORDER}
exit_counts = {'Early 1d': 0, 'On-Time': 0, 'Late 1d': 0}

pmt_total   = 0
rescued     = 0
worsened    = 0
improved    = 0
unchanged_n = 0
flipped     = 0  # Early→Late or Late→Early
pmt_skipped = 0

for r in segment_rows:
    old_dev = r['dev']
    before_full[dev_bucket(old_dev)] += 1

    if not r['pmt']:
        after_full[dev_bucket(old_dev)] += 1
        continue

    pmt_total += 1
    pk       = r['pk']
    inv_date = r['inv_date']
    da       = r['da']

    if not pk or not inv_date or not da:
        after_full[dev_bucket(old_dev)] += 1
        pmt_skipped += 1
        continue

    sim_pickup   = inv_date + timedelta(days=baseline_median)
    courier_tat  = (da - pk).days
    new_da       = sim_pickup + timedelta(days=courier_tat)
    new_dev      = (r['dlp'] - new_da).days

    if (old_dev > 0 and new_dev < 0) or (old_dev < 0 and new_dev > 0):
        flipped += 1

    if abs(new_dev) < 2:
        exit_counts[dev_bucket(new_dev)] = exit_counts.get(dev_bucket(new_dev), 0) + 1
        rescued += 1
    else:
        after_full[dev_bucket(new_dev)] += 1
        abs_chg = abs(new_dev) - abs(old_dev)
        if abs_chg > 0:   worsened    += 1
        elif abs_chg < 0: improved    += 1
        else:             unchanged_n += 1

pmt_simulated = pmt_total - pmt_skipped

# ── Output ────────────────────────────────────────────────────────────────────
print(f"Payment-pending in scope               : {pmt_total:,}  ({100*pmt_total/N:.1f}%)")
print(f"  Simulated                            : {pmt_simulated:,}")
print(f"  Skipped (missing dates)              : {pmt_skipped:,}")
print()

print("=" * 72)
print("RESCUE / WORSEN  (pmt-pending orders only, as % of full segment)")
print("=" * 72)
print(f"  Rescued  — exit egregious      : {rescued:>6,}  ({100*rescued/N:.2f}%)")
print(f"  Worsened — deeper into egr.    : {worsened:>6,}  ({100*worsened/N:.2f}%)")
print(f"  Improved — less severe, stay   : {improved:>6,}  ({100*improved/N:.2f}%)")
print(f"  Unchanged severity             : {unchanged_n:>6,}  ({100*unchanged_n/N:.2f}%)")
print(f"  Direction flip (Early↔Late)    : {flipped:>6,}  ({100*flipped/N:.2f}%)")
print()
for b, cnt in exit_counts.items():
    if cnt:
        print(f"    Exit → {b} ✓:  {cnt:,}  ({100*cnt/N:.2f}%)")
print()

# Group-level (includes exits in their classification)
after_incl = dict(after_full)
for b, cnt in exit_counts.items():
    after_incl[b] = after_incl.get(b, 0) + cnt

EARLY_K = ['Early 5d+', 'Early 4d', 'Early 3d', 'Early 2d', 'Early 1d']
OT_K    = ['On-Time']
LATE_K  = ['Late 1d', 'Late 2d', 'Late 3d', 'Late 4d', 'Late 5d+']

print("=" * 72)
print("GROUP-LEVEL SHIFT  (% of full segment, exits included in group)")
print("=" * 72)
hdr = f"{'Group':<12}  {'Before':>9}  {'After':>9}  {'Δ':>8}"
print(hdr); print('-' * len(hdr))
for label, keys in [('Early', EARLY_K), ('On-Time', OT_K), ('Late', LATE_K)]:
    bn = sum(before_full[k] for k in keys)
    an = sum(after_incl.get(k, 0) for k in keys)
    dp = 100*(an - bn)/N
    sign = '+' if dp >= 0 else ''
    print(f"{label:<12}  {100*bn/N:>8.1f}%  {100*an/N:>8.1f}%  {sign}{dp:>6.1f}pp")
print()

print("=" * 72)
print("DAY-LEVEL SHIFT  (% of full segment;  ✓ = exits egregious)")
print("=" * 72)
hdr2 = f"{'Bucket':<14}  {'Before':>9}  {'After':>9}  {'Δ':>9}"
print(hdr2); print('-' * len(hdr2))
for b in BUCKET_ORDER:
    bn = before_full[b]
    an = after_full[b]
    dp = 100*(an - bn)/N
    sign = '+' if dp >= 0 else ''
    print(f"{b:<14}  {100*bn/N:>8.2f}%  {100*an/N:>8.2f}%  {sign}{dp:>7.2f}pp")
for b in ['Early 1d', 'On-Time', 'Late 1d']:
    cnt = exit_counts.get(b, 0)
    if cnt:
        print(f"{b+' ✓':<14}  {'—':>9}  {100*cnt/N:>8.2f}%  +{100*cnt/N:>6.2f}pp")
print()
print(f"Total rescued: {rescued:,} ({100*rescued/N:.2f}% of segment)")
