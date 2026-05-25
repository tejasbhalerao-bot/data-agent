#!/usr/bin/env python3
"""
1.5 v2 — Same-courier cohort: promise direction vs adherence (with optional pre/post cutoff filter)
====================================================================================================
Adds --cohort / --cutoff-date to support 1.7 pre/post analysis.

Input:  raw-data/*pba-adherence-base-extract*.csv  (latest match)
Output: outputs/2026-05-25-1-5-promise-direction-adherence-v2[_PRE|_POST].csv

Usage:
  python 2026-05-25-aggregate-promise-direction-adherence-v2.py
  python 2026-05-25-aggregate-promise-direction-adherence-v2.py --cohort PRE --cutoff-date 2026-05-20
"""

import argparse
import glob
import math
import os

import pandas as pd

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR      = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')

BUCKET_ORDER    = ['Early', 'On-Time', 'Late', 'Not Picked Up', 'Not Delivered']
DIRECTION_ORDER = ['PBA_FASTER', 'SAME', 'INTERNAL_FASTER']


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
        raise ValueError("allocation_created_at missing — use v2 base extract query")
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


def classify_promise_direction(pba_tat: pd.Series, internal_tat: pd.Series) -> pd.Series:
    def _dir(row: pd.Series) -> str:
        p, i = row['pba'], row['internal']
        if pd.isna(p) or pd.isna(i):
            return 'UNKNOWN'
        if p < i:
            return 'PBA_FASTER'
        if p > i:
            return 'INTERNAL_FASTER'
        return 'SAME'

    return pd.DataFrame({'pba': pba_tat, 'internal': internal_tat}).apply(_dir, axis=1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='1.5 v2 Same-courier cohort: promise direction vs adherence')
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
        PROJECT_DIR, 'outputs', f'2026-05-25-1-5-promise-direction-adherence-v2{suffix}.csv'
    )

    input_path = find_latest(args.data_dir, '*pba-adherence-base-extract*.csv')
    print(f"Input:  {input_path}")

    df = pd.read_csv(input_path)
    print(f"Loaded: {len(df):,} rows (full dataset)")

    df = apply_cohort_filter(df, args.cohort, args.cutoff_date)
    if args.cohort != 'ALL':
        print(f"Cohort {args.cohort} (cutoff {args.cutoff_date}): {len(df):,} orders")

    same = df[df['hard_pba_partner_id'] == df['hard_internal_partner_id']].copy()
    cohort_size = len(same)
    print(f"Same-courier cohort: {cohort_size:,} orders ({round(cohort_size * 100.0 / len(df), 2)}%)")

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

    same['pba_bucket']        = classify_adherence(actual_tat, same['hard_pba_tat_days'],      pickup_null, attempt_null)
    same['internal_bucket']   = classify_adherence(actual_tat, same['hard_internal_tat_days'], pickup_null, attempt_null)
    same['promise_direction'] = classify_promise_direction(same['hard_pba_tat_days'], same['hard_internal_tat_days'])

    print("\nPromise direction distribution (same-courier cohort):")
    for d in DIRECTION_ORDER:
        n = (same['promise_direction'] == d).sum()
        print(f"  {d}: {n:,} ({round(n * 100.0 / cohort_size, 2)}%)")
    unknown = (same['promise_direction'] == 'UNKNOWN').sum()
    if unknown:
        print(f"  UNKNOWN (null TAT): {unknown:,}")

    same_filtered = same[same['pba_bucket'] != 'Excluded'].copy()
    direction_totals = same_filtered.groupby('promise_direction').size().rename('direction_total')

    rows = []
    for direction in DIRECTION_ORDER:
        grp = same_filtered[same_filtered['promise_direction'] == direction]
        if direction not in direction_totals.index:
            continue
        d_total = direction_totals[direction]
        for bucket in BUCKET_ORDER:
            pba_count      = (grp['pba_bucket']      == bucket).sum()
            internal_count = (grp['internal_bucket'] == bucket).sum()
            rows.append({
                'promise_direction':             direction,
                'adherence_bucket':              bucket,
                'direction_orders':              d_total,
                'direction_pct_of_cohort':       round(d_total      * 100.0 / cohort_size, 2),
                'pba_orders':                    pba_count,
                'pba_pct_within_direction':      round(pba_count      * 100.0 / d_total, 2),
                'internal_orders':               internal_count,
                'internal_pct_within_direction': round(internal_count * 100.0 / d_total, 2),
            })

    result = pd.DataFrame(rows)
    direction_order_map = {d: i for i, d in enumerate(DIRECTION_ORDER)}
    bucket_order_map    = {b: i for i, b in enumerate(BUCKET_ORDER)}
    result['_dir_sort']    = result['promise_direction'].map(direction_order_map)
    result['_bucket_sort'] = result['adherence_bucket'].map(bucket_order_map)
    result = (
        result
        .sort_values(['_dir_sort', '_bucket_sort'])
        .drop(columns=['_dir_sort', '_bucket_sort'])
        .reset_index(drop=True)
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result.to_csv(output_path, index=False)

    print(f"\nOutput: {output_path}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
