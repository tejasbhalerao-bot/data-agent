"""
SDD Inventory egregious analysis.

SDD + Inventory + |delivery deviation| >= 2 calendar days.
Reference (analysis #14): n=3,954, 46.3% of SDD egregious.

Dominant patterns from cross-tab:
  Late WH group  (C59+C60+C61): 37.1+18.8+16.1 = 72.0% — WH late, delivery late
  Early WH group (C62+C63)    : 13.3+10.1       = 23.4% — WH early, delivery still late

Mirrors the Non-SDD Inventory analysis (H9/H12/H16) but applied to the SDD segment.

  Part 1: Cohort sizing and WH × Dispatch × Delivery cross-tab
  Part 2: WH deviation magnitude for Late WH group (hours)
  Part 3: Payment pending check for Late WH group (mirror of Non-SDD Inv H9)
  Part 4: Doctor confirmation check for Late WH group (mirror of Non-SDD Inv H12)
  Part 5: Delivery TAT analysis for Early WH + Late Delivery group
  Part 6: WH processing type distribution
"""

import csv
import statistics
from datetime import datetime, date

CSV = 'archives/egregiously-miscalibrated-promises/raw-data/all-orders-july-2026.csv'


def to_date(s):
    if not s or not s.strip():
        return None
    s = s.strip()
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


# ── Load SDD Inventory egregious orders ──────────────────────────────────────
sdd_inv_all = []

with open(CSV, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        del_prom = to_date(row.get('digitised_delivery_promise', ''))
        del_att  = to_date(row.get('delivery_attempt_time', ''))
        if not del_prom or not del_att:
            continue
        if abs((del_prom - del_att).days) < 2:
            continue
        if is_true_str(row.get('digitised_is_sdd', '')) is not True:
            continue
        if is_true_str(row.get('digitised_is_inventory', '')) is not True:
            continue
        sdd_inv_all.append(row)

n_all = len(sdd_inv_all)
print(f"SDD Inventory egregious (all)  : {n_all:,}")
print(f"  [Ref: n=3,954 from analysis #14]")
print()


# ── Part 1: Cross-tab ─────────────────────────────────────────────────────────
print("=" * 70)
print("PART 1 — WH × Dispatch × Delivery Cx cross-tab for SDD Inventory")
print("=" * 70)

def classify(row):
    wh_prom  = to_dt(row.get('digitised_wh_promise', ''))
    awb_ts   = to_dt(row.get('awb_sticker_printed_ts', ''))
    disp_p   = to_date(row.get('digitised_dispatch_promise', ''))
    pickup   = to_date(row.get('pickup_time', ''))
    del_prom = to_date(row.get('digitised_delivery_promise', ''))
    del_att  = to_date(row.get('delivery_attempt_time', ''))

    if not wh_prom or not awb_ts:
        wh = '?'
    else:
        gap = (wh_prom - awb_ts).total_seconds()
        if gap > 0:
            wh = 'Early'
        elif gap < 0:
            wh = 'Late'
        else:
            wh = 'On-Time'

    if not disp_p or not pickup:
        dp = '?'
    else:
        d = (disp_p - pickup).days
        if d > 0:
            dp = 'Early'
        elif d < 0:
            dp = 'Late'
        else:
            dp = 'On-Time'

    if not del_prom or not del_att:
        dlv = '?'
    else:
        d = (del_prom - del_att).days
        if d > 0:
            dlv = 'Early'
        elif d < 0:
            dlv = 'Late'
        else:
            dlv = 'On-Time'

    return wh, dp, dlv

from collections import Counter
combos = Counter()
for r in sdd_inv_all:
    combos[classify(r)] += 1

print(f"{'Cohort':<4}  {'WH':<8} {'Dispatch':<10} {'Delivery':<10}  {'n':>6}  {'% of SDD Inv':>13}")
print('-' * 60)
cohort_num = 59
for combo, n in sorted(combos.items(), key=lambda x: -x[1]):
    pct = 100 * n / n_all
    print(f"C{cohort_num:<3}  {combo[0]:<8} {combo[1]:<10} {combo[2]:<10}  {n:>6}  {pct:>12.1f}%")
    cohort_num += 1
print()


# ── Define subgroups ──────────────────────────────────────────────────────────
late_wh_group  = []  # C59+C60+C61: WH Late, Delivery Late
early_wh_late  = []  # C62+C63: WH Early, Delivery Late

for r in sdd_inv_all:
    wh, dp, dlv = classify(r)
    if wh == 'Late' and dlv == 'Late':
        late_wh_group.append(r)
    elif wh == 'Early' and dlv == 'Late':
        early_wh_late.append(r)

n_late_wh  = len(late_wh_group)
n_early_wh_late = len(early_wh_late)
print(f"Late WH + Late Delivery group   : {n_late_wh:,}  ({100*n_late_wh/n_all:.1f}% of SDD Inv)")
print(f"Early WH + Late Delivery group  : {n_early_wh_late:,}  ({100*n_early_wh_late/n_all:.1f}% of SDD Inv)")
print()


# ── Part 2: WH deviation magnitude for Late WH group ─────────────────────────
print("=" * 70)
print("PART 2 — WH deviation magnitude for Late WH group (C59+C60+C61)")
print("  Ref: Non-SDD Inventory #21 — Late WH was 78.4% of that segment")
print("=" * 70)

late_wh_buckets = [
    ('Late >24 hrs',    24,  9999),
    ('Late 12–24 hrs',  12,    24),
    ('Late 8–12 hrs',    8,    12),
    ('Late 4–8 hrs',     4,     8),
    ('Late 2–4 hrs',     2,     4),
    ('Late 1–2 hrs',     1,     2),
    ('Late 30–60 min',  0.5,    1),
    ('Late <30 min',     0,   0.5),
    ('Early (any)',  -9999,     0),
]

wh_gaps_h = []
for r in late_wh_group:
    wh  = to_dt(r.get('digitised_wh_promise', ''))
    awb = to_dt(r.get('awb_sticker_printed_ts', ''))
    if wh and awb:
        # negative = AWB after WH promise = Late
        wh_gaps_h.append((awb - wh).total_seconds() / 3600)

print(f"{'Bucket':<22} {'n':>6}  {'% of Late-WH group':>19}")
print('-' * 52)
for label, lo, hi in late_wh_buckets:
    if label == 'Early (any)':
        n = sum(1 for g in wh_gaps_h if g < 0)
    else:
        n = sum(1 for g in wh_gaps_h if lo < g <= hi)
    pct = 100 * n / len(wh_gaps_h) if wh_gaps_h else 0
    print(f"{label:<22} {n:>6}  {pct:>18.1f}%")

if wh_gaps_h:
    print(f"\nMedian WH lateness : {statistics.median(wh_gaps_h):+.2f}h")
    print(f"% Late >24h        : {100*sum(1 for g in wh_gaps_h if g > 24)/len(wh_gaps_h):.1f}%")
    print(f"% Late >4h         : {100*sum(1 for g in wh_gaps_h if g > 4)/len(wh_gaps_h):.1f}%")
print()


# ── Part 3: Payment pending check ────────────────────────────────────────────
print("=" * 70)
print("PART 3 — Payment pending check for Late WH group")
print("  Ref: Non-SDD Inventory H9 — 64% of Late >24h had payment_pending_ts")
print("=" * 70)

print(f"{'Bucket':<22} {'n':>6}  {'With Pmt Pending':>17}  {'%':>6}")
print('-' * 58)
for label, lo, hi in late_wh_buckets:
    if label == 'Early (any)':
        bucket_rows = [r for r, g in zip(late_wh_group, wh_gaps_h) if g < 0]
    else:
        bucket_rows = [r for r, g in zip(
            [rr for rr in late_wh_group if to_dt(rr.get('awb_sticker_printed_ts')) and to_dt(rr.get('digitised_wh_promise'))],
            wh_gaps_h
        ) if lo < g <= hi]

    # Recompute per bucket cleanly
    bucket_rows = []
    for r, g in zip(late_wh_group, wh_gaps_h + [None] * (len(late_wh_group) - len(wh_gaps_h))):
        if g is None:
            continue
        if label == 'Early (any)' and g < 0:
            bucket_rows.append(r)
        elif label != 'Early (any)' and lo < g <= hi:
            bucket_rows.append(r)

    n_bucket = len(bucket_rows)
    if n_bucket == 0:
        continue
    n_pmt = sum(1 for r in bucket_rows if r.get('payment_pending_ts', '').strip())
    pct = 100 * n_pmt / n_bucket
    print(f"{label:<22} {n_bucket:>6}  {n_pmt:>17}  {pct:>5.1f}%")

# Overall
n_pmt_overall = sum(1 for r in late_wh_group if r.get('payment_pending_ts', '').strip())
print(f"\nOverall Late WH group with payment pending: {n_pmt_overall} ({100*n_pmt_overall/n_late_wh:.1f}%)")
print()


# ── Part 4: Doctor confirmation check ────────────────────────────────────────
print("=" * 70)
print("PART 4 — Doctor confirmation check for Late WH group")
print("  dr_confirm_ts > digitised_wh_promise = confirmation arrived after WH")
print("  Ref: Non-SDD Inventory H12 — 49–55% late confirmation in Late WH buckets")
print("=" * 70)

# Rebuild per-bucket with dr_confirm check
rows_with_wh_gap = []
for r in late_wh_group:
    wh  = to_dt(r.get('digitised_wh_promise', ''))
    awb = to_dt(r.get('awb_sticker_printed_ts', ''))
    if wh and awb:
        rows_with_wh_gap.append((r, (awb - wh).total_seconds() / 3600))

print(f"{'Bucket':<22} {'n':>6}  {'Dr Confirm Late':>16}  {'%':>6}  {'No Dr Leg':>10}")
print('-' * 68)
for label, lo, hi in late_wh_buckets:
    if label == 'Early (any)':
        bucket = [(r, g) for r, g in rows_with_wh_gap if g < 0]
    else:
        bucket = [(r, g) for r, g in rows_with_wh_gap if lo < g <= hi]
    if not bucket:
        continue
    n_bucket = len(bucket)
    n_late_conf = 0
    n_no_leg = 0
    for r, _ in bucket:
        wh = to_dt(r.get('digitised_wh_promise', ''))
        conf = to_dt(r.get('dr_confirm_ts', ''))
        if conf is None:
            n_no_leg += 1
        elif conf > wh:
            n_late_conf += 1
    pct = 100 * n_late_conf / n_bucket
    print(f"{label:<22} {n_bucket:>6}  {n_late_conf:>16}  {pct:>5.1f}%  {n_no_leg:>10}")

overall_late_conf = sum(1 for r, _ in rows_with_wh_gap
                        if (wh := to_dt(r.get('digitised_wh_promise', ''))) and
                        (conf := to_dt(r.get('dr_confirm_ts', ''))) and
                        conf > wh)
overall_no_leg = sum(1 for r, _ in rows_with_wh_gap if not r.get('dr_confirm_ts', '').strip())
print(f"\nOverall Late WH group: {overall_late_conf} late confirmation ({100*overall_late_conf/n_late_wh:.1f}%)")
print(f"Overall no dr_confirm_ts: {overall_no_leg} ({100*overall_no_leg/n_late_wh:.1f}%)")
print()


# ── Part 5: Delivery TAT analysis for Early WH + Late Delivery group ──────────
print("=" * 70)
print("PART 5 — Delivery TAT for Early WH + Late Delivery group (C62+C63)")
print("  WH early, delivery still late — is this a courier TAT problem?")
print("=" * 70)

promised_tat = []
actual_tat   = []
delivery_gap = []
tat_mins_vals = []

for r in early_wh_late:
    dp   = to_date(r.get('digitised_dispatch_promise', ''))
    dlp  = to_date(r.get('digitised_delivery_promise', ''))
    pk   = to_date(r.get('pickup_time', ''))
    da   = to_date(r.get('delivery_attempt_time', ''))
    try:
        tat_mins = float(r.get('digitised_delivery_tat_mins', '') or '')
    except (ValueError, TypeError):
        tat_mins = None

    if dp and dlp:
        promised_tat.append((dlp - dp).days)
    if pk and da:
        actual_tat.append((da - pk).days)
    if dlp and da:
        delivery_gap.append((da - dlp).days)   # positive = late (actual after promise)
    if tat_mins is not None:
        tat_mins_vals.append(tat_mins)

print("A. Promised TAT in calendar days (delivery_promise − dispatch_promise):")
for v in sorted(set(promised_tat)):
    n = sum(1 for d in promised_tat if d == v)
    pct = 100 * n / len(promised_tat)
    print(f"   {v:>3}d  {n:>6}  {pct:>7.1f}%")

if tat_mins_vals:
    import math
    print(f"\n   digitised_delivery_tat_mins stats:")
    print(f"   Median : {statistics.median(tat_mins_vals):.0f} min  ({statistics.median(tat_mins_vals)/60:.1f}h)")
    tat_ceil = [math.ceil(m / 1440) for m in tat_mins_vals]
    print(f"   Ceiling-days distribution:")
    for v in sorted(set(tat_ceil)):
        n_v = sum(1 for d in tat_ceil if d == v)
        pct = 100 * n_v / len(tat_ceil)
        print(f"     {v:>3}d  {n_v:>6}  {pct:>7.1f}%")
print()

print("B. Actual TAT in calendar days (delivery_attempt_date − pickup_date):")
for v in sorted(set(actual_tat)):
    n = sum(1 for d in actual_tat if d == v)
    pct = 100 * n / len(actual_tat)
    print(f"   {v:>3}d  {n:>6}  {pct:>7.1f}%")
print()

print("C. Delivery date gap = DATE(delivery_attempt) − DATE(delivery_promise)  [positive = late]:")
for v in sorted(set(delivery_gap)):
    n = sum(1 for d in delivery_gap if d == v)
    pct = 100 * n / len(delivery_gap)
    label = (f"Late {v}d" if v > 0
             else "On-Time" if v == 0
             else f"Early {abs(v)}d")
    print(f"   {label:<12}  {n:>6}  {pct:>7.1f}%")
print()


# ── Part 6: WH processing type ────────────────────────────────────────────────
print("=" * 70)
print("PART 6 — WH processing type for SDD Inventory egregious orders")
print("  Expected: SDD_INVENTORY; mismatch = misconfiguration")
print("=" * 70)

proc_types = {}
for r in sdd_inv_all:
    pt = r.get('wh_processing_type', '').strip() or 'MISSING'
    proc_types[pt] = proc_types.get(pt, 0) + 1

for pt, n in sorted(proc_types.items(), key=lambda x: -x[1]):
    print(f"  {pt:<40} {n:>5}  ({100*n/n_all:.1f}%)")
