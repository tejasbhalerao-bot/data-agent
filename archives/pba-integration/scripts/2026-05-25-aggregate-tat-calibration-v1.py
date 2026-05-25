#!/usr/bin/env python3
"""
2.5 — TAT calibration: ACCURATE / OVERESTIMATED / UNDERESTIMATED
=================================================================
Same-courier cohort only (hard_pba_partner_id == hard_internal_partner_id).

For each regime (PBA and Internal), classifies each order by how well the
promised TAT matched actual delivery:

  ACCURATE      — actual_tat == promised_tat
  OVERESTIMATED — actual_tat < promised_tat  (delivered faster; promise too conservative)
  UNDERESTIMATED— actual_tat > promised_tat  (delivered slower; breach)
  Not Picked Up — pickup_time is null
  Not Delivered — pickup present but no delivery attempt

Console:
  - Same-courier cohort size
  - Mean signed error (actual − promised) per regime
      Positive → promise too optimistic on average (breaches dominate)
      Negative → promise too conservative on average (over-delivers)

Input:  raw-data/*pba-adherence-base-extract*.csv  (latest match)
Output: outputs/2026-05-25-2-5-tat-calibration-v1.csv

Output schema:
  regime             — PBA / INTERNAL
  calibration_bucket — ACCURATE / OVERESTIMATED / UNDERESTIMATED /
                       Not Picked Up / Not Delivered / Excluded (tat <= 0)
  order_count
  pct_of_cohort

Usage:
  python 2026-05-25-aggregate-tat-calibration-v1.py
  python 2026-05-25-aggregate-tat-calibration-v1.py --data-dir ../raw-data
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
    PROJECT_DIR, 'outputs', '2026-05-25-2-5-tat-calibration-v1.csv'
)

BUCKET_ORDER = [
    'ACCURATE',
    'OVERESTIMATED',
    'UNDERESTIMATED',
    'Not Picked Up',
    'Not Delivered',
    'Excluded (tat <= 0)',
]


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
    return delta_seconds.apply(
        lambda s: math.ceil(s / 86400) if pd.notna(s) else float('nan')
    )


def classify_calibration(
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
            return 'Excluded (tat <= 0)'
        promised = row['promised_tat']
        if pd.isna(promised):
            return 'Excluded (tat <= 0)'
        if tat < promised:
            return 'OVERESTIMATED'
        if tat == promised:
            return 'ACCURATE'
        return 'UNDERESTIMATED'

    return df.apply(_classify, axis=1)


def mean_signed_error(
    actual_tat: pd.Series,
    promised_tat: pd.Series,
    pickup_null: pd.Series,
    attempt_null: pd.Series,
) -> float:
    """Mean of (actual - promised) for delivered orders with valid TAT."""
    mask = (
        ~pickup_null &
        ~attempt_null &
        actual_tat.notna() &
        promised_tat.notna() &
        (actual_tat > 0)
    )
    if mask.sum() == 0:
        return float('nan')
    errors = actual_tat[mask] - promised_tat[mask]
    return round(errors.mean(), 3)


def build_regime_table(
    label: str,
    buckets: pd.Series,
    cohort_size: int,
) -> list[dict]:
    rows = []
    for bucket in BUCKET_ORDER:
        count = (buckets == bucket).sum()
        rows.append({
            'regime':             label,
            'calibration_bucket': bucket,
            'order_count':        count,
            'pct_of_cohort':      round(count * 100.0 / cohort_size, 2),
        })
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='2.5 TAT calibration: ACCURATE / OVERESTIMATED / UNDERESTIMATED'
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

    # Same-courier cohort
    same = df[df['hard_pba_partner_id'] == df['hard_internal_partner_id']].copy()
    same = same.dropna(subset=['hard_pba_tat_days', 'hard_internal_tat_days'])
    cohort_size = len(same)
    print(f"Same-courier cohort: {cohort_size:,} orders ({round(cohort_size * 100.0 / total, 2)}% of total)")

    same['pickup_time']           = parse_dt(same['pickup_time'])
    same['delivery_attempt_time'] = parse_dt(same['delivery_attempt_time'])

    pickup_null  = same['pickup_time'].isna()
    attempt_null = same['delivery_attempt_time'].isna() & ~pickup_null
    actual_tat   = compute_actual_tat(same['pickup_time'], same['delivery_attempt_time'])

    pba_buckets      = classify_calibration(actual_tat, same['hard_pba_tat_days'],      pickup_null, attempt_null)
    internal_buckets = classify_calibration(actual_tat, same['hard_internal_tat_days'], pickup_null, attempt_null)

    # Mean signed error
    pba_mse      = mean_signed_error(actual_tat, same['hard_pba_tat_days'],      pickup_null, attempt_null)
    internal_mse = mean_signed_error(actual_tat, same['hard_internal_tat_days'], pickup_null, attempt_null)

    def mse_label(mse: float) -> str:
        if pd.isna(mse):
            return 'n/a'
        direction = 'too optimistic (breaches dominate)' if mse > 0 else 'too conservative (over-delivers)'
        return f"{mse:+.3f} days  →  {direction}"

    print(f"\nMean signed error (actual − promised):")
    print(f"  PBA:      {mse_label(pba_mse)}")
    print(f"  Internal: {mse_label(internal_mse)}")

    rows = (
        build_regime_table('PBA',      pba_buckets,      cohort_size) +
        build_regime_table('INTERNAL', internal_buckets, cohort_size)
    )

    result = pd.DataFrame(rows)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nOutput: {OUTPUT_PATH}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
