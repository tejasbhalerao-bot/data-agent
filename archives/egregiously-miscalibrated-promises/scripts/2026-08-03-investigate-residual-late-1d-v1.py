"""
Residual Late 1d investigation — Non-SDD Inventory egregious orders.

Cohort: dispatch_dev = -1, payment_pending_ts = NULL.
Goal: triangulate what is causing AWB to print late for non-payment-pending orders.

Parts:
  1. Sample orders (30) with all key timestamps
  2. AWB timing relative to dispatch promise (when does AWB print vs promise?)
  3. Invoice creation timing relative to dispatch promise
  4. WH deviation distribution (was WH late?)
  5. Order category mix vs On-Time baseline
  6. Courier mix vs On-Time baseline
  7. AWB-to-dispatch-promise gap in hours (intra-day breakdown)
"""

import csv
from datetime import datetime
import random

CSV = 'archives/egregiously-miscalibrated-promises/raw-data/all-orders-july-2026.csv'

random.seed(42)


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


cohort = []       # residual Late 1d (no pmt pending)
ontime = []       # On-Time (no pmt pending) — for baseline comparison

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
        pmt = row.get('payment_pending_ts', '').strip()

        if pmt:
            continue  # exclude payment pending

        if dispatch_dev == -1:
            cohort.append(dict(row))
        elif dispatch_dev == 0:
            ontime.append(dict(row))

print(f"Residual Late 1d (no pmt pending) : {len(cohort):,}")
print(f"On-Time (no pmt pending) baseline  : {len(ontime):,}")
print()

# ── Part 1: Sample orders ──────────────────────────────────────────────────
print("=" * 100)
print("PART 1 — 30 sample orders (random seed=42)")
print("=" * 100)
sample = random.sample(cohort, min(30, len(cohort)))

FIELDS = [
    'order_id',
    'digitised_dispatch_promise',
    'pickup_time',
    'invoice_create_ts',
    'awb_sticker_printed_ts',
    'digitised_wh_promise',
    'digitised_order_category',
    'digitised_delivery_partner',
    'shipping_delivery_partner',
]

# Print header
print('\t'.join(FIELDS))
for r in sample:
    print('\t'.join(r.get(f, '') or '' for f in FIELDS))
print()

# ── Part 2: AWB timing relative to dispatch promise ────────────────────────
print("=" * 70)
print("PART 2 — AWB print date relative to dispatch promise date")
print("  (awb_date - disp_promise_date) in calendar days")
print("=" * 70)

def awb_vs_promise(orders):
    dist = {}
    for r in orders:
        disp_prom = to_date(r.get('digitised_dispatch_promise', ''))
        awb_ts    = to_dt(r.get('awb_sticker_printed_ts', ''))
        if not disp_prom or not awb_ts:
            dist['missing'] = dist.get('missing', 0) + 1
            continue
        diff = (awb_ts.date() - disp_prom).days
        k = str(diff) if diff >= -2 else '-3+'
        dist[k] = dist.get(k, 0) + 1
    return dist

c_dist = awb_vs_promise(cohort)
o_dist = awb_vs_promise(ontime)

all_keys = sorted(set(list(c_dist.keys()) + list(o_dist.keys())),
                  key=lambda x: int(x) if x.lstrip('-').isdigit() else 99)

hdr = f"{'AWB vs promise (days)':<24}  {'Late1d n':>8}  {'Late1d %':>9}  {'OnTime n':>8}  {'OnTime %':>9}"
print(hdr)
print('-' * len(hdr))
for k in all_keys:
    cn = c_dist.get(k, 0)
    on = o_dist.get(k, 0)
    print(f"{k:<24}  {cn:>8,}  {100*cn/len(cohort):>8.1f}%  {on:>8,}  {100*on/len(ontime):>8.1f}%")
print()

# ── Part 3: Invoice creation relative to dispatch promise ──────────────────
print("=" * 70)
print("PART 3 — Invoice creation date relative to dispatch promise date")
print("  (invoice_date - disp_promise_date) in calendar days")
print("=" * 70)

def inv_vs_promise(orders):
    dist = {}
    for r in orders:
        disp_prom = to_date(r.get('digitised_dispatch_promise', ''))
        inv_ts    = to_dt(r.get('invoice_create_ts', ''))
        if not disp_prom or not inv_ts:
            dist['missing'] = dist.get('missing', 0) + 1
            continue
        diff = (inv_ts.date() - disp_prom).days
        k = str(diff) if abs(diff) <= 3 else ('+4+' if diff > 3 else '-4+')
        dist[k] = dist.get(k, 0) + 1
    return dist

c_inv = inv_vs_promise(cohort)
o_inv = inv_vs_promise(ontime)
all_inv_keys = sorted(set(list(c_inv.keys()) + list(o_inv.keys())),
                      key=lambda x: int(x) if x.lstrip('-').isdigit() else 99)

hdr3 = f"{'Invoice vs promise (days)':<26}  {'Late1d n':>8}  {'Late1d %':>9}  {'OnTime n':>8}  {'OnTime %':>9}"
print(hdr3)
print('-' * len(hdr3))
for k in all_inv_keys:
    cn = c_inv.get(k, 0)
    on = o_inv.get(k, 0)
    print(f"{k:<26}  {cn:>8,}  {100*cn/len(cohort):>8.1f}%  {on:>8,}  {100*on/len(ontime):>8.1f}%")
print()

# ── Part 4: WH deviation ──────────────────────────────────────────────────
print("=" * 70)
print("PART 4 — WH deviation: DATE(digitised_wh_promise) - DATE(awb_sticker_printed_ts)")
print("  Positive = AWB printed before WH promise (WH early)")
print("  Negative = AWB printed after WH promise (WH late)")
print("=" * 70)

def wh_dev(orders):
    dist = {}
    for r in orders:
        wh_prom = to_date(r.get('digitised_wh_promise', ''))
        awb_ts  = to_dt(r.get('awb_sticker_printed_ts', ''))
        if not wh_prom or not awb_ts:
            dist['missing'] = dist.get('missing', 0) + 1
            continue
        diff = (wh_prom - awb_ts.date()).days
        if diff >= 2:
            k = 'Early 2d+'
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
        dist[k] = dist.get(k, 0) + 1
    return dist

WH_ORDER = ['Early 2d+', 'Early 1d', 'On-Time', 'Late 1d', 'Late 2d', 'Late 3d+', 'missing']
c_wh = wh_dev(cohort)
o_wh = wh_dev(ontime)

hdr4 = f"{'WH deviation':<14}  {'Late1d n':>8}  {'Late1d %':>9}  {'OnTime n':>8}  {'OnTime %':>9}"
print(hdr4)
print('-' * len(hdr4))
for k in WH_ORDER:
    cn = c_wh.get(k, 0)
    on = o_wh.get(k, 0)
    if cn == 0 and on == 0:
        continue
    print(f"{k:<14}  {cn:>8,}  {100*cn/len(cohort):>8.1f}%  {on:>8,}  {100*on/len(ontime):>8.1f}%")
print()

# ── Part 5: Order category mix ────────────────────────────────────────────
print("=" * 70)
print("PART 5 — Order category mix vs On-Time baseline")
print("=" * 70)

def cat_dist(orders):
    d = {}
    for r in orders:
        k = r.get('digitised_order_category', '').strip() or 'UNKNOWN'
        d[k] = d.get(k, 0) + 1
    return d

c_cat = cat_dist(cohort)
o_cat = cat_dist(ontime)
all_cats = sorted(set(list(c_cat.keys()) + list(o_cat.keys())), key=lambda x: -c_cat.get(x, 0))

hdr5 = f"{'Category':<36}  {'Late1d n':>8}  {'Late1d %':>9}  {'OnTime n':>8}  {'OnTime %':>9}"
print(hdr5)
print('-' * len(hdr5))
for k in all_cats:
    cn = c_cat.get(k, 0)
    on = o_cat.get(k, 0)
    if cn == 0 and on == 0:
        continue
    print(f"{k:<36}  {cn:>8,}  {100*cn/len(cohort):>8.1f}%  {on:>8,}  {100*on/len(ontime):>8.1f}%")
print()

# ── Part 6: Courier mix ───────────────────────────────────────────────────
print("=" * 70)
print("PART 6 — Courier mix (digitised_delivery_partner) vs On-Time baseline")
print("=" * 70)

def courier_dist(orders):
    d = {}
    for r in orders:
        k = r.get('digitised_delivery_partner', '').strip() or 'UNKNOWN'
        d[k] = d.get(k, 0) + 1
    return d

c_cour = courier_dist(cohort)
o_cour = courier_dist(ontime)
all_couriers = sorted(set(list(c_cour.keys()) + list(o_cour.keys())), key=lambda x: -c_cour.get(x, 0))

hdr6 = f"{'Courier':<28}  {'Late1d n':>8}  {'Late1d %':>9}  {'OnTime n':>8}  {'OnTime %':>9}"
print(hdr6)
print('-' * len(hdr6))
for k in all_couriers[:15]:
    cn = c_cour.get(k, 0)
    on = o_cour.get(k, 0)
    print(f"{k:<28}  {cn:>8,}  {100*cn/len(cohort):>8.1f}%  {on:>8,}  {100*on/len(ontime):>8.1f}%")
print()

# ── Part 7: AWB print hour of day ────────────────────────────────────────
print("=" * 70)
print("PART 7 — Hour of day when AWB was printed (vs On-Time baseline)")
print("=" * 70)

def awb_hour(orders):
    d = {}
    for r in orders:
        awb_ts = to_dt(r.get('awb_sticker_printed_ts', ''))
        if not awb_ts:
            d['missing'] = d.get('missing', 0) + 1
            continue
        h = awb_ts.hour
        bucket = f"{h:02d}:00–{h:02d}:59"
        d[bucket] = d.get(bucket, 0) + 1
    return d

c_hr = awb_hour(cohort)
o_hr = awb_hour(ontime)
all_hrs = sorted(set(list(c_hr.keys()) + list(o_hr.keys())))

hdr7 = f"{'AWB print hour':<16}  {'Late1d n':>8}  {'Late1d %':>9}  {'OnTime n':>8}  {'OnTime %':>9}"
print(hdr7)
print('-' * len(hdr7))
for k in all_hrs:
    cn = c_hr.get(k, 0)
    on = o_hr.get(k, 0)
    if cn == 0 and on == 0:
        continue
    print(f"{k:<16}  {cn:>8,}  {100*cn/len(cohort):>8.1f}%  {on:>8,}  {100*on/len(ontime):>8.1f}%")
