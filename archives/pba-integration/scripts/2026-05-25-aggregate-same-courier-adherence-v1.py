#!/usr/bin/env python3
"""
1.3 — Same-courier cohort: top-level adherence PBA vs Internal
===============================================================
Filters to orders where hard_pba_partner_id == hard_internal_partner_id,
then computes top-level adherence for both regimes.

In this cohort PBA and Internal select the same courier — actual delivery is
the same for both. Difference in adherence comes purely from TAT promises.

Input:  raw-data/*pba-adherence-base-extract*.csv  (latest match)
Output: outputs/2026-05-25-1-3-same-courier-adherence-v1.csv

Output schema:
  adherence_bucket   — Early / On-Time / Late / Not Picked Up / Not Delivered
  pba_orders         — count, PBA regime
  pba_pct            — % of same-courier cohort
  internal_orders    — count, Internal regime
  internal_pct       — % of same-courier cohort

Console also prints cohort size and % of total orders.

Usage:
  python 2026-05-25-aggregate-same-courier-adherence-v1.py
  python 2026-05-25-aggregate-same-courier-adherence-v1.py --data-dir ../raw-data
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
OUTPUT_PATH = os.path.join(PROJECT_DIR, 'outputs', '2026-05-25-1-3-same-courier-adherence-v1.csv')

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


# ── MAIN ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='1.3 Same-courier cohort: top-level adherence PBA vs Internal'
    )
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR,
                        help='Directory containing base extract CSV')
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = find_latest(args.data_dir, '*pba-adherence-base-extract*.csv')
    print(f"Input:  {input_path}")

    df = pd.read_csv(input_path)
    total_rows = len(df)
    print(f"Loaded: {total_rows:,} rows (full dataset)")

    # Filter to same-courier cohort
    same = df[df['hard_pba_partner_id'] == df['hard_internal_partner_id']].copy()
    cohort_size = len(same)
    cohort_pct  = round(cohort_size * 100.0 / total_rows, 2)
    print(f"Same-courier cohort: {cohort_size:,} orders ({cohort_pct}% of total)")

    same['pickup_time']           = parse_dt(same['pickup_time'])
    same['delivery_attempt_time'] = parse_dt(same['delivery_attempt_time'])

    pickup_null  = same['pickup_time'].isna()
    attempt_null = same['delivery_attempt_time'].isna() & ~pickup_null
    actual_tat   = compute_actual_tat(same['pickup_time'], same['delivery_attempt_time'])

    excluded_count = (
        ~pickup_null & ~attempt_null &
        actual_tat.apply(lambda x: pd.notna(x) and x <= 0)
    ).sum()
    print(f"Excluded (actual_tat <= 0): {excluded_count:,} orders "
          f"({round(excluded_count * 100.0 / cohort_size, 2)}% of cohort)")

    same['pba_bucket']      = classify_adherence(actual_tat, same['hard_pba_tat_days'],
                                                  pickup_null, attempt_null)
    same['internal_bucket'] = classify_adherence(actual_tat, same['hard_internal_tat_days'],
                                                  pickup_null, attempt_null)

    # Denominator = cohort size (including excluded — transparent)
    n = cohort_size

    rows = []
    for bucket in BUCKET_ORDER:
        pba_count      = (same['pba_bucket']      == bucket).sum()
        internal_count = (same['internal_bucket'] == bucket).sum()
        rows.append({
            'adherence_bucket': bucket,
            'pba_orders':       pba_count,
            'pba_pct':          round(pba_count      * 100.0 / n, 2),
            'internal_orders':  internal_count,
            'internal_pct':     round(internal_count * 100.0 / n, 2),
        })

    result = pd.DataFrame(rows)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nOutput: {OUTPUT_PATH}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
