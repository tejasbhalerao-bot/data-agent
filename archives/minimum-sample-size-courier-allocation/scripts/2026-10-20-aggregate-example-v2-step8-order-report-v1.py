# Purpose: example step 8: order-level report for the 9 orders placed on 21 Sep on WH 37 x 271604
# Serves: worked example only (pre-brief); no metric
# Reads: archives/minimum-sample-size-courier-allocation/outputs/example-v2-step6-orders-2026-09-21.csv (from step 6 script v1)
#        archives/minimum-sample-size-courier-allocation/raw-data/orders-2026-07.csv .. orders-2026-09.csv (actual days, real promise)
#        archives/minimum-sample-size-courier-allocation/raw-data/op-2026-07.csv .. op-2026-09.csv (placed and invoice times)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/example-v2-step8-order-report-2026-09-21.csv
#         archives/minimum-sample-size-courier-allocation/outputs/example-v2-step8-order-report-2026-09-21.md
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-example-v2-step8-order-report-v1.py
#
# One row per order. Real result = actual days against the real promise (PROMISE_TAT).
# For each rule: winner at order placed and its promise, winner at invoice, A result (shipping courier's projected TAT, delay, class),
# B result (class, or excluded when the invoice winner is not the courier that shipped).
# x = 10, 15 and 20 are checked to be identical for every order and shown once.

import csv
import glob
from datetime import datetime

P = "archives/minimum-sample-size-courier-allocation/"
FMT = "%b %d, %Y, %I:%M %p"


def klass(d):
    return "Early" if d < 0 else ("On-Time" if d == 0 else "Late")


def main():
    rows = list(csv.DictReader(open(P + "outputs/example-v2-step6-orders-2026-09-21.csv", encoding="utf-8", newline="")))
    ids = []
    for r in rows:
        if r["order_id"] not in ids:
            ids.append(r["order_id"])
    by = {(r["order_id"], r["rule"]): r for r in rows}
    real = {}
    for fn in sorted(glob.glob(P + "raw-data/orders-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            o = r["ORDER_ID"].replace(",", "")
            if o in ids:
                a = datetime.strptime(r["DELIVERY_ATTEMPT_TIME"], FMT)
                p = datetime.strptime(r["PICKUP_TIME"], FMT)
                real[o] = (r["DELIVERY_PARTNER"], (a.date() - p.date()).days, int(r["PROMISE_TAT"]), a, p)
    op = {}
    for fn in sorted(glob.glob(P + "raw-data/op-2026-*.csv")):
        for r in csv.DictReader(open(fn, encoding="utf-8-sig", newline="")):
            o = r["ORDER_ID"].replace(",", "")
            if o in ids:
                op[o] = (datetime.strptime(r["DIGITISED_TS"], FMT), datetime.strptime(r["INVOICE_CREATE_TS"], FMT),
                         datetime.strptime(r["DIGITISED_WH_PROMISE"], FMT))

    same_x = all(all(by[(o, "x=10")][k] == by[(o, x)][k] for k in by[(o, "x=10")] if k != "rule") for o in ids for x in ("x=15", "x=20"))
    out, md = [], []
    for o in ids:
        c, days, pr, a, p = real[o]
        placed, inv, whp = op[o]
        t, x = by[(o, "today")], by[(o, "x=10")]

        def a_text(r):
            tat = int(r["A_projected_tat_days"])
            return f"{tat}d, {days - tat:+d}, {r['A_class']}"
        out.append([o, f"{placed:%d %b %H:%M}", f"{whp:%d %b %H:%M}", f"{inv:%d %b %H:%M}", c, days, pr, klass(days - pr),
                    t["placed_stage_winner"], t["simulated_promise_days"], t["invoice_stage_winner"], a_text(t), t["B_class"],
                    x["placed_stage_winner"], x["simulated_promise_days"], x["invoice_stage_winner"], a_text(x), x["B_class"]])
    head = ["order_id", "placed", "promised_wh_processing", "invoiced", "shipped_by", "actual_days", "real_promise_days", "real_result",
            "today_placed_winner", "today_promise_days", "today_invoice_winner", "today_A_(projected_tat,delay,class)", "today_B",
            "x10_15_20_placed_winner", "x10_15_20_promise_days", "x10_15_20_invoice_winner", "x10_15_20_A_(projected_tat,delay,class)", "x10_15_20_B"]
    with open(P + "outputs/example-v2-step8-order-report-2026-09-21.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(head)
        w.writerows(out)

    L = []
    L.append(f"x = 10, 15 and 20 identical for every order: {same_x}\n")
    L.append("### What actually happened")
    L.append("| Order | Placed | Invoiced | Shipped by | Actual days | Real promise | Real result |")
    L.append("|---|---|---|---|---|---|---|")
    for r in out:
        L.append(f"| {r[0]} | {r[1]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} | {r[7]} |")
    L.append("\n### Today's rule (x = 1) and the new rule (x = 10, 15, 20)")
    L.append("| Order | Shipped by | Today: winner at placed / invoice | Today: A | Today: B | New: winner at placed / invoice | New: promise | New: A | New: B |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for r in out:
        L.append(f"| {r[0]} | {r[4]} | {r[8]} / {r[10]} | {r[11]} | {r[12]} | {r[13]} / {r[15]} | {r[14]}d | {r[16]} | {r[17]} |")
    open(P + "outputs/example-v2-step8-order-report-2026-09-21.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
