"""Sanity checks for cohort-day-of-week-concentration.csv.

Checks:
1. overall n = 515,465 (all View 1 orders) and cohort n = 230,923 (the already-
   validated "not amazing" cohort), exactly as specified.
2. Weekday counts sum to overall/cohort n respectively.
3. Every count/pct/index matches an independent recount straight from the
   order-detail files.

Run: python3 archives/early-delivery-analysis/tests/2026-07-05-test-aggregate-cohort-day-of-week-concentration-v1.py
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
TS_FMT = "%b %d, %Y, %I:%M %p"
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
EXPECTED_OVERALL_N = 515_465
EXPECTED_COHORT_N = 230_923

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


def parse_dt(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, TS_FMT)
    except ValueError:
        return None


def main() -> None:
    failures: list[str] = []

    v2_delivery: dict[str, str] = {}
    with (OUT / "view2-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            v2_delivery[row["order_id"]] = row["delivery_leg"]

    overall_counts: dict[str, int] = defaultdict(int)
    cohort_counts: dict[str, int] = defaultdict(int)
    n_overall = 0
    n_cohort = 0

    with (OUT / "view1-orders-all.csv").open(newline="") as f:
        for row in csv.DictReader(f):
            digitised = parse_dt(row["digitised_ts"])
            if digitised is None:
                continue
            weekday = WEEKDAYS[digitised.weekday()]
            overall_counts[weekday] += 1
            n_overall += 1

            oid = row["order_id"]
            dl_v2 = v2_delivery.get(oid)
            if dl_v2 is None:
                continue
            triple = (row["dispatch_leg"], row["delivery_leg"], dl_v2)
            if triple not in TARGET_COHORTS:
                continue
            cohort_counts[weekday] += 1
            n_cohort += 1

    if n_overall != EXPECTED_OVERALL_N:
        failures.append(f"overall n={n_overall}, expected {EXPECTED_OVERALL_N}")
    if n_cohort != EXPECTED_COHORT_N:
        failures.append(f"cohort n={n_cohort}, expected {EXPECTED_COHORT_N}")

    if sum(overall_counts.values()) != n_overall:
        failures.append("overall weekday counts do not sum to n_overall")
    if sum(cohort_counts.values()) != n_cohort:
        failures.append("cohort weekday counts do not sum to n_cohort")

    with (OUT / "cohort-day-of-week-concentration.csv").open(newline="") as f:
        for r in csv.DictReader(f):
            day = r["weekday"]
            if int(r["cohort_n"]) != cohort_counts[day]:
                failures.append(f"{day}: CSV cohort_n={r['cohort_n']}, recount={cohort_counts[day]}")
            if int(r["overall_n"]) != overall_counts[day]:
                failures.append(f"{day}: CSV overall_n={r['overall_n']}, recount={overall_counts[day]}")
            exp_c_pct = round(cohort_counts[day] / n_cohort * 100, 2) if n_cohort else 0.0
            exp_o_pct = round(overall_counts[day] / n_overall * 100, 2) if n_overall else 0.0
            if abs(float(r["cohort_pct"]) - exp_c_pct) > 0.02:
                failures.append(f"{day}: CSV cohort_pct={r['cohort_pct']}, recompute={exp_c_pct}")
            if abs(float(r["overall_pct"]) - exp_o_pct) > 0.02:
                failures.append(f"{day}: CSV overall_pct={r['overall_pct']}, recompute={exp_o_pct}")
            exp_index = round(exp_c_pct / exp_o_pct, 2) if exp_o_pct else None
            csv_index = r["index_vs_overall"]
            if exp_index is not None and csv_index not in ("", "None"):
                if abs(float(csv_index) - exp_index) > 0.02:
                    failures.append(f"{day}: CSV index={csv_index}, recompute={exp_index}")

    if failures:
        print(f"FAIL -- {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS -- overall n={n_overall} matches expected {EXPECTED_OVERALL_N}, cohort "
          f"n={n_cohort} matches expected {EXPECTED_COHORT_N}, weekday counts sum "
          f"correctly for both, and every count/pct/index matches an independent recount.")


if __name__ == "__main__":
    main()
