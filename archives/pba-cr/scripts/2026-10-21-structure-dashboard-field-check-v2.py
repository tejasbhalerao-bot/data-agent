# Purpose: check a raw dump has every column the PBA CR dashboard needs, filled and in the expected format
# v2: adds record flags, fill counts for every column, and a profile of rows with a non-numeric ORDER_ID
# Serves: every metric in context/2026-10-18-dashboard-field-mapping-v1.md (Sections 1-4)
# Reads: the raw dump CSV given as the first argument (Q1 base query export)
# Writes: archives/pba-cr/outputs/<dump name>-field-check.txt
# Run with: python3 -I archives/pba-cr/scripts/2026-10-21-structure-dashboard-field-check-v2.py <csv path>

import csv
import math
import os
import sys
from datetime import datetime

TS_FORMAT = "%b %d, %Y, %I:%M %p"
SOFT_TYPES = {"COURIER_PBA", "COURIER_LEGACY_TAT_ADHERENCE", "COURIER_DDB_TAT_ADHERENCE", "NONE", ""}
HARD_TYPES = {"COURIER_PBA", "COURIER_LEGACY_TAT_ADHERENCE", "COURIER_DDB_TAT_ADHERENCE", "SDD", "NONE", ""}
INTERNAL = {"COURIER_LEGACY_TAT_ADHERENCE", "COURIER_DDB_TAT_ADHERENCE"}

TIMESTAMPS = ["ORDER_PLACED_AT", "PROMISED_WAREHOUSE_PROCESSING_TIME", "PBA_PROJECTED_DISPATCH_TIME",
              "PBA_PROJECTED_DELIVERY_TIME", "INTERNAL_PROJECTED_DISPATCH_TIME", "INTERNAL_PROJECTED_DELIVERY_TIME",
              "HARD_WH_PROCESSING_TIME", "PBA_HARD_PROJECTED_DISPATCH_TIME", "PBA_HARD_PROJECTED_DELIVERY_TIME",
              "BOX_VERIFIED_TS", "PICKUP_TIME", "DELIVERY_ATTEMPT_TIME"]

# Column -> (base it must be filled in, where the mapping uses it)
NEEDED = [
    ("ORDER_ID", "all", "every metric"),
    ("SDD_ENABLED", "all", "S1 M1; every base"),
    ("SOFT_SERVED_CANDIDATE_TYPE", "nonsdd", "S1 M2-M3; PBA and Internal bases"),
    ("PBA_IN_ROLLOUT", "nonsdd", "S1 M3"),
    ("HARD_SELECTED_CANDIDATE_TYPE", "nonsdd", "Hard PBA and Hard Internal bases"),
    ("WH_ID", "soft", "lanes (S2 M9-M10, M13; S3 M2; S4 lane adjusted)"),
    ("PINCODE", "soft", "lanes"),
    ("PROMISED_WAREHOUSE_PROCESSING_TIME", "soft", "S2 M1-M4, M9; S4 M1"),
    ("PBA_PROJECTED_DISPATCH_TIME", "soft", "S2 M5, M8, M10; S4 M2"),
    ("PBA_PROJECTED_DELIVERY_TIME", "soft", "S2 M1, M4, M5, M8-M10; S4 M1-M2"),
    ("INTERNAL_PROJECTED_DISPATCH_TIME", "soft", "S2 M6-M7, M10; S4 M2"),
    ("INTERNAL_PROJECTED_DELIVERY_TIME", "soft", "S2 M2-M3, M6-M7, M9-M10; S4 M1-M2"),
    ("SOFT_SERVED_PARTNER", "soft", "S3 M1-M2 soft"),
    ("HARD_BOOKED_PARTNER", "hard", "S3 M1-M2 hard"),
    ("PBA_HARD_PROJECTED_DISPATCH_TIME", "hard_pba", "S2 M11, M13; S4 M4"),
    ("PBA_HARD_PROJECTED_DELIVERY_TIME", "hard_pba", "S2 M11, M13; S4 M3-M4"),
    ("HARD_WH_PROCESSING_TIME", "hard_pba", "S4 M3"),
    ("INTERNAL_HARD_PARTNER_TAT_IN_DAYS", "hard_internal", "S2 M12-M13; S4 M4"),
    ("BOX_VERIFIED_TS", "soft", "S4 M1, M3 (actual start)"),
    ("PICKUP_TIME", "soft", "S1 M5; S4 M2, M4 (actual start)"),
    ("DELIVERY_ATTEMPT_TIME", "soft", "S1 M6; S4 every measure (actual)"),
]

lines = []


def say(text=""):
    print(text)
    lines.append(text)


def filled(v):
    return v is not None and v.strip() != ""


def parse_ts(v):
    try:
        return datetime.strptime(v.strip(), TS_FORMAT)
    except ValueError:
        return None


def parse_num(v):
    try:
        return float(v.replace(",", "").strip())
    except ValueError:
        return None


def pct(n, d):
    return "n/a" if d == 0 else f"{n / d * 100:.1f}%"


def main():
    path = sys.argv[1]
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        rows = list(reader)

    say(f"File: {os.path.basename(path)}")
    say(f"Rows: {len(rows)}")
    ids = [r.get("ORDER_ID", "") for r in rows]
    say(f"Distinct ORDER_ID: {len(set(ids))}  duplicate rows by ORDER_ID: {len(ids) - len(set(ids))}")
    placed = [parse_ts(r["ORDER_PLACED_AT"]) for r in rows if filled(r.get("ORDER_PLACED_AT"))]
    placed = [p for p in placed if p]
    if placed:
        say(f"ORDER_PLACED_AT range: {min(placed):%Y-%m-%d %H:%M} to {max(placed):%Y-%m-%d %H:%M}")
        days = {}
        for p in placed:
            days[p.date()] = days.get(p.date(), 0) + 1
        say("Orders by placement date: " + ", ".join(f"{d:%d %b} {n}" for d, n in sorted(days.items())))

    say("\n== 0. Record flags and fill counts, all rows ==")
    for c in ("HAS_SOFT_RECORD", "HAS_HARD_RECORD", "HAS_SHIPMENT_RECORD", "IS_FALLBACK_PROMISE", "FLOW"):
        if c in header:
            counts = {}
            for r in rows:
                counts[r[c] or "<blank>"] = counts.get(r[c] or "<blank>", 0) + 1
            say(f"  {c}: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda x: -x[1])))
    empty = [c for c in header if not any(filled(r[c]) for r in rows)]
    say(f"  Columns with no value in any row ({len(empty)} of {len(header)}): {', '.join(empty)}")
    odd = [r for r in rows if not r["ORDER_ID"].strip().isdigit()]
    if odd:
        say(f"  Rows with a non-numeric ORDER_ID: {len(odd)}")
        for c in header:
            vals = {r[c] for r in odd}
            if any(filled(v) for v in vals):
                say(f"    {c}: filled {sum(filled(r[c]) for r in odd)}/{len(odd)}, e.g. {sorted(v for v in vals if filled(v))[:3]}")

    say("\n== 1. Columns present ==")
    missing = [c for c, _, _ in NEEDED if c not in header]
    for c, _, use in NEEDED:
        say(f"  [{'x' if c in header else ' '}] {c}  ({use})")
    if missing:
        say(f"  MISSING: {', '.join(missing)}")
        return finish(path)

    nonsdd = [r for r in rows if r["SDD_ENABLED"] == "false"]
    pba = [r for r in nonsdd if r["SOFT_SERVED_CANDIDATE_TYPE"] == "COURIER_PBA"]
    internal = [r for r in nonsdd if r["SOFT_SERVED_CANDIDATE_TYPE"] in INTERNAL]
    hard_pba = [r for r in nonsdd if r["HARD_SELECTED_CANDIDATE_TYPE"] == "COURIER_PBA"]
    hard_internal = [r for r in nonsdd if r["HARD_SELECTED_CANDIDATE_TYPE"] in INTERNAL]
    pba_lanes = {(r["WH_ID"], r["PINCODE"]) for r in pba}
    int_lanes = {(r["WH_ID"], r["PINCODE"]) for r in internal}
    common = pba_lanes & int_lanes

    say("\n== 2. Bases ==")
    say(f"  Non-SDD (SDD_ENABLED = 'false'): {len(nonsdd)}")
    say(f"  PBA base: {len(pba)}   Internal base: {len(internal)}")
    say(f"  Hard PBA base: {len(hard_pba)}   Hard Internal base: {len(hard_internal)}")
    say(f"  Common lane set: {len(common)} lanes  (PBA-base lanes {len(pba_lanes)}, Internal-base lanes {len(int_lanes)})")
    say(f"  PBA base on common lanes: {sum((r['WH_ID'], r['PINCODE']) in common for r in pba)}   "
        f"Internal base on common lanes: {sum((r['WH_ID'], r['PINCODE']) in common for r in internal)}")
    say(f"  Hard PBA base on common lanes: {sum((r['WH_ID'], r['PINCODE']) in common for r in hard_pba)}   "
        f"Hard Internal base on common lanes: {sum((r['WH_ID'], r['PINCODE']) in common for r in hard_internal)}")

    say("\n== 3. Values in the expected format ==")
    bad = {
        "SDD_ENABLED": [v for v in (r["SDD_ENABLED"] for r in rows) if v not in ("true", "false")],
        "PBA_IN_ROLLOUT": [v for v in (r["PBA_IN_ROLLOUT"] for r in rows) if v not in ("true", "false", "")],
        "SOFT_SERVED_CANDIDATE_TYPE": [v for v in (r["SOFT_SERVED_CANDIDATE_TYPE"] for r in rows) if v not in SOFT_TYPES],
        "HARD_SELECTED_CANDIDATE_TYPE": [v for v in (r["HARD_SELECTED_CANDIDATE_TYPE"] for r in rows) if v not in HARD_TYPES],
        "ORDER_ID": [v for v in ids if not v.strip().isdigit()],
        "WH_ID": [r["WH_ID"] for r in rows if filled(r["WH_ID"]) and not r["WH_ID"].strip().isdigit()],
        "PINCODE": [r["PINCODE"] for r in rows if filled(r["PINCODE"]) and not (r["PINCODE"].strip().isdigit() and len(r["PINCODE"].strip()) == 6)],
        "INTERNAL_HARD_PARTNER_TAT_IN_DAYS": [r["INTERNAL_HARD_PARTNER_TAT_IN_DAYS"] for r in rows
                                              if filled(r["INTERNAL_HARD_PARTNER_TAT_IN_DAYS"]) and parse_num(r["INTERNAL_HARD_PARTNER_TAT_IN_DAYS"]) is None],
    }
    for c in TIMESTAMPS:
        bad[c] = [r[c] for r in rows if filled(r[c]) and parse_ts(r[c]) is None]
    for c, vals in bad.items():
        say(f"  [{'x' if not vals else ' '}] {c}: {len(vals)} unexpected" + (f", e.g. {sorted(set(vals))[:5]}" if vals else ""))
    for c in ("SOFT_SERVED_CANDIDATE_TYPE", "HARD_SELECTED_CANDIDATE_TYPE", "PBA_IN_ROLLOUT", "SDD_ENABLED"):
        counts = {}
        for r in rows:
            counts[r[c] or "<blank>"] = counts.get(r[c] or "<blank>", 0) + 1
        say(f"  {c} values: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda x: -x[1])))

    say("\n== 4. Fill rate in the base each column serves ==")
    bases = {"all": ("all rows", rows), "nonsdd": ("non-SDD", nonsdd), "hard": ("Hard PBA + Hard Internal", hard_pba + hard_internal),
             "hard_pba": ("Hard PBA base", hard_pba), "hard_internal": ("Hard Internal base", hard_internal)}
    for c, base, use in NEEDED:
        if base == "soft":
            a = sum(filled(r[c]) for r in pba)
            b = sum(filled(r[c]) for r in internal)
            say(f"  {c}: PBA base {a}/{len(pba)} ({pct(a, len(pba))}); Internal base {b}/{len(internal)} ({pct(b, len(internal))})")
        else:
            name, rs = bases[base]
            n = sum(filled(r[c]) for r in rs)
            say(f"  {c}: {name} {n}/{len(rs)} ({pct(n, len(rs))})")

    say("\n== 5. Data errors the mapping leaves out and reports ==")

    def neg_days(rs, start, end):
        n = 0
        for r in rs:
            if filled(r[start]) and filled(r[end]):
                s, e = parse_ts(r[start]), parse_ts(r[end])
                if s and e and (e.date() - s.date()).days < 0:
                    n += 1
        return n

    checks = [
        ("PBA base", pba, "PROMISED_WAREHOUSE_PROCESSING_TIME", "PBA_PROJECTED_DELIVERY_TIME"),
        ("PBA base", pba, "PBA_PROJECTED_DISPATCH_TIME", "PBA_PROJECTED_DELIVERY_TIME"),
        ("Internal base", internal, "PROMISED_WAREHOUSE_PROCESSING_TIME", "INTERNAL_PROJECTED_DELIVERY_TIME"),
        ("Internal base", internal, "INTERNAL_PROJECTED_DISPATCH_TIME", "INTERNAL_PROJECTED_DELIVERY_TIME"),
        ("Hard PBA base", hard_pba, "PBA_HARD_PROJECTED_DISPATCH_TIME", "PBA_HARD_PROJECTED_DELIVERY_TIME"),
        ("Hard PBA base", hard_pba, "HARD_WH_PROCESSING_TIME", "PBA_HARD_PROJECTED_DELIVERY_TIME"),
        ("all rows", rows, "BOX_VERIFIED_TS", "DELIVERY_ATTEMPT_TIME"),
        ("all rows", rows, "PICKUP_TIME", "DELIVERY_ATTEMPT_TIME"),
    ]
    for name, rs, s, e in checks:
        say(f"  negative days, {name}: {s} -> {e}: {neg_days(rs, s, e)}")
    neg_tat = sum(1 for r in hard_internal if filled(r["INTERNAL_HARD_PARTNER_TAT_IN_DAYS"])
                  and (parse_num(r["INTERNAL_HARD_PARTNER_TAT_IN_DAYS"]) or 0) < 0)
    say(f"  negative INTERNAL_HARD_PARTNER_TAT_IN_DAYS, Hard Internal base: {neg_tat}")
    for c in ("BOX_VERIFIED_TS", "PICKUP_TIME"):
        n = sum(1 for r in pba + internal + hard_pba + hard_internal if filled(r["DELIVERY_ATTEMPT_TIME"]) and not filled(r[c]))
        say(f"  attempted but {c} blank (any base, counted per base membership): {n}")
    tats = [parse_num(r["INTERNAL_HARD_PARTNER_TAT_IN_DAYS"]) for r in hard_internal if filled(r["INTERNAL_HARD_PARTNER_TAT_IN_DAYS"])]
    tats = [t for t in tats if t is not None]
    if tats:
        whole = sum(1 for t in tats if t == math.floor(t))
        say(f"  INTERNAL_HARD_PARTNER_TAT_IN_DAYS: min {min(tats)}, max {max(tats)}, whole numbers {whole}/{len(tats)}")

    say("\n== 6. Actuals available for Sections 1 and 4 ==")
    for name, rs in (("PBA base", pba), ("Internal base", internal), ("Hard PBA base", hard_pba), ("Hard Internal base", hard_internal)):
        p = sum(filled(r["PICKUP_TIME"]) for r in rs)
        a = sum(filled(r["DELIVERY_ATTEMPT_TIME"]) for r in rs)
        say(f"  {name}: picked up {p}/{len(rs)} ({pct(p, len(rs))}); delivery attempted {a}/{len(rs)} ({pct(a, len(rs))})")

    finish(path)


def finish(path):
    name = os.path.splitext(os.path.basename(path))[0]
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", f"{name}-field-check.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWrote {os.path.normpath(out)}")


if __name__ == "__main__":
    main()
