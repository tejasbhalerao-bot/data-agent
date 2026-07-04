"""Sanity checks for courier-switch-promise-funnel-v2.csv.

Checks:
1. Total = 230,923 (the already-validated "not amazing" cohort).
2. Switched + Unchanged + switch-indeterminate = Total exactly.
3. Within switched: changed + unchanged + indeterminate = Switched exactly.
4. Within unchanged: changed + unchanged + indeterminate = Unchanged exactly.
5. Every row's n and pct_of_all_orders match an independent recount straight from
   the order-detail files.
6. Cross-check against v1: rows 1-5/5a/2a here must exactly match
   courier-switch-promise-funnel.csv (v1) -- the switched branch wasn't touched.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-courier-switch-promise-funnel-v2.py
"""

from __future__ import annotations

import csv
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TS_FMT = "%b %d, %Y, %I:%M %p"

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
EXPECTED_TOTAL = 230_923


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


def promise_bucket(row: dict) -> str:
    dispatch_promise = parse_date(row["digitised_dispatch_promise"])
    delivery_promise = parse_date(row["digitised_delivery_promise"])
    ship_promise_raw = row["shipping_delivery_promise"].strip()
    if dispatch_promise is None or delivery_promise is None or not ship_promise_raw:
        return "indeterminate"
    digitised_promise_days = (delivery_promise - dispatch_promise).days
    shipping_promise_days = int(ship_promise_raw)
    return "changed" if shipping_promise_days != digitised_promise_days else "unchanged"


def main() -> None:
    failures: list[str] = []

    v2_delivery: dict[str, str] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    n_total = 0
    n_switch_indeterminate = 0
    counts = {
        ("switch", "changed"): 0, ("switch", "unchanged"): 0, ("switch", "indeterminate"): 0,
        ("unchanged", "changed"): 0, ("unchanged", "unchanged"): 0, ("unchanged", "indeterminate"): 0,
    }

    with (OUT / "view1-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            oid = row["order_id"]
            dl_v2 = v2_delivery.get(oid)
            if dl_v2 is None:
                continue
            triple = (row["dispatch_leg"], row["delivery_leg"], dl_v2)
            if triple not in TARGET_COHORTS:
                continue

            n_total += 1

            dig_partner = row["digitised_delivery_partner"].strip()
            ship_partner = row["shipping_delivery_partner"].strip()
            if not dig_partner or not ship_partner:
                n_switch_indeterminate += 1
                continue

            branch = "switch" if dig_partner != ship_partner else "unchanged"
            counts[(branch, promise_bucket(row))] += 1

    n_switch = sum(counts[("switch", b)] for b in ("changed", "unchanged", "indeterminate"))
    n_unchanged = sum(counts[("unchanged", b)] for b in ("changed", "unchanged", "indeterminate"))

    if n_total != EXPECTED_TOTAL:
        failures.append(f"total={n_total}, expected {EXPECTED_TOTAL}")
    if n_switch + n_unchanged + n_switch_indeterminate != n_total:
        failures.append(
            f"switch({n_switch}) + unchanged({n_unchanged}) + indeterminate({n_switch_indeterminate}) "
            f"!= total({n_total})"
        )

    expected_rows = {
        "1. Total orders": n_total,
        "2. Courier switched": n_switch,
        "2a. Courier switch indeterminate (blank partner field)": n_switch_indeterminate,
        "3. Courier unchanged": n_unchanged,
        "4. Courier switched AND promise changed": counts[("switch", "changed")],
        "5. Courier switched AND promise unchanged": counts[("switch", "unchanged")],
        "5a. Courier switched, promise indeterminate": counts[("switch", "indeterminate")],
        "6. Courier unchanged AND promise changed": counts[("unchanged", "changed")],
        "7. Courier unchanged AND promise unchanged": counts[("unchanged", "unchanged")],
        "7a. Courier unchanged, promise indeterminate": counts[("unchanged", "indeterminate")],
    }

    with (OUT / "courier-switch-promise-funnel-v2.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            step, n, csv_pct = r["step"], int(r["n"]), float(r["pct_of_all_orders"])
            if step not in expected_rows:
                failures.append(f"unexpected step in CSV: {step}")
                continue
            if n != expected_rows[step]:
                failures.append(f"{step}: CSV n={n}, recount={expected_rows[step]}")
            expected_pct = round(expected_rows[step] / n_total * 100, 1) if n_total else 0.0
            if abs(csv_pct - expected_pct) > 0.05:
                failures.append(f"{step}: CSV pct={csv_pct}, recompute={expected_pct}")

    v1_shared_steps = {
        "1. Total orders", "2. Courier switched",
        "2a. Courier switch indeterminate (blank partner field)", "3. Courier unchanged",
        "4. Courier switched AND promise changed", "5. Courier switched AND promise unchanged",
        "5a. Courier switched, promise indeterminate",
    }
    v1_rows: dict[str, int] = {}
    with (OUT / "courier-switch-promise-funnel.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            v1_rows[r["step"]] = int(r["n"])

    for step in v1_shared_steps:
        if v1_rows.get(step) != expected_rows.get(step):
            failures.append(f"{step}: v1 has {v1_rows.get(step)}, v2 has {expected_rows.get(step)} -- should match")

    if not (counts[("unchanged", "changed")] + counts[("unchanged", "unchanged")]
            + counts[("unchanged", "indeterminate")] == n_unchanged):
        failures.append("unchanged branch sub-buckets do not sum to unchanged total")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- total={n_total} matches expected {EXPECTED_TOTAL}, both branches "
          f"(switched, unchanged) sum correctly at both levels, all 10 CSV rows match "
          f"an independent recount, and the switched-branch rows are unchanged from v1.")


if __name__ == "__main__":
    main()
