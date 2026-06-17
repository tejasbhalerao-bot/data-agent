"""Courier early/on-time/late by DESTINATION CITY, + week-over-week stability for top cities.

City derived from digitised_delivery_pincode via pgeocode (GeoNames India, offline cache).
    city = county_name  (district-level; e.g. 400001 -> Mumbai, 560001 -> Bengaluru).
    Caveat: GeoNames-derived, NOT a Truemeds canonical pincode->city master.

Metric (day-level): offset = date(delivery_attempt_time) - date(digitised_delivery_promise)
    <= -1 Early | 0 On-Time | >= +1 Late
Scope: delivered, digitised_ts >= 2026-05-08, Courier (digitised_is_sdd == false).
Week key: ISO week of digitised_ts.
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

import pgeocode  # noqa: E402  (after SSL env is set, for the one-time GeoNames fetch)

RAW_PATH = Path(__file__).resolve().parents[1] / "raw-data" / "early-delivery-raw-may-2026.csv"
OUT_CITY = Path(__file__).resolve().parents[1] / "outputs" / "courier-city-distribution-v1.csv"
OUT_WEEK = Path(__file__).resolve().parents[1] / "outputs" / "courier-city-week-v1.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"
CUTOVER = date(2026, 5, 8)
TOP_N = 10


def parse_dt(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def main() -> None:
    seen: set[str] = set()
    records: list[tuple[str, str, str]] = []  # (pincode, week_key, bucket)
    pincodes: set[str] = set()

    with open(RAW_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            oid = (row["order_id"] or "").replace(",", "").strip()
            if oid in seen:
                continue
            seen.add(oid)
            attempt = parse_dt(row["delivery_attempt_time"])
            if attempt is None:
                continue
            digitised = parse_dt(row["digitised_ts"])
            if digitised is None or digitised.date() < CUTOVER:
                continue
            promise = parse_dt(row["digitised_delivery_promise"])
            if promise is None:
                continue
            if (row["digitised_is_sdd"] or "").strip().lower() != "false":  # courier only
                continue

            pin = (row["digitised_delivery_pincode"] or "").strip()
            iso = digitised.isocalendar()
            week = f"{iso[0]}-W{iso[1]:02d}"
            offset = (attempt.date() - promise.date()).days
            bucket = "early" if offset <= -1 else "ontime" if offset == 0 else "late"
            records.append((pin, week, bucket))
            if pin:
                pincodes.add(pin)

    # ---- geocode unique pincodes -> city (county_name) ----
    nomi = pgeocode.Nominatim("IN")
    plist = sorted(pincodes)
    res = nomi.query_postal_code(plist)
    pin2city: dict[str, str] = {}
    for pin, county in zip(plist, res["county_name"].tolist()):
        pin2city[pin] = county if isinstance(county, str) and county.strip() else "(unknown-pincode)"

    def city_of(pin: str) -> str:
        return "(blank-pincode)" if not pin else pin2city.get(pin, "(unknown-pincode)")

    # ---- aggregate ----
    city = defaultdict(lambda: {"early": 0, "ontime": 0, "late": 0})
    city_week = defaultdict(lambda: {"early": 0, "ontime": 0, "late": 0})
    total = total_early = 0
    weeks: set[str] = set()
    for pin, week, bucket in records:
        c = city_of(pin)
        city[c][bucket] += 1
        city_week[(c, week)][bucket] += 1
        weeks.add(week)
        total += 1
        if bucket == "early":
            total_early += 1

    crows = []
    for c, d in city.items():
        n = d["early"] + d["ontime"] + d["late"]
        crows.append((c, n, d["early"], d["ontime"], d["late"]))
    crows.sort(key=lambda r: -r[2])

    print(f"courier total={total}  total_early={total_early}  cities={len(crows)}  weeks={sorted(weeks)}\n")
    print(f"{'city':>22} {'n':>8} {'early_n':>8} {'early%':>7} {'ontime%':>8} {'late%':>6} {'%ofEarly':>9}")
    cum_n = cum_e = 0
    for c, n, e, o, l in crows[:25]:
        cum_n += n
        cum_e += e
        print(f"{c:>22} {n:>8d} {e:>8d} {e/n*100:6.1f}% {o/n*100:7.1f}% {l/n*100:5.1f}% {e/total_early*100:8.1f}%")
    print(f"\n  top-25 cities: {cum_n/total*100:.1f}% of courier volume, {cum_e/total_early*100:.1f}% of early")

    # ---- week-over-week for top cities ----
    top_cities = [c for c, *_ in crows[:TOP_N]]
    wk_sorted = sorted(weeks)
    print(f"\n=== WEEK-OVER-WEEK early% (n) for top {TOP_N} cities ===")
    print(f"{'city':>22} " + " ".join(f"{w:>14}" for w in wk_sorted))
    for c in top_cities:
        cells = []
        for w in wk_sorted:
            d = city_week.get((c, w))
            if d:
                n = d["early"] + d["ontime"] + d["late"]
                cells.append(f"{d['early']/n*100:4.0f}% ({n:>5d})")
            else:
                cells.append(f"{'-':>12}")
        print(f"{c:>22} " + " ".join(f"{x:>14}" for x in cells))

    # ---- write outputs ----
    OUT_CITY.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CITY, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["city", "n", "early_n", "ontime_n", "late_n", "early_pct",
                     "ontime_pct", "late_pct", "pct_of_all_early"])
        for c, n, e, o, l in crows:
            wr.writerow([c, n, e, o, l, round(e/n*100, 1), round(o/n*100, 1),
                         round(l/n*100, 1), round(e/total_early*100, 1)])
    with open(OUT_WEEK, "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["city", "week", "n", "early_n", "early_pct"])
        for (c, w), d in sorted(city_week.items()):
            n = d["early"] + d["ontime"] + d["late"]
            wr.writerow([c, w, n, d["early"], round(d["early"]/n*100, 1)])
    print(f"\nwrote -> {OUT_CITY}\nwrote -> {OUT_WEEK}")


if __name__ == "__main__":
    main()
