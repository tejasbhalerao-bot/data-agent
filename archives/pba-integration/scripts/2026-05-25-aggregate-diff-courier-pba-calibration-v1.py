#!/usr/bin/env python3
"""
1.6 — Different-courier cohort: PBA calibration for deprioritised Internal courier
====================================================================================
For orders where PBA selected a different courier than Internal, this script checks
whether PBA's EDD estimate for the Internal courier (the one it deprioritised) was
accurate — i.e. did actual delivery match what PBA predicted?

Key question: is PBA correctly modelling the Internal courier's speed, or is it
systematically over/under-estimating it when deciding to deprioritise it?

Input:  raw-data/*pba-diff-courier-internal-rank*.csv  (latest match)
Output: outputs/2026-05-25-1-6-diff-courier-pba-calibration-v1.csv

Output schema:
  calibration_bucket         — ACCURATE / PBA_OVERESTIMATED / PBA_UNDERESTIMATED /
                               NOT_IN_PREF_ARRAY / Not Picked Up / Not Delivered
  order_count                — orders in bucket
  pct_of_cohort              — % of different-courier cohort

Calibration logic (where pba_edd_for_internal_courier is not null):
  actual_tat_days = CEIL((delivery_attempt_time - pickup_time) / 86400)
  pba_edd_days    = CEIL(pba_edd_for_internal_courier)   -- EDD score is in days
  ACCURATE          — actual_tat_days == pba_edd_days
  PBA_OVERESTIMATED — pba_edd_days > actual_tat_days  (PBA thought slower, courier was faster)
  PBA_UNDERESTIMATED— pba_edd_days < actual_tat_days  (PBA thought faster, courier was slower)

Console also prints:
  - Cohort size + % of all orders
  - % of cohort where Internal courier not found in preference array
  - Internal courier rank distribution (rank 1, 2, 3 …)

Usage:
  python 2026-05-25-aggregate-diff-courier-pba-calibration-v1.py
  python 2026-05-25-aggregate-diff-courier-pba-calibration-v1.py --data-dir ../raw-data
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
OUTPUT_PATH = os.path.join(
    PROJECT_DIR, 'outputs', '2026-05-25-1-6-diff-courier-pba-calibration-v1.csv'
)

CALIBRATION_ORDER = [
    'ACCURATE',
    'PBA_OVERESTIMATED',
    'PBA_UNDERESTIMATED',
    'NOT_IN_PREF_ARRAY',
    'Not Picked Up',
    'Not Delivered',
]


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


# ── MAIN ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='1.6 Different-courier cohort: PBA calibration for Internal courier'
    )
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR,
                        help='Directory containing diff-courier base extract CSV')
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = find_latest(args.data_dir, '*pba-diff-courier-internal-rank*.csv')
    print(f"Input:  {input_path}")

    df = pd.read_csv(input_path)
    cohort_size = len(df)
    print(f"Loaded: {cohort_size:,} rows (different-courier cohort)")

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
    print(f"Excluded (actual_tat <= 0): {excluded_count:,} orders "
          f"({round(excluded_count * 100.0 / cohort_size, 2)}% of cohort)")

    # Internal courier rank distribution
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

    excluded_row_count = (df['calibration_bucket'] == 'Excluded').sum()
    rows.append({
        'calibration_bucket': 'Excluded (tat <= 0)',
        'order_count':        excluded_row_count,
        'pct_of_cohort':      round(excluded_row_count * 100.0 / cohort_size, 2),
    })

    result = pd.DataFrame(rows)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nOutput: {OUTPUT_PATH}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
