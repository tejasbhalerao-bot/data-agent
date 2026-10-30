# Purpose: independent recount of Section 2 soft metric 1 (PBA base, WH to Delivery on the PBA promise) for 23 Oct 10:00-11:00 IST,
#          rebuilt in Python from raw records without the SQL base logic; the result must match the SQL slice run exactly
# Serves: Dashboard S2 M1 check (verification protocol: independent recount)
# Reads: archives/pba-cr/raw-data/dashboard/s2/recount-step1-23oct-10am-11am.json  (raw promise versions, ETA record keys, order statuses)
#        archives/pba-cr/raw-data/dashboard/s2/recount-step2-23oct-10am-11am.json  (PBA candidate group of the ETA records named in step 2)
#        archives/pba-cr/raw-data/dashboard/s2/pba-side_check-slice-23oct-10am-11am.json (the SQL slice run being checked)
#        (all local only, never pushed)
# Writes: step "keys": queries-dump/dashboard/s2-promise_soft-promise_m1_check-raw-recount-step2-23oct-10am-11am.sql
#         step "compare": archives/pba-cr/outputs/dashboard-s2-m1-raw-recount.txt
# Run with: python3 archives/pba-cr/scripts/2026-10-30-structure-dashboard-s2-m1-raw-recount-v1.py keys|compare

import json, os, sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
R = f"{ROOT}/raw-data/dashboard/s2"
Q = f"{ROOT}/queries-dump/dashboard"
IST = timezone(timedelta(hours=5, minutes=30))
START, END = datetime(2026, 10, 23, 10, tzinfo=IST), datetime(2026, 10, 23, 11, tzinfo=IST)

lines = []
def say(t=""): print(t); lines.append(t)
def check(ok, label):
    say(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    if not ok: raise SystemExit(f"check failed: {label}")

def ts(s):
    """'2026-10-23 10:25:48.000 +0530' or ISO '2026-10-24T17:00:00+05:30' -> aware datetime"""
    s = s.strip().replace("T", " ")
    if s.endswith("Z"): s = s[:-1] + " +0000"
    for f in ("%Y-%m-%d %H:%M:%S.%f %z", "%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S.%f%z", "%Y-%m-%d %H:%M:%S%z"):
        try: return datetime.strptime(s, f)
        except ValueError: pass
    raise ValueError(s)

def rows_of(path):
    j = json.load(open(path)); d = j["data"]; cols = [c["name"] for c in d["cols"]]
    assert not d.get("rows_truncated") and j["row_count"] == len(d["rows"]) < 2000, path
    return j, [dict(zip(cols, r)) for r in d["rows"]]

def as_list(v): return json.loads(v) if isinstance(v, str) else (v or [])

def pba_base():
    """Apply the rules from the field mapping to raw records: placed in the hour, latest promise version, standing ETA record,
    served by COURIER_PBA, SDD off, latest order status not 49/312."""
    j, rows = rows_of(f"{R}/recount-step1-23oct-10am-11am.json")
    check(j["json_query"]["stages"][0]["native"].strip() == open(f"{Q}/s2-promise_soft-promise_m1_check-raw-recount-step1-23oct-10am-11am.sql").read().strip(),
          "step 1: SQL Metabase ran is the saved file")
    out, why = {}, {}
    for r in rows:
        sed = as_list(r["SED_ROWS"]); eta = as_list(r["ETA_ROWS"]); od = as_list(r["OD_ROWS"])
        placed = min(ts(x["created_at"]) for x in sed)
        if not (START <= placed < END): why["placed outside the hour"] = why.get("placed outside the hour", 0) + 1; continue
        latest = max(sed, key=lambda x: int(x["version"]))
        mine = [e for e in eta if e["request_id"] == latest["request_id"]]
        if not mine: why["no ETA record for the standing promise"] = why.get("no ETA record for the standing promise", 0) + 1; continue
        stand = max(mine, key=lambda e: e["created_at"])
        if stand["served"] != "COURIER_PBA": why["standing record not served by PBA"] = why.get("standing record not served by PBA", 0) + 1; continue
        if latest["sdd_enabled"] is not False: why["SDD on or blank"] = why.get("SDD on or blank", 0) + 1; continue
        if not od: why["no order status row"] = why.get("no order status row", 0) + 1; continue
        st = max(od, key=lambda o: o["ts"])["status"]
        if st in (49, 312): why["latest status 49/312 (dropped)"] = why.get("latest status 49/312 (dropped)", 0) + 1; continue
        out[r["REFERENCE_ID"]] = dict(request_id=latest["request_id"], stand_created=stand["created_at"], pwpt=latest["pwpt"])
    say(f"  [INFO] {len(rows)} raw orders read; PBA base in the hour: {len(out)}; left out: {why}")
    return out

mode = sys.argv[1]
base = pba_base()

if mode == "keys":
    vals = ",\n        ".join(f"('{k}', '{v['request_id']}')" for k, v in sorted(base.items()))
    sql = f"""WITH k AS (
    -- Section 2 soft metric 1, independent recount, step 2: the PBA candidate group of every ETA record carrying each order's standing request id
    -- (keys written by scripts/2026-10-30-structure-dashboard-s2-m1-raw-recount-v1.py keys; the script picks the standing record itself)
    SELECT column1 AS reference_id, column2 AS request_id FROM VALUES
        {vals}
)
SELECT i.reference_id, i.request_id, i.created_at::STRING AS created_at,
       TO_VARCHAR(FILTER(TRY_PARSE_JSON(TO_VARCHAR(i.eval_candidates)), c -> c:candidate_type::STRING = 'COURIER_PBA')) AS pba_groups
FROM prod_silver_db.logistics.logistics_eta_instrumentation i
JOIN k ON k.reference_id = i.reference_id AND k.request_id = i.request_id
WHERE i.created_at >= '2026-10-22 10:00:00'::TIMESTAMP_NTZ AND i.created_at < '2026-11-02 11:00:00'::TIMESTAMP_NTZ
ORDER BY 1, 3
"""
    open(f"{Q}/s2-promise_soft-promise_m1_check-raw-recount-step2-23oct-10am-11am.sql", "w").write(sql)
    say(f"  wrote step 2 query with {len(base)} keys")

elif mode == "compare":
    j, rows = rows_of(f"{R}/recount-step2-23oct-10am-11am.json")
    check(j["json_query"]["stages"][0]["native"].strip() == open(f"{Q}/s2-promise_soft-promise_m1_check-raw-recount-step2-23oct-10am-11am.sql").read().strip(),
          "step 2: SQL Metabase ran is the saved file")
    by = {}
    for r in rows: by.setdefault(r["REFERENCE_ID"], []).append(r)
    hist, multi = {}, 0
    for k, v in base.items():
        recs = by.get(k, [])
        check(any(x["CREATED_AT"] == v["stand_created"] for x in recs), f"{k}: standing ETA record found in step 2")
        rec = max(recs, key=lambda x: x["CREATED_AT"])
        groups = as_list(rec["PBA_GROUPS"])
        if len(groups) != 1: multi += 1
        ev = [e for g in groups for e in (g.get("evaluated_candidates") or [])]  # array order, as the base orders by index
        pick = next((e for e in ev if str(e.get("eligible")).lower() == "true"), None)
        buf = next((b for g in groups for b in (g.get("buffer_adjusted_candidates") or []) if str(b.get("rank")) in ("1", "1.0")), None)
        dl = (buf or {}).get("delivery_time") or (pick or {}).get("delivery_time")
        if dl is None or v["pwpt"] is None: days = None
        else: days = (ts(dl).astimezone(IST).date() - ts(v["pwpt"]).astimezone(IST).date()).days
        hist[days] = hist.get(days, 0) + 1
    say(f"  [INFO] orders whose ETA record has more than one PBA candidate group: {multi}")
    js, srows = rows_of(f"{R}/pba-side_check-slice-23oct-10am-11am.json")
    sql_hist = {r["DAYS"]: r["N_ORDERS"] for r in srows if r["BASE_GROUP"] == "PBA" and r["MEASURE"] == "WH_PBA"}
    say(f"  Python recount (days: orders): {dict(sorted(hist.items(), key=lambda x: (x[0] is None, x[0] or 0)))}")
    say(f"  SQL slice run   (days: orders): {dict(sorted(sql_hist.items(), key=lambda x: (x[0] is None, x[0] or 0)))}")
    check(sum(hist.values()) == sum(sql_hist.values()), f"PBA base size matches: {sum(hist.values())} vs {sum(sql_hist.values())}")
    check(hist == sql_hist, "promise-day distribution matches order for order count")
    os.makedirs(f"{ROOT}/outputs", exist_ok=True)
    open(f"{ROOT}/outputs/dashboard-s2-m1-raw-recount.txt", "w").write("\n".join(lines) + "\n")
