"""
Simulation: what happens to dispatch deviation distribution if payment pending is eliminated?

Counterfactual assumption: for every payment-pending order, the AWB would have been
printed at invoice_create_ts + 0.4h (the observed non-pmt baseline).
Same-day courier pickup is universal — so simulated pickup date = DATE(simulated_awb_ts).

For non-pmt orders: actual dispatch deviation unchanged.
For pmt orders: simulated dispatch deviation = digitised_dispatch_promise - simulated_pickup_date.

Superset: Non-SDD Inventory, |delivery deviation| >= 2 calendar days.
"""

import csv
from datetime import datetime, timedelta

CSV = 'archives/egregiously-miscalibrated-promises/raw-data/all-orders-july-2026.csv'

NON_PMT_BASELINE_HOURS = 0.4


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


def bucket(days):
    if days >= 3:
        return 'Early 3d+'
    if days == 2:
        return 'Early 2d'
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
    return 'Late 4d+'


BUCKET_ORDER = ['Early 3d+', 'Early 2d', 'Early 1d', 'On-Time',
                'Late 1d', 'Late 2d', 'Late 3d', 'Late 4d+']

actual   = {b: 0 for b in BUCKET_ORDER}
sim      = {b: 0 for b in BUCKET_ORDER}

# Track individual order shifts for pmt orders
shifts = []  # (actual_dev, sim_dev)

superset_n = 0
skipped = 0
pmt_simulated = 0
pmt_missing_invoice = 0

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

        actual_dev = (disp_prom - pickup).days
        actual[bucket(actual_dev)] += 1

        pmt = row.get('payment_pending_ts', '').strip()

        if not pmt:
            # Non-pmt: simulation unchanged
            sim[bucket(actual_dev)] += 1
        else:
            invoice_ts = to_dt(row.get('invoice_create_ts', ''))
            if not invoice_ts:
                # Can't simulate — keep actual
                sim[bucket(actual_dev)] += 1
                pmt_missing_invoice += 1
                continue

            simulated_awb_ts     = invoice_ts + timedelta(hours=NON_PMT_BASELINE_HOURS)
            simulated_pickup_date = simulated_awb_ts.date()
            sim_dev              = (disp_prom - simulated_pickup_date).days

            sim[bucket(sim_dev)] += 1
            shifts.append((actual_dev, sim_dev))
            pmt_simulated += 1

effective_n = superset_n - skipped

print(f"Non-SDD Inventory egregious superset : {superset_n:,}")
print(f"Skipped (missing dispatch/pickup ts)  : {skipped:,}")
print(f"Effective n                           : {effective_n:,}")
print(f"Pmt orders simulated                  : {pmt_simulated:,}")
print(f"Pmt orders without invoice ts         : {pmt_missing_invoice:,}")
print()

# ── Distribution comparison ────────────────────────────────────────────────
print("=" * 80)
print("DISPATCH DEVIATION DISTRIBUTION — Actual vs Simulated (no payment pending)")
print("=" * 80)
hdr = (f"{'Bucket':<14}  {'Actual n':>8}  {'Actual %':>9}  "
       f"{'Sim n':>8}  {'Sim %':>9}  {'Delta n':>8}  {'Delta pp':>9}")
print(hdr)
print('-' * len(hdr))
for b in BUCKET_ORDER:
    an = actual[b]
    sn = sim[b]
    ap = 100 * an / effective_n
    sp = 100 * sn / effective_n
    dn = sn - an
    dp = sp - ap
    sign = '+' if dp >= 0 else ''
    print(f"{b:<14}  {an:>8,}  {ap:>8.1f}%  {sn:>8,}  {sp:>8.1f}%  "
          f"{dn:>+8,}  {sign}{dp:>7.1f}pp")

print()

# ── Group-level summary ────────────────────────────────────────────────────
def group_n(d, keys):
    return sum(d[k] for k in keys)

early_keys  = ['Early 3d+', 'Early 2d', 'Early 1d']
late_keys   = ['Late 1d', 'Late 2d', 'Late 3d', 'Late 4d+']

print("=" * 60)
print("GROUP SUMMARY")
print("=" * 60)
hdr2 = f"{'Group':<12}  {'Actual n':>8}  {'Actual %':>9}  {'Sim n':>8}  {'Sim %':>9}  {'Delta pp':>9}"
print(hdr2)
print('-' * len(hdr2))
for label, keys in [('Early', early_keys), ('On-Time', ['On-Time']), ('Late', late_keys)]:
    an = group_n(actual, keys)
    sn = group_n(sim, keys)
    ap = 100 * an / effective_n
    sp = 100 * sn / effective_n
    dp = sp - ap
    sign = '+' if dp >= 0 else ''
    print(f"{label:<12}  {an:>8,}  {ap:>8.1f}%  {sn:>8,}  {sp:>8.1f}%  {sign}{dp:>7.1f}pp")

print()

# ── Where pmt orders actually land ────────────────────────────────────────
print("=" * 60)
print("PMT ORDER SHIFTS — where do pmt orders move to?")
print(f"(n={pmt_simulated:,} pmt orders simulated)")
print("=" * 60)
from_to = {}
for (ad, sd) in shifts:
    key = (bucket(ad), bucket(sd))
    from_to[key] = from_to.get(key, 0) + 1

print(f"{'From bucket':<14}  {'To bucket':<14}  {'n':>7}  {'% of pmt':>9}")
print('-' * 50)
for (frm, to), cnt in sorted(from_to.items(), key=lambda x: -x[1]):
    print(f"{frm:<14}  {to:<14}  {cnt:>7,}  {100*cnt/pmt_simulated:>8.1f}%")
