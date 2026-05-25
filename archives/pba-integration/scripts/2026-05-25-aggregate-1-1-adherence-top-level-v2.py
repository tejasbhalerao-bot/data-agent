#!/usr/bin/env python3
"""
1.1 v2 — Top-level adherence: PBA vs Internal (with optional pre/post cutoff filter)
======================================================================================
Adds --cohort / --cutoff-date to support 1.7 pre/post analysis.
Requires v2 base extract (allocation_created_at column) when --cohort != ALL.

Input:  raw-data/*pba-adherence-base-extract*.csv  (latest match)
Output: outputs/2026-05-25-1-1-adherence-top-level-v2[_PRE|_POST].csv

Usage:
  python 2026-05-25-aggregate-1-1-adherence-top-level-v2.py
  python 2026-05-25-aggregate-1-1-adherence-top-level-v2.py --cohort PRE --cutoff-date 2026-05-20
  python 2026-05-25-aggregate-1-1-adherence-top-level-v2.py --cohort POST --cutoff-date 2026-05-20
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


# ── HELPERS ───────────────────────────────────────────────────────────────────

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

    df = pd.DataFrame({
        'pickup_null':  pickup_null,
        'attempt_null': attempt_null,
        'actual_tat':   actual_tat,
        'promised_tat': promised_tat,
    })
    return df.apply(_classify, axis=1)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='1.1 v2 Top-level adherence: PBA vs Internal')
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR)
    parser.add_argument('--cohort', choices=['ALL', 'PRE', 'POST'], default='ALL',
                        help='ALL (default) | PRE (before cutoff) | POST (on/after cutoff)')
    parser.add_argument('--cutoff-date', default=None,
                        help='YYYY-MM-DD cutoff date. Required when --cohort != ALL')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cohort != 'ALL' and not args.cutoff_date:
        raise ValueError("--cutoff-date required when --cohort is PRE or POST")

    suffix = f'_{args.cohort}' if args.cohort != 'ALL' else ''
    output_path = os.path.join(
        PROJECT_DIR, 'outputs', f'2026-05-25-1-1-adherence-top-level-v2{suffix}.csv'
    )

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

    excluded_mask  = ~pickup_null & ~attempt_null & actual_tat.apply(lambda x: pd.notna(x) and x <= 0)
    excluded_count = excluded_mask.sum()
    print(f"Excluded (actual_tat <= 0): {excluded_count:,} ({round(excluded_count * 100.0 / total_rows, 2)}%)")

    df['pba_bucket']      = classify_adherence(actual_tat, df['hard_pba_tat_days'],      pickup_null, attempt_null)
    df['internal_bucket'] = classify_adherence(actual_tat, df['hard_internal_tat_days'], pickup_null, attempt_null)

    rows = []
    for bucket in BUCKET_ORDER:
        pba_count      = (df['pba_bucket']      == bucket).sum()
        internal_count = (df['internal_bucket'] == bucket).sum()
        rows.append({
            'adherence_bucket': bucket,
            'pba_orders':       pba_count,
            'pba_pct':          round(pba_count      * 100.0 / total_rows, 2),
            'internal_orders':  internal_count,
            'internal_pct':     round(internal_count * 100.0 / total_rows, 2),
        })
    rows.append({
        'adherence_bucket': 'Excluded (tat <= 0)',
        'pba_orders':       excluded_count,
        'pba_pct':          round(excluded_count * 100.0 / total_rows, 2),
        'internal_orders':  excluded_count,
        'internal_pct':     round(excluded_count * 100.0 / total_rows, 2),
    })

    result = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result.to_csv(output_path, index=False)

    print(f"\nOutput: {output_path}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
