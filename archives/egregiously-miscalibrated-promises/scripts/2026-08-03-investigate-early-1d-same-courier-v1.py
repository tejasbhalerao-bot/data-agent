"""
Early 1d dispatch — same-courier group: timestamp-level verification of the
courier-cutoff rule.

Rule: if digitised_wh_promise time > courier cutoff time, the system pushes
dispatch to D+1. Early 1d manifests when WH actually packs BEFORE the cutoff
on day D, so the courier collects same-day despite the D+1 promise.

Hypothesis: for same-courier Early 1d orders, awb_sticker_printed_ts should
consistently fall BEFORE digitised_wh_promise (same calendar day, earlier
time-of-day) — i.e. the WH finished before the assumed cutoff window.

Parts:
  1. Cohort sizes
  2. awb_ts vs wh_promise_ts: timestamp gap in hours (positive = AWB before promise)
  3. Calendar-day relationship: same day / AWB day before / AWB day after
  4. WH promise hour-of-day distribution (same-courier Early 1d vs On-Time)
  5. AWB print hour-of-day distribution (same-courier Early 1d vs On-Time)
  6. For same-day orders: how many hours before the WH promise did AWB print?
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


early1d_same = []   # same-courier Early 1d
ontime_same  = []   # same-courier On-Time (baseline)

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

        dispatch_dev = (disp_prom - pickup).days

        dig_courier  = row.get('digitised_delivery_partner', '').strip()
        ship_courier = row.get('shipping_delivery_partner', '').strip()
        same_courier = bool(dig_courier and ship_courier and
                            dig_courier == ship_courier)
        if not same_courier:
            continue

        if dispatch_dev == 1:
            early1d_same.append(dict(row))
        elif dispatch_dev == 0:
            ontime_same.append(dict(row))


print(f"Same-courier Early 1d : {len(early1d_same):,}")
print(f"Same-courier On-Time  : {len(ontime_same):,}")
print()


# ── Part 2: timestamp gap (wh_promise - awb) in hours ────────────────────────
print("=" * 72)
print("PART 2 — (digitised_wh_promise - awb_sticker_printed_ts) in hours")
print("  Positive = AWB before WH promise  |  Negative = AWB after WH promise")
print("=" * 72)

def ts_gaps(orders):
    gaps, missing = [], 0
    for r in orders:
        wh  = to_dt(r.get('digitised_wh_promise', ''))
        awb = to_dt(r.get('awb_sticker_printed_ts', ''))
        if not wh or not awb:
            missing += 1
            continue
        gaps.append((wh - awb).total_seconds() / 3600)
    return gaps, missing

e_gaps, e_miss = ts_gaps(early1d_same)
o_gaps, o_miss = ts_gaps(ontime_same)

def p(gaps, threshold):
    return 100 * sum(1 for g in gaps if g > threshold) / len(gaps) if gaps else 0

def pb(gaps, lo, hi):
    return 100 * sum(1 for g in gaps if lo < g <= hi) / len(gaps) if gaps else 0

row_fmt = f"{{:<42}}  {{:>13}}  {{:>13}}"
print(row_fmt.format('Metric', 'Early 1d same', 'On-Time same'))
print('-' * 72)
print(row_fmt.format('n with both timestamps', f"{len(e_gaps):,}", f"{len(o_gaps):,}"))
print(row_fmt.format('null wh_ts or awb_ts', f"{e_miss:,}", f"{o_miss:,}"))
if e_gaps:
    print(row_fmt.format('Median gap (h)', f"{statistics.median(e_gaps):.1f}h", f"{statistics.median(o_gaps):.1f}h"))
    print(row_fmt.format('% AWB before WH promise (gap > 0h)',  f"{p(e_gaps,  0):.1f}%", f"{p(o_gaps,  0):.1f}%"))
    print(row_fmt.format('% AWB >4h before WH promise',         f"{p(e_gaps,  4):.1f}%", f"{p(o_gaps,  4):.1f}%"))
    print(row_fmt.format('% AWB 0–4h before WH promise',        f"{pb(e_gaps, 0, 4):.1f}%", f"{pb(o_gaps, 0, 4):.1f}%"))
    print(row_fmt.format('% AWB after WH promise (gap ≤ 0h)',   f"{100-p(e_gaps, 0):.1f}%", f"{100-p(o_gaps, 0):.1f}%"))
print()


# ── Part 3: calendar-day relationship ────────────────────────────────────────
print("=" * 72)
print("PART 3 — Calendar-day: awb_date vs digitised_wh_promise date")
print("=" * 72)

def calday(orders):
    d = {}
    for r in orders:
        wh  = to_dt(r.get('digitised_wh_promise', ''))
        awb = to_dt(r.get('awb_sticker_printed_ts', ''))
        if not wh or not awb:
            d['missing'] = d.get('missing', 0) + 1
            continue
        diff = (wh.date() - awb.date()).days
        k = (f'AWB {diff}d before WH promise' if diff > 1
             else 'AWB 1d before WH promise' if diff == 1
             else 'Same calendar day' if diff == 0
             else 'AWB after WH promise')
        d[k] = d.get(k, 0) + 1
    return d

e_cd = calday(early1d_same)
o_cd = calday(ontime_same)
keys = ['AWB 1d before WH promise', 'Same calendar day',
        'AWB after WH promise', 'missing']
for k2, v in e_cd.items():
    if k2 not in keys:
        keys.insert(0, k2)

hdr = f"{'Calendar relationship':<32}  {'Early1d n':>9}  {'Early1d %':>10}  {'OT n':>7}  {'OT %':>8}"
print(hdr); print('-' * len(hdr))
for k in keys:
    en = e_cd.get(k, 0); on = o_cd.get(k, 0)
    ep = 100*en/len(early1d_same) if early1d_same else 0
    op = 100*on/len(ontime_same)  if ontime_same  else 0
    print(f"{k:<32}  {en:>9,}  {ep:>9.1f}%  {on:>7,}  {op:>7.1f}%")
print()


# ── Part 4: WH promise hour-of-day ───────────────────────────────────────────
print("=" * 72)
print("PART 4 — digitised_wh_promise hour-of-day")
print("=" * 72)

def hr_dist(orders, field):
    d = {}
    for r in orders:
        ts = to_dt(r.get(field, ''))
        if not ts:
            d['missing'] = d.get('missing', 0) + 1
            continue
        d[ts.hour] = d.get(ts.hour, 0) + 1
    return d

e_wh = hr_dist(early1d_same, 'digitised_wh_promise')
o_wh = hr_dist(ontime_same,  'digitised_wh_promise')

hdr4 = f"{'Hour':<8}  {'Early1d n':>9}  {'Early1d %':>10}  {'OT n':>7}  {'OT %':>8}"
print(hdr4); print('-' * len(hdr4))
for h in range(24):
    en = e_wh.get(h, 0); on = o_wh.get(h, 0)
    if en == 0 and on == 0:
        continue
    ep = 100*en/len(early1d_same) if early1d_same else 0
    op = 100*on/len(ontime_same)  if ontime_same  else 0
    print(f"{h:02d}:00    {en:>9,}  {ep:>9.1f}%  {on:>7,}  {op:>7.1f}%  {'█'*int(ep/1.5)}")
print()


# ── Part 5: AWB print hour-of-day ────────────────────────────────────────────
print("=" * 72)
print("PART 5 — awb_sticker_printed_ts hour-of-day")
print("=" * 72)

e_awb = hr_dist(early1d_same, 'awb_sticker_printed_ts')
o_awb = hr_dist(ontime_same,  'awb_sticker_printed_ts')

hdr5 = f"{'Hour':<8}  {'Early1d n':>9}  {'Early1d %':>10}  {'OT n':>7}  {'OT %':>8}"
print(hdr5); print('-' * len(hdr5))
for h in range(24):
    en = e_awb.get(h, 0); on = o_awb.get(h, 0)
    if en == 0 and on == 0:
        continue
    ep = 100*en/len(early1d_same) if early1d_same else 0
    op = 100*on/len(ontime_same)  if ontime_same  else 0
    print(f"{h:02d}:00    {en:>9,}  {ep:>9.1f}%  {on:>7,}  {op:>7.1f}%  {'█'*int(ep/1.5)}")
print()


# ── Part 6: same-day orders — hours saved before WH promise ──────────────────
print("=" * 72)
print("PART 6 — Same-day orders: hours AWB printed before WH promise")
print("  (only orders where awb_date == wh_promise_date)")
print("=" * 72)

def same_day_gaps(orders):
    gaps = []
    for r in orders:
        wh  = to_dt(r.get('digitised_wh_promise', ''))
        awb = to_dt(r.get('awb_sticker_printed_ts', ''))
        if not wh or not awb:
            continue
        if wh.date() != awb.date():
            continue
        gaps.append((wh - awb).total_seconds() / 3600)
    return gaps

e_sd = same_day_gaps(early1d_same)
o_sd = same_day_gaps(ontime_same)

print(f"{'Metric':<42}  {'Early1d':>13}  {'On-Time':>13}")
print('-' * 72)
print(f"{'n same-day orders':<42}  {len(e_sd):>13,}  {len(o_sd):>13,}")
if e_sd:
    print(f"{'% AWB before WH promise':<42}  {100*sum(1 for g in e_sd if g>0)/len(e_sd):>12.1f}%  {100*sum(1 for g in o_sd if g>0)/len(o_sd) if o_sd else 0:>12.1f}%")
    print(f"{'Median hours before WH promise':<42}  {statistics.median(e_sd):>12.1f}h  {statistics.median(o_sd) if o_sd else 0:>12.1f}h")

print()
print("  Bucket                          Early1d %   On-Time %")
print("  " + "-" * 55)
for label, lo, hi in [
    ('AWB after WH promise (≤0h)',  -999,  0),
    ('0–2h before',                    0,  2),
    ('2–4h before',                    2,  4),
    ('4–6h before',                    4,  6),
    ('6–8h before',                    6,  8),
    ('>8h before',                     8,  999),
]:
    ep = 100*sum(1 for g in e_sd if lo < g <= hi)/len(e_sd) if e_sd else 0
    op = 100*sum(1 for g in o_sd if lo < g <= hi)/len(o_sd) if o_sd else 0
    print(f"  {label:<32}  {ep:>8.1f}%   {op:>8.1f}%")
