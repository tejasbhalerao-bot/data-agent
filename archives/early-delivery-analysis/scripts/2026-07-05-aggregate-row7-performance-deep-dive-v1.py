"""Row 7 (courier unchanged AND promise unchanged, n=57,195) deep dive -- the slice of
the 230,923-order "not amazing" cohort that courier-switch/promise-drift hypotheses
cannot touch at all, since neither changed.

IMPORTANT, stated up front (same structural point as rows 4/6): because promise is
UNCHANGED here, shipping_delivery_promise == digitised-derived promise_duration_days
for every order, so classifying actual vs shipping promise is mathematically
identical to View 2's already-validated delivery_leg for these orders. On-Time will
be exactly 0% -- structural, since row 7 (like rows 4/6) is drawn from the
230,923-order cohort that excludes delivery_view2=On-Time by construction. Not a bug.

  actual_duration_days = date(delivery_attempt_time) - date(pickup_time)
  shipping_promise_days = shipping_delivery_promise (== digitised promise_duration_days here)
  outcome: actual < promise = Early, == = On-Time, > = Late

Emits 3 files:
  outputs/row7-shipping-promise-performance.csv   -- n, Early/On-Time/Late n+%
  outputs/row7-late-early-magnitude.csv            -- Early by 1/2+ days, Late by 1/2+ days, % of row7 n
  outputs/row7-courier-breakdown.csv               -- per-courier Early/On-Time/Late n+% (of that courier's own n)
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1_PATH = ROOT / "outputs" / "view1-orders-all.csv"
V2_PATH = ROOT / "outputs" / "view2-orders-all.csv"
OUT_PERF = ROOT / "outputs" / "row7-shipping-promise-performance.csv"
OUT_MAG = ROOT / "outputs" / "row7-late-early-magnitude.csv"
OUT_COURIER = ROOT / "outputs" / "row7-courier-breakdown.csv"
TS_FMT = "%b %d, %Y, %I:%M %p"
OUTCOMES = ["Early", "On-Time", "Late"]

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


def pct(part: int, whole: int) -> float:
    return round(part / whole * 100, 1) if whole else 0.0


def main() -> None:
    v2_rows: dict[str, dict[str, str]] = {}
    with V2_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            v2_rows[row["order_id"]] = row

    overall = defaultdict(int)
    magnitude = defaultdict(int)
    courier_tally: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    n_row7 = 0

    with V1_PATH.open(newline="") as f:
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
                continue  # not row 7 -- courier switched or indeterminate

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
                continue  # not row 7 -- promise changed

            actual_days = (delivery_attempt - pickup).days
            diff = actual_days - shipping_promise_days
            outcome = "Early" if diff < 0 else "Late" if diff > 0 else "On-Time"

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

    with OUT_PERF.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["n"] + [f"{o.lower().replace('-', '')}_n" for o in OUTCOMES]
                    + [f"{o.lower().replace('-', '')}_pct" for o in OUTCOMES])
        counts = [overall[o] for o in OUTCOMES]
        wr.writerow([n_row7] + counts + [pct(c, n_row7) for c in counts])

    with OUT_MAG.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["bucket", "n", "pct_of_row7"])
        for bucket in ["early_2plus", "early_1", "late_1", "late_2plus"]:
            n = magnitude[bucket]
            wr.writerow([bucket, n, pct(n, n_row7)])

    ranked_couriers = sorted(courier_tally, key=lambda c: -courier_tally[c]["n"])
    with OUT_COURIER.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["courier", "n", "pct_of_row7"] + [f"{o.lower().replace('-', '')}_n" for o in OUTCOMES]
                    + [f"{o.lower().replace('-', '')}_pct" for o in OUTCOMES])
        for courier in ranked_couriers:
            t = courier_tally[courier]
            n = t["n"]
            counts = [t[o] for o in OUTCOMES]
            wr.writerow([courier, n, pct(n, n_row7)] + counts + [pct(c, n) for c in counts])

    print(f"row7 n: {n_row7}")
    print(f"overall: {dict(overall)}")
    print(f"magnitude: {dict(magnitude)}")
    print(f"distinct couriers: {len(ranked_couriers)}")
    print(f"wrote: {OUT_PERF}")
    print(f"wrote: {OUT_MAG}")
    print(f"wrote: {OUT_COURIER}")


if __name__ == "__main__":
    main()
