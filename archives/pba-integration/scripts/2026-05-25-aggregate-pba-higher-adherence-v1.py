#!/usr/bin/env python3
"""
2.4 — Adherence where PBA promise is higher (slower) than Internal
===================================================================
Filters to orders where hard_pba_tat_days > hard_internal_tat_days.
On that cohort, computes adherence for both PBA and Internal regimes.

Key question: when PBA commits a slower promise than Internal, does actual
delivery still meet that slower promise? Tests whether PBA's conservative
promise buffers translate into better adherence.

Input:  raw-data/*pba-adherence-base-extract*.csv  (latest match)
Output: outputs/2026-05-25-2-4-pba-higher-adherence-v1.csv

Output schema:
  adherence_bucket   — Early / On-Time / Late / Not Picked Up / Not Delivered
  pba_orders         — count, PBA regime
  pba_pct            — % of cohort
  internal_orders    — count, Internal regime
  internal_pct       — % of cohort

Console prints:
  - PBA-higher cohort size + % of total
  - Whether PBA adherence (Early + On-Time) crosses 80% threshold

Usage:
  python 2026-05-25-aggregate-pba-higher-adherence-v1.py
  python 2026-05-25-aggregate-pba-higher-adherence-v1.py --data-dir ../raw-data
"""

import argparse
import glob
import math
import os

import pandas as pd

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR      = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')
OUTPUT_PATH      = os.path.join(
    PROJECT_DIR, 'outputs', '2026-05-25-2-4-pba-higher-adherence-v1.csv'
)

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='2.4 Adherence where PBA promise is higher (slower) than Internal'
    )
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = find_latest(args.data_dir, '*pba-adherence-base-extract*.csv')
    print(f"Input:  {input_path}")

    df = pd.read_csv(input_path)
    total = len(df)
    print(f"Loaded: {total:,} rows")

    # Filter: PBA promises slower than Internal
    cohort = df[df['hard_pba_tat_days'] > df['hard_internal_tat_days']].copy()
    cohort_size = len(cohort)
    print(f"PBA-higher cohort: {cohort_size:,} orders ({round(cohort_size * 100.0 / total, 2)}% of total)")

    cohort['pickup_time']           = parse_dt(cohort['pickup_time'])
    cohort['delivery_attempt_time'] = parse_dt(cohort['delivery_attempt_time'])

    pickup_null  = cohort['pickup_time'].isna()
    attempt_null = cohort['delivery_attempt_time'].isna() & ~pickup_null
    actual_tat   = compute_actual_tat(cohort['pickup_time'], cohort['delivery_attempt_time'])

    excluded_count = (
        ~pickup_null & ~attempt_null &
        actual_tat.apply(lambda x: pd.notna(x) and x <= 0)
    ).sum()
    print(f"Excluded (actual_tat <= 0): {excluded_count:,} ({round(excluded_count * 100.0 / cohort_size, 2)}%)")

    cohort['pba_bucket']      = classify_adherence(actual_tat, cohort['hard_pba_tat_days'],      pickup_null, attempt_null)
    cohort['internal_bucket'] = classify_adherence(actual_tat, cohort['hard_internal_tat_days'], pickup_null, attempt_null)

    rows = []
    for bucket in BUCKET_ORDER:
        pba_count      = (cohort['pba_bucket']      == bucket).sum()
        internal_count = (cohort['internal_bucket'] == bucket).sum()
        rows.append({
            'adherence_bucket': bucket,
            'pba_orders':       pba_count,
            'pba_pct':          round(pba_count      * 100.0 / cohort_size, 2),
            'internal_orders':  internal_count,
            'internal_pct':     round(internal_count * 100.0 / cohort_size, 2),
        })
    excluded_row = (cohort['pba_bucket'] == 'Excluded').sum()
    rows.append({
        'adherence_bucket': 'Excluded (tat <= 0)',
        'pba_orders':       excluded_row,
        'pba_pct':          round(excluded_row * 100.0 / cohort_size, 2),
        'internal_orders':  excluded_row,
        'internal_pct':     round(excluded_row * 100.0 / cohort_size, 2),
    })

    result = pd.DataFrame(rows)

    # 80% threshold check
    pba_adherent = (
        (cohort['pba_bucket'] == 'Early').sum() +
        (cohort['pba_bucket'] == 'On-Time').sum()
    )
    pba_adherence_rate = round(pba_adherent * 100.0 / cohort_size, 2)
    threshold_met = pba_adherence_rate >= 80.0
    print(f"\nPBA adherence (Early + On-Time): {pba_adherence_rate}% "
          f"— {'✓ MEETS' if threshold_met else '✗ BELOW'} 80% threshold")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nOutput: {OUTPUT_PATH}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
