#!/usr/bin/env python3
"""
2.1 — Promise distribution: PBA vs Internal
============================================
Distribution of promised TAT in days (1d / 2d / 3d / 4d / 5d / 6d / 7d / 7d+)
for both PBA and Internal regimes across all HARD-allocation orders.

Key question: is PBA systematically compressing promises toward lower day buckets,
and if so, is that compression uniform or concentrated in specific couriers / lanes?

Input:  raw-data/*pba-adherence-base-extract*.csv  (latest match)
Output: outputs/2026-05-25-2-1-promise-distribution-v1.csv

Output schema:
  tat_bucket     — 1d / 2d / 3d / 4d / 5d / 6d / 7d / 7d+
  pba_orders     — orders with PBA promise in this bucket
  pba_pct        — % of all orders (PBA promise)
  internal_orders— orders with Internal promise in this bucket
  internal_pct   — % of all orders (Internal promise)

Console also prints:
  - Total orders loaded
  - Null TAT counts (PBA + Internal) excluded from distribution

Usage:
  python 2026-05-25-aggregate-promise-distribution-v1.py
  python 2026-05-25-aggregate-promise-distribution-v1.py --data-dir ../raw-data
"""

import argparse
import glob
import os

import pandas as pd

# ── PATHS ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR      = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')
OUTPUT_PATH      = os.path.join(
    PROJECT_DIR, 'outputs', '2026-05-25-2-1-promise-distribution-v1.csv'
)

BUCKET_ORDER = ['1d', '2d', '3d', '4d', '5d', '6d', '7d', '7d+']


# ── HELPERS ───────────────────────────────────────────────────────────────────

def find_latest(directory: str, pattern: str) -> str:
    matches = sorted(glob.glob(os.path.join(directory, pattern)))
    if not matches:
        raise FileNotFoundError(
            f"No file matching '{pattern}' in '{directory}'.\n"
            f"Files present: {sorted(os.listdir(directory))}"
        )
    return matches[-1]


def bucket_tat(days) -> str:
    if pd.isna(days):
        return None
    d = int(days)
    if d <= 0:
        return None
    if d >= 8:
        return '7d+'
    return f'{d}d'


# ── MAIN ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='2.1 Promise distribution: PBA vs Internal'
    )
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR,
                        help='Directory containing adherence base extract CSV')
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = find_latest(args.data_dir, '*pba-adherence-base-extract*.csv')
    print(f"Input:  {input_path}")

    df = pd.read_csv(input_path)
    total = len(df)
    print(f"Loaded: {total:,} rows")

    pba_null      = df['hard_pba_tat_days'].isna().sum()
    internal_null = df['hard_internal_tat_days'].isna().sum()
    if pba_null:
        print(f"PBA TAT null: {pba_null:,} ({round(pba_null * 100.0 / total, 2)}%) — excluded from distribution")
    if internal_null:
        print(f"Internal TAT null: {internal_null:,} ({round(internal_null * 100.0 / total, 2)}%) — excluded from distribution")

    df['pba_bucket']      = df['hard_pba_tat_days'].apply(bucket_tat)
    df['internal_bucket'] = df['hard_internal_tat_days'].apply(bucket_tat)

    rows = []
    for bucket in BUCKET_ORDER:
        pba_count      = (df['pba_bucket']      == bucket).sum()
        internal_count = (df['internal_bucket'] == bucket).sum()
        rows.append({
            'tat_bucket':      bucket,
            'pba_orders':      pba_count,
            'pba_pct':         round(pba_count      * 100.0 / total, 2),
            'internal_orders': internal_count,
            'internal_pct':    round(internal_count * 100.0 / total, 2),
        })

    result = pd.DataFrame(rows)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nOutput: {OUTPUT_PATH}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
