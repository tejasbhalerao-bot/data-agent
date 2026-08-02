"""
Non-SDD Non-Inventory — Delivery TAT deviation exploratory study.

For the egregious Non-SDD Non-Inventory superset (n=29,813):
  Part 1: Raw digitised / shipping / actual TAT distributions
  Part 2: TAT deviation buckets (digitised TAT - actual TAT, in days)
  Part 3: H3 — courier change (digitised_delivery_partner != shipping_delivery_partner)
  Part 4: H4 — promise change (digitised TAT days != shipping TAT days)
  Part 5: H5-H8 cross-tab (promise_changed x courier_changed) per TAT bucket
  Part 6: Same-courier orders — dig/ship/actual TAT combos per TAT bucket
"""

import csv
from datetime import datetime

CSV = 'archives/egregiously-miscalibrated-promises/raw-data/all-orders-july-2026.csv'

EGREGIOUS_N = 96424


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


def is_true_str(s):
    if s is None:
        return None
    s = s.strip().lower()
    if s in ('true', '1', 'yes'):
        return True
    if s in ('false', '0', 'no'):
        return False
    return None


def tat_bucket(dev_days):
    if dev_days >= 4:
        return 'Early 4d+'
    if dev_days == 3:
        return 'Early 3d'
    if dev_days == 2:
        return 'Early 2d'
    if dev_days == 1:
        return 'Early 1d'
    if dev_days == 0:
        return 'On-Time'
    if dev_days == -1:
        return 'Late 1d'
    if dev_days == -2:
        return 'Late 2d'
    return 'Late 3d+'


TAT_ORDER = ['Early 4d+', 'Early 3d', 'Early 2d', 'Early 1d',
             'On-Time', 'Late 1d', 'Late 2d', 'Late 3d+']

superset_n = 0
skipped = 0

dig_tat_dist = {}
ship_tat_dist = {}
act_tat_dist = {}

stats = {b: {
    'n': 0,
    'has_shipping': 0,
    'courier_changed': 0,
    'promise_changed': 0,
    'both_changed': 0,
    'courier_only': 0,
    'neither': 0,
    'promise_only': 0,
} for b in TAT_ORDER}

same_courier_tat = {b: {} for b in TAT_ORDER}

with open(CSV, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        del_prom = to_date(row.get('digitised_delivery_promise', ''))
        del_att = to_date(row.get('delivery_attempt_time', ''))
        if not del_prom or not del_att:
            continue
        if abs((del_prom - del_att).days) < 2:
            continue
        if is_true_str(row.get('digitised_is_sdd', '')) is not False:
            continue
        if is_true_str(row.get('digitised_is_inventory', '')) is not False:
            continue

        superset_n += 1

        disp_prom = to_date(row.get('digitised_dispatch_promise', ''))
        pickup = to_date(row.get('pickup_time', ''))
        if not disp_prom or not pickup:
            skipped += 1
            continue

        dig_tat_days = (del_prom - disp_prom).days
        act_tat_days = (del_att - pickup).days

        ship_tat_raw = row.get('shipping_delivery_promise', '').strip()
        ship_tat_days = None
        if ship_tat_raw:
            try:
                ship_tat_days = float(ship_tat_raw)
            except Exception:
                pass

        dev = dig_tat_days - act_tat_days
        bkt = tat_bucket(dev)

        dig_tat_dist[dig_tat_days] = dig_tat_dist.get(dig_tat_days, 0) + 1
        act_tat_dist[act_tat_days] = act_tat_dist.get(act_tat_days, 0) + 1
        if ship_tat_days is not None:
            k = int(round(ship_tat_days))
            ship_tat_dist[k] = ship_tat_dist.get(k, 0) + 1

        s = stats[bkt]
        s['n'] += 1

        dig_partner = row.get('digitised_delivery_partner', '').strip()
        ship_partner = row.get('shipping_delivery_partner', '').strip()
        courier_changed = bool(dig_partner and ship_partner and dig_partner != ship_partner)
        if courier_changed:
            s['courier_changed'] += 1

        promise_changed = False
        if ship_tat_days is not None:
            s['has_shipping'] += 1
            ship_int = int(round(ship_tat_days))
            promise_changed = (dig_tat_days != ship_int)
            if promise_changed:
                s['promise_changed'] += 1

            if promise_changed and courier_changed:
                s['both_changed'] += 1
            elif courier_changed:
                s['courier_only'] += 1
            elif promise_changed:
                s['promise_only'] += 1
            else:
                s['neither'] += 1

            if not courier_changed:
                key = (dig_tat_days, ship_int, act_tat_days)
                same_courier_tat[bkt][key] = same_courier_tat[bkt].get(key, 0) + 1

effective_n = superset_n - skipped

print(f"Non-SDD Non-Inventory egregious superset : {superset_n:,}")
print(f"Skipped (missing dispatch/pickup ts)      : {skipped:,}")
print(f"Effective n for analysis                  : {effective_n:,}")
print()

# ---- Part 1 ----
print("=" * 74)
print("PART 1 — Raw TAT distributions (digitised / shipping / actual)")
print("=" * 74)
hdr = (f"{'TAT (d)':>8}  {'Dig n':>8}  {'Dig %':>7}  "
       f"{'Ship n':>8}  {'Ship %':>7}  {'Act n':>8}  {'Act %':>7}")
print(hdr)
print('-' * len(hdr))
all_days = sorted(set(list(dig_tat_dist) + list(ship_tat_dist) + list(act_tat_dist)))
for d in all_days:
    dn = dig_tat_dist.get(d, 0)
    sn = ship_tat_dist.get(d, 0)
    an = act_tat_dist.get(d, 0)
    if dn == 0 and sn == 0 and an == 0:
        continue
    print(f"{d:>8}  {dn:>8,}  {100*dn/effective_n:>6.1f}%  "
          f"{sn:>8,}  {100*sn/effective_n:>6.1f}%  "
          f"{an:>8,}  {100*an/effective_n:>6.1f}%")
print()

# ---- Part 2 ----
print("=" * 74)
print("PART 2 — TAT deviation buckets (digitised TAT − actual TAT, in days)")
print("  Positive = courier faster than promised (early delivery TAT)")
print("=" * 74)
hdr2 = f"{'Bucket':<12}  {'n':>7}  {'% of set':>9}  {'% of egregious':>15}"
print(hdr2)
print('-' * len(hdr2))
for b in TAT_ORDER:
    bn = stats[b]['n']
    print(f"{b:<12}  {bn:>7,}  {100*bn/effective_n:>8.1f}%  {100*bn/EGREGIOUS_N:>14.1f}%")
print()

# ---- Part 3 ----
print("=" * 74)
print("PART 3 — H3: Courier change (digitised → shipping) per TAT bucket")
print("=" * 74)
hdr3 = f"{'Bucket':<12}  {'n':>7}  {'Courier chg n':>14}  {'Courier chg %':>14}"
print(hdr3)
print('-' * len(hdr3))
for b in TAT_ORDER:
    s = stats[b]
    bn = s['n']
    if bn == 0:
        continue
    print(f"{b:<12}  {bn:>7,}  {s['courier_changed']:>14,}  "
          f"{100*s['courier_changed']/bn:>13.1f}%")
print()

# ---- Part 4 ----
print("=" * 74)
print("PART 4 — H4: Promise change (digitised TAT ≠ shipping TAT) per TAT bucket")
print("  Denominator = orders with shipping TAT present")
print("=" * 74)
hdr4 = f"{'Bucket':<12}  {'n':>7}  {'Has ship TAT':>13}  {'Promise chg':>12}  {'%':>7}"
print(hdr4)
print('-' * len(hdr4))
for b in TAT_ORDER:
    s = stats[b]
    bn = s['n']
    hs = s['has_shipping']
    if bn == 0:
        continue
    pct = 100 * s['promise_changed'] / hs if hs > 0 else 0.0
    print(f"{b:<12}  {bn:>7,}  {hs:>13,}  {s['promise_changed']:>12,}  {pct:>6.1f}%")
print()

# ---- Part 5 ----
print("=" * 74)
print("PART 5 — H5–H8 cross-tab: Promise change × Courier change")
print("  H5=both changed  H6=courier only  H7=neither  H8=promise only")
print("  Denominator = orders with shipping TAT present")
print("=" * 74)
hdr5 = (f"{'Bucket':<12}  {'Has ship':>9}  {'H5 both%':>9}  "
        f"{'H6 Cx%':>8}  {'H7 neither%':>12}  {'H8 Px%':>9}")
print(hdr5)
print('-' * len(hdr5))
for b in TAT_ORDER:
    s = stats[b]
    hs = s['has_shipping']
    if hs == 0:
        continue
    p = lambda x: f"{100*x/hs:6.1f}%"
    print(f"{b:<12}  {hs:>9,}  {p(s['both_changed']):>9}  "
          f"{p(s['courier_only']):>8}  {p(s['neither']):>12}  {p(s['promise_only']):>9}")
print()

# ---- Part 6 ----
print("=" * 74)
print("PART 6 — Same-courier orders: top (dig TAT, ship TAT, actual TAT) combos")
print("  Tests whether shipping layer corrects the digitised TAT promise")
print("=" * 74)
for b in TAT_ORDER:
    combos = same_courier_tat[b]
    if not combos:
        continue
    total = sum(combos.values())
    sorted_combos = sorted(combos.items(), key=lambda x: -x[1])[:8]
    print(f"\n  {b}  (same-courier n={total:,})")
    print(f"  {'Dig TAT':>8}  {'Ship TAT':>9}  {'Act TAT':>8}  {'n':>7}  {'% of bucket':>12}")
    print(f"  {'-'*8}  {'-'*9}  {'-'*8}  {'-'*7}  {'-'*12}")
    for (d, sh, a), cnt in sorted_combos:
        print(f"  {d:>8}  {sh:>9}  {a:>8}  {cnt:>7,}  {100*cnt/total:>11.1f}%")
