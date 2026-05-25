#!/usr/bin/env python3
"""
2.2 — Average promise TAT per courier: PBA vs Internal
=======================================================
Computes mean promised TAT (in days) per courier for both PBA and Internal
regimes. Highlights which couriers see the largest TAT compression under PBA.

Key question: which courier sees the largest gap between PBA and Internal
promise? Is PBA systematically compressing promises for specific couriers?

Input:  raw-data/*pba-adherence-base-extract*.csv  (latest match)
Output: outputs/2026-05-25-2-2-avg-tat-per-courier-v1.csv

Output schema:
  courier_name           — partner name
  pba_order_count        — orders where PBA selected this courier
  pba_avg_tat_days       — mean hard_pba_tat_days for those orders
  internal_order_count   — orders where Internal selected this courier
  internal_avg_tat_days  — mean hard_internal_tat_days for those orders
  tat_compression        — internal_avg_tat_days - pba_avg_tat_days
                           (positive = PBA promises faster than Internal)

Sorted by tat_compression DESC. Couriers present in one regime only → NaN
in the other regime's columns.

Usage:
  python 2026-05-25-aggregate-avg-tat-per-courier-v1.py
  python 2026-05-25-aggregate-avg-tat-per-courier-v1.py --data-dir ../raw-data
"""

import argparse
import glob
import os

import pandas as pd

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR      = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')
OUTPUT_PATH      = os.path.join(
    PROJECT_DIR, 'outputs', '2026-05-25-2-2-avg-tat-per-courier-v1.csv'
)


def find_latest(directory: str, pattern: str) -> str:
    matches = sorted(glob.glob(os.path.join(directory, pattern)))
    if not matches:
        raise FileNotFoundError(
            f"No file matching '{pattern}' in '{directory}'.\n"
            f"Files present: {sorted(os.listdir(directory))}"
        )
    return matches[-1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='2.2 Average promise TAT per courier: PBA vs Internal'
    )
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = find_latest(args.data_dir, '*pba-adherence-base-extract*.csv')
    print(f"Input:  {input_path}")

    df = pd.read_csv(input_path)
    print(f"Loaded: {len(df):,} rows")

    # PBA side: group by pba_partner_name
    pba_grp = (
        df.dropna(subset=['pba_partner_name', 'hard_pba_tat_days'])
        .groupby('pba_partner_name')
        .agg(
            pba_order_count=('hard_pba_tat_days', 'count'),
            pba_avg_tat_days=('hard_pba_tat_days', 'mean'),
        )
        .round(2)
        .rename_axis('courier_name')
        .reset_index()
    )

    # Internal side: group by internal_partner_name
    int_grp = (
        df.dropna(subset=['internal_partner_name', 'hard_internal_tat_days'])
        .groupby('internal_partner_name')
        .agg(
            internal_order_count=('hard_internal_tat_days', 'count'),
            internal_avg_tat_days=('hard_internal_tat_days', 'mean'),
        )
        .round(2)
        .rename_axis('courier_name')
        .reset_index()
    )

    # Outer join — preserve couriers present in either regime
    result = pba_grp.merge(int_grp, on='courier_name', how='outer')

    result['tat_compression'] = (
        result['internal_avg_tat_days'] - result['pba_avg_tat_days']
    ).round(2)

    result = result.sort_values('tat_compression', ascending=False).reset_index(drop=True)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nOutput: {OUTPUT_PATH}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
