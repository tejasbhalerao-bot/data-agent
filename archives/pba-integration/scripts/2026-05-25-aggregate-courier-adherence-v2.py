#!/usr/bin/env python3
"""
1.2 v2 — Courier-level adherence: PBA vs Internal (with optional pre/post cutoff filter)
==========================================================================================
Adds --cohort / --cutoff-date to support 1.7 pre/post analysis.
Requires v2 base extract (allocation_created_at column) when --cohort != ALL.

Input:  raw-data/*pba-adherence-base-extract*.csv  (latest match)
Output:
  outputs/2026-05-25-1-2-courier-adherence-pba-v2[_PRE|_POST].csv
  outputs/2026-05-25-1-2-courier-adherence-internal-v2[_PRE|_POST].csv

Usage:
  python 2026-05-25-aggregate-courier-adherence-v2.py
  python 2026-05-25-aggregate-courier-adherence-v2.py --cohort PRE --cutoff-date 2026-05-20
  python 2026-05-25-aggregate-courier-adherence-v2.py --cohort POST --cutoff-date 2026-05-20
"""

import argparse
import glob
import math
import os

import pandas as pd

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR      = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')

BUCKET_ORDER = ['Early', 'On-Time', 'Late', 'Not Picked Up', 'Not Delivered']


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


def build_courier_summary(df: pd.DataFrame, courier_col: str,
                           bucket_col: str, total_orders: int) -> pd.DataFrame:
    filtered = df[df[bucket_col] != 'Excluded'].copy()
    grouped = (
        filtered
        .groupby([courier_col, bucket_col])
        .size()
        .reset_index(name='order_count')
        .rename(columns={courier_col: 'courier_name', bucket_col: 'adherence_bucket'})
    )
    courier_totals = grouped.groupby('courier_name')['order_count'].transform('sum')
    grouped['pct_within_courier'] = (grouped['order_count'] * 100.0 / courier_totals).round(2)
    grouped['pct_of_total']       = (grouped['order_count'] * 100.0 / total_orders).round(2)
    bucket_order_map = {b: i for i, b in enumerate(BUCKET_ORDER)}
    grouped['_bucket_sort'] = grouped['adherence_bucket'].map(bucket_order_map)
    return (
        grouped
        .sort_values(['courier_name', '_bucket_sort'])
        .drop(columns=['_bucket_sort'])
        .reset_index(drop=True)
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='1.2 v2 Courier-level adherence: PBA vs Internal')
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR)
    parser.add_argument('--cohort', choices=['ALL', 'PRE', 'POST'], default='ALL')
    parser.add_argument('--cutoff-date', default=None, help='YYYY-MM-DD')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cohort != 'ALL' and not args.cutoff_date:
        raise ValueError("--cutoff-date required when --cohort is PRE or POST")

    suffix = f'_{args.cohort}' if args.cohort != 'ALL' else ''
    out_pba      = os.path.join(PROJECT_DIR, 'outputs', f'2026-05-25-1-2-courier-adherence-pba-v2{suffix}.csv')
    out_internal = os.path.join(PROJECT_DIR, 'outputs', f'2026-05-25-1-2-courier-adherence-internal-v2{suffix}.csv')

    input_path = find_latest(args.data_dir, '*pba-adherence-base-extract*.csv')
    print(f"Input:  {input_path}")

    df = pd.read_csv(input_path)
    print(f"Loaded: {len(df):,} rows")

    df = apply_cohort_filter(df, args.cohort, args.cutoff_date)
    total_rows = len(df)
    if args.cohort != 'ALL':
        print(f"Cohort {args.cohort} (cutoff {args.cutoff_date}): {total_rows:,} orders")

    df['pickup_time']           = parse_dt(df['pickup_time'])
    df['delivery_attempt_time'] = parse_dt(df['delivery_attempt_time'])

    pickup_null  = df['pickup_time'].isna()
    attempt_null = df['delivery_attempt_time'].isna() & ~pickup_null
    actual_tat   = compute_actual_tat(df['pickup_time'], df['delivery_attempt_time'])

    excluded_count = (
        ~pickup_null & ~attempt_null &
        actual_tat.apply(lambda x: pd.notna(x) and x <= 0)
    ).sum()
    print(f"Excluded (actual_tat <= 0): {excluded_count:,} ({round(excluded_count * 100.0 / total_rows, 2)}%)")

    df['pba_bucket']      = classify_adherence(actual_tat, df['hard_pba_tat_days'],      pickup_null, attempt_null)
    df['internal_bucket'] = classify_adherence(actual_tat, df['hard_internal_tat_days'], pickup_null, attempt_null)

    pba_summary      = build_courier_summary(df, 'pba_partner_name',      'pba_bucket',      total_rows)
    internal_summary = build_courier_summary(df, 'internal_partner_name', 'internal_bucket', total_rows)

    os.makedirs(os.path.dirname(out_pba), exist_ok=True)
    pba_summary.to_csv(out_pba, index=False)
    internal_summary.to_csv(out_internal, index=False)

    print(f"\nPBA output:      {out_pba}")
    print(pba_summary.to_string(index=False))
    print(f"\nInternal output: {out_internal}")
    print(internal_summary.to_string(index=False))


if __name__ == '__main__':
    main()
