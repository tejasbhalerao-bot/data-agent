"""
Early 1d dispatch — switched-courier group: timestamp-level investigation.

Context: rule engine sets dispatch_promise = D+1 when digitised_wh_promise time
exceeds the original (digitised) courier's same-day cutoff. If a different courier
is assigned at shipping time (shipping_delivery_partner ≠ digitised_delivery_partner),
the dispatch promise is NOT recalculated. If the replacement courier's cutoff is
later, it can still collect same-day → dispatch < promise by 1 day → Early 1d.

The group splits nearly 50/50:
  Sub-group A (AWB before WH promise, ~49.5%): WH promise at 17-18:00, same
    mechanism as same-courier — WH finishes early, courier switch is incidental.
  Sub-group B (AWB after WH promise, ~50.5%): WH promise at 13:00, original
    courier had early cutoff (~12:00), system set D+1, WH overran by ~1.2h,
    replacement courier (later cutoff) rescues same-day dispatch.

Parts:
  1. Cohort sizes (switched Early 1d, same-courier Early 1d, switched On-Time)
  2. AWB vs WH promise gap — overall distribution
  3. Calendar-day relationship
  4. Split AWB-before vs AWB-after and profile each sub-group
  5. WH promise hour by sub-group
  6. AWB print hour by sub-group
  7. Overshoot magnitude for AWB-after group
"""

import csv
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


switched_e1d = []
same_e1d     = []
switched_ot  = []

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
        dc  = row.get('digitised_delivery_partner', '').strip()
        sc  = row.get('shipping_delivery_partner', '').strip()
        is_switch = bool(dc and sc and dc != sc)
        is_same   = bool(dc and sc and dc == sc)

        if dev == 1:
            if is_switch:
                switched_e1d.append(dict(row))
            elif is_same:
                same_e1d.append(dict(row))
        elif dev == 0 and is_switch:
            switched_ot.append(dict(row))


# ── Part 1: cohort sizes ────────────────────────────────────────────────────
print(f"Switched-courier Early 1d : {len(switched_e1d):,}")
print(f"Same-courier Early 1d     : {len(same_e1d):,}  (comparison)")
print(f"Switched-courier On-Time  : {len(switched_ot):,}")
print()


def ts_gap(orders):
    gaps, miss = [], 0
    for r in orders:
        wh  = to_dt(r.get('digitised_wh_promise', ''))
        awb = to_dt(r.get('awb_sticker_printed_ts', ''))
        if wh and awb:
            gaps.append((wh - awb).total_seconds() / 3600)
        else:
            miss += 1
    return gaps, miss


def hr_dist(orders, field):
    d = {}
    for r in orders:
        ts = to_dt(r.get(field, ''))
        if ts:
            d[ts.hour] = d.get(ts.hour, 0) + 1
    return d


# ── Part 2: overall gap distribution ────────────────────────────────────────
print("=" * 70)
print("PART 2 — (wh_promise − awb_ts) gap in hours")
print("  Positive = AWB before WH promise  |  Negative = AWB after")
print("=" * 70)

sw_gaps, sw_m = ts_gap(switched_e1d)
sa_gaps, sa_m = ts_gap(same_e1d)
ot_gaps, ot_m = ts_gap(switched_ot)

buckets = [
    ('>4h before',     4,   999),
    ('1–4h before',    1,     4),
    ('30–60m before',  0.5,   1),
    ('0–30m before',   0,   0.5),
    ('0–30m after',   -0.5,   0),
    ('30m–2h after',  -2,  -0.5),
    ('>2h after',    -999,   -2),
]
hdr = f"{'Bucket':<22} {'Switched%':>10} {'Same-cour%':>11} {'Sw OT%':>9}"
print(hdr)
print('-' * len(hdr))
for label, lo, hi in buckets:
    sp = 100 * sum(1 for g in sw_gaps if lo < g <= hi) / len(sw_gaps) if sw_gaps else 0
    ap = 100 * sum(1 for g in sa_gaps if lo < g <= hi) / len(sa_gaps) if sa_gaps else 0
    op = 100 * sum(1 for g in ot_gaps if lo < g <= hi) / len(ot_gaps) if ot_gaps else 0
    print(f"{label:<22} {sp:>9.1f}% {ap:>10.1f}% {op:>8.1f}%")

print(f"\nMedian  Switched={statistics.median(sw_gaps):+.2f}h  Same={statistics.median(sa_gaps):+.2f}h  Sw-OT={statistics.median(ot_gaps):+.2f}h")
print(f"% AWB before WH promise: Switched={100*sum(1 for g in sw_gaps if g>0)/len(sw_gaps):.1f}%  "
      f"Same={100*sum(1 for g in sa_gaps if g>0)/len(sa_gaps):.1f}%  "
      f"Sw-OT={100*sum(1 for g in ot_gaps if g>0)/len(ot_gaps):.1f}%")
print()


# ── Part 3: calendar-day relationship ────────────────────────────────────────
print("=" * 70)
print("PART 3 — Calendar-day: awb_date vs wh_promise_date")
print("=" * 70)

def calday(orders):
    d = {}
    for r in orders:
        wh  = to_dt(r.get('digitised_wh_promise', ''))
        awb = to_dt(r.get('awb_sticker_printed_ts', ''))
        if not wh or not awb:
            d['missing'] = d.get('missing', 0) + 1
            continue
        diff = (wh.date() - awb.date()).days
        k = ('AWB 1d before' if diff == 1
             else 'Same day' if diff == 0
             else f'AWB {diff}d before' if diff > 1
             else 'AWB after')
        d[k] = d.get(k, 0) + 1
    return d

sw_cd = calday(switched_e1d)
sa_cd = calday(same_e1d)
keys = ['AWB 1d before', 'Same day', 'AWB after', 'missing']
hdr3 = f"{'Relationship':<18} {'Switched%':>10} {'Same-cour%':>11}"
print(hdr3)
print('-' * len(hdr3))
for k in keys:
    sp = 100 * sw_cd.get(k, 0) / len(switched_e1d) if switched_e1d else 0
    ap = 100 * sa_cd.get(k, 0) / len(same_e1d) if same_e1d else 0
    print(f"{k:<18} {sp:>9.1f}% {ap:>10.1f}%")
print()


# ── Part 4 & 5: split AWB-before / AWB-after and profile each ────────────────
sw_before = [r for r in switched_e1d
             if (to_dt(r.get('digitised_wh_promise', '')) and
                 to_dt(r.get('awb_sticker_printed_ts', '')) and
                 to_dt(r.get('digitised_wh_promise', '')) > to_dt(r.get('awb_sticker_printed_ts', '')))]
sw_after  = [r for r in switched_e1d
             if (to_dt(r.get('digitised_wh_promise', '')) and
                 to_dt(r.get('awb_sticker_printed_ts', '')) and
                 to_dt(r.get('digitised_wh_promise', '')) <= to_dt(r.get('awb_sticker_printed_ts', '')))]

print("=" * 70)
print("PART 4 — Sub-group split (timestamp level)")
print("=" * 70)
print(f"  AWB before WH promise (WH finished early, courier switch incidental):")
print(f"    n={len(sw_before):,}  ({100*len(sw_before)/len(switched_e1d):.1f}%)")
print(f"  AWB after WH promise (WH overran original cutoff, switch triggered):")
print(f"    n={len(sw_after):,}  ({100*len(sw_after)/len(switched_e1d):.1f}%)")
print()

print("=" * 70)
print("PART 5 — WH promise hour by sub-group")
print("=" * 70)

wh_bef = hr_dist(sw_before, 'digitised_wh_promise')
wh_aft = hr_dist(sw_after,  'digitised_wh_promise')
wh_sam = hr_dist(same_e1d,  'digitised_wh_promise')

hdr5 = f"{'Hour':<8} {'Bef (early WH)%':>16} {'Aft (overrun)%':>15} {'Same-cour%':>11}"
print(hdr5)
print('-' * len(hdr5))
for h in range(8, 22):
    bp = 100 * wh_bef.get(h, 0) / len(sw_before) if sw_before else 0
    ap = 100 * wh_aft.get(h, 0) / len(sw_after)  if sw_after  else 0
    sp = 100 * wh_sam.get(h, 0) / len(same_e1d)  if same_e1d  else 0
    if max(bp, ap, sp) < 0.5:
        continue
    print(f"{h:02d}:00   {bp:>15.1f}% {ap:>14.1f}% {sp:>10.1f}%")

print()
for threshold in [14, 15, 16, 17, 18]:
    bp = 100 * sum(v for h, v in wh_bef.items() if h >= threshold) / len(sw_before) if sw_before else 0
    ap = 100 * sum(v for h, v in wh_aft.items() if h >= threshold) / len(sw_after)  if sw_after  else 0
    sp = 100 * sum(v for h, v in wh_sam.items() if h >= threshold) / len(same_e1d)  if same_e1d  else 0
    print(f"  WH promise ≥ {threshold:02d}:00  Before:{bp:5.1f}%  After:{ap:5.1f}%  Same-cour:{sp:5.1f}%")
print()


# ── Part 6: AWB print hour by sub-group ──────────────────────────────────────
print("=" * 70)
print("PART 6 — AWB print hour by sub-group")
print("=" * 70)

ab_bef = hr_dist(sw_before, 'awb_sticker_printed_ts')
ab_aft = hr_dist(sw_after,  'awb_sticker_printed_ts')

hdr6 = f"{'Hour':<8} {'Bef (early WH)%':>16} {'Aft (overrun)%':>15}"
print(hdr6)
print('-' * len(hdr6))
for h in range(8, 22):
    bp = 100 * ab_bef.get(h, 0) / len(sw_before) if sw_before else 0
    ap = 100 * ab_aft.get(h, 0) / len(sw_after)  if sw_after  else 0
    if max(bp, ap) < 0.5:
        continue
    print(f"{h:02d}:00   {bp:>15.1f}% {ap:>14.1f}%")
print()


# ── Part 7: overshoot for AWB-after group ────────────────────────────────────
print("=" * 70)
print("PART 7 — AWB-after sub-group: overshoot (awb - wh_promise)")
print("=" * 70)

overshot = []
for r in sw_after:
    wh  = to_dt(r.get('digitised_wh_promise', ''))
    awb = to_dt(r.get('awb_sticker_printed_ts', ''))
    if wh and awb:
        overshot.append((awb - wh).total_seconds() / 3600)

if overshot:
    s = sorted(overshot)
    print(f"  n: {len(overshot):,}")
    print(f"  Median overshoot : {statistics.median(overshot):.2f}h")
    print(f"  p25              : {s[len(s)//4]:.2f}h")
    print(f"  p75              : {s[3*len(s)//4]:.2f}h")
    print(f"  % within 1h      : {100*sum(1 for g in overshot if g<=1)/len(overshot):.1f}%")
    print(f"  % within 2h      : {100*sum(1 for g in overshot if g<=2)/len(overshot):.1f}%")
    print(f"  % > 4h           : {100*sum(1 for g in overshot if g>4)/len(overshot):.1f}%")
    print()
    print("  Overshoot bucket distribution:")
    for label, lo, hi in [
        ('0–30m', 0, 0.5), ('30m–1h', 0.5, 1), ('1–2h', 1, 2),
        ('2–4h', 2, 4),    ('>4h', 4, 999),
    ]:
        pct = 100 * sum(1 for g in overshot if lo < g <= hi) / len(overshot)
        print(f"    {label:<10} {pct:.1f}%")
