# Purpose: compare two raw dumps column by column: present in each, and how often each column is filled
# Serves: dump checks before the PBA CR dashboard is built (context/2026-10-18-dashboard-field-mapping-v1.md)
# Reads: two raw dump CSVs given as arguments: the reference dump first (e.g. raw-data/fahad-raw-dump-3.csv), then the new one
# Writes: archives/pba-cr/outputs/<new dump name>-vs-<reference dump name>.md
# Run with: python3 -I archives/pba-cr/scripts/2026-10-21-structure-dump-field-comparison-v1.py <reference csv> <new csv>

import csv
import os
import sys


def load(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        counts = dict.fromkeys(header, 0)
        n = 0
        for row in reader:
            n += 1
            for c in header:
                v = row.get(c)
                if v is not None and v.strip() != "":
                    counts[c] += 1
    return header, counts, n


def rate(filled, n):
    return f"{filled / n * 100:.1f}%" if n else "n/a"


def status(in_ref, in_new, ref_fill, new_fill):
    if not in_new:
        return "Dropped"
    if not in_ref:
        return "New column" + (" (empty)" if new_fill == 0 else "")
    if ref_fill > 0 and new_fill == 0:
        return "Emptied"
    if ref_fill == 0 and new_fill > 0:
        return "Now filled"
    if ref_fill == 0 and new_fill == 0:
        return "Empty in both"
    return "Filled in both"


def main():
    ref_path, new_path = sys.argv[1], sys.argv[2]
    ref_h, ref_c, ref_n = load(ref_path)
    new_h, new_c, new_n = load(new_path)
    ref_name = os.path.splitext(os.path.basename(ref_path))[0]
    new_name = os.path.splitext(os.path.basename(new_path))[0]

    order = list(ref_h) + [c for c in new_h if c not in ref_h]
    lines = [f"Reference: {ref_name} ({ref_n} rows, {len(ref_h)} columns)",
             f"New: {new_name} ({new_n} rows, {len(new_h)} columns)", "",
             "| # | Column | Ref position | New position | Ref filled | Ref % | New filled | New % | Status |",
             "|---|---|---|---|---|---|---|---|---|"]
    tally = {}
    for i, c in enumerate(order, 1):
        in_ref, in_new = c in ref_h, c in new_h
        rf, nf = ref_c.get(c, 0), new_c.get(c, 0)
        s = status(in_ref, in_new, rf, nf)
        tally[s] = tally.get(s, 0) + 1
        lines.append(f"| {i} | `{c}` | {ref_h.index(c) + 1 if in_ref else '-'} | {new_h.index(c) + 1 if in_new else '-'} | "
                     f"{rf if in_ref else '-'} | {rate(rf, ref_n) if in_ref else '-'} | "
                     f"{nf if in_new else '-'} | {rate(nf, new_n) if in_new else '-'} | {s} |")
    lines += ["", "Status counts: " + ", ".join(f"{k} {v}" for k, v in sorted(tally.items(), key=lambda x: -x[1]))]

    text = "\n".join(lines)
    print(text)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", f"{new_name}-vs-{ref_name}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(f"\nWrote {os.path.normpath(out)}")


if __name__ == "__main__":
    main()
