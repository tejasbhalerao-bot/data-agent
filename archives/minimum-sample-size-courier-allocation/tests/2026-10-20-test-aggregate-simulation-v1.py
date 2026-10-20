# Tests for archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-simulation-v1.py
# Run with: python3 archives/minimum-sample-size-courier-allocation/tests/2026-10-20-test-aggregate-simulation-v1.py
# Covers the parts that classify, do arithmetic on dates or times, or join: buckets, percentile and adherence (against a plain-list
# reference), ladder stops, tie-break, schedule adjustment, classes, and the 9-order example from the process-flow note.

import importlib.util
import math
import random
import unittest

import numpy as np

SPEC = importlib.util.spec_from_file_location(
    "sim", "archives/minimum-sample-size-courier-allocation/scripts/2026-10-20-aggregate-simulation-v1.py")
sim = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sim)


def reference(actuals, delays, pct=0.85):
    """Plain-list version of the Strategy 1 method used in the 9-order example (step 3 script)."""
    s = sorted(actuals)
    pos = pct * (len(s) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    lane_tat = math.ceil(s[lo] + (s[hi] - s[lo]) * (pos - lo))
    counts = [0] * 9
    for d in delays:
        counts[sim.bucket_of(d)] += 1
    cum, n = 0, len(actuals)
    for c in counts:
        cum += c
        if cum / n >= pct:
            return lane_tat, 100 * cum / n
    return lane_tat, 100.0


class Core(unittest.TestCase):
    def test_buckets(self):
        self.assertEqual([sim.bucket_of(d) for d in (-9, -4, -3, -2, -1, 0, 1, 2, 3, 4, 7)], [0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 8])

    def test_matches_reference_on_random_pools(self):
        rnd = random.Random(7)
        for _ in range(500):
            n = rnd.randint(1, 80)
            actuals = [rnd.randint(0, 9) for _ in range(n)]
            promises = [rnd.randint(1, 7) for _ in range(n)]
            delays = [a - p for a, p in zip(actuals, promises)]
            ah = np.bincount(actuals, minlength=12)
            bh = np.bincount([sim.bucket_of(d) for d in delays], minlength=9)
            self.assertEqual(sim.tat_adh_from_hists(ah, bh), reference(actuals, delays))

    def test_example_pool_195_micro_7d(self):
        # 44 orders: 20 took 2 days, 19 took 3, 5 took 4 (9-order example). Lane TAT 3 days; adherence 95.45%.
        actuals = [2] * 20 + [3] * 19 + [4] * 5
        delays = [-4] * 2 + [-3] * 1 + [-2] * 1 + [-1] * 11 + [0] * 18 + [1] * 9 + [2] * 2
        tat, adh = reference(actuals, delays)
        self.assertEqual(tat, 3)
        self.assertAlmostEqual(adh, 95.4545, places=3)

    def test_ladder_stops(self):
        c = np.zeros((4, 16), int)
        c[0, 0] = 1                    # row 0: one order at pincode 7d, nothing wider
        c[0, 1:] = 1
        c[1, :4] = 1                   # row 1: 1 order at the pincode, 12 from micro 7d (step 4) onwards
        c[1, 4:] = 12
        c[2, 15] = 6                   # row 2: only the widest pool has orders, 6 of them
        # row 3: nothing anywhere
        stop, code = sim.stop_for_rule(c, None)                       # today: pincode 7d if it has any order, else ops config
        self.assertEqual(list(stop), [0, 0, sim.OPS, sim.OPS])
        stop, code = sim.stop_for_rule(c, 10)
        self.assertEqual(list(code), [sim.WIDEST, 4, sim.WIDEST, sim.OPS])   # row 0: 1 order everywhere < 10 -> widest pool
        self.assertEqual(list(stop[:3]), [15, 4, 15])
        stop, code = sim.stop_for_rule(c, 15)                          # row 1: 12 < 15 everywhere -> widest pool
        self.assertEqual(list(code), [sim.WIDEST, sim.WIDEST, sim.WIDEST, sim.OPS])
        stop, code = sim.stop_for_rule(c, 1 + 0)                       # a threshold of 1 stops at the first step with an order
        self.assertEqual(list(code[:2]), [0, 0])

    def test_tie_break_order(self):
        inf = np.inf
        tie = np.array([[2.0, inf, 2.0, 2.1, inf, 4.5]])      # 195 and 225 tie
        self.assertEqual(sim.pick_winner(tie)[0], 0)
        tie2 = np.array([[inf, 2.0, inf, 2.0, 2.0, inf]])     # 185, 246, 286 tie: 185 wins
        self.assertEqual(sim.pick_winner(tie2)[0], 1)
        none = np.full((1, 6), inf)
        self.assertEqual(sim.pick_winner(none)[0], -1)

    def test_schedule_adjustment(self):
        cutoff = np.array([18 * 60, 18 * 60 + 15, -1])
        clock = np.array([18 * 60, 18 * 60 + 16, 23 * 60])
        self.assertEqual(list(sim.schedule_adjustment(clock, cutoff)), [0, 1, 0])  # equal is not after; no cutoff = 0

    def test_classes(self):
        self.assertEqual(list(sim.class_of(np.array([-3, -1, 0, 1, 4]))), [0, 0, 1, 2, 2])

    def test_priority_is_the_agreed_order(self):
        self.assertEqual(sim.PRIORITY, ["195", "185", "225", "246", "286", "247"])

    def test_warehouse_19_uses_40(self):
        self.assertEqual(list(sim.eff(np.array([19, 20, 40]))), [40, 20, 40])


if __name__ == "__main__":
    unittest.main()
