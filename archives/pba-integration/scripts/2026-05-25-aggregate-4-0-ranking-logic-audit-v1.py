#!/usr/bin/env python3
"""
4.0 — Ranking logic correctness audit
======================================
Validates that Clickpost PBA's preference array ranking follows the documented
tie-break hierarchy:  EDD ASC → PRICING ASC → AVERAGE_TAT ASC → TOTAL_SCORE ASC

Checks run (all against dp1 vs dp2 comparison — rank 1 vs rank 2):

  Check 1 — Allocation match:
    Does hard_pba_partner_id == dp1_partner_id?
    Mismatches indicate the allocated courier is NOT rank 1 in the preference array.

  Check 2 — EDD ordering:
    Is dp1_edd <= dp2_edd for all orders that have a dp2?
    Violations = dp1 does not have the best EDD score.

  Check 3 — Pricing tie-break:
    When dp1_edd == dp2_edd, is dp1_pricing <= dp2_pricing?
    Violations = pricing tie-break not respected.

  Check 4 — AVERAGE_TAT tie-break:
    When dp1_edd == dp2_edd AND dp1_pricing == dp2_pricing,
    is dp1_avg_tat <= dp2_avg_tat?
    Violations = AVERAGE_TAT tie-break not respected.

Checks 2–4 use dp1 vs dp2 only (first two slots). This is the most visible
and impactful comparison — the gap between rank 1 and rank 2 determines which
courier gets the order.

Input:  raw-data/*pba-allocation-with-pref-array*.csv  (latest match — use v2 extract)
Output: outputs/2026-05-25-4-0-ranking-logic-audit-v1.csv

Output schema:
  check_id            — 1 / 2 / 3 / 4
  check_name          — human-readable label
  total_eligible      — orders where check applies
  pass_count          — orders that pass
  fail_count          — orders that fail
  pass_rate_pct       — pass_count / total_eligible × 100

Console:
  - Flag any check with pass_rate_pct < 95%
  - Print sample failing rows for each failed check (up to 5)

Usage:
  python 2026-05-25-aggregate-4-0-ranking-logic-audit-v1.py
  python 2026-05-25-aggregate-4-0-ranking-logic-audit-v1.py --data-dir ../raw-data
"""

import argparse
import glob
import os

import pandas as pd

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR      = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')
OUTPUT_PATH      = os.path.join(
    PROJECT_DIR, 'outputs', '2026-05-25-4-0-ranking-logic-audit-v1.csv'
)

PASS_THRESHOLD = 95.0  # flag check if pass_rate_pct drops below this


def find_latest(directory: str, pattern: str) -> str:
    matches = sorted(glob.glob(os.path.join(directory, pattern)))
    if not matches:
        raise FileNotFoundError(
            f"No file matching '{pattern}' in '{directory}'.\n"
            f"Files present: {sorted(os.listdir(directory))}"
        )
    return matches[-1]


def run_check(
    check_id: int,
    check_name: str,
    mask_eligible: pd.Series,
    mask_pass: pd.Series,
    df: pd.DataFrame,
    sample_cols: list[str],
) -> dict:
    eligible = mask_eligible.sum()
    passing  = (mask_eligible & mask_pass).sum()
    failing  = eligible - passing
    rate     = round(passing * 100.0 / eligible, 2) if eligible > 0 else float('nan')

    flag = ' ⚠ BELOW THRESHOLD' if (pd.notna(rate) and rate < PASS_THRESHOLD) else ''
    print(f"\nCheck {check_id}: {check_name}")
    print(f"  Eligible: {eligible:,}  Pass: {passing:,}  Fail: {failing:,}  Rate: {rate}%{flag}")

    if failing > 0:
        fail_rows = df[mask_eligible & ~mask_pass][sample_cols].head(5)
        print(f"  Sample failing rows:")
        print(fail_rows.to_string(index=False, max_colwidth=30))

    return {
        'check_id':       check_id,
        'check_name':     check_name,
        'total_eligible': eligible,
        'pass_count':     passing,
        'fail_count':     failing,
        'pass_rate_pct':  rate,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='4.0 Ranking logic correctness audit'
    )
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = find_latest(args.data_dir, '*pba-allocation-with-pref-array*.csv')
    print(f"Input:  {input_path}")

    df = pd.read_csv(input_path)
    total = len(df)
    print(f"Loaded: {total:,} rows")

    # Coerce numeric cols — they may load as object if mixed null/string
    num_cols = [
        'hard_pba_partner_id', 'dp1_partner_id', 'dp2_partner_id',
        'dp1_edd', 'dp2_edd',
        'dp1_pricing', 'dp2_pricing',
        'dp1_avg_tat', 'dp2_avg_tat',
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    results = []

    # ------------------------------------------------------------------
    # Check 1: Allocated courier == rank-1 courier
    # Eligible: all orders where dp1_partner_id is not null
    # ------------------------------------------------------------------
    c1_eligible = df['dp1_partner_id'].notna()
    c1_pass     = df['hard_pba_partner_id'] == df['dp1_partner_id']
    results.append(run_check(
        1, 'Allocated courier == dp1 (rank-1)',
        c1_eligible, c1_pass, df,
        ['order_id', 'hard_pba_partner_id', 'pba_partner_name',
         'dp1_partner_id', 'dp1_account_code'],
    ))

    # ------------------------------------------------------------------
    # Check 2: EDD ordering — dp1_edd <= dp2_edd
    # Eligible: orders where both dp1_edd and dp2_edd are not null
    # ------------------------------------------------------------------
    c2_eligible = df['dp1_edd'].notna() & df['dp2_edd'].notna()
    c2_pass     = df['dp1_edd'] <= df['dp2_edd']
    results.append(run_check(
        2, 'EDD ordering: dp1_edd <= dp2_edd',
        c2_eligible, c2_pass, df,
        ['order_id', 'dp1_account_code', 'dp1_edd', 'dp2_account_code', 'dp2_edd'],
    ))

    # ------------------------------------------------------------------
    # Check 3: Pricing tie-break — when EDD tied, dp1_pricing <= dp2_pricing
    # Eligible: orders where dp1_edd == dp2_edd (both not null)
    # ------------------------------------------------------------------
    c3_eligible = (
        df['dp1_edd'].notna() & df['dp2_edd'].notna() &
        df['dp1_pricing'].notna() & df['dp2_pricing'].notna() &
        (df['dp1_edd'] == df['dp2_edd'])
    )
    c3_pass = df['dp1_pricing'] <= df['dp2_pricing']
    results.append(run_check(
        3, 'Pricing tie-break (EDD tied): dp1_pricing <= dp2_pricing',
        c3_eligible, c3_pass, df,
        ['order_id', 'dp1_account_code', 'dp1_edd', 'dp1_pricing',
         'dp2_account_code', 'dp2_edd', 'dp2_pricing'],
    ))

    # ------------------------------------------------------------------
    # Check 4: AVERAGE_TAT tie-break — when EDD + pricing tied, dp1_avg_tat <= dp2_avg_tat
    # Eligible: orders where dp1_edd == dp2_edd AND dp1_pricing == dp2_pricing
    # ------------------------------------------------------------------
    c4_eligible = (
        df['dp1_edd'].notna() & df['dp2_edd'].notna() &
        df['dp1_pricing'].notna() & df['dp2_pricing'].notna() &
        df['dp1_avg_tat'].notna() & df['dp2_avg_tat'].notna() &
        (df['dp1_edd'] == df['dp2_edd']) &
        (df['dp1_pricing'] == df['dp2_pricing'])
    )
    c4_pass = df['dp1_avg_tat'] <= df['dp2_avg_tat']
    results.append(run_check(
        4, 'AVERAGE_TAT tie-break (EDD+pricing tied): dp1_avg_tat <= dp2_avg_tat',
        c4_eligible, c4_pass, df,
        ['order_id', 'dp1_account_code', 'dp1_edd', 'dp1_pricing', 'dp1_avg_tat',
         'dp2_account_code', 'dp2_edd', 'dp2_pricing', 'dp2_avg_tat'],
    ))

    result = pd.DataFrame(results)

    # Summary
    flagged = result[result['pass_rate_pct'] < PASS_THRESHOLD]
    print(f"\n{'='*60}")
    if flagged.empty:
        print(f"All checks passed (>= {PASS_THRESHOLD}% pass rate). Ranking logic appears correct.")
    else:
        print(f"FLAGGED checks (pass_rate < {PASS_THRESHOLD}%):")
        for _, row in flagged.iterrows():
            print(f"  Check {int(row['check_id'])}: {row['check_name']} — {row['pass_rate_pct']}%")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nOutput: {OUTPUT_PATH}")
    print(result.to_string(index=False))


if __name__ == '__main__':
    main()
