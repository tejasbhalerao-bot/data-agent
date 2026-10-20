# Purpose: figures the note quotes that are sums or differences of summary rows: M7 grouped by geography, and the spread across x of M1 to M4
# Serves: M1, M2, M3, M4, M7
# Reads: archives/minimum-sample-size-courier-allocation/outputs/sim-v2-summary.csv (from aggregate-simulation-v2.py)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/note-derived-figures-v1.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-note-derived-figures-v1.py

import csv

P = "archives/minimum-sample-size-courier-allocation/outputs/"


def main():
    rows = list(csv.DictReader(open(P + "sim-v2-summary.csv", encoding="utf-8")))
    out = [["figure", "rule", "value"]]
    groups = {}
    for r in rows:
        if r["metric"].startswith("M7"):
            cut = r["cut"]
            if cut == "ops config" or cut.startswith("widest"):
                g = cut
            elif cut.startswith("pincode") and cut.endswith("7d"):
                g = "pincode 7d"
            elif cut.startswith("pincode"):
                g = "pincode 14d to 28d"
            else:
                g = cut.split(" ")[0] + " any window"
            groups[(r["rule"], g)] = groups.get((r["rule"], g), 0) + float(r["value"])
    for (rule, g), v in sorted(groups.items()):
        out.append([f"M7 {g} %", rule, round(v, 2)])
    for rule in ("today", "x=10", "x=15", "x=20"):
        pin = sum(v for (r, g), v in groups.items() if r == rule and g.startswith("pincode"))
        out.append(["M7 pincode, all windows %", rule, round(pin, 2)])
    sc = "complete dates"
    for metric in ("M1 adherence %", "M2 adherence % (reported only if invoice courier shipped it)", "M3 orders not reported in M2 %", "M4 average promise (days)"):
        vals = [float(r["value"]) for r in rows if r["metric"] == metric and r["date_scope"] == sc and r["cut"] == "all" and r["rule"] != "today"]
        out.append([f"spread across x = 10, 15, 20 of {metric}", "x", round(max(vals) - min(vals), 3)])
        v10 = [float(r["value"]) for r in rows if r["metric"] == metric and r["date_scope"] == sc and r["cut"] == "all" and r["rule"] == "x=10"][0]
        v20 = [float(r["value"]) for r in rows if r["metric"] == metric and r["date_scope"] == sc and r["cut"] == "all" and r["rule"] == "x=20"][0]
        out.append([f"{metric}: x = 20 minus x = 10", "x", round(v20 - v10, 3)])
    with open(P + "note-derived-figures-v1.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(out)
    for r in out:
        print(r)


if __name__ == "__main__":
    main()
