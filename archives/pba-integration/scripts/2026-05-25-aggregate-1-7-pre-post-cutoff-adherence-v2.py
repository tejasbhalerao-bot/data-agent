#!/usr/bin/env python3
"""
1.7 v2 — Pre/post cutoff adherence: per-courier PBA vs Internal
================================================================
For each courier, classifies orders as PRE or POST based on whether
allocation_created_at (IST, time-of-day) falls before or after the
warehouse × courier cutoff time defined in context/2026-05-12-cutoff-times.csv.

v1 used a single calendar --cutoff-date argument and is superseded by this script.

Key question: does placing an order before vs after the cutoff time affect
adherence differently under PBA vs Internal?

Inputs:
  raw-data/*pba-adherence-base-extract*.csv    (v3 extract — needs warehouse_id)
  context/2026-05-12-cutoff-times.csv
  context/warehouse-id-mapping.csv

Output: outputs/2026-05-25-1-7-pre-post-cutoff-adherence-v2.csv

Output schema:
  courier_name       — partner name
  regime             — INTERNAL / PBA
  pre_post           — PRE / POST
  pre_post_total     — total orders in this courier × regime × pre_post
  adherence_bucket   — Early / On-Time / Late / Not Picked Up / Not Delivered
  orders             — count
  pct_within_pre_post — % of pre_post_total

Console prints per courier × regime table + UNKNOWN / exclusion counts.

IMPORTANT — PARTNER → CUTOFF COLUMN MAPPING:
  See PARTNER_CUTOFF_COLUMN_PATTERNS below. If partner names from
  m_system_value_master differ from expected patterns, update this list.
  Run script once and check "Unmatched partner names" in console output.

Usage:
  python 2026-05-25-aggregate-1-7-pre-post-cutoff-adherence-v2.py
  python 2026-05-25-aggregate-1-7-pre-post-cutoff-adherence-v2.py --data-dir ../raw-data
"""

import argparse
import glob
import math
import os
from datetime import time as dtime

import pandas as pd

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR      = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
CONTEXT_DIR      = os.path.join(PROJECT_DIR, 'context')
DEFAULT_DATA_DIR = os.path.join(PROJECT_DIR, 'raw-data')
OUTPUT_PATH      = os.path.join(PROJECT_DIR, 'outputs', '2026-05-25-1-7-pre-post-cutoff-adherence-v2.csv')

CUTOFF_CSV      = os.path.join(CONTEXT_DIR, '2026-05-12-cutoff-times.csv')
WAREHOUSE_MAP_CSV = os.path.join(CONTEXT_DIR, 'warehouse-id-mapping.csv')

BUCKET_ORDER = ['Early', 'On-Time', 'Late', 'Not Picked Up', 'Not Delivered']

# ── COURIER → CUTOFF COLUMN MAPPING ──────────────────────────────────────────
# Matched case-insensitively against partner_name (most specific first).
# Update patterns here if m_system_value_master uses different naming.
PARTNER_CUTOFF_COLUMN_PATTERNS = [
    ('bluedart express',   'Bluedart Express ANKW'),
    ('bluedart',           'Bluedart ANKW'),
    ('delhivery ndd',      'Delhivery NDD'),
    ('delhivery express',  'Delhivery Express ANKW'),
    ('delhivery surface',  'Delhivery Surface ANKW'),
    ('delhivery',          'Delhivery Surface ANKW'),
    ('xpressbees express', 'XpressBees Express ANKW'),
    ('xpressbees surface', 'XpressBees SurfaceANKW'),
    ('xpressbees',         'XpressBees Express ANKW'),
    ('shiprocket ndd',     'Shiprocket NDD'),
    ('shiprocket',         'Shiprocket Courier'),
    ('shadowfax express',  'Shadowfax Express'),
    ('shadowfax surface',  'Shadowfax Surface'),
    ('shadowfax',          'Shadowfax Surface'),
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


def get_cutoff_column(partner_name: str) -> str | None:
    name_lower = partner_name.lower().strip()
    for pattern, col in PARTNER_CUTOFF_COLUMN_PATTERNS:
        if pattern in name_lower:
            return col
    return None


def parse_cutoff_time(val) -> dtime | None:
    if pd.isna(val) or str(val).strip() == '':
        return None
    s = str(val).strip()
    for fmt in ('%H:%M:%S', '%H:%M', '%I:%M %p', '%I:%M:%S %p'):
        try:
            return pd.to_datetime(s, format=fmt).time()
        except Exception:
            continue
    return None


def parse_dt(series: pd.Series) -> pd.Series:
    # IST — parse without UTC assumption
    return pd.to_datetime(series, errors='coerce')


def compute_actual_tat(pickup: pd.Series, attempt: pd.Series) -> pd.Series:
    delta_seconds = (attempt - pickup).dt.total_seconds()
    return delta_seconds.apply(lambda s: math.ceil(s / 86400) if pd.notna(s) else float('nan'))


def classify_adherence(actual_tat: pd.Series, promised_tat: pd.Series,
                        pickup_null: pd.Series, attempt_null: pd.Series) -> pd.Series:
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
            return 'Excluded'
        promised = row['promised_tat']
        if pd.isna(promised):
            return 'Excluded'
        if tat < promised:
            return 'Early'
        if tat == promised:
            return 'On-Time'
        return 'Late'

    return df.apply(_classify, axis=1)


def classify_pre_post(order_time: dtime | None, cutoff_time: dtime | None) -> str:
    if order_time is None or cutoff_time is None:
        return 'UNKNOWN'
    return 'PRE' if order_time < cutoff_time else 'POST'


def build_cutoff_lookup(cutoff_df: pd.DataFrame) -> dict:
    """Build {(city, column): datetime.time} lookup from cutoff CSV."""
    lookup = {}
    for _, row in cutoff_df.iterrows():
        city = str(row['Row Labels']).strip()
        for col in cutoff_df.columns:
            if col in ('Row Labels', 'Source Pincode'):
                continue
            t = parse_cutoff_time(row[col])
            if t is not None:
                lookup[(city, col)] = t
    return lookup


# ── MAIN ──────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='1.7 v2 Pre/post cutoff adherence: per-courier PBA vs Internal'
    )
    parser.add_argument('--data-dir', default=DEFAULT_DATA_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # ── Load inputs ──
    input_path = find_latest(args.data_dir, '*pba-adherence-base-extract*.csv')
    print(f"Input:        {input_path}")

    df = pd.read_csv(input_path)
    total = len(df)
    print(f"Loaded:       {total:,} rows")

    if 'warehouse_id' not in df.columns:
        raise ValueError("warehouse_id missing — export v3 base extract query")

    cutoff_df   = pd.read_csv(CUTOFF_CSV)
    warehouse_df = pd.read_csv(WAREHOUSE_MAP_CSV)

    # Build lookups
    warehouse_city = dict(zip(warehouse_df['warehouse_id'], warehouse_df['city_label']))
    cutoff_lookup  = build_cutoff_lookup(cutoff_df)

    # ── Parse timestamps (IST — no UTC conversion) ──
    df['allocation_created_at'] = parse_dt(df['allocation_created_at'])
    df['order_time_ist']        = df['allocation_created_at'].dt.time

    df['pickup_time']           = parse_dt(df['pickup_time'])
    df['delivery_attempt_time'] = parse_dt(df['delivery_attempt_time'])

    pickup_null  = df['pickup_time'].isna()
    attempt_null = df['delivery_attempt_time'].isna() & ~pickup_null
    actual_tat   = compute_actual_tat(df['pickup_time'], df['delivery_attempt_time'])

    df['pba_bucket']      = classify_adherence(actual_tat, df['hard_pba_tat_days'],      pickup_null, attempt_null)
    df['internal_bucket'] = classify_adherence(actual_tat, df['hard_internal_tat_days'], pickup_null, attempt_null)

    # ── PRE/POST classification per regime ──
    def get_pre_post(row: pd.Series, partner_col: str) -> str:
        city       = warehouse_city.get(row['warehouse_id'])
        if not city or pd.isna(city):
            return 'UNKNOWN'
        partner    = row[partner_col]
        if pd.isna(partner):
            return 'UNKNOWN'
        cutoff_col = get_cutoff_column(str(partner))
        if cutoff_col is None:
            return 'UNKNOWN'
        cutoff_t   = cutoff_lookup.get((city, cutoff_col))
        return classify_pre_post(row['order_time_ist'], cutoff_t)

    df['pba_pre_post']      = df.apply(lambda r: get_pre_post(r, 'pba_partner_name'),      axis=1)
    df['internal_pre_post'] = df.apply(lambda r: get_pre_post(r, 'internal_partner_name'), axis=1)

    # ── Log unmatched partner names ──
    unmatched_pba = df.loc[
        df['pba_pre_post'] == 'UNKNOWN', 'pba_partner_name'
    ].dropna().unique()
    unmatched_int = df.loc[
        df['internal_pre_post'] == 'UNKNOWN', 'internal_partner_name'
    ].dropna().unique()
    if len(unmatched_pba) or len(unmatched_int):
        print("\nUnmatched partner names (update PARTNER_CUTOFF_COLUMN_PATTERNS if wrong):")
        for n in sorted(set(list(unmatched_pba) + list(unmatched_int))):
            print(f"  {n}")

    # ── Build output rows ──
    output_rows = []

    for regime, partner_col, bucket_col, pre_post_col in [
        ('INTERNAL', 'internal_partner_name', 'internal_bucket', 'internal_pre_post'),
        ('PBA',      'pba_partner_name',      'pba_bucket',      'pba_pre_post'),
    ]:
        for courier, grp in df.groupby(partner_col):
            if pd.isna(courier):
                continue
            for pp in ('PRE', 'POST'):
                pp_grp = grp[grp[pre_post_col] == pp]
                pp_total = len(pp_grp)
                if pp_total == 0:
                    continue
                # Exclude anomalies from pct denominator
                valid = pp_grp[pp_grp[bucket_col] != 'Excluded']
                valid_total = len(valid)
                denom = valid_total if valid_total > 0 else 1

                for bucket in BUCKET_ORDER:
                    count = (valid[bucket_col] == bucket).sum()
                    output_rows.append({
                        'courier_name':       courier,
                        'regime':             regime,
                        'pre_post':           pp,
                        'pre_post_total':     pp_total,
                        'adherence_bucket':   bucket,
                        'orders':             count,
                        'pct_within_pre_post': round(count * 100.0 / denom, 2),
                    })

    result = pd.DataFrame(output_rows)

    # ── Sort ──
    regime_order = {'INTERNAL': 0, 'PBA': 1}
    pp_order     = {'PRE': 0, 'POST': 1}
    bucket_map   = {b: i for i, b in enumerate(BUCKET_ORDER)}
    result['_r']  = result['regime'].map(regime_order)
    result['_pp'] = result['pre_post'].map(pp_order)
    result['_b']  = result['adherence_bucket'].map(bucket_map)
    result = (
        result
        .sort_values(['courier_name', '_r', '_pp', '_b'])
        .drop(columns=['_r', '_pp', '_b'])
        .reset_index(drop=True)
    )

    # ── Console output ──
    print(f"\nTotal UNKNOWN (PBA pre_post):      {(df['pba_pre_post']      == 'UNKNOWN').sum():,}")
    print(f"Total UNKNOWN (Internal pre_post): {(df['internal_pre_post'] == 'UNKNOWN').sum():,}")

    for courier in result['courier_name'].unique():
        print(f"\n{'='*60}")
        print(f"  {courier}")
        print(f"{'='*60}")
        for regime in ('INTERNAL', 'PBA'):
            sub = result[(result['courier_name'] == courier) & (result['regime'] == regime)]
            if sub.empty:
                continue
            print(f"\n  [{regime}]")
            for pp in ('PRE', 'POST'):
                pp_sub = sub[sub['pre_post'] == pp]
                if pp_sub.empty:
                    continue
                pp_total = pp_sub['pre_post_total'].iloc[0]
                print(f"    {pp} ({pp_total:,} orders):")
                for _, row in pp_sub.iterrows():
                    print(f"      {row['adherence_bucket']:15s} {row['orders']:5,}  ({row['pct_within_pre_post']:5.1f}%)")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)
    print(f"\nOutput: {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
