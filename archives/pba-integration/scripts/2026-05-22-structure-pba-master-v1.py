#!/usr/bin/env python3
"""
PBA Master Structuring Script
==============================
Joins 5 source tables into one flat analysis-ready CSV.
Output: archives/pba-integration/outputs/2026-05-22-pba-master-v1.csv

Shadow mode context:
  - Internal courier ALWAYS executes. PBA is counterfactual.
  - TATs in allocation_metadata are in minutes → CEIL(x/1440) for days.
  - projected_dispatch_time in allocation_metadata is epoch milliseconds.
  - Preference array ranking: EDD ASC → PRICING ASC → AVERAGE_TAT ASC → TOTAL_SCORE ASC → PRIORITY ASC.
  - Excluded couriers: Shiprocket, Shadowfax (all variants).

For production: swap INPUT file paths to full CSV dumps.
"""

import json
import math
import os
from datetime import datetime, time as dtime
from typing import Any, Optional

import pandas as pd

# ── PATHS ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))

CONTEXT_DIR = os.path.join(REPO_ROOT, 'archives', 'pba-integration', 'context')
OUTPUT_DIR = os.path.join(REPO_ROOT, 'archives', 'pba-integration', 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

INPUT = {
    'allocation_audit': os.path.join(CONTEXT_DIR, '2026-05-22-sample-logistics_allocation_audit.csv'),
    'rails_api_audit':  os.path.join(CONTEXT_DIR, '2026-05-22-sample-logistics_rails_api_audit.csv'),
    'delivery_partner': os.path.join(CONTEXT_DIR, '2026-05-22-sample-logistics_delivery_partner.csv'),
    'order_tat':        os.path.join(CONTEXT_DIR, '2026-05-22-sample-order_tat_details.csv'),
    'delivery_tracker': os.path.join(CONTEXT_DIR, '2026-05-22-sample-delivery_date_tracker.csv'),
    'cutoff_times':     os.path.join(CONTEXT_DIR, '2026-05-12-cutoff-times.csv'),
}

OUTPUT_FILE = os.path.join(OUTPUT_DIR, '2026-05-22-pba-master-v1.csv')

# ── PRICING (source: 2026-05-22-courier-pricing-snapshot.md) ─────────────────
# Couriers NOT in this dict → default pricing (no configured price in Clickpost).
KNOWN_PRICING: dict[str, float] = {
    'Bluedart Express ANKW':   89.21,
    'Bluedart ANKW':           77.17,
    'XpressBees Express ANKW': 83.19,
    'XpressBees Surace ANKW':  65.14,  # typo preserved from source data
    'Delhivery Express ANKW':  71.15,
    'Delhivery Surface ANKW':  59.12,
}

EXCLUDED_ACCOUNT_CODES: set[str] = {
    'Shiprocket Courier', 'Shiprocket NDD', 'Shiprocket',
    'Shadowfax Surface', 'Shadowfax Express',
}


# ── HELPERS ───────────────────────────────────────────────────────────────────

def clean_order_id(val: Any) -> Optional[int]:
    """Strip comma-formatting: '6,939,617' → 6939617."""
    if pd.isna(val):
        return None
    try:
        return int(str(val).replace(',', '').strip())
    except ValueError:
        return None


def parse_json_safe(s: Any) -> dict:
    if pd.isna(s) or str(s).strip() == '':
        return {}
    try:
        return json.loads(s)
    except Exception:
        return {}


def epoch_ms_to_dt(val: Any) -> Optional[datetime]:
    """Epoch milliseconds → datetime. Returns None if invalid or 'null'."""
    if val is None or str(val).strip() in ('', 'null', 'None'):
        return None
    try:
        return datetime.fromtimestamp(int(float(val)) / 1000)
    except Exception:
        return None


def parse_dt(val: Any) -> Optional[datetime]:
    """Parse common date string formats → datetime. Returns None on failure."""
    if pd.isna(val) or str(val).strip() == '':
        return None
    formats = [
        '%b %d, %Y, %I:%M %p',    # Jul 31, 2020, 5:41 PM
        '%Y-%m-%dT%H:%M:%S.%f%z',
        '%Y-%m-%dT%H:%M:%S%z',
        '%Y-%m-%d %H:%M:%S',
    ]
    s = str(val).strip()
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return pd.to_datetime(val).to_pydatetime()
    except Exception:
        return None


def tat_min_to_days(minutes: Any) -> Optional[int]:
    """CEIL(minutes / 1440) → days. Returns None if invalid."""
    try:
        return math.ceil(float(minutes) / 1440)
    except (TypeError, ValueError):
        return None


def compute_actual_tat_days(
    pickup_time: Optional[datetime],
    actual_delivery_date: Optional[datetime],
) -> Optional[int]:
    """CEIL((actual_delivery_date - pickup_time).total_seconds() / 86400)."""
    if pickup_time is None or actual_delivery_date is None:
        return None
    try:
        # Strip tzinfo to avoid mixed-aware/naive arithmetic
        pt = pickup_time.replace(tzinfo=None)
        ad = actual_delivery_date.replace(tzinfo=None)
        delta = ad - pt
        if delta.total_seconds() <= 0:
            return None
        return math.ceil(delta.total_seconds() / 86400)
    except Exception:
        return None


def lookup_pricing(account_code: str) -> Optional[float]:
    """Return configured price or None (= default/unconfigured pricing)."""
    return KNOWN_PRICING.get(account_code)


# ── STEP 1: DELIVERY PARTNER LOOKUP ──────────────────────────────────────────

def build_partner_lookup(df_partner: pd.DataFrame) -> dict[int, dict]:
    """
    Returns dict: delivery_partner_id (int) → {
        account_code (str),
        delivery_partner_name (str),
        clickpost_partner_id (int | None),
    }
    """
    lookup: dict[int, dict] = {}
    for _, row in df_partner.iterrows():
        try:
            pid = int(row['delivery_partner_id'])
        except (ValueError, TypeError):
            continue
        meta = parse_json_safe(row.get('metadata', ''))
        cp_id_raw = meta.get('clickpost_partner_id')
        try:
            cp_id: Optional[int] = int(cp_id_raw) if cp_id_raw is not None else None
        except (ValueError, TypeError):
            cp_id = None
        lookup[pid] = {
            'account_code':          meta.get('ankw_account_code', ''),
            'delivery_partner_name': meta.get('delivery_partner_name', ''),
            'clickpost_partner_id':  cp_id,
        }
    return lookup


# ── STEP 2: ALLOCATION AUDIT → one row per order ─────────────────────────────

def process_allocation_audit(
    df_alloc: pd.DataFrame,
    partner_lookup: dict[int, dict],
) -> pd.DataFrame:
    """
    Parse allocation_metadata JSON.
    Dedupe per order_id × allocation_type → latest updated_at.
    Pivot SOFT and HARD side-by-side.
    Returns: DataFrame with one row per order_id.
    """
    df = df_alloc.copy()
    df['order_id'] = df['pk'].str.replace('ORD#', '', regex=False).apply(
        lambda x: int(x) if str(x).isdigit() else None
    )
    df = df.dropna(subset=['order_id'])
    df['order_id'] = df['order_id'].astype(int)
    df['updated_at'] = pd.to_datetime(df['updated_at'], utc=True, errors='coerce')
    df['meta'] = df['allocation_metadata'].apply(parse_json_safe)

    # Dedupe: latest updated_at per order_id × allocation_type
    df = (df.sort_values('updated_at')
            .groupby(['order_id', 'allocation_type'])
            .last()
            .reset_index())

    def extract_side(sub_df: pd.DataFrame, prefix: str) -> pd.DataFrame:
        rows = []
        for _, row in sub_df.iterrows():
            m: dict = row['meta']

            def safe_int(v: Any) -> Optional[int]:
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return None

            pba_pid = safe_int(m.get('pba_partner_id'))
            int_pid = safe_int(m.get('internal_partner_id'))
            pba_info = partner_lookup.get(pba_pid, {})
            int_info = partner_lookup.get(int_pid, {})

            r: dict = {
                'order_id': row['order_id'],
                f'{prefix}_pba_partner_id':       pba_pid,
                f'{prefix}_pba_partner_name':      pba_info.get('delivery_partner_name', ''),
                f'{prefix}_pba_account_code':      pba_info.get('account_code', ''),
                f'{prefix}_pba_tat_days':          tat_min_to_days(m.get('pba_tat')),
                f'{prefix}_internal_partner_id':   int_pid,
                f'{prefix}_internal_partner_name': int_info.get('delivery_partner_name', ''),
                f'{prefix}_internal_account_code': int_info.get('account_code', ''),
                f'{prefix}_internal_tat_days':     tat_min_to_days(m.get('internal_tat')),
            }
            if prefix == 'hard':
                r['warehouse_id'] = m.get('warehouse_id')
                r['pincode'] = m.get('pincode')
                r['projected_dispatch_epoch'] = m.get('projected_dispatch_time')
            rows.append(r)
        return pd.DataFrame(rows).set_index('order_id')

    soft_wide = extract_side(df[df['allocation_type'] == 'SOFT'], 'soft')
    hard_wide = extract_side(df[df['allocation_type'] == 'HARD'], 'hard')
    merged = hard_wide.join(soft_wide, how='outer').reset_index()

    merged['projected_dispatch_time'] = merged['projected_dispatch_epoch'].apply(epoch_ms_to_dt)
    merged = merged.drop(columns=['projected_dispatch_epoch'])

    merged['same_courier_flag'] = (
        merged['hard_pba_partner_id'] == merged['hard_internal_partner_id']
    )

    def tat_comparison(row: pd.Series) -> Optional[str]:
        pba = row['hard_pba_tat_days']
        internal = row['hard_internal_tat_days']
        if pd.isna(pba) or pd.isna(internal):
            return None
        if pba < internal:
            return 'PBA_FASTER'
        if pba > internal:
            return 'INTERNAL_FASTER'
        return 'SAME'

    merged['tat_comparison'] = merged.apply(tat_comparison, axis=1)
    merged['pba_cost_per_shipment'] = merged['hard_pba_account_code'].apply(lookup_pricing)
    merged['internal_cost_per_shipment'] = merged['hard_internal_account_code'].apply(lookup_pricing)

    return merged


# ── STEP 3: CUTOFF TIMES LOOKUP ──────────────────────────────────────────────

def build_cutoff_lookup(df_cutoff: pd.DataFrame) -> dict[tuple[str, str], dtime]:
    """
    Returns dict: (source_pincode_str, normalized_account_code) → time object.
    Normalized: strip all spaces, lowercase (handles 'XpressBees SurfaceANKW' quirk).
    """
    lookup: dict[tuple[str, str], dtime] = {}
    for _, row in df_cutoff.iterrows():
        pincode = str(row.get('Source Pincode', '')).strip()
        for col in df_cutoff.columns:
            if col in ('Row Labels', 'Source Pincode'):
                continue
            val = row[col]
            if pd.isna(val) or str(val).strip() == '':
                continue
            try:
                parts = str(val).strip().split(':')
                cutoff = dtime(int(parts[0]), int(parts[1]))
                key = (pincode, col.strip().replace(' ', '').lower())
                lookup[key] = cutoff
            except Exception:
                continue
    return lookup


def get_is_pre_cutoff(
    projected_dispatch_time: Optional[datetime],
    pickup_pincode: Optional[str],
    internal_account_code: Optional[str],
    cutoff_lookup: dict[tuple[str, str], dtime],
) -> Optional[bool]:
    """
    True if time-of-day(projected_dispatch_time) < cutoff for warehouse × courier.
    Returns None when data missing or courier not configured in cutoff CSV.
    """
    if any(v is None for v in [projected_dispatch_time, pickup_pincode, internal_account_code]):
        return None
    try:
        dispatch_tod = projected_dispatch_time.time()  # type: ignore[union-attr]
        pincode_str = str(pickup_pincode).strip()
        courier_key = str(internal_account_code).strip().replace(' ', '').lower()
        cutoff = cutoff_lookup.get((pincode_str, courier_key))
        if cutoff is None:
            return None
        return dispatch_tod < cutoff
    except Exception:
        return None


# ── STEP 4: RAILS API AUDIT → flattened preference array ─────────────────────

def process_rails_api_audit(df_rails: pd.DataFrame) -> pd.DataFrame:
    """
    Filter: pk starts with RECOMMEND# (PBA records only).
    Extract order_id from pk.
    Dedupe: latest created_at per order_id.
    Flatten preference_array into rank{n}_* columns.
    Excludes Shiprocket / Shadowfax from array before ranking.
    Returns: DataFrame with one row per order_id.
    """
    df = df_rails[df_rails['pk'].str.startswith('RECOMMEND#')].copy()
    df['order_id'] = df['pk'].str.replace('RECOMMEND#', '', regex=False).astype(int)
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True, errors='coerce')
    df = df.sort_values('created_at').groupby('order_id').last().reset_index()

    def get_pickup_pincode(req_str: Any) -> Optional[str]:
        return parse_json_safe(req_str).get('pickup_pincode')

    def parse_pref_array(resp_str: Any) -> list:
        d = parse_json_safe(resp_str)
        try:
            return d['result'][0]['preference_array']
        except (KeyError, IndexError, TypeError):
            return []

    df['pickup_pincode'] = df['request_payload'].apply(get_pickup_pincode)
    df['pref_array'] = df['response_payload'].apply(parse_pref_array)

    results = []
    for _, row in df.iterrows():
        pref_array = [
            c for c in row['pref_array']
            if c.get('account_code', '') not in EXCLUDED_ACCOUNT_CODES
        ]
        pref_array = sorted(pref_array, key=lambda x: x.get('priority', 9999))

        record: dict = {
            'order_id':                  row['order_id'],
            'pickup_pincode':            row['pickup_pincode'],
            'pref_array_total_couriers': len(pref_array),
        }

        for i, courier in enumerate(pref_array):
            rank = i + 1
            sc = courier.get('scores_computation', {})
            sp_actual = sc.get('scoring_params_actual', {})
            sp_source = sc.get('scoring_params_source', {})
            account_code = courier.get('account_code', '')

            record[f'rank{rank}_partner_id']     = courier.get('cp_id')
            record[f'rank{rank}_courier_name']   = courier.get('courier_name', '')
            record[f'rank{rank}_account_code']   = account_code
            record[f'rank{rank}_edd']            = sp_actual.get('EDD')
            record[f'rank{rank}_pricing']        = sp_actual.get('PRICING')
            record[f'rank{rank}_avg_tat']        = sp_actual.get('AVERAGE_TAT')
            record[f'rank{rank}_total_score']    = sc.get('total_score')
            record[f'rank{rank}_pricing_source'] = sp_source.get('PRICING', 'DEFAULT_VALUE')

        results.append(record)

    return pd.DataFrame(results)


# ── STEP 5: INTERNAL COURIER POSITION IN PREFERENCE ARRAY ────────────────────

def enrich_internal_pref_position(
    master_df: pd.DataFrame,
    rails_df: pd.DataFrame,
    partner_lookup: dict[int, dict],
) -> pd.DataFrame:
    """
    For each order: locate internal courier in flattened preference array.
    Match on: clickpost_partner_id (cp_id) AND account_code.
    Returns DataFrame: order_id + internal_in_pref_array + internal_actual_rank
                       + internal_pref_edd / _pricing / _avg_tat.
    """
    cp_id_map: dict[int, int] = {
        pid: info['clickpost_partner_id']
        for pid, info in partner_lookup.items()
        if info.get('clickpost_partner_id') is not None
    }
    ac_map: dict[int, str] = {
        pid: info['account_code']
        for pid, info in partner_lookup.items()
    }

    rails_indexed = rails_df.set_index('order_id')
    rank_pid_cols = sorted(
        [c for c in rails_df.columns if c.startswith('rank') and c.endswith('_partner_id')],
        key=lambda c: int(c.replace('rank', '').replace('_partner_id', '')),
    )

    rows = []
    for _, mrow in master_df.iterrows():
        order_id: int = mrow['order_id']
        int_pid_raw = mrow.get('hard_internal_partner_id')

        default: dict = {
            'order_id':               order_id,
            'internal_in_pref_array': False,
            'internal_actual_rank':   None,
            'internal_pref_edd':      None,
            'internal_pref_pricing':  None,
            'internal_pref_avg_tat':  None,
        }

        if int_pid_raw is None or order_id not in rails_indexed.index:
            rows.append(default)
            continue

        try:
            int_pid = int(int_pid_raw)
        except (TypeError, ValueError):
            rows.append(default)
            continue

        int_cp_id = cp_id_map.get(int_pid)
        int_ac = ac_map.get(int_pid, '')
        if int_cp_id is None:
            rows.append(default)
            continue

        rail_row = rails_indexed.loc[order_id]

        found = False
        for col in rank_pid_cols:
            rank_num = int(col.replace('rank', '').replace('_partner_id', ''))
            try:
                row_cp_id = int(rail_row.get(col))
            except (TypeError, ValueError):
                continue
            row_ac = rail_row.get(f'rank{rank_num}_account_code', '')

            if row_cp_id == int_cp_id and row_ac == int_ac:
                rows.append({
                    'order_id':               order_id,
                    'internal_in_pref_array': True,
                    'internal_actual_rank':   rank_num,
                    'internal_pref_edd':      rail_row.get(f'rank{rank_num}_edd'),
                    'internal_pref_pricing':  rail_row.get(f'rank{rank_num}_pricing'),
                    'internal_pref_avg_tat':  rail_row.get(f'rank{rank_num}_avg_tat'),
                })
                found = True
                break

        if not found:
            rows.append(default)

    return pd.DataFrame(rows)


# ── STEP 6: ORDER TAT DETAILS ─────────────────────────────────────────────────

def process_order_tat(df_tat: pd.DataFrame) -> pd.DataFrame:
    df = df_tat.copy()
    df['order_id'] = df['order_id'].apply(clean_order_id)
    df = df.dropna(subset=['order_id'])
    df['order_id'] = df['order_id'].astype(int)
    df['pickup_time'] = df['pickup_time'].apply(parse_dt)
    df['delivery_attempt_time'] = df['delivery_attempt_time'].apply(parse_dt)
    return df[['order_id', 'pickup_time', 'delivery_attempt_time']].drop_duplicates('order_id')


# ── STEP 7: DELIVERY DATE TRACKER ─────────────────────────────────────────────

def process_delivery_tracker(df_tracker: pd.DataFrame) -> pd.DataFrame:
    df = df_tracker.copy()
    df['order_id'] = df['order_id'].apply(clean_order_id)
    df = df.dropna(subset=['order_id'])
    df['order_id'] = df['order_id'].astype(int)
    df['actual_delivery_date'] = df['actual_delivery_date'].apply(parse_dt)
    df['promised_delivery_date'] = df['promised_delivery_date'].apply(parse_dt)
    return (df[['order_id', 'actual_delivery_date', 'promised_delivery_date']]
              .drop_duplicates('order_id'))


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Loading source files...")
    df_alloc   = pd.read_csv(INPUT['allocation_audit'])
    df_rails   = pd.read_csv(INPUT['rails_api_audit'])
    df_partner = pd.read_csv(INPUT['delivery_partner'])
    df_tat     = pd.read_csv(INPUT['order_tat'])
    df_tracker = pd.read_csv(INPUT['delivery_tracker'])
    df_cutoff  = pd.read_csv(INPUT['cutoff_times'])

    print("Building partner lookup...")
    partner_lookup = build_partner_lookup(df_partner)

    print("Building cutoff times lookup...")
    cutoff_lookup = build_cutoff_lookup(df_cutoff)

    print("Processing allocation audit (Step 2)...")
    master = process_allocation_audit(df_alloc, partner_lookup)

    print("Flattening preference array from rails API audit (Step 4)...")
    rails_flat = process_rails_api_audit(df_rails)

    print("Enriching internal courier pref array position (Step 5)...")
    internal_pref = enrich_internal_pref_position(master, rails_flat, partner_lookup)

    print("Processing order TAT details (Step 6)...")
    tat_df = process_order_tat(df_tat)

    print("Processing delivery date tracker (Step 7)...")
    tracker_df = process_delivery_tracker(df_tracker)

    print("Joining all tables...")
    result = (master
              .merge(rails_flat, on='order_id', how='left')
              .merge(internal_pref, on='order_id', how='left')
              .merge(tat_df, on='order_id', how='left')
              .merge(tracker_df, on='order_id', how='left'))

    print("Deriving is_pre_cutoff...")
    result['is_pre_cutoff'] = result.apply(
        lambda row: get_is_pre_cutoff(
            row.get('projected_dispatch_time'),
            row.get('pickup_pincode'),
            row.get('hard_internal_account_code'),
            cutoff_lookup,
        ),
        axis=1,
    )

    print("Deriving actual_tat_days...")
    result['actual_tat_days'] = result.apply(
        lambda row: compute_actual_tat_days(
            row.get('pickup_time'),
            row.get('actual_delivery_date'),
        ),
        axis=1,
    )

    # pickup_pincode is an internal join key from rails; not needed in output
    result = result.drop(columns=['pickup_pincode'], errors='ignore')

    print(f"Writing output → {OUTPUT_FILE}")
    result.to_csv(OUTPUT_FILE, index=False)

    rank_cols = [c for c in result.columns if c.startswith('rank')]
    max_rank = max(
        (int(c.split('_')[0].replace('rank', '')) for c in rank_cols if c.startswith('rank')),
        default=0,
    )
    print(f"Done. {len(result):,} rows × {len(result.columns):,} columns.")
    print(f"Preference array: up to rank {max_rank} ({len(rank_cols)} rank columns).")


if __name__ == '__main__':
    main()
