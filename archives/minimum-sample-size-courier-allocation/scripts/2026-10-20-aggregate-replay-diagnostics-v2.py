# Purpose: how closely does the replay of today's rule reproduce what really happened (promise and courier)?
# Serves: M8 (replay match); supporting check for the whole simulation
# Reads: archives/minimum-sample-size-courier-allocation/outputs/sim-v2-orders.csv (from aggregate-simulation-v2.py), rule "today" rows only
# Writes: archives/minimum-sample-size-courier-allocation/outputs/replay-diagnostics-v2.csv
# Run with: python3 archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-replay-diagnostics-v2.py
#
# Placed dates up to 24 Sep 2026 (complete dates, see sim-v2-matchrate.csv) are used.
# Checks: (1) replayed promise vs the real promise (PROMISE_TAT); (2) the shipping courier's own projected TAT at order placed vs the real promise;
# (3) share of orders where today's replayed invoice winner is the courier that shipped; each overall and by warehouse.

import csv
import collections
from datetime import datetime, timedelta

P = "archives/minimum-sample-size-courier-allocation/outputs/"
BASE = datetime(2026, 7, 1)
CUT = datetime(2026, 9, 24, 23, 59)


def main():
    tot = collections.Counter()
    by = collections.defaultdict(collections.Counter)
    diff = collections.Counter()
    for r in csv.DictReader(open(P + "sim-v2-orders.csv", encoding="utf-8")):
        if r["rule"] != "today":
            continue
        if BASE + timedelta(minutes=int(r["placed_min"])) > CUT:
            continue
        for scope, key in (("all", "all"), ("wh", r["warehouse"])):
            c = tot if scope == "all" else by[key]
            c["orders"] += 1
            real = int(r["real_promise_days"])
            if r["promise_days"] != "":
                c["has_replay_promise"] += 1
                c["replay_promise_equal"] += int(r["promise_days"]) == real
                if scope == "all":
                    diff[int(r["promise_days"]) - real] += 1
            if r["shipping_courier_projected_tat"] != "":
                c["has_proj"] += 1
                c["proj_equal"] += int(r["shipping_courier_projected_tat"]) == real
            c["invoice_winner_is_shipper"] += r["invoice_winner"] == r["shipping_courier"]
    rows = [["scope", "orders", "replay promise equals real promise %", "shipping courier projected TAT equals real promise %", "invoice winner is the courier that shipped %"]]

    def line(name, c):
        return [name, c["orders"], round(100 * c["replay_promise_equal"] / c["has_replay_promise"], 2) if c["has_replay_promise"] else "",
                round(100 * c["proj_equal"] / c["has_proj"], 2) if c["has_proj"] else "", round(100 * c["invoice_winner_is_shipper"] / c["orders"], 2)]
    rows.append(line("all warehouses", tot))
    for k in sorted(by, key=int):
        rows.append(line(f"warehouse {k}", by[k]))
    with open(P + "replay-diagnostics-v2.csv", "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)
    for r in rows:
        print(r)
    print("replayed promise minus real promise (days) -> orders:", dict(sorted(diff.items())))


if __name__ == "__main__":
    main()
