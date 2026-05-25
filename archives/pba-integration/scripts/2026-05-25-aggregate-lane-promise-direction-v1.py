#!/usr/bin/env python3
"""
2.3 — Lane promise direction: % lower / same / higher under PBA
================================================================
At warehouse × pincode × courier: what % of orders does PBA promise
faster / same / slower than Internal?

Same-courier cohort only (hard_pba_partner_id == hard_internal_partner_id).
Cross-reference with 1.8 lane drill-down for combined signal.

Inputs:
  raw-data/*pba-adherence-base-extract*.csv  (latest match)
  raw-data/*pba-lane-extract*.csv            (latest match)

Output: outputs/2026-05-25-2-3-lane-promise-direction-v1.csv

Output schema:
  warehouse_id        — source warehouse
  drop_pincode        — destination pincode
  courier_name        — same for both regimes in same-courier cohort
  order_count         — orders in this lane
  pba_lower_count     — PBA promises faster (pba_tat < internal_tat)
  pba_lower_pct
  same_count          — equal promise
  same_pct
  pba_higher_count    — PBA promises slower (pba_tat > internal_tat)
  pba_higher_pct

Sorted by order_count DESC.

Usage:
  python 2026-05-25-aggregate-lane-promise-direction-v1.py
  python 2026-05-25-aggregate-lane-promise-direction-v1.py --data-dir ../raw-data
"""

import argparse
import glob
import os

import pandas as pd

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR      = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')
OUTPUT_PATH      = os.path.join(
    PROJECT_DIR, 'outputs', '2026-05-25-2-3-lane-promise-direction-v1.csv'
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
        description='2.3 Lane promise direction: % lower/same/higher under PBA'
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
    print(f"Loaded base:  {len(base):,} rows")
    print(f"Loaded lane:  {len(lane):,} rows")

    df = base.merge(lane[['order_id', 'warehouse_id', 'drop_pincode']],
                    on='order_id', how='inner')
    print(f"After merge:  {len(df):,} rows")

    same = df[df['hard_pba_partner_id'] == df['hard_internal_partner_id']].copy()
    print(f"Same-courier cohort: {len(same):,} orders")

    same = same.dropna(subset=['hard_pba_tat_days', 'hard_internal_tat_days'])

    rows = []
    for (wh_id, pincode, courier), grp in same.groupby(
        ['warehouse_id', 'drop_pincode', 'pba_partner_name']
    ):
        total  = len(grp)
        lower  = (grp['hard_pba_tat_days'] <  grp['hard_internal_tat_days']).sum()
        equal  = (grp['hard_pba_tat_days'] == grp['hard_internal_tat_days']).sum()
        higher = (grp['hard_pba_tat_days'] >  grp['hard_internal_tat_days']).sum()
        rows.append({
            'warehouse_id':     wh_id,
            'drop_pincode':     pincode,
            'courier_name':     courier,
            'order_count':      total,
            'pba_lower_count':  lower,
            'pba_lower_pct':    round(lower  * 100.0 / total, 2),
            'same_count':       equal,
            'same_pct':         round(equal  * 100.0 / total, 2),
            'pba_higher_count': higher,
            'pba_higher_pct':   round(higher * 100.0 / total, 2),
        })

    result = (
        pd.DataFrame(rows)
        .sort_values('order_count', ascending=False)
        .reset_index(drop=True)
    )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nTotal lanes: {len(result):,}")
    print(f"\nOutput: {OUTPUT_PATH}")
    print(result.head(20).to_string(index=False))


if __name__ == '__main__':
    main()
