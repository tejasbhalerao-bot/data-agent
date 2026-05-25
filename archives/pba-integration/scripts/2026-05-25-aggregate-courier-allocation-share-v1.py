#!/usr/bin/env python3
"""
3.1 — Courier allocation share: PBA vs Internal
================================================
Which couriers gained or lost volume share under PBA compared to Internal?

For every order, PBA selected one courier and Internal selected one courier.
This script counts how many times each courier was selected by each regime
and computes share percentages and the delta.

Input:  raw-data/*pba-adherence-base-extract*.csv  (latest match)
Output: outputs/2026-05-25-3-1-courier-allocation-share-v1.csv

Output schema:
  courier_name        — courier
  pba_order_count     — times PBA selected this courier
  pba_share_pct       — % of all PBA orders
  internal_order_count— times Internal selected this courier
  internal_share_pct  — % of all Internal orders
  share_delta         — pba_share_pct − internal_share_pct
                        positive = PBA gave more volume, negative = PBA gave less

Sorted by share_delta DESC.

Console:
  - Total orders loaded
  - Top 5 gainers (couriers PBA preferred over Internal)
  - Top 5 losers  (couriers PBA shifted volume away from)

Usage:
  python 2026-05-25-aggregate-courier-allocation-share-v1.py
  python 2026-05-25-aggregate-courier-allocation-share-v1.py --data-dir ../raw-data
"""

import argparse
import glob
import os

import pandas as pd

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR      = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')
OUTPUT_PATH      = os.path.join(
    PROJECT_DIR, 'outputs', '2026-05-25-3-1-courier-allocation-share-v1.csv'
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
        description='3.1 Courier allocation share: PBA vs Internal'
    )
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = find_latest(args.data_dir, '*pba-adherence-base-extract*.csv')
    print(f"Input:  {input_path}")

    df = pd.read_csv(input_path)
    total = len(df)
    print(f"Loaded: {total:,} orders")

    # Count PBA selections
    pba_counts = (
        df.groupby('pba_partner_name')
        .size()
        .reset_index(name='pba_order_count')
        .rename(columns={'pba_partner_name': 'courier_name'})
    )

    # Count Internal selections
    internal_counts = (
        df.groupby('internal_partner_name')
        .size()
        .reset_index(name='internal_order_count')
        .rename(columns={'internal_partner_name': 'courier_name'})
    )

    result = pd.merge(pba_counts, internal_counts, on='courier_name', how='outer')
    result['pba_order_count']      = result['pba_order_count'].fillna(0).astype(int)
    result['internal_order_count'] = result['internal_order_count'].fillna(0).astype(int)

    result['pba_share_pct']      = (result['pba_order_count']      * 100.0 / total).round(2)
    result['internal_share_pct'] = (result['internal_order_count'] * 100.0 / total).round(2)
    result['share_delta']        = (result['pba_share_pct'] - result['internal_share_pct']).round(2)

    result = result.sort_values('share_delta', ascending=False).reset_index(drop=True)

    gainers = result[result['share_delta'] > 0].head(5)
    losers  = result[result['share_delta'] < 0].tail(5).sort_values('share_delta')

    print(f"\nTop 5 gainers under PBA (more volume than Internal):")
    for _, row in gainers.iterrows():
        print(f"  {row['courier_name']:<35} +{row['share_delta']:.2f}%  "
              f"(PBA: {row['pba_order_count']:,}  Internal: {row['internal_order_count']:,})")

    print(f"\nTop 5 losers under PBA (less volume than Internal):")
    for _, row in losers.iterrows():
        print(f"  {row['courier_name']:<35} {row['share_delta']:.2f}%  "
              f"(PBA: {row['pba_order_count']:,}  Internal: {row['internal_order_count']:,})")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nOutput: {OUTPUT_PATH}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
