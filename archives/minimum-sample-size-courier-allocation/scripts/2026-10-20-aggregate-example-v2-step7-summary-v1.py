# Purpose: example step 7: summarise the 9-order example by rule (adherence A and B, exclusions, promise, replay match)
# Serves: worked example only (pre-brief); no metric
# Reads: archives/minimum-sample-size-courier-allocation/outputs/example-v2-step6-orders-2026-09-21.csv (from step 6 script v1)
#        archives/minimum-sample-size-courier-allocation/raw-data/orders-2026-09.csv (real promise and actual days of each order)
# Writes: archives/minimum-sample-size-courier-allocation/outputs/example-v2-step7-summary-2026-09-21.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-example-v2-step7-summary-v1.py
#
# Per rule: A adherence = (Early + On-Time) / orders; B adherence = (Early + On-Time) / orders not excluded;
# excluded share = excluded / orders; average simulated promise (order placed stage winner's lane TAT);
# replay match = orders where today's invoice-stage winner is the courier that actually shipped.
# "Real" row: each order's real outcome against its real promise (PROMISE_TAT).

import csv
from datetime import datetime

P = "archives/minimum-sample-size-courier-allocation/"
FMT = "%b %d, %Y, %I:%M %p"


def main():
    rows = list(csv.DictReader(open(P + "outputs/example-v2-step6-orders-2026-09-21.csv", encoding="utf-8", newline="")))
    ids = {r["order_id"] for r in rows}
    real = {}
    for r in csv.DictReader(open(P + "raw-data/orders-2026-09.csv", encoding="utf-8-sig", newline="")):
        o = r["ORDER_ID"].replace(",", "")
        if o in ids:
            a = datetime.strptime(r["DELIVERY_ATTEMPT_TIME"], FMT)
            p = datetime.strptime(r["PICKUP_TIME"], FMT)
            real[o] = ((a.date() - p.date()).days, int(r["PROMISE_TAT"]))
    n = len(ids)
    out = []
    ok_real = sum(1 for d, pr in real.values() if d <= pr)
    out.append(["real (actual vs real promise)", n, "", ok_real, round(100 * ok_real / n, 1), "", "", round(sum(pr for _, pr in real.values()) / n, 2), ""])
    print(f"Orders: {n}")
    print(f"Real: {ok_real} of {n} early or on time = {100 * ok_real / n:.1f}%; average real promise {sum(pr for _, pr in real.values()) / n:.2f} days")
    for rule in ["today", "x=10", "x=15", "x=20"]:
        rr = [r for r in rows if r["rule"] == rule]
        a_ok = sum(1 for r in rr if r["A_class"] in ("Early", "On-Time"))
        b_in = [r for r in rr if r["B_class"] != "excluded"]
        b_ok = sum(1 for r in b_in if r["B_class"] in ("Early", "On-Time"))
        excl = len(rr) - len(b_in)
        promise = sum(int(r["simulated_promise_days"]) for r in rr) / len(rr)
        match = sum(1 for r in rr if r["invoice_stage_winner"] == r["shipping_courier"])
        b_pct = round(100 * b_ok / len(b_in), 1) if b_in else ""
        out.append([rule, len(rr), a_ok, b_ok, round(100 * a_ok / len(rr), 1), b_pct, excl, round(promise, 2), match])
        print(f"{rule:6s}: A {a_ok}/{len(rr)} = {100 * a_ok / len(rr):.1f}% | B {b_ok}/{len(b_in)}"
              f"{' = ' + str(b_pct) + '%' if b_in else ''} | excluded {excl} of {len(rr)} | average simulated promise {promise:.2f} days"
              f" | invoice winner = shipping courier on {match} of {len(rr)}")
    with open(P + "outputs/example-v2-step7-summary-2026-09-21.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rule", "orders", "A_early_or_on_time", "B_early_or_on_time", "A_adherence_pct", "B_adherence_pct", "B_excluded", "avg_promise_days", "invoice_winner_equals_shipping_courier"])
        w.writerows(out)


if __name__ == "__main__":
    main()
