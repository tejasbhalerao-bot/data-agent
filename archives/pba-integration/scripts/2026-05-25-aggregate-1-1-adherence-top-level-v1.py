#!/usr/bin/env python3
"""
1.1 — Top-level adherence: PBA vs Internal
============================================
Reads base extract CSV from raw-data/, computes adherence buckets per order,
outputs a summary table to outputs/.

Input:  raw-data/*pba-adherence-base-extract*.csv  (latest match)
Output: outputs/2026-05-25-1-1-adherence-top-level-v1.csv

Adherence classification (applied against both hard_pba_tat_days and hard_internal_tat_days):
  actual_tat_days = CEIL((delivery_attempt_time - pickup_time).total_seconds() / 86400)

  Not Picked Up  — pickup_time is NULL
  Not Delivered  — delivery_attempt_time is NULL (pickup present)
  Excluded       — actual_tat_days <= 0 (data anomaly)
  Early          — actual_tat_days < promised_tat_days
  On-Time        — actual_tat_days == promised_tat_days
  Late           — actual_tat_days > promised_tat_days

Usage:
  python 2026-05-25-aggregate-1-1-adherence-top-level-v1.py
  python 2026-05-25-aggregate-1-1-adherence-top-level-v1.py --data-dir ../raw-data
"""

import argparse
import glob
import math
import os
from typing import Optional

import pandas as pd

# ── PATHS ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')
OUTPUT_PATH      = os.path.join(PROJECT_DIR, 'outputs', '2026-05-25-1-1-adherence-top-level-v1.csv')

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


def parse_dt(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True, errors='coerce')


def compute_actual_tat(pickup: pd.Series, attempt: pd.Series) -> pd.Series:
    """CEIL((delivery_attempt_time - pickup_time) / 86400). Returns float; NaN where inputs are NaT."""
    delta_seconds = (attempt - pickup).dt.total_seconds()
    return delta_seconds.apply(lambda s: math.ceil(s / 86400) if pd.notna(s) else float('nan'))


def classify_adherence(actual_tat: pd.Series, promised_tat: pd.Series,
                        pickup_null: pd.Series, attempt_null: pd.Series) -> pd.Series:
    """
    Returns adherence bucket per order.
    Priority: Not Picked Up > Not Delivered > Excluded > Early/On-Time/Late
    """
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
    parser = argparse.ArgumentParser(description='1.1 Top-level adherence: PBA vs Internal')
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR,
                        help='Directory containing base extract CSV')
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = find_latest(args.data_dir, '*pba-adherence-base-extract*.csv')
    print(f"Input:  {input_path}")

    df = pd.read_csv(input_path)
    total_rows = len(df)
    print(f"Loaded: {total_rows:,} rows")

    # Parse timestamps
    df['pickup_time']           = parse_dt(df['pickup_time'])
    df['delivery_attempt_time'] = parse_dt(df['delivery_attempt_time'])

    pickup_null  = df['pickup_time'].isna()
    attempt_null = df['delivery_attempt_time'].isna() & ~pickup_null

    actual_tat = compute_actual_tat(df['pickup_time'], df['delivery_attempt_time'])

    # Log anomalies
    excluded_mask = (
        ~pickup_null & ~attempt_null &
        actual_tat.apply(lambda x: pd.notna(x) and x <= 0)
    )
    excluded_count = excluded_mask.sum()
    excluded_pct   = round(excluded_count * 100.0 / total_rows, 2)
    print(f"Excluded (actual_tat <= 0): {excluded_count:,} orders ({excluded_pct}% of total)")

    # Classify per regime
    df['pba_bucket']      = classify_adherence(actual_tat, df['hard_pba_tat_days'],
                                               pickup_null, attempt_null)
    df['internal_bucket'] = classify_adherence(actual_tat, df['hard_internal_tat_days'],
                                               pickup_null, attempt_null)

    # Denominator: all orders including excluded (transparent reporting)
    n = total_rows

    summary_rows = []
    for bucket in BUCKET_ORDER:
        pba_count      = (df['pba_bucket']      == bucket).sum()
        internal_count = (df['internal_bucket'] == bucket).sum()
        summary_rows.append({
            'adherence_bucket':    bucket,
            'pba_orders':          pba_count,
            'pba_pct':             round(pba_count      * 100.0 / n, 2),
            'internal_orders':     internal_count,
            'internal_pct':        round(internal_count * 100.0 / n, 2),
        })

    # Excluded row for transparency
    summary_rows.append({
        'adherence_bucket': 'Excluded (tat <= 0)',
        'pba_orders':       excluded_count,
        'pba_pct':          excluded_pct,
        'internal_orders':  excluded_count,
        'internal_pct':     excluded_pct,
    })

    result = pd.DataFrame(summary_rows)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nOutput: {OUTPUT_PATH}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
