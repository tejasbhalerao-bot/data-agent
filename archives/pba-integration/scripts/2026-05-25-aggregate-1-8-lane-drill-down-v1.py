#!/usr/bin/env python3
"""
1.8 — Lane-level drill-down: PBA vs Internal adherence
=======================================================
Same-courier cohort only (hard_pba_partner_id == hard_internal_partner_id).
Groups by warehouse_id × drop_pincode × courier_name. Computes PBA and
Internal adherence rates per lane. Classifies each lane as PBA_BETTER /
SAME / INTERNAL_BETTER.

Run only on lanes where aggregate (1.1–1.6) shows material signal.

Inputs:
  raw-data/*pba-adherence-base-extract*.csv  (latest match — v1/v2/v3 all work)
  raw-data/*pba-lane-extract*.csv            (latest match)

Output: outputs/2026-05-25-1-8-lane-drill-down-v1.csv

Output schema:
  warehouse_id           — source warehouse
  drop_pincode           — destination pincode
  courier_name           — same for both regimes in same-courier cohort
  order_count            — orders in this lane × courier
  pba_adherence_pct      — (Early + On-Time) % under PBA promise
  internal_adherence_pct — (Early + On-Time) % under Internal promise
  pba_late_pct           — Late % under PBA promise
  internal_late_pct      — Late % under Internal promise
  comparison             — PBA_BETTER / SAME / INTERNAL_BETTER

Sorted by order_count DESC (highest-volume lanes first).
Console prints top 10 worst lanes by pba_late_pct + comparison distribution.

Usage:
  python 2026-05-25-aggregate-1-8-lane-drill-down-v1.py
  python 2026-05-25-aggregate-1-8-lane-drill-down-v1.py --data-dir ../raw-data
"""

import argparse
import glob
import math
import os

import pandas as pd

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR      = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')
OUTPUT_PATH      = os.path.join(PROJECT_DIR, 'outputs', '2026-05-25-1-8-lane-drill-down-v1.csv')


# ── HELPERS ───────────────────────────────────────────────────────────────────

def find_latest(directory: str, pattern: str) -> str:
    matches = sorted(glob.glob(os.path.join(directory, pattern)))
    if not matches:
        raise FileNotFoundError(
            f"No file matching '{pattern}' in '{directory}'.\n"
            f"Files present: {sorted(os.listdir(directory))}"
        )
    return matches[-1]


def parse_dt(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors='coerce')


def compute_actual_tat(pickup: pd.Series, attempt: pd.Series) -> pd.Series:
    delta_seconds = (attempt - pickup).dt.total_seconds()
    return delta_seconds.apply(lambda s: math.ceil(s / 86400) if pd.notna(s) else float('nan'))


def classify_adherence(actual_tat: pd.Series, promised_tat: pd.Series,
                        pickup_null: pd.Series, attempt_null: pd.Series) -> pd.Series:
    df = pd.DataFrame({
        'pickup_null':  pickup_null,
        'attempt_null': attempt_null,
        'actual_tat':   actual_tat,
        'promised_tat': promised_tat,
    })

    def _classify(row: pd.Series) -> str:
        if row['pickup_null']:
            return 'Not Picked Up'
        if row['attempt_null']:
            return 'Not Delivered'
        tat = row['actual_tat']
        if pd.isna(tat) or tat <= 0:
            return 'Excluded'
        promised = row['promised_tat']
        if pd.isna(promised):
            return 'Excluded'
        if tat < promised:
            return 'Early'
        if tat == promised:
            return 'On-Time'
        return 'Late'

    return df.apply(_classify, axis=1)


def adherence_pct(bucket_series: pd.Series, total: int) -> float:
    if total == 0:
        return 0.0
    adherent = bucket_series.isin(['Early', 'On-Time']).sum()
    return round(adherent * 100.0 / total, 2)


def late_pct(bucket_series: pd.Series, total: int) -> float:
    if total == 0:
        return 0.0
    late = (bucket_series == 'Late').sum()
    return round(late * 100.0 / total, 2)


def compare(pba_adh: float, int_adh: float) -> str:
    if pba_adh > int_adh:
        return 'PBA_BETTER'
    if pba_adh < int_adh:
        return 'INTERNAL_BETTER'
    return 'SAME'


# ── MAIN ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='1.8 Lane-level drill-down: PBA vs Internal')
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    base_path = find_latest(args.data_dir, '*pba-adherence-base-extract*.csv')
    lane_path = find_latest(args.data_dir, '*pba-lane-extract*.csv')
    print(f"Base extract: {base_path}")
    print(f"Lane extract: {lane_path}")

    base = pd.read_csv(base_path)
    lane = pd.read_csv(lane_path)
    print(f"Loaded base:  {len(base):,} rows")
    print(f"Loaded lane:  {len(lane):,} rows")

    # Merge lane data into base extract
    df = base.merge(lane[['order_id', 'warehouse_id', 'drop_pincode']],
                    on='order_id', how='inner')
    print(f"After merge:  {len(df):,} rows ({len(base) - len(df):,} unmatched dropped)")

    # Same-courier cohort only
    same = df[df['hard_pba_partner_id'] == df['hard_internal_partner_id']].copy()
    cohort_size = len(same)
    print(f"Same-courier cohort: {cohort_size:,} orders ({round(cohort_size * 100.0 / len(df), 2)}%)")

    # Compute adherence
    same['pickup_time']           = parse_dt(same['pickup_time'])
    same['delivery_attempt_time'] = parse_dt(same['delivery_attempt_time'])

    pickup_null  = same['pickup_time'].isna()
    attempt_null = same['delivery_attempt_time'].isna() & ~pickup_null
    actual_tat   = compute_actual_tat(same['pickup_time'], same['delivery_attempt_time'])

    excluded_count = (
        ~pickup_null & ~attempt_null &
        actual_tat.apply(lambda x: pd.notna(x) and x <= 0)
    ).sum()
    print(f"Excluded (actual_tat <= 0): {excluded_count:,} ({round(excluded_count * 100.0 / cohort_size, 2)}%)")

    same['pba_bucket']      = classify_adherence(actual_tat, same['hard_pba_tat_days'],      pickup_null, attempt_null)
    same['internal_bucket'] = classify_adherence(actual_tat, same['hard_internal_tat_days'], pickup_null, attempt_null)

    # Exclude anomalies before lane aggregation
    same_valid = same[same['pba_bucket'] != 'Excluded'].copy()

    # Aggregate per lane
    rows = []
    group_cols = ['warehouse_id', 'drop_pincode', 'pba_partner_name']
    for (wh_id, pincode, courier), grp in same_valid.groupby(group_cols):
        total = len(grp)
        pba_adh  = adherence_pct(grp['pba_bucket'],      total)
        int_adh  = adherence_pct(grp['internal_bucket'], total)
        pba_late = late_pct(grp['pba_bucket'],      total)
        int_late = late_pct(grp['internal_bucket'], total)
        rows.append({
            'warehouse_id':            wh_id,
            'drop_pincode':            pincode,
            'courier_name':            courier,
            'order_count':             total,
            'pba_adherence_pct':       pba_adh,
            'internal_adherence_pct':  int_adh,
            'pba_late_pct':            pba_late,
            'internal_late_pct':       int_late,
            'comparison':              compare(pba_adh, int_adh),
        })

    result = pd.DataFrame(rows).sort_values('order_count', ascending=False).reset_index(drop=True)

    # ── Console output ──
    print(f"\nTotal lanes: {len(result):,}")

    print("\nComparison distribution:")
    for label in ('PBA_BETTER', 'SAME', 'INTERNAL_BETTER'):
        cnt = (result['comparison'] == label).sum()
        print(f"  {label}: {cnt:,} ({round(cnt * 100.0 / len(result), 2)}%)")

    print("\nTop 10 worst lanes by pba_late_pct:")
    top10 = result.nlargest(10, 'pba_late_pct')[
        ['warehouse_id', 'drop_pincode', 'courier_name', 'order_count',
         'pba_late_pct', 'internal_late_pct', 'comparison']
    ]
    print(top10.to_string(index=False))

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)
    print(f"\nOutput: {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
