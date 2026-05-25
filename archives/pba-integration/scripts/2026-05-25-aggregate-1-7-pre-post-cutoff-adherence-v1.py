#!/usr/bin/env python3
"""
1.7 — Pre/post cutoff adherence: PBA vs Internal
==================================================
Applies a cutoff date to split orders into PRE and POST cohorts, then computes
top-level adherence for both PBA and Internal regimes in each cohort side-by-side.

Key question: did adherence pattern change after a configuration or go-live event?
Run on questions 1.1–1.6 where aggregate results show material signal.

Input:  raw-data/*pba-adherence-base-extract*.csv  (latest match, must be v2)
Output: outputs/2026-05-25-1-7-pre-post-cutoff-adherence-v1.csv

Output schema:
  cohort                 — PRE / POST
  cohort_orders          — total orders in cohort
  adherence_bucket       — Early / On-Time / Late / Not Picked Up / Not Delivered
  pba_orders             — count, PBA regime
  pba_pct                — % of cohort
  internal_orders        — count, Internal regime
  internal_pct           — % of cohort

Console prints:
  - Cutoff date used
  - PRE cohort size + % of total
  - POST cohort size + % of total
  - Excluded count per cohort

Usage:
  python 2026-05-25-aggregate-1-7-pre-post-cutoff-adherence-v1.py --cutoff-date 2026-05-20
  python 2026-05-25-aggregate-1-7-pre-post-cutoff-adherence-v1.py --cutoff-date 2026-05-20 --data-dir ../raw-data
"""

import argparse
import glob
import math
import os

import pandas as pd

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR      = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')
OUTPUT_PATH      = os.path.join(PROJECT_DIR, 'outputs', '2026-05-25-1-7-pre-post-cutoff-adherence-v1.csv')

BUCKET_ORDER = ['Early', 'On-Time', 'Late', 'Not Picked Up', 'Not Delivered']


def find_latest(directory: str, pattern: str) -> str:
    matches = sorted(glob.glob(os.path.join(directory, pattern)))
    if not matches:
        raise FileNotFoundError(
            f"No file matching '{pattern}' in '{directory}'.\n"
            f"Files present: {sorted(os.listdir(directory))}"
        )
    return matches[-1]


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


def compute_cohort_summary(df: pd.DataFrame, label: str, total_all: int) -> list[dict]:
    """Run adherence classification on a cohort slice and return summary rows."""
    cohort_size = len(df)
    print(f"\n{label} cohort: {cohort_size:,} orders ({round(cohort_size * 100.0 / total_all, 2)}% of total)")

    df = df.copy()
    df['pickup_time']           = parse_dt(df['pickup_time'])
    df['delivery_attempt_time'] = parse_dt(df['delivery_attempt_time'])

    pickup_null  = df['pickup_time'].isna()
    attempt_null = df['delivery_attempt_time'].isna() & ~pickup_null
    actual_tat   = compute_actual_tat(df['pickup_time'], df['delivery_attempt_time'])

    excluded_count = (
        ~pickup_null & ~attempt_null &
        actual_tat.apply(lambda x: pd.notna(x) and x <= 0)
    ).sum()
    print(f"  Excluded (actual_tat <= 0): {excluded_count:,} ({round(excluded_count * 100.0 / cohort_size, 2)}%)")

    df['pba_bucket']      = classify_adherence(actual_tat, df['hard_pba_tat_days'],      pickup_null, attempt_null)
    df['internal_bucket'] = classify_adherence(actual_tat, df['hard_internal_tat_days'], pickup_null, attempt_null)

    rows = []
    for bucket in BUCKET_ORDER:
        pba_count      = (df['pba_bucket']      == bucket).sum()
        internal_count = (df['internal_bucket'] == bucket).sum()
        rows.append({
            'cohort':          label,
            'cohort_orders':   cohort_size,
            'adherence_bucket': bucket,
            'pba_orders':      pba_count,
            'pba_pct':         round(pba_count      * 100.0 / cohort_size, 2),
            'internal_orders': internal_count,
            'internal_pct':    round(internal_count * 100.0 / cohort_size, 2),
        })
    rows.append({
        'cohort':           label,
        'cohort_orders':    cohort_size,
        'adherence_bucket': 'Excluded (tat <= 0)',
        'pba_orders':       excluded_count,
        'pba_pct':          round(excluded_count * 100.0 / cohort_size, 2),
        'internal_orders':  excluded_count,
        'internal_pct':     round(excluded_count * 100.0 / cohort_size, 2),
    })
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='1.7 Pre/post cutoff adherence: PBA vs Internal')
    parser.add_argument('--cutoff-date', required=True, help='YYYY-MM-DD split date')
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = find_latest(args.data_dir, '*pba-adherence-base-extract*.csv')
    print(f"Input:      {input_path}")
    print(f"Cutoff:     {args.cutoff_date}")

    df = pd.read_csv(input_path)
    total = len(df)
    print(f"Loaded:     {total:,} rows")

    if 'allocation_created_at' not in df.columns:
        raise ValueError("allocation_created_at missing — export v2 base extract query")

    df['allocation_created_at'] = pd.to_datetime(df['allocation_created_at'], utc=True, errors='coerce')
    cutoff = pd.Timestamp(args.cutoff_date, tz='UTC')

    pre  = df[df['allocation_created_at'] <  cutoff].reset_index(drop=True)
    post = df[df['allocation_created_at'] >= cutoff].reset_index(drop=True)

    rows = compute_cohort_summary(pre,  'PRE',  total)
    rows += compute_cohort_summary(post, 'POST', total)

    result = pd.DataFrame(rows)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nOutput: {OUTPUT_PATH}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
