# Test: the full simulation reproduces the 9-order example exactly
# Run with: python3 archives/minimum-sample-size-courier-allocation/tests/2026-10-20-test-simulation-matches-example-v1.py
# Needs outputs/sim-v1-orders.csv (from aggregate-simulation-v1.py) and outputs/example-v2-step6-orders-2026-09-21.csv (the vetted example, step 6 script v1).
# For each of the 9 orders and each rule it checks the order placed winner, the promise and the invoice winner against the example,
# and the M1 and M2 classes against the definitions (M1: actual days vs the promise; M2: only when the invoice winner shipped the order).

import csv

P = "archives/minimum-sample-size-courier-allocation/outputs/"


def main():
    ex = {(r["order_id"], r["rule"]): r for r in csv.DictReader(open(P + "example-v2-step6-orders-2026-09-21.csv", encoding="utf-8"))}
    ids = {k[0] for k in ex}
    sim = {}
    for r in csv.DictReader(open(P + "sim-v1-orders.csv", encoding="utf-8")):
        if r["order_id"] in ids:
            sim[(r["order_id"], r["rule"])] = r
    fails, checks = 0, 0
    for k, e in ex.items():
        s = sim.get(k)
        checks += 1
        if s is None:
            print("MISSING in simulation:", k)
            fails += 1
            continue
        want = (e["placed_stage_winner"], e["simulated_promise_days"], e["invoice_stage_winner"])
        got = (s["placed_winner"], s["promise_days"], s["invoice_winner"])
        delay = int(s["actual_days"]) - int(s["promise_days"])
        m1 = "Early" if delay < 0 else ("On-Time" if delay == 0 else "Late")
        m2 = m1 if s["invoice_winner"] == s["shipping_courier"] else ""
        ok = want == got and s["M1"] == m1 and s["M2"] == m2
        if not ok:
            fails += 1
            print("MISMATCH", k, "example", want, "simulation", got, "M1", s["M1"], m1, "M2", s["M2"], m2)
    print(f"{checks} order x rule rows compared, {fails} mismatches, {len(ids)} orders")
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()
