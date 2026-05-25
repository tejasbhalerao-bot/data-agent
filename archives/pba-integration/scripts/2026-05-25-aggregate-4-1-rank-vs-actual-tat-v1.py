#!/usr/bin/env python3
"""
4.1 — Does rank 1 actually deliver faster? Rank vs actual TAT
==============================================================
For each order, determines what rank the actual (Internal) courier held in
PBA's preference array, then compares actual delivered TAT across ranks.

Hypothesis: PBA rank 1 should deliver faster than rank 2, which should
deliver faster than rank 3, etc. If this doesn't hold, PBA's ranking signal
is not reliably predicting real-world delivery speed.

Rank assignment:
  Same-courier cohort   → PBA selected = Internal = rank 1 by definition
  Different-courier cohort → Internal courier's rank from diff-courier-internal-rank extract
                             (NULL internal_rank = Internal not in PBA's preference array)

Actual TAT = CEIL((delivery_attempt_time - pickup_time) / 86400 seconds)
Only orders with valid pickup + delivery attempt are included in TAT stats.

Inputs:
  raw-data/*pba-adherence-base-extract*.csv          (latest match)
  raw-data/*pba-diff-courier-internal-rank*.csv      (latest match)

Output: outputs/2026-05-25-4-1-rank-vs-actual-tat-v1.csv

Output schema:
  internal_rank_in_pba_array  — 1 / 2 / 3 / 4 / 5 / 6 / Not In Array
  order_count                 — total orders at this rank
  delivered_order_count       — orders with valid actual TAT
  avg_actual_tat_days         — mean actual TAT for delivered orders
  adherence_rate_pct          — (Early + On-Time) / delivered_order_count × 100
                                using Internal promised TAT as benchmark

Console:
  - Rank distribution (order counts)
  - Whether avg_actual_tat increases monotonically with rank (expected)
  - Flag if rank 2 or 3 outperforms rank 1

Usage:
  python 2026-05-25-aggregate-4-1-rank-vs-actual-tat-v1.py
  python 2026-05-25-aggregate-4-1-rank-vs-actual-tat-v1.py --data-dir ../raw-data
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
    PROJECT_DIR, 'outputs', '2026-05-25-4-1-rank-vs-actual-tat-v1.csv'
)

RANK_ORDER = ['1', '2', '3', '4', '5', '6', 'Not In Array']


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='4.1 Rank vs actual TAT — does rank 1 actually deliver faster?'
    )
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    base_path = find_latest(args.data_dir, '*pba-adherence-base-extract*.csv')
    rank_path = find_latest(args.data_dir, '*pba-diff-courier-internal-rank*.csv')
    print(f"Base extract:       {base_path}")
    print(f"Rank extract:       {rank_path}")

    base = pd.read_csv(base_path)
    rank = pd.read_csv(rank_path)
    print(f"Loaded base: {len(base):,} rows")
    print(f"Loaded rank: {len(rank):,} rows")

    # ----------------------------------------------------------------
    # Same-courier cohort: PBA selected == Internal → Internal is rank 1
    # ----------------------------------------------------------------
    same = base[base['hard_pba_partner_id'] == base['hard_internal_partner_id']].copy()
    same['internal_rank_in_pba_array'] = 1
    print(f"Same-courier cohort (rank=1): {len(same):,} orders")

    # ----------------------------------------------------------------
    # Different-courier cohort: rank from rank extract
    # rank extract column: look for internal_rank or similar
    # ----------------------------------------------------------------
    # Normalise rank column name — the extract may use 'internal_rank' or
    # 'internal_courier_rank' depending on which query version was run.
    rank_col_candidates = [c for c in rank.columns if 'rank' in c.lower()]
    if not rank_col_candidates:
        raise ValueError(
            f"No rank column found in {rank_path}. Columns: {list(rank.columns)}"
        )
    rank_col = rank_col_candidates[0]
    print(f"Using rank column: '{rank_col}'")

    diff = rank[['order_id', rank_col]].copy()
    diff = diff.rename(columns={rank_col: 'internal_rank_in_pba_array'})
    # Merge with base to get TAT and promised TAT
    diff = diff.merge(
        base[['order_id', 'hard_internal_tat_days',
              'pickup_time', 'delivery_attempt_time']],
        on='order_id', how='inner'
    )
    # Rows from same-courier cohort must not also appear in diff extract.
    # Drop any overlap (order_id present in same cohort).
    same_ids = set(same['order_id'])
    diff = diff[~diff['order_id'].isin(same_ids)]
    print(f"Different-courier cohort: {len(diff):,} orders")

    # Normalise rank values: null → 'Not In Array', int → string
    diff['internal_rank_in_pba_array'] = diff['internal_rank_in_pba_array'].apply(
        lambda v: 'Not In Array' if pd.isna(v) else str(int(v))
    )

    # Align same-courier frame columns
    same_aligned = same[['order_id', 'hard_internal_tat_days',
                          'pickup_time', 'delivery_attempt_time',
                          'internal_rank_in_pba_array']].copy()
    same_aligned['internal_rank_in_pba_array'] = same_aligned['internal_rank_in_pba_array'].astype(str)

    combined = pd.concat([same_aligned, diff], ignore_index=True)
    print(f"Combined: {len(combined):,} orders")

    combined['pickup_time']           = parse_dt(combined['pickup_time'])
    combined['delivery_attempt_time'] = parse_dt(combined['delivery_attempt_time'])
    combined['actual_tat']            = compute_actual_tat(
        combined['pickup_time'], combined['delivery_attempt_time']
    )

    # Adherence using Internal promised TAT
    def is_adherent(row: pd.Series) -> bool | None:
        if pd.isna(row['actual_tat']) or row['actual_tat'] <= 0:
            return None
        if pd.isna(row['hard_internal_tat_days']):
            return None
        return row['actual_tat'] <= row['hard_internal_tat_days']

    combined['adherent'] = combined.apply(is_adherent, axis=1)

    rows = []
    for rank_label in RANK_ORDER:
        grp = combined[combined['internal_rank_in_pba_array'] == rank_label]
        n_orders    = len(grp)
        delivered   = grp[grp['actual_tat'].notna() & (grp['actual_tat'] > 0)]
        n_delivered = len(delivered)
        avg_tat     = round(delivered['actual_tat'].mean(), 3) if n_delivered > 0 else float('nan')
        adherent_n  = delivered['adherent'].sum() if n_delivered > 0 else 0
        adh_rate    = round(adherent_n * 100.0 / n_delivered, 2) if n_delivered > 0 else float('nan')
        rows.append({
            'internal_rank_in_pba_array': rank_label,
            'order_count':                n_orders,
            'delivered_order_count':      n_delivered,
            'avg_actual_tat_days':        avg_tat,
            'adherence_rate_pct':         adh_rate,
        })

    result = pd.DataFrame(rows)

    # Monotonicity check on ranks 1–6
    ranked_tats = [
        (r['internal_rank_in_pba_array'], r['avg_actual_tat_days'])
        for _, r in result.iterrows()
        if r['internal_rank_in_pba_array'] != 'Not In Array'
           and pd.notna(r['avg_actual_tat_days'])
           and r['delivered_order_count'] > 0
    ]

    print(f"\nRank vs avg actual TAT:")
    for rank_label, avg in ranked_tats:
        print(f"  Rank {rank_label}: {avg:.3f} days")

    violations = []
    for i in range(1, len(ranked_tats)):
        prev_rank, prev_tat = ranked_tats[i - 1]
        curr_rank, curr_tat = ranked_tats[i]
        if curr_tat < prev_tat:
            violations.append((prev_rank, prev_tat, curr_rank, curr_tat))

    if not violations:
        print("✓ Monotonic — higher rank = slower actual delivery (expected pattern).")
    else:
        print("⚠ Non-monotonic — lower-ranked courier delivers faster than higher rank:")
        for pr, pt, cr, ct in violations:
            print(f"  Rank {pr} avg={pt:.3f}d  >  Rank {cr} avg={ct:.3f}d  ← rank {cr} outperforms rank {pr}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nOutput: {OUTPUT_PATH}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
