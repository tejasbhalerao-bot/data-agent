"""Sanity checks for row7-shipping-promise-performance.csv, row7-late-early-magnitude.csv,
and row7-courier-breakdown.csv.

Checks:
1. n = 57,195, matching the already-validated row 7 total from
   courier-switch-promise-funnel-v2.csv exactly.
2. On-Time = 0 -- structural, since row 7 (like rows 4/6) is drawn from the
   230,923-order cohort that excludes delivery_view2=On-Time by construction.
3. Every order's outcome (Early/On-Time/Late computed against shipping_delivery_promise)
   matches view2-orders-all.csv's own delivery_leg exactly -- since promise is
   unchanged in row 7, shipping promise == digitised-derived promise, so the two
   classifications must be mathematically identical.
4. Magnitude buckets (early_2plus/early_1/late_1/late_2plus) sum to n exactly.
5. Courier breakdown rows sum to n exactly, and each courier's own Early+On-Time+Late
   sums to that courier's n.
6. Every count/pct across all 3 files matches an independent recount.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-row7-performance-deep-dive-v1.py
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TS_FMT = "%b %d, %Y, %I:%M %p"
OUTCOMES = ["Early", "On-Time", "Late"]
EXPECTED_N = 57_195

TARGET_COHORTS = {
    ("On-Time", "Early", "Early"),
    ("On-Time", "Late", "Late"),
    ("Early", "On-Time", "Late"),
    ("Early", "Early", "Early"),
    ("Late", "On-Time", "Early"),
    ("Early", "Early", "Late"),
    ("Late", "Late", "Late"),
    ("Early", "Late", "Late"),
    ("Late", "Early", "Early"),
    ("Late", "Late", "Early"),
}


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


def main() -> None:
    failures: list[str] = []

    v2_rows: dict[str, dict[str, str]] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    overall = defaultdict(int)
    magnitude = defaultdict(int)
    courier_tally: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    n_row7 = 0
    view2_mismatches = 0

    with (OUT / "view1-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            oid = row["order_id"]
            r2 = v2_rows.get(oid)
            if r2 is None:
                continue
            triple = (row["dispatch_leg"], row["delivery_leg"], r2["delivery_leg"])
            if triple not in TARGET_COHORTS:
                continue

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            if not dig_partner or not ship_partner or dig_partner != ship_partner:
                continue

            dispatch_promise = parse_date(row["digitised_dispatch_promise"])
            delivery_promise = parse_date(row["digitised_delivery_promise"])
            pickup = parse_date(row["pickup_time"])
            delivery_attempt = parse_date(row["delivery_attempt_time"])
            ship_promise_raw = row["shipping_delivery_promise"].strip()
            if dispatch_promise is None or delivery_promise is None or not ship_promise_raw:
                continue

            digitised_promise_days = (delivery_promise - dispatch_promise).days
            shipping_promise_days = int(ship_promise_raw)
            if shipping_promise_days != digitised_promise_days:
                continue

            actual_days = (delivery_attempt - pickup).days
            diff = actual_days - shipping_promise_days
            outcome = "Early" if diff < 0 else "Late" if diff > 0 else "On-Time"

            if outcome != r2["delivery_leg"]:
                view2_mismatches += 1

            n_row7 += 1
            overall[outcome] += 1

            if diff == -1:
                magnitude["early_1"] += 1
            elif diff <= -2:
                magnitude["early_2plus"] += 1
            elif diff == 1:
                magnitude["late_1"] += 1
            elif diff >= 2:
                magnitude["late_2plus"] += 1

            courier_tally[dig_partner]["n"] += 1
            courier_tally[dig_partner][outcome] += 1

    if n_row7 != EXPECTED_N:
        failures.append(f"n={n_row7}, expected {EXPECTED_N}")
    if overall["On-Time"] != 0:
        failures.append(f"On-Time={overall['On-Time']}, expected 0 (structural)")
    if view2_mismatches:
        failures.append(f"{view2_mismatches} orders: outcome vs shipping promise disagrees with View 2's own delivery_leg")

    mag_sum = sum(magnitude.values())
    if mag_sum != n_row7:
        failures.append(f"magnitude buckets sum to {mag_sum}, expected n={n_row7}")

    with (OUT / "row7-shipping-promise-performance.csv").open(newline="") as f:
        r = next(csv.DictReader(f))
        if int(r["n"]) != n_row7:
            failures.append(f"perf CSV n={r['n']}, recount={n_row7}")
        for o in OUTCOMES:
            col = o.lower().replace("-", "")
            expected_n = overall[o]
            if int(r[f"{col}_n"]) != expected_n:
                failures.append(f"perf CSV {o}_n={r[f'{col}_n']}, recount={expected_n}")
            expected_pct = round(expected_n / n_row7 * 100, 1) if n_row7 else 0.0
            if abs(float(r[f"{col}_pct"]) - expected_pct) > 0.05:
                failures.append(f"perf CSV {o}_pct={r[f'{col}_pct']}, recompute={expected_pct}")

    mag_csv: dict[str, int] = {}
    with (OUT / "row7-late-early-magnitude.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            mag_csv[r["bucket"]] = int(r["n"])
            expected_pct = round(magnitude[r["bucket"]] / n_row7 * 100, 1) if n_row7 else 0.0
            if abs(float(r["pct_of_row7"]) - expected_pct) > 0.05:
                failures.append(f"magnitude CSV {r['bucket']} pct={r['pct_of_row7']}, recompute={expected_pct}")
    for bucket in ["early_2plus", "early_1", "late_1", "late_2plus"]:
        if mag_csv.get(bucket, 0) != magnitude[bucket]:
            failures.append(f"magnitude CSV {bucket}={mag_csv.get(bucket, 0)}, recount={magnitude[bucket]}")

    courier_csv_total = 0
    with (OUT / "row7-courier-breakdown.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            c = r["courier"]
            n = courier_tally[c]["n"]
            courier_csv_total += int(r["n"])
            if int(r["n"]) != n:
                failures.append(f"courier {c}: CSV n={r['n']}, recount={n}")
            for o in OUTCOMES:
                col = o.lower().replace("-", "")
                expected_n = courier_tally[c][o]
                if int(r[f"{col}_n"]) != expected_n:
                    failures.append(f"courier {c}/{o}: CSV n={r[f'{col}_n']}, recount={expected_n}")
            outcome_sum = sum(courier_tally[c][o] for o in OUTCOMES)
            if outcome_sum != n:
                failures.append(f"courier {c}: Early+On-Time+Late={outcome_sum}, expected n={n}")

    if courier_csv_total != n_row7:
        failures.append(f"courier breakdown sums to {courier_csv_total}, expected n_row7={n_row7}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- n={n_row7} matches expected {EXPECTED_N}, On-Time=0 as structurally "
          f"required, outcome agrees with View 2's own delivery_leg for every order, "
          f"magnitude buckets sum to n exactly, courier breakdown sums to n exactly "
          f"with each courier's outcomes summing to its own n, and all CSV values "
          f"match an independent recount.")


if __name__ == "__main__":
    main()
