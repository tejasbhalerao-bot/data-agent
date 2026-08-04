"""
SDD Non-Inventory Cohort 69 validation.

Hypothesis (Tejas, 2026-08-04): Cohort 69 (WH Early + Dispatch Early +
Delivery Early, ~90.8% of SDD Non-Inventory egregious) has the same root
cause as Non-SDD Non-Inventory Cohort 40 — the WH promise assumes
Non-Inventory procurement time that doesn't exist, so the order is invoiced
and packed far before the WH promise, causing early dispatch and early
delivery vs an over-padded promise.

Validation mirrors the Cohort 40 analysis (analyses #12, #45, #46):
  Part 1: Cohort sizing
  Part 2: WH deviation magnitude (AWB-based) — compare to Cohort 40 (51.5% >24h)
  Part 3: Invoice vs AWB — payment pending check (Cohort 40 had zero invoices after WH promise)
  Part 4: Dispatch deviation magnitude in calendar days
  Part 5: Delivery promise structure — promised TAT, actual TAT, delivery date gap
  Part 6: WH processing type distribution
"""

import csv
import math
import statistics
from datetime import datetime

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


# ── Load cohorts ─────────────────────────────────────────────────────────────
sdd_non_inv_all = []
cohort_69       = []

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
        if is_true_str(row.get('digitised_is_inventory', '')) is not False:
            continue

        sdd_non_inv_all.append(row)

        wh_prom   = to_dt(row.get('digitised_wh_promise', ''))
        awb_ts    = to_dt(row.get('awb_sticker_printed_ts', ''))
        disp_prom = to_date(row.get('digitised_dispatch_promise', ''))
        pickup    = to_date(row.get('pickup_time', ''))

        if not wh_prom or not awb_ts or not disp_prom or not pickup:
            continue

        wh_early   = wh_prom > awb_ts
        disp_early = disp_prom > pickup
        del_early  = del_prom > del_att

        if wh_early and disp_early and del_early:
            cohort_69.append(row)

n_all = len(sdd_non_inv_all)
n_c69 = len(cohort_69)

print(f"SDD Non-Inventory egregious (all)  : {n_all:,}")
print(f"Cohort 69 (WH+Disp+Del Early)      : {n_c69:,}  ({100*n_c69/n_all:.1f}% of SDD Non-Inv)")
print(f"  [Ref: Cohort 40 was 87.7% of Non-SDD Non-Inv; C69 was 90.8% in Analysis #14]")
print()


# ── Part 2: WH deviation magnitude (AWB-based) ───────────────────────────────
print("=" * 70)
print("PART 2 — WH deviation magnitude for Cohort 69 (AWB-based)")
print("  Ref: Cohort 40 — 51.5% Early >24h, 21.2% 4–8h, 13.2% 8–12h")
print("=" * 70)

wh_buckets = [
    ('Early >24 hrs',   24,   9999),
    ('Early 12–24 hrs', 12,     24),
    ('Early 8–12 hrs',   8,     12),
    ('Early 4–8 hrs',    4,      8),
    ('Early 2–4 hrs',    2,      4),
    ('Early 1–2 hrs',    1,      2),
    ('Early 30–60 min',  0.5,    1),
    ('Early <30 min',    0,    0.5),
    ('Late (any)',    -9999,      0),
]

gaps_h = []
for r in cohort_69:
    wh  = to_dt(r.get('digitised_wh_promise', ''))
    awb = to_dt(r.get('awb_sticker_printed_ts', ''))
    if wh and awb:
        gaps_h.append((wh - awb).total_seconds() / 3600)

print(f"{'Bucket':<22} {'n':>6}  {'% of C69':>9}")
print('-' * 42)
for label, lo, hi in wh_buckets:
    if label == 'Late (any)':
        n = sum(1 for g in gaps_h if g < 0)
    else:
        n = sum(1 for g in gaps_h if lo < g <= hi)
    pct = 100 * n / len(gaps_h) if gaps_h else 0
    print(f"{label:<22} {n:>6}  {pct:>8.1f}%")

if gaps_h:
    print(f"\nMedian WH gap : {statistics.median(gaps_h):+.2f}h")
    print(f"% Early >4h   : {100*sum(1 for g in gaps_h if g > 4)/len(gaps_h):.1f}%")
print()


# ── Part 3: Invoice vs AWB ────────────────────────────────────────────────────
print("=" * 70)
print("PART 3 — Invoice vs AWB payment pending check for Cohort 69")
print("  Ref: Cohort 40 had ZERO invoices after WH promise")
print("=" * 70)

inv_gaps_h = []
inv_after = 0
for r in cohort_69:
    wh  = to_dt(r.get('digitised_wh_promise', ''))
    inv = to_dt(r.get('invoice_create_ts', ''))
    if not wh or not inv:
        continue
    gap = (wh - inv).total_seconds() / 3600
    inv_gaps_h.append(gap)
    if gap < 0:
        inv_after += 1

print(f"{'Bucket':<22} {'n':>6}  {'% of C69':>9}")
print('-' * 42)
for label, lo, hi in wh_buckets:
    if label == 'Late (any)':
        n = sum(1 for g in inv_gaps_h if g < 0)
    else:
        n = sum(1 for g in inv_gaps_h if lo < g <= hi)
    pct = 100 * n / len(inv_gaps_h) if inv_gaps_h else 0
    print(f"{label:<22} {n:>6}  {pct:>8.1f}%")

if inv_gaps_h:
    print(f"\nMedian invoice gap: {statistics.median(inv_gaps_h):+.2f}h")
    print(f"Invoices AFTER WH promise : {inv_after} "
          f"({100*inv_after/len(inv_gaps_h):.2f}%)")
print()


# ── Part 4: Dispatch deviation magnitude ─────────────────────────────────────
print("=" * 70)
print("PART 4 — Dispatch deviation magnitude for Cohort 69 (calendar days)")
print("  Ref: Cohort 40 — 54.8% Early 1d, 32.6% Early 2d, 7.5% On-Time")
print("=" * 70)

disp_devs = []
for r in cohort_69:
    dp = to_date(r.get('digitised_dispatch_promise', ''))
    pk = to_date(r.get('pickup_time', ''))
    if dp and pk:
        disp_devs.append((dp - pk).days)

for dev in sorted(set(disp_devs), reverse=True):
    n = sum(1 for d in disp_devs if d == dev)
    pct = 100 * n / len(disp_devs)
    label = (f"Early {dev}d" if dev > 0
             else "On-Time" if dev == 0
             else f"Late {abs(dev)}d")
    print(f"  {label:<14} {n:>6}  {pct:>7.1f}%")
print()


# ── Part 5: Delivery promise structure ───────────────────────────────────────
print("=" * 70)
print("PART 5 — Delivery promise structure for Cohort 69")
print("=" * 70)

promised_tat_days = []
actual_tat_days   = []
delivery_gaps_d   = []
tat_mins_vals     = []

for r in cohort_69:
    dp  = to_date(r.get('digitised_dispatch_promise', ''))
    dlp = to_date(r.get('digitised_delivery_promise', ''))
    pk  = to_date(r.get('pickup_time', ''))
    da  = to_date(r.get('delivery_attempt_time', ''))
    try:
        tat_mins = float(r.get('digitised_delivery_tat_mins', '') or '')
    except (ValueError, TypeError):
        tat_mins = None

    if dp and dlp:
        promised_tat_days.append((dlp - dp).days)
    if pk and da:
        actual_tat_days.append((da - pk).days)
    if dlp and da:
        delivery_gaps_d.append((dlp - da).days)
    if tat_mins is not None:
        tat_mins_vals.append(tat_mins)

print("A. Promised TAT in calendar days (delivery_promise − dispatch_promise):")
for v in sorted(set(promised_tat_days), reverse=True):
    n = sum(1 for d in promised_tat_days if d == v)
    pct = 100 * n / len(promised_tat_days)
    print(f"   {v:>3}d  {n:>6}  {pct:>7.1f}%")

if tat_mins_vals:
    print(f"\n   digitised_delivery_tat_mins stats:")
    print(f"   Median : {statistics.median(tat_mins_vals):.0f} min  "
          f"({statistics.median(tat_mins_vals)/60:.1f}h)")
    print(f"   Min    : {min(tat_mins_vals):.0f} min")
    print(f"   Max    : {max(tat_mins_vals):.0f} min")
    tat_ceil = [math.ceil(m / 1440) for m in tat_mins_vals]
    print(f"   Ceiling-days distribution:")
    for v in sorted(set(tat_ceil), reverse=True):
        n = sum(1 for d in tat_ceil if d == v)
        pct = 100 * n / len(tat_ceil)
        print(f"     {v:>3}d  {n:>6}  {pct:>7.1f}%")
print()

print("B. Actual TAT in calendar days (delivery_attempt_date − pickup_date):")
for v in sorted(set(actual_tat_days)):
    n = sum(1 for d in actual_tat_days if d == v)
    pct = 100 * n / len(actual_tat_days)
    print(f"   {v:>3}d  {n:>6}  {pct:>7.1f}%")
print()

print("C. Delivery date gap = DATE(delivery_promise) − DATE(delivery_attempt)  [positive = early]:")
for v in sorted(set(delivery_gaps_d), reverse=True):
    n = sum(1 for d in delivery_gaps_d if d == v)
    pct = 100 * n / len(delivery_gaps_d)
    label = (f"Early {v}d" if v > 0
             else "On-Time" if v == 0
             else f"Late {abs(v)}d")
    print(f"   {label:<12}  {n:>6}  {pct:>7.1f}%")
print()


# ── Part 6: WH processing type ───────────────────────────────────────────────
print("=" * 70)
print("PART 6 — WH processing type for Cohort 69")
print("  Expected: SDD_Non_Inventory; mismatch = misconfiguration")
print("=" * 70)

proc_types = {}
for r in cohort_69:
    pt = r.get('wh_processing_type', '').strip() or 'MISSING'
    proc_types[pt] = proc_types.get(pt, 0) + 1

for pt, n in sorted(proc_types.items(), key=lambda x: -x[1]):
    print(f"  {pt:<40} {n:>5}  ({100*n/n_c69:.1f}%)")
