"""
Simulation: combined E.1 + E.2 fix for Non-SDD Non-Inventory segment.

E.1 (WH Promise Calibration) — applied to ALL orders:
  new_promise = DATE(invoice_create_ts + 0.4h) + (delivery_promise - dispatch_promise).days
  This recalibrates the delivery promise as if dispatch had been based on invoice timing
  (goods confirmed ready) rather than the procurement-lag assumption in the WH promise.

E.2 (Payment Pending) — applied to pmt-pending orders ON TOP OF E.1:
  sim_pickup           = DATE(invoice_create_ts) + 0 days  [baseline gap = 0 for Non-Inv]
  sim_delivery_attempt = sim_pickup + (actual_delivery - actual_pickup).days
  For non-pmt orders: sim_delivery_attempt = actual_delivery (unchanged).

new_dev = new_promise - sim_delivery_attempt
An order exits egregious if |new_dev| < 2.

All percentages expressed as % of full segment N (29,813).
Both group-level and day-level shifts are reported.
"""

import csv
import statistics
from datetime import datetime, timedelta

CSV = 'archives/egregiously-miscalibrated-promises/raw-data/all-orders-july-2026.csv'

NON_PMT_BASELINE_HOURS = 0.4  # same offset used in E.1


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


def to_date(s):
    dt = to_dt(s)
    return dt.date() if dt else None


def dev_bucket(d):
    if d >= 5:   return 'Early 5d+'
    if d == 4:   return 'Early 4d'
    if d == 3:   return 'Early 3d'
    if d == 2:   return 'Early 2d'
    if d == 1:   return 'Early 1d'
    if d == 0:   return 'On-Time'
    if d == -1:  return 'Late 1d'
    if d == -2:  return 'Late 2d'
    if d == -3:  return 'Late 3d'
    if d == -4:  return 'Late 4d'
    return 'Late 5d+'


BUCKET_ORDER = [
    'Early 5d+', 'Early 4d', 'Early 3d', 'Early 2d',
    'Early 1d', 'On-Time', 'Late 1d',
    'Late 2d', 'Late 3d', 'Late 4d', 'Late 5d+',
]

# ── Pass 1: load segment, compute baseline gap for pmt ────────────────────────
segment_rows  = []
baseline_gaps = []

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
        inv_ts   = to_dt(row.get('invoice_create_ts', ''))
        ddp      = to_date(row.get('digitised_dispatch_promise', ''))
        pmt      = row.get('payment_pending_ts', '').strip()

        segment_rows.append({
            'dlp': dlp, 'da': da, 'dev': dev,
            'pk': pk, 'inv_ts': inv_ts, 'ddp': ddp, 'pmt': pmt,
        })

        # baseline gap: pct of non-pmt orders with pickup on same day as invoice
        if not pmt and pk and inv_ts:
            baseline_gaps.append((pk - inv_ts.date()).days)

N               = len(segment_rows)
baseline_median = int(statistics.median(baseline_gaps)) if baseline_gaps else 0

print(f"Non-SDD Non-Inventory egregious n      : {N:,}")
print(f"Non-pmt baseline from                  : {len(baseline_gaps):,} orders")
print(f"Baseline gap median                    : {baseline_median} day(s)")
print()

# ── Pass 2: simulate ──────────────────────────────────────────────────────────
before_full = {b: 0 for b in BUCKET_ORDER}
after_full  = {b: 0 for b in BUCKET_ORDER}
exit_counts = {}  # bucket → n exits (non-egregious after sim)

total_skipped   = 0
pmt_total       = 0
pmt_skipped     = 0

# Track combined-specific stats vs E.1-alone
e1_rescued_also  = 0  # rescued by E.1 alone AND by combined
combined_extra   = 0  # rescued by combined but NOT by E.1 alone
combined_missed  = 0  # rescued by E.1 alone but NOT by combined (pmt only)
rescued_total    = 0
worsened         = 0  # |new_dev| > |old_dev| and still egregious

for r in segment_rows:
    old_dev = r['dev']
    before_full[dev_bucket(old_dev)] += 1

    dlp    = r['dlp']
    da     = r['da']
    pk     = r['pk']
    inv_ts = r['inv_ts']
    ddp    = r['ddp']
    pmt    = r['pmt']

    # E.1 requires inv_ts and ddp
    if not inv_ts or not ddp:
        after_full[dev_bucket(old_dev)] += 1
        total_skipped += 1
        continue

    # E.1: recalibrate delivery promise
    e1_dispatch_sim = (inv_ts + timedelta(hours=NON_PMT_BASELINE_HOURS)).date()
    promised_tat    = (dlp - ddp).days
    new_promise     = e1_dispatch_sim + timedelta(days=promised_tat)

    if not pmt:
        # Non-pmt: E.1 only; actual delivery unchanged
        sim_da  = da
        new_dev = (new_promise - sim_da).days
    else:
        pmt_total += 1
        if not pk or not da:
            # Can't simulate E.2; fall back to E.1 only
            sim_da  = da
            new_dev = (new_promise - sim_da).days
            pmt_skipped += 1
        else:
            # E.2: simulate pickup on invoice day
            sim_pickup  = e1_dispatch_sim + timedelta(days=baseline_median)
            courier_tat = (da - pk).days
            sim_da      = sim_pickup + timedelta(days=courier_tat)
            new_dev     = (new_promise - sim_da).days

    # Compare with E.1-alone result for pmt orders (for diagnostic breakdown)
    if pmt and pk and da and inv_ts and ddp:
        e1_dev_alone = (new_promise - da).days
        if abs(e1_dev_alone) < 2 and abs(new_dev) < 2:
            e1_rescued_also += 1
        elif abs(e1_dev_alone) >= 2 and abs(new_dev) < 2:
            combined_extra += 1
        elif abs(e1_dev_alone) < 2 and abs(new_dev) >= 2:
            combined_missed += 1

    if abs(new_dev) < 2:
        rescued_total += 1
        b = dev_bucket(new_dev)
        exit_counts[b] = exit_counts.get(b, 0) + 1
    else:
        after_full[dev_bucket(new_dev)] += 1
        if abs(new_dev) > abs(old_dev):
            worsened += 1

# ── After-including exits ─────────────────────────────────────────────────────
after_incl = dict(after_full)
for b, cnt in exit_counts.items():
    after_incl[b] = after_incl.get(b, 0) + cnt

EARLY_K = ['Early 5d+', 'Early 4d', 'Early 3d', 'Early 2d', 'Early 1d']
OT_K    = ['On-Time']
LATE_K  = ['Late 1d', 'Late 2d', 'Late 3d', 'Late 4d', 'Late 5d+']

# ── Output ────────────────────────────────────────────────────────────────────
print(f"Skipped (missing inv_ts or ddp)        : {total_skipped:,}")
print(f"Payment-pending in segment             : {pmt_total:,}  ({100*pmt_total/N:.1f}%)")
print(f"  Pmt skipped (missing pk/da)          : {pmt_skipped:,}")
print()

print("=" * 72)
print("RESCUE SUMMARY  (as % of full segment)")
print("=" * 72)
print(f"  Total rescued — exit egregious : {rescued_total:>6,}  ({100*rescued_total/N:.2f}%)")
print(f"  Worsened — deeper into egr.    : {worsened:>6,}  ({100*worsened/N:.2f}%)")
print()
for b in BUCKET_ORDER:
    cnt = exit_counts.get(b, 0)
    if cnt:
        print(f"    Exit → {b} ✓: {cnt:,}  ({100*cnt/N:.2f}%)")
print()

print("=" * 72)
print("PMT-ORDER DIAGNOSTIC (combined vs E.1 alone)")
print("=" * 72)
pmt_sim_n = pmt_total - pmt_skipped
print(f"  Rescued by BOTH E.1 and combined    : {e1_rescued_also:,}")
print(f"  Extra rescues (combined only)        : {combined_extra:,}")
print(f"  Missed rescues (E.1 alone only)      : {combined_missed:,}")
print()

print("=" * 72)
print("GROUP-LEVEL SHIFT  (% of full segment, exits included in group)")
print("=" * 72)
hdr = f"{'Group':<12}  {'Before':>9}  {'After':>9}  {'Δ':>8}"
print(hdr); print('-' * len(hdr))
for label, keys in [('Early', EARLY_K), ('On-Time', OT_K), ('Late', LATE_K)]:
    bn = sum(before_full[k] for k in keys)
    an = sum(after_incl.get(k, 0) for k in keys)
    dp = 100 * (an - bn) / N
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
    dp = 100 * (an - bn) / N
    sign = '+' if dp >= 0 else ''
    print(f"{b:<14}  {100*bn/N:>8.2f}%  {100*an/N:>8.2f}%  {sign}{dp:>7.2f}pp")
for b in BUCKET_ORDER:
    cnt = exit_counts.get(b, 0)
    if cnt:
        label = b + ' ✓'
        print(f"{label:<14}  {'—':>9}  {100*cnt/N:>8.2f}%  +{100*cnt/N:>6.2f}pp")
print()
print(f"Total rescued: {rescued_total:,}  ({100*rescued_total/N:.2f}% of segment)")
print(f"Total worsened: {worsened:,}  ({100*worsened/N:.2f}% of segment)")
