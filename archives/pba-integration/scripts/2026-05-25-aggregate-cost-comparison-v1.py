#!/usr/bin/env python3
"""
3.2 — Per-shipment cost: PBA vs Internal
=========================================
Using the fixed Clickpost PBA pricing snapshot (as of 2026-05-22), computes
the implied per-shipment cost for PBA and Internal courier selections.

Pricing (per shipment, from context/2026-05-22-courier-pricing-snapshot.md):
  Bluedart Express    89.21
  Bluedart Surface    77.17
  Xpressbees Express  83.19
  Xpressbees Surface  65.14
  Delhivery Express   71.15
  Delhivery Surface   59.12
  All others          unmapped (excluded from cost totals)

No RTO or redelivery adjustment applied.

Input:  raw-data/*pba-adherence-base-extract*.csv  (latest match)
Output: outputs/2026-05-25-3-2-cost-comparison-v1.csv

Output schema (two sections stacked):
  regime              — PBA / INTERNAL
  courier_name        — courier
  order_count         — orders assigned to this courier under this regime
  price_per_shipment  — fixed price from snapshot (null if unmapped)
  total_cost          — order_count × price_per_shipment
  share_pct           — % of regime's mapped orders

Console:
  - Unmapped couriers + order counts (both regimes)
  - Total cost PBA vs Internal (mapped orders only)
  - Cost per order PBA vs Internal
  - Cost delta: (pba_cost_per_order − internal_cost_per_order)

Usage:
  python 2026-05-25-aggregate-cost-comparison-v1.py
  python 2026-05-25-aggregate-cost-comparison-v1.py --data-dir ../raw-data
"""

import argparse
import glob
import os

import pandas as pd

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR      = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')
OUTPUT_PATH      = os.path.join(
    PROJECT_DIR, 'outputs', '2026-05-25-3-2-cost-comparison-v1.csv'
)

# Pricing snapshot — 2026-05-22-courier-pricing-snapshot.md
# Keys must match partner_name values in base extract exactly (case-sensitive).
# Add/update entries here if new couriers are onboarded.
PRICING: dict[str, float] = {
    'Bluedart Express':    89.21,
    'Bluedart Surface':    77.17,
    'Xpressbees Express':  83.19,
    'Xpressbees Surface':  65.14,
    'Delhivery Express':   71.15,
    'Delhivery Surface':   59.12,
}


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
        description='3.2 Per-shipment cost: PBA vs Internal'
    )
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR)
    return parser.parse_args()


def build_regime_table(df: pd.DataFrame, name_col: str, label: str) -> pd.DataFrame:
    counts = (
        df.groupby(name_col)
        .size()
        .reset_index(name='order_count')
        .rename(columns={name_col: 'courier_name'})
    )
    counts['regime']             = label
    counts['price_per_shipment'] = counts['courier_name'].map(PRICING)
    counts['total_cost']         = counts['order_count'] * counts['price_per_shipment']

    mapped = counts[counts['price_per_shipment'].notna()].copy()
    mapped_total = mapped['order_count'].sum()
    counts['share_pct'] = (counts['order_count'] * 100.0 / mapped_total).round(2)

    return counts[['regime', 'courier_name', 'order_count',
                   'price_per_shipment', 'total_cost', 'share_pct']] \
           .sort_values('order_count', ascending=False) \
           .reset_index(drop=True)


def main() -> None:
    args = parse_args()

    input_path = find_latest(args.data_dir, '*pba-adherence-base-extract*.csv')
    print(f"Input:  {input_path}")

    df = pd.read_csv(input_path)
    print(f"Loaded: {len(df):,} orders")

    pba_table      = build_regime_table(df, 'pba_partner_name',      'PBA')
    internal_table = build_regime_table(df, 'internal_partner_name', 'INTERNAL')

    # Unmapped couriers
    for label, tbl in [('PBA', pba_table), ('INTERNAL', internal_table)]:
        unmapped = tbl[tbl['price_per_shipment'].isna()]
        if not unmapped.empty:
            print(f"\nUnmapped couriers ({label}) — excluded from cost totals:")
            for _, row in unmapped.iterrows():
                print(f"  {row['courier_name']:<35} {row['order_count']:,} orders")

    # Cost summary
    for label, tbl in [('PBA', pba_table), ('INTERNAL', internal_table)]:
        mapped = tbl[tbl['price_per_shipment'].notna()]
        total_orders = mapped['order_count'].sum()
        total_cost   = mapped['total_cost'].sum()
        cpo          = round(total_cost / total_orders, 4) if total_orders > 0 else float('nan')
        print(f"\n{label}:")
        print(f"  Mapped orders:    {total_orders:,}")
        print(f"  Total cost:       ₹{total_cost:,.2f}")
        print(f"  Cost per order:   ₹{cpo:.4f}")

    pba_mapped      = pba_table[pba_table['price_per_shipment'].notna()]
    internal_mapped = internal_table[internal_table['price_per_shipment'].notna()]

    pba_cpo = (pba_mapped['total_cost'].sum() / pba_mapped['order_count'].sum()
               if pba_mapped['order_count'].sum() > 0 else float('nan'))
    int_cpo = (internal_mapped['total_cost'].sum() / internal_mapped['order_count'].sum()
               if internal_mapped['order_count'].sum() > 0 else float('nan'))
    delta   = round(pba_cpo - int_cpo, 4)
    direction = 'more expensive' if delta > 0 else 'cheaper'
    print(f"\nCost delta (PBA − Internal): ₹{delta:+.4f} per order  →  PBA is {direction}")

    result = pd.concat([pba_table, internal_table], ignore_index=True)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nOutput: {OUTPUT_PATH}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
