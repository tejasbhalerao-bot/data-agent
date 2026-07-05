"""Geographic concentration check for rows 4, 6, and 7 (courier-switch-promise-funnel-v2.csv)
-- pincode and city level, indexed against the 515,396-order common View1/View2
baseline population to distinguish real concentration from "this pincode just has
a lot of orders anyway".

City derived from digitised_delivery_pincode via pgeocode (GeoNames India, offline
cache) -- same method as 2026-06-16-aggregate-courier-city-distribution-v1.py.
  city = county_name (district-level; NOT a Truemeds canonical pincode->city master).

index_vs_baseline = (row's % of that pincode/city) / (baseline's % of that pincode/city).
  1.0 = no signal (matches overall order share), >1 = over-represented in that row,
  <1 = under-represented.

Emits:
  outputs/geo-concentration-pincode.csv -- wide format, one row per pincode appearing
    in row4/6/7, with n/pct for row4/row6/row7/baseline + index for each row.
  outputs/geo-concentration-city.csv -- same, at city level.
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

import pgeocode  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PINCODE = ROOT / "outputs" / "geo-concentration-pincode.csv"
OUT_CITY = ROOT / "outputs" / "geo-concentration-city.csv"
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
POPULATIONS = ["row4", "row6", "row7", "baseline"]


def parse_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT).date()
    except ValueError:
        return None


def pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 2) if whole else 0.0


def classify_row(row: dict) -> str | None:
    """Returns 'row4', 'row6', 'row7', or None (not one of the three)."""
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
    return None  # switched AND unchanged promise = row 5, not in scope


def main() -> None:
    v2_delivery: dict[str, str] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    pincode_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    n_totals: dict[str, int] = defaultdict(int)
    all_pincodes: set[str] = set()

    with V1_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            oid = row["order_id"]
            dl_v2 = v2_delivery.get(oid)
            if dl_v2 is None:
                continue  # not in the common View1/View2 universe

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

    # ---- geocode ----
    nomi = pgeocode.Nominatim("IN")
    plist = sorted(p for p in all_pincodes if p != "(blank-pincode)")
    res = nomi.query_postal_code(plist)
    pin2city: dict[str, str] = {}
    for pin, county in zip(plist, res["county_name"].tolist()):
        pin2city[pin] = county if isinstance(county, str) and county.strip() else "(unknown-pincode)"
    pin2city["(blank-pincode)"] = "(blank-pincode)"

    city_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for pop in POPULATIONS:
        for pin, n in pincode_counts[pop].items():
            city_counts[pop][pin2city.get(pin, "(unknown-pincode)")] += n

    def write_wide(path: Path, counts: dict[str, dict[str, int]], key_name: str) -> None:
        scope_keys = set(counts["row4"]) | set(counts["row6"]) | set(counts["row7"])
        rows = []
        for key in scope_keys:
            row_data = {"key": key}
            for pop in POPULATIONS:
                n = counts[pop].get(key, 0)
                row_data[f"{pop}_n"] = n
                row_data[f"{pop}_pct"] = pct(n, n_totals[pop])
            for pop in ("row4", "row6", "row7"):
                base_pct = row_data["baseline_pct"]
                row_data[f"{pop}_index"] = round(row_data[f"{pop}_pct"] / base_pct, 2) if base_pct else None
            rows.append(row_data)
        rows.sort(key=lambda r: -(r["row4_n"] + r["row6_n"] + r["row7_n"]))

        with path.open("w", newline="") as f:
            wr = csv.writer(f)
            header = [key_name]
            for pop in POPULATIONS:
                header += [f"{pop}_n", f"{pop}_pct"]
            header += ["row4_index", "row6_index", "row7_index"]
            wr.writerow(header)
            for r in rows:
                out = [r["key"]]
                for pop in POPULATIONS:
                    out += [r[f"{pop}_n"], r[f"{pop}_pct"]]
                out += [r["row4_index"], r["row6_index"], r["row7_index"]]
                wr.writerow(out)

    write_wide(OUT_PINCODE, pincode_counts, "pincode")
    write_wide(OUT_CITY, city_counts, "city")

    for pop in POPULATIONS:
        print(f"{pop}: n={n_totals[pop]}")
    print(f"distinct pincodes overall: {len(all_pincodes)}")
    print(f"wrote: {OUT_PINCODE}")
    print(f"wrote: {OUT_CITY}")


if __name__ == "__main__":
    main()
