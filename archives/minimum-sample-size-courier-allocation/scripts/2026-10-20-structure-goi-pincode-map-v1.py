# Purpose: give each pincode one state, district, division and macro-cluster by majority of post-office rows
# Serves: pooling ladder (micro-cluster, macro-cluster, state rungs); no metric
# Reads: archives/minimum-sample-size-courier-allocation/raw-data/goi-pincode-directory.csv (GOI file supplied by Tejas, not a query)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/goi-pincode-map.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-structure-goi-pincode-map-v1.py
#
# Rule (agreed with Tejas 2026-10-20): the GOI file has one row per post office, so a pincode can name
# several districts, divisions or states. For each pincode, take the (state, district, division)
# combination that appears on the most post-office rows, ignoring rows where state or district is "NA".
# The three values are chosen together so the district and division always belong to the same office.
# A tie is broken alphabetically and flagged in tie_flag. A pincode whose rows are all "NA" is flagged
# in no_valid_row and left with blank state and district.

import csv
import collections

SRC = "archives/minimum-sample-size-courier-allocation/raw-data/goi-pincode-directory.csv"
OUT = "archives/minimum-sample-size-courier-allocation/outputs/goi-pincode-map.csv"


def norm(s):
    return " ".join(s.strip().upper().split())


def main():
    counts = collections.defaultdict(collections.Counter)
    all_pins = set()
    with open(SRC, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            pin = r["pincode"].strip()
            all_pins.add(pin)
            state, dist, div = norm(r["statename"]), norm(r["district"]), norm(r["divisionname"])
            if state in ("", "NA") or dist in ("", "NA") or div in ("", "NA"):
                continue
            counts[pin][(state, dist, div)] += 1

    rows = []
    ties = 0
    conflicts = 0
    for pin in sorted(all_pins):
        c = counts.get(pin)
        if not c:
            rows.append([pin, pin[:3], "", "", "", 0, 0, 0, "Y"])
            continue
        ranked = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
        (state, dist, div), top = ranked[0]
        tie = len(ranked) > 1 and ranked[1][1] == top
        ties += tie
        conflicts += len(ranked) > 1
        rows.append([pin, pin[:3], state, dist, div, top, sum(c.values()), "Y" if tie else "", ""])

    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pincode", "macro_cluster", "state", "district", "division",
                    "rows_for_chosen", "rows_valid", "tie_flag", "no_valid_row"])
        w.writerows(rows)

    print("pincodes mapped:", len(rows))
    print("pincodes with more than one valid (state, district, division):", conflicts)
    print("of which ties:", ties)
    print("pincodes with no valid row:", sum(1 for r in rows if r[8] == "Y"))
    print("distinct macro-clusters:", len({r[1] for r in rows}))
    print("distinct (state, district, division) micro-clusters:",
          len({(r[2], r[3], r[4]) for r in rows if r[2]}))


if __name__ == "__main__":
    main()
