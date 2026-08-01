"""
H16 — Late 3d+ dispatch driven by DOCTOR_AND_HA_CALL_REQUIRED / HA call SLA.

For each dispatch deviation bucket, shows:
  - Total orders
  - % DOCTOR_AND_HA_CALL_REQUIRED
  - % HA_CALL_REQUIRED (HA only, no doctor)
  - % DOCTOR_CALL_REQUIRED (doctor only, no HA)
  - % AUTO_CONFIRM / NO_CALL / other
  - % payment pending (H9, cross-check)

Superset: Non-SDD Inventory, |delivery deviation| >= 2 calendar days.
"""

import csv
from datetime import datetime, date

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
            return date.fromisoformat(s[:10])
        except Exception:
            return None


def is_true_str(s):
    if s is None:
        return None
    s = s.strip().lower()
    if s in ('true', '1', 'yes'):
        return True
    if s in ('false', '0', 'no'):
        return False
    return None


def dispatch_bucket(days):
    if days >= 2:
        return 'Early 2d+'
    if days == 1:
        return 'Early 1d'
    if days == 0:
        return 'On-Time'
    if days == -1:
        return 'Late 1d'
    if days == -2:
        return 'Late 2d'
    if days == -3:
        return 'Late 3d'
    if days == -4:
        return 'Late 4d'
    if days == -5:
        return 'Late 5d'
    return 'Late 6d+'


BUCKET_ORDER = [
    'Early 2d+', 'Early 1d', 'On-Time',
    'Late 1d', 'Late 2d', 'Late 3d', 'Late 4d', 'Late 5d', 'Late 6d+',
]

stats = {b: {
    'n': 0,
    'doctor_and_ha': 0,
    'ha_only': 0,
    'doctor_only': 0,
    'no_call': 0,
    'pmt_pending': 0,
} for b in BUCKET_ORDER}

total_superset = 0
skipped_no_dispatch = 0

with open(CSV, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Egregious superset filter
        del_prom = to_date(row['digitised_delivery_promise'])
        del_att  = to_date(row['delivery_attempt_time'])
        if not del_prom or not del_att:
            continue
        if abs((del_prom - del_att).days) < 2:
            continue
        if is_true_str(row['digitised_is_sdd']) is not False:
            continue
        if is_true_str(row['digitised_is_inventory']) is not True:
            continue

        total_superset += 1

        # Dispatch deviation
        disp_prom = to_date(row['digitised_dispatch_promise'])
        pickup    = to_date(row['pickup_time'])

        if not disp_prom or not pickup:
            skipped_no_dispatch += 1
            continue

        dev_days = (disp_prom - pickup).days
        bkt = dispatch_bucket(dev_days)

        cat = row.get('digitised_order_category', '').strip()
        pmt = row.get('payment_pending_ts', '').strip()

        stats[bkt]['n'] += 1
        if cat == 'DOCTOR_AND_HA_CALL_REQUIRED':
            stats[bkt]['doctor_and_ha'] += 1
        elif cat in ('HA_CALL_REQUIRED', 'HA_CALL_ONLY'):
            stats[bkt]['ha_only'] += 1
        elif cat in ('DOCTOR_CALL_REQUIRED', 'DOCTOR_CALL_ONLY'):
            stats[bkt]['doctor_only'] += 1
        else:
            stats[bkt]['no_call'] += 1

        if pmt:
            stats[bkt]['pmt_pending'] += 1


print(f"Egregious Non-SDD Inventory superset: {total_superset:,}")
print(f"Skipped (missing dispatch/pickup ts): {skipped_no_dispatch:,}")
print()

hdr = (
    f"{'Bucket':<12} {'N':>7}  {'Dr+HA%':>7}  "
    f"{'HA-only%':>8}  {'Dr-only%':>8}  {'No-call%':>8}  {'PmtPend%':>8}"
)
print(hdr)
print('-' * len(hdr))

for bkt in BUCKET_ORDER:
    s = stats[bkt]
    n = s['n']
    if n == 0:
        print(f"{bkt:<12} {'0':>7}")
        continue
    pct = lambda x: f"{100*x/n:6.1f}%"
    print(
        f"{bkt:<12} {n:>7}  {pct(s['doctor_and_ha']):>7}  "
        f"{pct(s['ha_only']):>8}  {pct(s['doctor_only']):>8}  "
        f"{pct(s['no_call']):>8}  {pct(s['pmt_pending']):>8}"
    )

print()
print("HA-involved = DOCTOR_AND_HA_CALL_REQUIRED + HA_CALL_REQUIRED + HA_CALL_ONLY")
print()
hdr2 = f"{'Bucket':<12} {'N':>7}  {'HA-invlvd%':>10}  {'PmtPend%':>8}"
print(hdr2)
print('-' * len(hdr2))
for bkt in BUCKET_ORDER:
    s = stats[bkt]
    n = s['n']
    if n == 0:
        print(f"{bkt:<12} {'0':>7}")
        continue
    ha_inv = s['doctor_and_ha'] + s['ha_only']
    pct = lambda x: f"{100*x/n:6.1f}%"
    print(f"{bkt:<12} {n:>7}  {pct(ha_inv):>10}  {pct(s['pmt_pending']):>8}")
