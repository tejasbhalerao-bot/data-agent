#!/usr/bin/env python3
"""
3.3 — Per-courier per-lane TAT assignment bias
===============================================
Same-courier cohort only (hard_pba_partner_id == hard_internal_partner_id).

For each courier × warehouse × drop_pincode lane, computes average PBA TAT
and average Internal TAT, and the delta (pba_avg - internal_avg).

  Negative delta → PBA more aggressive (lower promise than Internal)
  Zero delta     → same promise
  Positive delta → PBA more conservative (higher promise than Internal)

Key question: is PBA systematically under-promising for couriers it prefers
(giving them a "better" TAT to win ranking), and over-promising for couriers
it deprioritises?

Inputs:
  raw-data/*pba-adherence-base-extract*.csv  (latest match)
  raw-data/*pba-lane-extract*.csv            (latest match)

Output: outputs/2026-05-25-3-3-courier-lane-tat-delta-v1.csv

Output schema:
  courier_name        — courier (same for both regimes in same-courier cohort)
  warehouse_id        — source warehouse
  drop_pincode        — destination pincode
  order_count         — orders in this lane
  pba_avg_tat         — avg PBA promised TAT (days)
  internal_avg_tat    — avg Internal promised TAT (days)
  tat_delta           — pba_avg_tat − internal_avg_tat
  direction           — PBA_LOWER / SAME / PBA_HIGHER

Sorted by tat_delta ASC (most aggressive PBA promises first).

Console:
  - Same-courier cohort size
  - Per-courier summary: mean tat_delta across lanes, flagging < −0.5d
  - Most aggressive lanes (top 10 by tat_delta ASC)

Usage:
  python 2026-05-25-aggregate-courier-lane-tat-delta-v1.py
  python 2026-05-25-aggregate-courier-lane-tat-delta-v1.py --data-dir ../raw-data
"""

import argparse
import glob
import os

import pandas as pd

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR      = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')
OUTPUT_PATH      = os.path.join(
    PROJECT_DIR, 'outputs', '2026-05-25-3-3-courier-lane-tat-delta-v1.csv'
)

AGGRESSION_THRESHOLD = -0.5  # days — flag couriers with mean_tat_delta below this


def find_latest(directory: str, pattern: str) -> str:
    matches = sorted(glob.glob(os.path.join(directory, pattern)))
    if not matches:
        raise FileNotFoundError(
            f"No file matching '{pattern}' in '{directory}'.\n"
            f"Files present: {sorted(os.listdir(directory))}"
        )
    return matches[-1]


def direction_label(delta: float) -> str:
    if delta < 0:
        return 'PBA_LOWER'
    if delta > 0:
        return 'PBA_HIGHER'
    return 'SAME'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='3.3 Per-courier per-lane TAT assignment bias'
    )
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    base_path = find_latest(args.data_dir, '*pba-adherence-base-extract*.csv')
    lane_path = find_latest(args.data_dir, '*pba-lane-extract*.csv')
    print(f"Base extract: {base_path}")
    print(f"Lane extract: {lane_path}")

    base = pd.read_csv(base_path)
    lane = pd.read_csv(lane_path)
    print(f"Loaded base: {len(base):,} rows")
    print(f"Loaded lane: {len(lane):,} rows")

    df = base.merge(lane[['order_id', 'warehouse_id', 'drop_pincode']],
                    on='order_id', how='inner')
    print(f"After merge: {len(df):,} rows")

    # Same-courier cohort
    same = df[df['hard_pba_partner_id'] == df['hard_internal_partner_id']].copy()
    same = same.dropna(subset=['hard_pba_tat_days', 'hard_internal_tat_days'])
    cohort_size = len(same)
    print(f"Same-courier cohort: {cohort_size:,} orders")

    rows = []
    for (courier, wh_id, pincode), grp in same.groupby(
        ['pba_partner_name', 'warehouse_id', 'drop_pincode']
    ):
        n            = len(grp)
        pba_avg      = round(grp['hard_pba_tat_days'].mean(), 3)
        internal_avg = round(grp['hard_internal_tat_days'].mean(), 3)
        delta        = round(pba_avg - internal_avg, 3)
        rows.append({
            'courier_name':    courier,
            'warehouse_id':    wh_id,
            'drop_pincode':    pincode,
            'order_count':     n,
            'pba_avg_tat':     pba_avg,
            'internal_avg_tat': internal_avg,
            'tat_delta':       delta,
            'direction':       direction_label(delta),
        })

    result = (
        pd.DataFrame(rows)
        .sort_values('tat_delta', ascending=True)
        .reset_index(drop=True)
    )

    # Per-courier summary
    courier_summary = (
        result.groupby('courier_name')
        .apply(lambda g: pd.Series({
            'lane_count':       len(g),
            'total_orders':     g['order_count'].sum(),
            'mean_tat_delta':   round((g['tat_delta'] * g['order_count']).sum() / g['order_count'].sum(), 3),
        }))
        .reset_index()
        .sort_values('mean_tat_delta')
    )

    print(f"\nCourier-level TAT delta summary (order-weighted mean):")
    for _, row in courier_summary.iterrows():
        flag = ' ⚠ SYSTEMATICALLY AGGRESSIVE' if row['mean_tat_delta'] < AGGRESSION_THRESHOLD else ''
        print(f"  {row['courier_name']:<35} mean_delta={row['mean_tat_delta']:+.3f}d  "
              f"({int(row['total_orders']):,} orders, {int(row['lane_count'])} lanes){flag}")

    print(f"\nTop 10 most aggressive PBA lanes (lowest tat_delta):")
    print(result.head(10).to_string(index=False))

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nOutput: {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
