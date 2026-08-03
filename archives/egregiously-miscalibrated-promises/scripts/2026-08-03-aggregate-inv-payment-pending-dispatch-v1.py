"""
Non-SDD Inventory — Payment pending rate across dispatch deviation buckets.

Superset: digitised_is_sdd=False, digitised_is_inventory=True,
          |delivery_promise - delivery_attempt| >= 2 calendar days.

Dispatch deviation = DATE(digitised_dispatch_promise) - DATE(pickup_time)
  Positive = dispatch was early (courier picked up before promised date)
  Zero     = on time
  Negative = dispatch was late

Part 1: High-level — Early / On-Time / Late group totals + payment pending %
Part 2: Day-level — per deviation day, n + payment pending %
Part 3: Invoice→AWB gap (hours) for pmt-pending vs non-pmt-pending, per group and per day
"""

import csv
import statistics
from datetime import datetime

CSV = 'archives/egregiously-miscalibrated-promises/raw-data/all-orders-july-2026.csv'

EGREGIOUS_N = 96424
INV_SUPERSET_N = 57688


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
            from datetime import date
            return date.fromisoformat(s[:10])
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


superset_n = 0
skipped = 0

# day_stats: dev_days -> {n, pmt, pmt_gaps: [], non_pmt_gaps: []}
day_stats = {}

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

        superset_n += 1

        disp_prom = to_date(row.get('digitised_dispatch_promise', ''))
        pickup    = to_date(row.get('pickup_time', ''))
        if not disp_prom or not pickup:
            skipped += 1
            continue

        dev = (disp_prom - pickup).days
        pmt = bool(row.get('payment_pending_ts', '').strip())

        invoice_ts = to_dt(row.get('invoice_create_ts', ''))
        awb_ts     = to_dt(row.get('awb_sticker_printed_ts', ''))
        gap_hrs = None
        if invoice_ts and awb_ts:
            diff = (awb_ts - invoice_ts).total_seconds() / 3600
            if diff >= 0:
                gap_hrs = diff

        if dev not in day_stats:
            day_stats[dev] = {'n': 0, 'pmt': 0, 'pmt_gaps': [], 'non_pmt_gaps': []}
        day_stats[dev]['n'] += 1
        if pmt:
            day_stats[dev]['pmt'] += 1
            if gap_hrs is not None:
                day_stats[dev]['pmt_gaps'].append(gap_hrs)
        else:
            if gap_hrs is not None:
                day_stats[dev]['non_pmt_gaps'].append(gap_hrs)

effective_n = superset_n - skipped

print(f"Non-SDD Inventory egregious superset : {superset_n:,}")
print(f"Skipped (missing dispatch/pickup ts)  : {skipped:,}")
print(f"Effective n for analysis              : {effective_n:,}")
print()

# ── Part 1: High-level groups ──────────────────────────────────────────────
early_n = early_pmt = 0
ontime_n = ontime_pmt = 0
late_n = late_pmt = 0

for dev, s in day_stats.items():
    if dev > 0:
        early_n  += s['n'];  early_pmt  += s['pmt']
    elif dev == 0:
        ontime_n += s['n'];  ontime_pmt += s['pmt']
    else:
        late_n   += s['n'];  late_pmt   += s['pmt']

print("=" * 60)
print("PART 1 — Payment pending rate by dispatch group")
print("=" * 60)
hdr = f"{'Group':<12}  {'n':>7}  {'% of set':>9}  {'Pmt pend n':>11}  {'Pmt pend %':>11}"
print(hdr)
print('-' * len(hdr))
for label, n, pmt in [('Early', early_n, early_pmt),
                       ('On-Time', ontime_n, ontime_pmt),
                       ('Late', late_n, late_pmt)]:
    pct_set = 100 * n / effective_n if effective_n else 0
    pct_pmt = 100 * pmt / n if n else 0
    print(f"{label:<12}  {n:>7,}  {pct_set:>8.1f}%  {pmt:>11,}  {pct_pmt:>10.1f}%")
print()

# ── Part 2: Day-level breakdown ────────────────────────────────────────────
print("=" * 60)
print("PART 2 — Payment pending rate at day-level dispatch deviation")
print("  Positive dev = dispatch early; negative = dispatch late")
print("=" * 60)
hdr2 = f"{'Dev (days)':>11}  {'Label':<14}  {'n':>7}  {'% of set':>9}  {'Pmt pend n':>11}  {'Pmt pend %':>11}"
print(hdr2)
print('-' * len(hdr2))

for dev in sorted(day_stats.keys(), reverse=True):
    s = day_stats[dev]
    n = s['n']
    if n == 0:
        continue
    pct_set = 100 * n / effective_n
    pct_pmt = 100 * s['pmt'] / n

    if dev > 0:
        label = f"Early {dev}d" if dev <= 5 else f"Early {dev}d+"
    elif dev == 0:
        label = "On-Time"
    else:
        label = f"Late {abs(dev)}d" if abs(dev) <= 5 else f"Late {abs(dev)}d+"

    print(f"{dev:>11}  {label:<14}  {n:>7,}  {pct_set:>8.1f}%  {s['pmt']:>11,}  {pct_pmt:>10.1f}%")

# ── Part 3: Invoice→AWB gap by group ──────────────────────────────────────

def gap_summary(gaps):
    if not gaps:
        return ('—', '—', '—')
    med = statistics.median(gaps)
    p25 = sorted(gaps)[int(len(gaps) * 0.25)]
    p75 = sorted(gaps)[int(len(gaps) * 0.75)]
    return (f"{med:.1f}h", f"{p25:.1f}h", f"{p75:.1f}h")


print()
print("=" * 90)
print("PART 3a — Invoice→AWB gap: payment-pending vs non-pmt-pending, by dispatch group")
print("  Gap = awb_sticker_printed_ts − invoice_create_ts (hours, non-negative only)")
print("=" * 90)
hdr3 = (f"{'Group':<12}  {'Pmt n':>6}  {'Pmt med':>8}  {'Pmt p25':>8}  {'Pmt p75':>8}"
        f"  {'Non-pmt n':>9}  {'Non-pmt med':>11}  {'Non-pmt p25':>11}  {'Non-pmt p75':>11}")
print(hdr3)
print('-' * len(hdr3))

groups = [
    ('Early',   {k: v for k, v in day_stats.items() if k > 0}),
    ('On-Time', {0:  day_stats[0]} if 0 in day_stats else {}),
    ('Late',    {k: v for k, v in day_stats.items() if k < 0}),
]
for label, buckets in groups:
    pmt_gaps = []
    non_pmt_gaps = []
    for s in buckets.values():
        pmt_gaps.extend(s['pmt_gaps'])
        non_pmt_gaps.extend(s['non_pmt_gaps'])
    pm, pp25, pp75 = gap_summary(pmt_gaps)
    nm, np25, np75 = gap_summary(non_pmt_gaps)
    print(f"{label:<12}  {len(pmt_gaps):>6,}  {pm:>8}  {pp25:>8}  {pp75:>8}"
          f"  {len(non_pmt_gaps):>9,}  {nm:>11}  {np25:>11}  {np75:>11}")

print()
print("=" * 90)
print("PART 3b — Invoice→AWB gap at day-level (material rows only: n >= 50)")
print("=" * 90)
hdr3b = (f"{'Dev':>6}  {'Label':<14}  {'Pmt n':>6}  {'Pmt med':>8}  {'Pmt p25':>8}  {'Pmt p75':>8}"
         f"  {'Non-pmt n':>9}  {'Non-pmt med':>11}  {'Non-pmt p25':>11}  {'Non-pmt p75':>11}")
print(hdr3b)
print('-' * len(hdr3b))
for dev in sorted(day_stats.keys(), reverse=True):
    s = day_stats[dev]
    if s['n'] < 50:
        continue
    if dev > 0:
        label = f"Early {dev}d"
    elif dev == 0:
        label = "On-Time"
    else:
        label = f"Late {abs(dev)}d"
    pm, pp25, pp75 = gap_summary(s['pmt_gaps'])
    nm, np25, np75 = gap_summary(s['non_pmt_gaps'])
    print(f"{dev:>6}  {label:<14}  {len(s['pmt_gaps']):>6,}  {pm:>8}  {pp25:>8}  {pp75:>8}"
          f"  {len(s['non_pmt_gaps']):>9,}  {nm:>11}  {np25:>11}  {np75:>11}")
