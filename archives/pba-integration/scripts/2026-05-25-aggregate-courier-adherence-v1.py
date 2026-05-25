#!/usr/bin/env python3
"""
1.2 — Courier-level adherence: PBA vs Internal
================================================
Reads base extract CSV, computes adherence per courier, outputs two separate
tables — one for PBA, one for Internal.

Input:  raw-data/*pba-adherence-base-extract*.csv  (latest match)
Output:
  outputs/2026-05-25-1-2-courier-adherence-pba-v1.csv
  outputs/2026-05-25-1-2-courier-adherence-internal-v1.csv

Output schema (both tables):
  courier_name       — partner name
  adherence_bucket   — Early / On-Time / Late / Not Picked Up / Not Delivered
  order_count        — orders in this courier × bucket
  pct_within_courier — % of this courier's total orders
  pct_of_total       — % of all orders across all couriers

Adherence classification (same as 1.1):
  actual_tat_days = CEIL((delivery_attempt_time - pickup_time).total_seconds() / 86400)
  Not Picked Up  — pickup_time is NULL
  Not Delivered  — delivery_attempt_time is NULL (pickup present)
  Excluded       — actual_tat_days <= 0 (logged, excluded from output tables)
  Early          — actual_tat_days < promised_tat_days
  On-Time        — actual_tat_days == promised_tat_days
  Late           — actual_tat_days > promised_tat_days

Usage:
  python 2026-05-25-aggregate-courier-adherence-v1.py
  python 2026-05-25-aggregate-courier-adherence-v1.py --data-dir ../raw-data
"""

import argparse
import glob
import math
import os

import pandas as pd

# ── PATHS ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')
OUTPUT_PBA      = os.path.join(PROJECT_DIR, 'outputs', '2026-05-25-1-2-courier-adherence-pba-v1.csv')
OUTPUT_INTERNAL = os.path.join(PROJECT_DIR, 'outputs', '2026-05-25-1-2-courier-adherence-internal-v1.csv')

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
    delta_seconds = (attempt - pickup).dt.total_seconds()
    return delta_seconds.apply(lambda s: math.ceil(s / 86400) if pd.notna(s) else float('nan'))


def classify_adherence(
    actual_tat: pd.Series,
    promised_tat: pd.Series,
    pickup_null: pd.Series,
    attempt_null: pd.Series,
) -> pd.Series:
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


def build_courier_summary(
    df: pd.DataFrame,
    courier_col: str,
    bucket_col: str,
    total_orders: int,
) -> pd.DataFrame:
    """
    Aggregate order counts per courier × adherence bucket.
    Excludes 'Excluded' bucket from output (logged separately).
    """
    filtered = df[df[bucket_col] != 'Excluded'].copy()

    grouped = (
        filtered
        .groupby([courier_col, bucket_col])
        .size()
        .reset_index(name='order_count')
        .rename(columns={courier_col: 'courier_name', bucket_col: 'adherence_bucket'})
    )

    # pct_within_courier
    courier_totals = grouped.groupby('courier_name')['order_count'].transform('sum')
    grouped['pct_within_courier'] = (grouped['order_count'] * 100.0 / courier_totals).round(2)

    # pct_of_total — denominator is all orders including excluded
    grouped['pct_of_total'] = (grouped['order_count'] * 100.0 / total_orders).round(2)

    # Sort: courier name, then bucket order
    bucket_order_map = {b: i for i, b in enumerate(BUCKET_ORDER)}
    grouped['_bucket_sort'] = grouped['adherence_bucket'].map(bucket_order_map)
    grouped = (
        grouped
        .sort_values(['courier_name', '_bucket_sort'])
        .drop(columns=['_bucket_sort'])
        .reset_index(drop=True)
    )

    return grouped


# ── MAIN ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='1.2 Courier-level adherence: PBA vs Internal')
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

    df['pickup_time']           = parse_dt(df['pickup_time'])
    df['delivery_attempt_time'] = parse_dt(df['delivery_attempt_time'])

    pickup_null  = df['pickup_time'].isna()
    attempt_null = df['delivery_attempt_time'].isna() & ~pickup_null
    actual_tat   = compute_actual_tat(df['pickup_time'], df['delivery_attempt_time'])

    # Log exclusions
    excluded_count = (
        ~pickup_null & ~attempt_null &
        actual_tat.apply(lambda x: pd.notna(x) and x <= 0)
    ).sum()
    print(f"Excluded (actual_tat <= 0): {excluded_count:,} orders "
          f"({round(excluded_count * 100.0 / total_rows, 2)}% of total)")

    df['pba_bucket']      = classify_adherence(actual_tat, df['hard_pba_tat_days'],
                                               pickup_null, attempt_null)
    df['internal_bucket'] = classify_adherence(actual_tat, df['hard_internal_tat_days'],
                                               pickup_null, attempt_null)

    pba_summary      = build_courier_summary(df, 'pba_partner_name',      'pba_bucket',      total_rows)
    internal_summary = build_courier_summary(df, 'internal_partner_name', 'internal_bucket', total_rows)

    os.makedirs(os.path.dirname(OUTPUT_PBA), exist_ok=True)
    pba_summary.to_csv(OUTPUT_PBA, index=False)
    internal_summary.to_csv(OUTPUT_INTERNAL, index=False)

    print(f"\nPBA output:      {OUTPUT_PBA}")
    print(pba_summary.to_string(index=False))
    print(f"\nInternal output: {OUTPUT_INTERNAL}")
    print(internal_summary.to_string(index=False))


if __name__ == '__main__':
    main()
