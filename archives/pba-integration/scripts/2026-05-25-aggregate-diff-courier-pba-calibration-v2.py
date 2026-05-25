#!/usr/bin/env python3
"""
1.6 v2 — Different-courier cohort: PBA calibration for deprioritised Internal courier
(with optional pre/post cutoff filter)
=======================================================================================
Adds --cohort / --cutoff-date to support 1.7 pre/post analysis.
Requires v2 diff-courier-internal-rank query (allocation_created_at column) when --cohort != ALL.

Input:  raw-data/*pba-diff-courier-internal-rank*.csv  (latest match)
Output: outputs/2026-05-25-1-6-diff-courier-pba-calibration-v2[_PRE|_POST].csv

Usage:
  python 2026-05-25-aggregate-diff-courier-pba-calibration-v2.py
  python 2026-05-25-aggregate-diff-courier-pba-calibration-v2.py --cohort PRE --cutoff-date 2026-05-20
"""

import argparse
import glob
import math
import os

import pandas as pd

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR      = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')

CALIBRATION_ORDER = [
    'ACCURATE',
    'PBA_OVERESTIMATED',
    'PBA_UNDERESTIMATED',
    'NOT_IN_PREF_ARRAY',
    'Not Picked Up',
    'Not Delivered',
]


def find_latest(directory: str, pattern: str) -> str:
    matches = sorted(glob.glob(os.path.join(directory, pattern)))
    if not matches:
        raise FileNotFoundError(
            f"No file matching '{pattern}' in '{directory}'.\n"
            f"Files present: {sorted(os.listdir(directory))}"
        )
    return matches[-1]


def apply_cohort_filter(df: pd.DataFrame, cohort: str, cutoff_date: str) -> pd.DataFrame:
    if cohort == 'ALL':
        return df
    if 'allocation_created_at' not in df.columns:
        raise ValueError("allocation_created_at missing — use v2 diff-courier-internal-rank query")
    df = df.copy()
    df['allocation_created_at'] = pd.to_datetime(df['allocation_created_at'], utc=True, errors='coerce')
    cutoff = pd.Timestamp(cutoff_date, tz='UTC')
    if cohort == 'PRE':
        return df[df['allocation_created_at'] < cutoff].reset_index(drop=True)
    return df[df['allocation_created_at'] >= cutoff].reset_index(drop=True)


def parse_dt(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True, errors='coerce')


def compute_actual_tat(pickup: pd.Series, attempt: pd.Series) -> pd.Series:
    delta_seconds = (attempt - pickup).dt.total_seconds()
    return delta_seconds.apply(lambda s: math.ceil(s / 86400) if pd.notna(s) else float('nan'))


def classify_calibration(row: pd.Series) -> str:
    if pd.isna(row['pickup_time']):
        return 'Not Picked Up'
    if pd.isna(row['delivery_attempt_time']):
        return 'Not Delivered'
    if pd.isna(row['pba_edd_for_internal_courier']):
        return 'NOT_IN_PREF_ARRAY'
    actual = row['actual_tat_days']
    if pd.isna(actual) or actual <= 0:
        return 'Excluded'
    pba_edd = math.ceil(float(row['pba_edd_for_internal_courier']))
    if actual == pba_edd:
        return 'ACCURATE'
    if pba_edd > actual:
        return 'PBA_OVERESTIMATED'
    return 'PBA_UNDERESTIMATED'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='1.6 v2 Different-courier cohort: PBA calibration')
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR)
    parser.add_argument('--cohort', choices=['ALL', 'PRE', 'POST'], default='ALL')
    parser.add_argument('--cutoff-date', default=None, help='YYYY-MM-DD')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cohort != 'ALL' and not args.cutoff_date:
        raise ValueError("--cutoff-date required when --cohort is PRE or POST")

    suffix = f'_{args.cohort}' if args.cohort != 'ALL' else ''
    output_path = os.path.join(
        PROJECT_DIR, 'outputs', f'2026-05-25-1-6-diff-courier-pba-calibration-v2{suffix}.csv'
    )

    input_path = find_latest(args.data_dir, '*pba-diff-courier-internal-rank*.csv')
    print(f"Input:  {input_path}")

    df = pd.read_csv(input_path)
    print(f"Loaded: {len(df):,} rows (different-courier cohort)")

    df = apply_cohort_filter(df, args.cohort, args.cutoff_date)
    cohort_size = len(df)
    if args.cohort != 'ALL':
        print(f"Cohort {args.cohort} (cutoff {args.cutoff_date}): {cohort_size:,} orders")

    df['pickup_time']           = parse_dt(df['pickup_time'])
    df['delivery_attempt_time'] = parse_dt(df['delivery_attempt_time'])

    actual_tat = compute_actual_tat(df['pickup_time'], df['delivery_attempt_time'])
    df['actual_tat_days'] = actual_tat

    excluded_count = (
        df['pickup_time'].notna() &
        df['delivery_attempt_time'].notna() &
        df['pba_edd_for_internal_courier'].notna() &
        actual_tat.apply(lambda x: pd.notna(x) and x <= 0)
    ).sum()
    print(f"Excluded (actual_tat <= 0): {excluded_count:,} ({round(excluded_count * 100.0 / cohort_size, 2)}%)")

    print("\nInternal courier rank in PBA preference array:")
    not_found = df['internal_courier_pba_rank'].isna().sum()
    print(f"  Not in array: {not_found:,} ({round(not_found * 100.0 / cohort_size, 2)}%)")
    rank_dist = df['internal_courier_pba_rank'].dropna().astype(int).value_counts().sort_index()
    for rank, cnt in rank_dist.items():
        print(f"  Rank {rank}: {cnt:,} ({round(cnt * 100.0 / cohort_size, 2)}%)")

    df['calibration_bucket'] = df.apply(classify_calibration, axis=1)

    rows = []
    for bucket in CALIBRATION_ORDER:
        count = (df['calibration_bucket'] == bucket).sum()
        rows.append({
            'calibration_bucket': bucket,
            'order_count':        count,
            'pct_of_cohort':      round(count * 100.0 / cohort_size, 2),
        })
    excluded_row = (df['calibration_bucket'] == 'Excluded').sum()
    rows.append({
        'calibration_bucket': 'Excluded (tat <= 0)',
        'order_count':        excluded_row,
        'pct_of_cohort':      round(excluded_row * 100.0 / cohort_size, 2),
    })

    result = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result.to_csv(output_path, index=False)

    print(f"\nOutput: {output_path}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
