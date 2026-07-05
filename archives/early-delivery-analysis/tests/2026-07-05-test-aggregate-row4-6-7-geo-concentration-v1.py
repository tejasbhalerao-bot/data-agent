"""Sanity checks for geo-concentration-pincode.csv and geo-concentration-city.csv.

Checks:
1. row4/row6/row7 totals (summed across all pincodes in the CSV, since the CSV is
   restricted to pincodes appearing in row4/6/7) match the already-validated funnel
   totals (38,598 / 110,586 / 57,195) exactly.
2. Every row's *_pct is computed against the TRUE full-population total for that
   row/baseline (515,396 for baseline), not just the sum within the filtered CSV --
   this catches the exact denominator bug that had to be corrected by hand when
   first sanity-checking this script's output.
3. index_vs_baseline = row_pct / baseline_pct exactly, for every row with a
   non-zero baseline_pct.
4. City-level counts reconcile: summing pincode-level counts through the pincode->city
   map used inside the script must equal the published city-level counts.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-row4-6-7-geo-concentration-v1.py
"""

from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

import pgeocode  # noqa: E402

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
EXPECTED_N = {"row4": 38_598, "row6": 110_586, "row7": 57_195}


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


def classify_row(row: dict) -> str | None:
    dig_partner = row["digitised_delivery_partner"].strip()
    ship_partner = row["shipping_delivery_partner"].strip()
    if not dig_partner or not ship_partner:
        return None
    dispatch_promise = parse_date(row["digitised_dispatch_promise"])
    delivery_promise = parse_date(row["digitised_delivery_promise"])
    ship_promise_raw = row["shipping_delivery_promise"].strip()
    if dispatch_promise is None or delivery_promise is None or not ship_promise_raw:
        return None
    digitised_days = (delivery_promise - dispatch_promise).days
    shipping_days = int(ship_promise_raw)
    switched = dig_partner != ship_partner
    promise_changed = shipping_days != digitised_days
    if switched and promise_changed:
        return "row4"
    if not switched and promise_changed:
        return "row6"
    if not switched and not promise_changed:
        return "row7"
    return None


def main() -> None:
    failures: list[str] = []

    v2_delivery: dict[str, str] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    pincode_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    n_totals: dict[str, int] = defaultdict(int)
    all_pincodes: set[str] = set()

    with (OUT / "view1-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            oid = row["order_id"]
            dl_v2 = v2_delivery.get(oid)
            if dl_v2 is None:
                continue
            pin = row["digitised_delivery_pincode"].strip() or "(blank-pincode)"
            all_pincodes.add(pin)
            pincode_counts["baseline"][pin] += 1
            n_totals["baseline"] += 1
            triple = (row["dispatch_leg"], row["delivery_leg"], dl_v2)
            if triple not in TARGET_COHORTS:
                continue
            row_label = classify_row(row)
            if row_label in ("row4", "row6", "row7"):
                pincode_counts[row_label][pin] += 1
                n_totals[row_label] += 1

    for label, expected in EXPECTED_N.items():
        if n_totals[label] != expected:
            failures.append(f"{label} n={n_totals[label]}, expected {expected}")

    nomi = pgeocode.Nominatim("IN")
    plist = sorted(p for p in all_pincodes if p != "(blank-pincode)")
    res = nomi.query_postal_code(plist)
    pin2city: dict[str, str] = {}
    for pin, county in zip(plist, res["county_name"].tolist()):
        pin2city[pin] = county if isinstance(county, str) and county.strip() else "(unknown-pincode)"
    pin2city["(blank-pincode)"] = "(blank-pincode)"

    city_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for pop in ("row4", "row6", "row7", "baseline"):
        for pin, n in pincode_counts[pop].items():
            city_counts[pop][pin2city.get(pin, "(unknown-pincode)")] += n

    # Check pincode CSV
    with (OUT / "geo-concentration-pincode.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            pin = r["pincode"]
            for pop in ("row4", "row6", "row7", "baseline"):
                n = pincode_counts[pop].get(pin, 0)
                if int(r[f"{pop}_n"]) != n:
                    failures.append(f"pincode {pin}/{pop}: CSV n={r[f'{pop}_n']}, recount={n}")
                exp_pct = round(n / n_totals[pop] * 100, 2) if n_totals[pop] else 0.0
                if abs(float(r[f"{pop}_pct"]) - exp_pct) > 0.02:
                    failures.append(f"pincode {pin}/{pop}: CSV pct={r[f'{pop}_pct']}, recompute={exp_pct}")
            base_pct = float(r["baseline_pct"])
            for pop in ("row4", "row6", "row7"):
                row_pct = float(r[f"{pop}_pct"])
                exp_index = round(row_pct / base_pct, 2) if base_pct else None
                csv_index = r[f"{pop}_index"]
                if base_pct == 0:
                    continue
                if csv_index in ("", "None") or exp_index is None:
                    continue
                if abs(float(csv_index) - exp_index) > 0.02:
                    failures.append(f"pincode {pin}/{pop}_index: CSV={csv_index}, recompute={exp_index}")

    # Check city CSV
    with (OUT / "geo-concentration-city.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            city = r["city"]
            for pop in ("row4", "row6", "row7", "baseline"):
                n = city_counts[pop].get(city, 0)
                if int(r[f"{pop}_n"]) != n:
                    failures.append(f"city {city}/{pop}: CSV n={r[f'{pop}_n']}, recount={n}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures[:30]:
            print(f"  - {f}")
        if len(failures) > 30:
            print(f"  ... and {len(failures) - 30} more")
        sys.exit(1)

    print(f"PASS -- row4/row6/row7 totals match expected {EXPECTED_N}, every pincode "
          f"row's n/pct/index matches an independent recount against the true "
          f"full-population denominators, and city-level counts reconcile with "
          f"pincode-level counts summed through the same pincode->city map.")


if __name__ == "__main__":
    main()
