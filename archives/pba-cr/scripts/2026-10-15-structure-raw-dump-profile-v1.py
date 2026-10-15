"""Profile the PBA CR base extract (no metrics).

Purpose: describe the shape, completeness and internal consistency of the Q1 base extract before any metric work.
Serves: none (data check for M1-M5; produces no metric figures)
Reads:  archives/pba-cr/raw-data/fahad-raw-dump-1.csv (Q1 v2 output; local only)
Writes: archives/pba-cr/outputs/fahad-raw-dump-1-profile.txt (local only)
Run:    python3 archives/pba-cr/scripts/2026-10-15-structure-raw-dump-profile-v1.py
"""
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "raw-data" / "fahad-raw-dump-1.csv"
OUT = ROOT / "outputs" / "fahad-raw-dump-1-profile.txt"

csv.field_size_limit(10**9)
lines = []


def say(*a):
    lines.append(" ".join(str(x) for x in a))


def ts(v):
    """Metabase display format, e.g. 'Oct 14, 2026, 4:26 PM' (IST, minute precision)."""
    v = (v or "").strip()
    if not v:
        return None
    for f in ("%b %d, %Y, %I:%M %p", "%B %d, %Y, %I:%M %p"):
        try:
            return datetime.strptime(v, f)
        except ValueError:
            pass
    return "BAD"


def iso(v):
    """Array timestamps: '2026-10-16T18:30:00+05:30' or '2026-10-16 18:30:00.000 +0530'. Returns naive IST."""
    if not v:
        return None
    v = str(v).strip()
    for f in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S.%f %z"):
        try:
            return datetime.strptime(v, f).replace(tzinfo=None)
        except ValueError:
            pass
    return "BAD"


def num(v):
    v = (v or "").strip().replace(",", "")
    if v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return "BAD"


def arr(v):
    v = (v or "").strip()
    if not v:
        return None
    try:
        return json.loads(v)
    except ValueError:
        return "BAD"


def blank(v):
    return (v or "").strip() == ""


def pct(n, d):
    return f"{n} / {d} ({100.0 * n / d:.1f}%)" if d else f"{n} / 0"


def dist(name, values, top=12):
    c = Counter(values)
    say(f"  {name}:")
    for k, n in c.most_common(top):
        say(f"    {k if k != '' else '<blank>'}: {pct(n, sum(c.values()))}")
    if len(c) > top:
        say(f"    ... {len(c) - top} more values")


rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
cols = list(rows[0].keys())
N = len(rows)

say("== 1. Shape and grain ==")
say("  rows:", N, " columns:", len(cols))
ids = Counter(r["ORDER_ID"] for r in rows)
say("  distinct order_id:", len(ids), " duplicated order_ids:", sum(1 for k, n in ids.items() if n > 1))
dup_full = len(rows) - len({tuple(r.values()) for r in rows})
say("  fully duplicated rows:", dup_full)

say("\n== 2. Placement window ==")
placed = [ts(r["ORDER_PLACED_AT"]) for r in rows]
bad = sum(1 for p in placed if p == "BAD")
ok = [p for p in placed if isinstance(p, datetime)]
say("  unparseable order_placed_at:", bad, " blank:", sum(1 for p in placed if p is None))
if ok:
    say("  earliest:", min(ok), " latest:", max(ok))
    byday = Counter(p.date().isoformat() for p in ok)
    for d in sorted(byday):
        say(f"    {d}: {byday[d]}")
    cr = datetime(2026, 10, 14, 23, 5)
    say("  placed before CR soft go-live (14 Oct 23:05):", pct(sum(1 for p in ok if p < cr), len(ok)))

say("\n== 3. Record coverage and cohort flags (all rows) ==")
for c in ["HAS_SOFT_RECORD", "HAS_HARD_RECORD", "HAS_SHIPMENT_RECORD", "IS_FALLBACK_PROMISE", "SDD_ENABLED",
          "FLOW", "DELIVERY_TYPE", "PBA_IN_ROLLOUT", "PAYMENT_METHOD", "TASK_PROCESSING_TYPE"]:
    dist(c, [r[c] for r in rows])
say("  has_soft_record by sdd_enabled:")
for k, n in Counter((r["SDD_ENABLED"], r["HAS_SOFT_RECORD"]) for r in rows).most_common():
    say(f"    sdd={k[0]} soft={k[1]}: {n}")

courier = [r for r in rows if r["HAS_SOFT_RECORD"] == "true" and r["FLOW"] == "COURIER"]
C = len(courier)
say("\n== 4. Soft record, courier rows with a soft record (n =", C, ") ==")
for c in ["SOFT_SCREEN", "SOFT_CALLER", "SOFT_SERVED_CANDIDATE_TYPE", "PBA_EVALUATED", "PBA_DECISION",
          "PBA_DECISION_DETAIL", "PBA_SOFT_SELECTED_TYPE", "PBA_CACHE_LOOKUP", "PBA_CUTOFF_WINDOW",
          "INTERNAL_CANDIDATE_TYPE", "PBA_IS_COLD_CHAIN", "PBA_IS_EXPRESS_ELIGIBLE", "SOFT_MATCHED"]:
    dist(c, [r[c] for r in courier])
say("  soft_matched vs soft_matched_flag:")
for k, n in Counter((r["SOFT_MATCHED"], r["SOFT_MATCHED_FLAG"]) for r in courier).most_common():
    say(f"    recomputed={k[0]} flag={k[1]}: {n}")
gap = []
for r in courier:
    a, b = ts(r["ORDER_PLACED_AT"]), ts(r["SOFT_PROMISE_AT"])
    if isinstance(a, datetime) and isinstance(b, datetime):
        gap.append((b - a).total_seconds() / 60)
if gap:
    gap.sort()
    say("  soft_promise_at minus order_placed_at, minutes: min", gap[0], " median", gap[len(gap) // 2],
        " max", gap[-1], " >60 min:", sum(1 for g in gap if g > 60))

say("\n== 5. Fill rates of brief columns, courier rows with a soft record ==")
brief = ["ORDER_ID", "WH_ID", "PINCODE", "PBA_IN_ROLLOUT", "ORDER_PLACED_AT", "PROMISED_WAREHOUSE_PROCESSING_TIME",
         "PBA_SOFT_SELECTED_DELIVERY_PARTNER", "PBA_SOFT_SELECTED_PARTNER_TAT_IN_DAYS", "PBA_PROJECTED_DISPATCH_TIME",
         "PBA_PROJECTED_DELIVERY_TIME", "INTERNAL_SOFT_SELECTED_DELIVERY_PARTNER",
         "INTERNAL_SOFT_SELECTED_PARTNER_TAT_IN_DAYS", "INTERNAL_PROJECTED_DISPATCH_TIME",
         "INTERNAL_PROJECTED_DELIVERY_TIME", "INTERNAL_DROP_BUFFER", "INTERNAL_PICKUP_BUFFER", "PBA_DROP_BUFFER",
         "PBA_PICKUP_BUFFER", "PBA_IS_COLD_CHAIN", "PBA_IS_EXPRESS_ELIGIBLE", "PBA_SOFT_SELECTED_TYPE",
         "PBA_SOFT_PREFERENCE_ARRAY", "INTERNAL_SOFT_PREFERENCE_ARRAY", "FLOW",
         "PBA_HARD_SELECTED_DELIVERY_PARTNER", "PBA_HARD_PARTNER_TAT_IN_DAYS", "PBA_HARD_PROJECTED_DISPATCH_TIME",
         "PBA_HARD_PROJECTED_DELIVERY_TIME", "PBA_HARD_PREFERENCE_ARRAY", "INTERNAL_HARD_SELECTED_DELIVERY_PARTNER",
         "INTERNAL_HARD_PARTNER_TAT_IN_DAYS", "INTERNAL_HARD_PROJECTED_DISPATCH_TIME",
         "INTERNAL_HARD_PROJECTED_DELIVERY_TIME", "INTERNAL_HARD_PREFERENCE_ARRAY", "BOX_VERIFIED_TS",
         "AWB_PRINT_TS", "PICKUP_TIME", "DELIVERY_ATTEMPT_TIME"]
for c in brief:
    say(f"  {c}: filled {pct(sum(1 for r in courier if not blank(r[c])), C)}")

hardrows = [r for r in courier if r["HAS_HARD_RECORD"] == "true"]
H = len(hardrows)
say("\n== 6. Hard record, courier rows with soft and hard records (n =", H, ") ==")
for c in ["HARD_OUTCOME", "HARD_SELECTED_CANDIDATE_TYPE", "PBA_HARD_DECISION", "INTERNAL_HARD_CANDIDATE_TYPE"]:
    dist(c, [r[c] for r in hardrows])
say("  hard_allocated_at minus order_placed_at, hours:")
hg = []
for r in hardrows:
    a, b = ts(r["ORDER_PLACED_AT"]), ts(r["HARD_ALLOCATED_AT"])
    if isinstance(a, datetime) and isinstance(b, datetime):
        hg.append((b - a).total_seconds() / 3600)
if hg:
    hg.sort()
    say("    min", round(hg[0], 2), " median", round(hg[len(hg) // 2], 2), " max", round(hg[-1], 2),
        " negative:", sum(1 for g in hg if g < 0))

say("\n== 7. Consistency checks ==")


def agree(label, rs, fa, fb, cond=lambda r: True):
    sub = [r for r in rs if cond(r) and not blank(r[fa]) and not blank(r[fb])]
    n = sum(1 for r in sub if r[fa].strip() == r[fb].strip())
    say(f"  {label}: equal {pct(n, len(sub))}")


agree("soft served partner = promised partner (latest version)", courier, "SOFT_SERVED_PARTNER",
      "PROMISED_DELIVERY_PARTNER")
agree("soft served delivery time = promised delivery time", courier, "SOFT_SERVED_DELIVERY_TIME",
      "PROMISED_DELIVERY_TIME")
agree("soft served dispatch time = promised dispatch time", courier, "SOFT_SERVED_DISPATCH_TIME",
      "PROMISED_DISPATCH_TIME")
agree("served=LEGACY/DDB: internal soft pick = served partner", courier, "INTERNAL_SOFT_SELECTED_DELIVERY_PARTNER",
      "SOFT_SERVED_PARTNER", lambda r: r["SOFT_SERVED_CANDIDATE_TYPE"] != "COURIER_PBA")
agree("served=PBA: PBA soft pick = served partner", courier, "PBA_SOFT_SELECTED_DELIVERY_PARTNER",
      "SOFT_SERVED_PARTNER", lambda r: r["SOFT_SERVED_CANDIDATE_TYPE"] == "COURIER_PBA")
agree("hard=LEGACY/DDB: internal hard pick = booked partner", hardrows, "INTERNAL_HARD_SELECTED_DELIVERY_PARTNER",
      "HARD_BOOKED_PARTNER", lambda r: r["HARD_SELECTED_CANDIDATE_TYPE"] in (
          "COURIER_LEGACY_TAT_ADHERENCE", "COURIER_DDB_TAT_ADHERENCE"))
agree("hard=PBA: PBA hard pick = booked partner", hardrows, "PBA_HARD_SELECTED_DELIVERY_PARTNER",
      "HARD_BOOKED_PARTNER", lambda r: r["HARD_SELECTED_CANDIDATE_TYPE"] == "COURIER_PBA")
agree("shipped partner = hard booked partner", hardrows, "SHIPPED_DELIVERY_PARTNER", "HARD_BOOKED_PARTNER")
agree("shipped partner = soft served partner", courier, "SHIPPED_DELIVERY_PARTNER", "SOFT_SERVED_PARTNER")
agree("box verified = hard WH processing time", hardrows, "BOX_VERIFIED_TS", "HARD_WH_PROCESSING_TIME")

say("\n  Promise construction (minute precision, IST):")


def construct(label, pt_col, disp_col, del_col, tat_col, rs):
    n = pt_hit = disp_hit = neither = 0
    for r in rs:
        pt, dp, dl, tat = ts(r[pt_col]), ts(r[disp_col]), ts(r[del_col]), num(r[tat_col])
        if not all(isinstance(x, datetime) for x in (pt, dp, dl)) or not isinstance(tat, float):
            continue
        n += 1
        t = timedelta(minutes=round(tat * 1440))
        if abs((pt + t - dl).total_seconds()) <= 60:
            pt_hit += 1
        elif abs((dp + t - dl).total_seconds()) <= 60:
            disp_hit += 1
        else:
            neither += 1
    say(f"    {label}: n={n}; delivery = WH processing + TAT: {pct(pt_hit, n)}; "
        f"= dispatch + TAT: {pct(disp_hit, n)}; neither: {pct(neither, n)}")


cr = datetime(2026, 10, 14, 23, 5)
pre = [r for r in courier if isinstance(ts(r["SOFT_PROMISE_AT"]), datetime) and ts(r["SOFT_PROMISE_AT"]) < cr]
post = [r for r in courier if isinstance(ts(r["SOFT_PROMISE_AT"]), datetime) and ts(r["SOFT_PROMISE_AT"]) >= cr]
for lab, rs in (("before 14 Oct 23:05", pre), ("from 14 Oct 23:05", post)):
    construct(f"PBA soft, {lab}", "PROMISED_WAREHOUSE_PROCESSING_TIME", "PBA_PROJECTED_DISPATCH_TIME",
              "PBA_PROJECTED_DELIVERY_TIME", "PBA_SOFT_SELECTED_PARTNER_TAT_IN_DAYS", rs)
    construct(f"Internal soft, {lab}", "PROMISED_WAREHOUSE_PROCESSING_TIME", "INTERNAL_PROJECTED_DISPATCH_TIME",
              "INTERNAL_PROJECTED_DELIVERY_TIME", "INTERNAL_SOFT_SELECTED_PARTNER_TAT_IN_DAYS", rs)
construct("PBA hard (all)", "HARD_WH_PROCESSING_TIME", "PBA_HARD_PROJECTED_DISPATCH_TIME",
          "PBA_HARD_PROJECTED_DELIVERY_TIME", "PBA_HARD_PARTNER_TAT_IN_DAYS", hardrows)

say("\n== 8. Arrays ==")


def arrays(col, rs, rank_key=None):
    lens, bad, rank_dupe, empty = [], 0, 0, 0
    for r in rs:
        a = arr(r[col])
        if a is None:
            continue
        if a == "BAD":
            bad += 1
            continue
        if not a:
            empty += 1
        lens.append(len(a))
        if rank_key:
            ranks = [x.get(rank_key) for x in a]
            if len(ranks) != len(set(ranks)):
                rank_dupe += 1
    lens.sort()
    say(f"  {col}: present {len(lens) + bad}, unparseable {bad}, empty {empty}, "
        f"length min/median/max {lens[0] if lens else '-'}/{lens[len(lens) // 2] if lens else '-'}/"
        f"{lens[-1] if lens else '-'}" + (f", rows with repeated ranks {rank_dupe}" if rank_key else ""))


arrays("PBA_SOFT_PREFERENCE_ARRAY", courier)
arrays("INTERNAL_SOFT_PREFERENCE_ARRAY", courier, "rank")
arrays("PBA_HARD_PREFERENCE_ARRAY", hardrows)
arrays("INTERNAL_HARD_PREFERENCE_ARRAY", hardrows, "rank")
first_is_pick = n = 0
for r in courier:
    a = arr(r["PBA_SOFT_PREFERENCE_ARRAY"])
    if isinstance(a, list) and a and not blank(r["PBA_SOFT_SELECTED_DELIVERY_PARTNER"]):
        n += 1
        elig = [x for x in a if x.get("eligible")]
        if elig and str(elig[0].get("partner")) == r["PBA_SOFT_SELECTED_DELIVERY_PARTNER"].strip():
            first_is_pick += 1
say("  PBA soft pick = first eligible partner in its array:", pct(first_is_pick, n))
ineligible = Counter()
for r in courier:
    a = arr(r["PBA_SOFT_PREFERENCE_ARRAY"])
    if isinstance(a, list):
        ineligible[sum(1 for x in a if not x.get("eligible"))] += 1
say("  ineligible partners per PBA soft array:", dict(sorted(ineligible.items())))

say("\n== 9. Actuals, courier rows with a soft record ==")
for c in ["BOX_VERIFIED_TS", "PICKUP_TIME", "DELIVERY_ATTEMPT_TIME", "DELIVERED_TIME"]:
    say(f"  {c}: filled {pct(sum(1 for r in courier if not blank(r[c])), C)}")
order_bad = 0
seq = 0
for r in courier:
    b, p, a = ts(r["BOX_VERIFIED_TS"]), ts(r["PICKUP_TIME"]), ts(r["DELIVERY_ATTEMPT_TIME"])
    if all(isinstance(x, datetime) for x in (b, p, a)):
        seq += 1
        if not (b <= p <= a):
            order_bad += 1
say("  rows with box verified, pickup and attempt all filled:", seq, " out of order (not box <= pickup <= attempt):",
    order_bad)

say("\n== 10. Unparseable values ==")
tcols = [c for c in cols if c.endswith(("_AT", "_TIME", "_TS")) and c != "SOFT_CALLER"]
for c in tcols:
    b = sum(1 for r in rows if ts(r[c]) == "BAD")
    if b:
        say(f"  {c}: {b} unparseable")
ncols = [c for c in cols if "TAT_IN_DAYS" in c or "BUFFER" in c or "MINUTES" in c or c.endswith("_PARTNER")]
for c in ncols:
    b = sum(1 for r in rows if num(r[c]) == "BAD")
    if b:
        say(f"  {c}: {b} non-numeric")
say("  (no lines above = all timestamp and numeric columns parse)")

say("\n== 11. Follow-ups ==")
miss = tie = 0
for r in hardrows:
    a = arr(r["INTERNAL_HARD_PREFERENCE_ARRAY"])
    if isinstance(a, list):
        rk = [x.get("rank") for x in a]
        if None in rk:
            miss += 1
        elif len(rk) != len(set(rk)):
            tie += 1
say("  internal hard arrays with unranked partners (no 'rank' key):", miss, " with tied ranks:", tie)
say("  soft caller x soft promise more than 60 min after placement:")
gc = Counter()
for r in courier:
    a, b = ts(r["ORDER_PLACED_AT"]), ts(r["SOFT_PROMISE_AT"])
    gc[(r["SOFT_CALLER"], (b - a).total_seconds() > 3600)] += 1
for k in sorted(gc):
    say(f"    {k[0]}, >60 min={k[1]}: {gc[k]}")
dist("ETA_DETAILS_VERSION (courier rows with soft record)", [r["ETA_DETAILS_VERSION"] for r in courier], top=6)
say("  PBA hard construction by hard_allocated_at hour (PT = WH processing + TAT, DISP = dispatch + TAT):")
hc = Counter()
for r in hardrows:
    pt, dp, dl, ha = (ts(r["HARD_WH_PROCESSING_TIME"]), ts(r["PBA_HARD_PROJECTED_DISPATCH_TIME"]),
                      ts(r["PBA_HARD_PROJECTED_DELIVERY_TIME"]), ts(r["HARD_ALLOCATED_AT"]))
    tat = num(r["PBA_HARD_PARTNER_TAT_IN_DAYS"])
    if not all(isinstance(x, datetime) for x in (pt, dp, dl, ha)) or not isinstance(tat, float):
        continue
    t = timedelta(minutes=round(tat * 1440))
    if pt != dp and abs((pt + t - dl).total_seconds()) <= 60:
        k = "PT"
    elif abs((dp + t - dl).total_seconds()) <= 60:
        k = "DISP"
    else:
        k = "other"
    hc[(ha.strftime("%Y-%m-%d %H:00"), k)] += 1
for h in sorted({k[0] for k in hc}):
    say(f"    {h}: PT {hc.get((h, 'PT'), 0)}, DISP {hc.get((h, 'DISP'), 0)}, other {hc.get((h, 'other'), 0)}")
nosoft = [r for r in rows if r["HAS_SOFT_RECORD"] == "false" and r["SDD_ENABLED"] == "false"]
dist("non-SDD rows without a soft record: IS_FALLBACK_PROMISE", [r["IS_FALLBACK_PROMISE"] for r in nosoft])
dist("non-SDD rows without a soft record: TASK_PROCESSING_TYPE", [r["TASK_PROCESSING_TYPE"] for r in nosoft])
nonnum = [r["ORDER_ID"] for r in rows if not r["ORDER_ID"].strip().isdigit()]
say("  non-numeric order_ids:", len(nonnum), " blank sdd_enabled among them:",
    sum(1 for r in rows if not r["ORDER_ID"].strip().isdigit() and blank(r["SDD_ENABLED"])))

OUT.parent.mkdir(exist_ok=True)
OUT.write_text("\n".join(lines) + "\n")
print("\n".join(lines))
