#!/usr/bin/env python3
"""S1: ETA-F1 test vs control, Summary -> Order Placed. Serves M1, M2, M4.
Input: archives/eta-framing-xp/raw-data/dashboard-funnels.csv (Mixpanel dashboard 11538578, read 2026-10-26)
Output: archives/eta-framing-xp/outputs/eta-f1-significance.csv (and stdout)
Run with: python3 archives/eta-framing-xp/scripts/<this file>
"""
import csv, math
from statistics import NormalDist
N = NormalDist()
rows = list(csv.DictReader(open("archives/eta-framing-xp/raw-data/dashboard-funnels.csv")))
out = []
for cut in ["overall", "new_users", "returning_users"]:
    t = next(r for r in rows if r["cut"] == cut and r["variant"] == "test")
    c = next(r for r in rows if r["cut"] == cut and r["variant"] == "control")
    nt, xt, nc, xc = int(t["summary_users"]), int(t["order_users"]), int(c["summary_users"]), int(c["order_users"])
    pt, pc = xt / nt, xc / nc
    d = pt - pc
    se_u = math.sqrt(pt*(1-pt)/nt + pc*(1-pc)/nc)
    pp = (xt + xc) / (nt + nc)
    z = d / math.sqrt(pp*(1-pp)*(1/nt + 1/nc))
    p = 2 * (1 - N.cdf(abs(z)))
    mde = (N.inv_cdf(0.975) + N.inv_cdf(0.8)) * math.sqrt(2*pc*(1-pc)/min(nt, nc))
    n_need = 2 * (N.inv_cdf(0.975) + N.inv_cdf(0.8))**2 * pc*(1-pc) / 0.01**2
    out.append(dict(cut=cut, n_test=nt, n_control=nc, conv_test=round(pt*100, 2), conv_control=round(pc*100, 2),
        diff_pp=round(d*100, 2), ci_low_pp=round((d-1.96*se_u)*100, 2), ci_high_pp=round((d+1.96*se_u)*100, 2),
        z=round(z, 2), p_value=round(p, 3), bounce_test=round((1-pt)*100, 2), bounce_control=round((1-pc)*100, 2),
        detectable_pp_at_80_power=round(mde*100, 2), n_per_arm_needed_for_1pp=round(n_need)))
# group-size check on unique summary users (dashboard report 93208927)
a, b = 37204, 36659
chi = (a-b)**2 / ((a+b)/2) * 1  # (a-e)^2/e + (b-e)^2/e with e=(a+b)/2 equals (a-b)^2/(2e)... computed explicitly:
e = (a+b)/2
chi = (a-e)**2/e + (b-e)**2/e
srm_p = 2 * (1 - N.cdf(math.sqrt(chi)))
print("SRM check (test 37204 vs control 36659 unique summary users): chi2=%.2f p=%.3f share_test=%.2f%%" % (chi, srm_p, a/(a+b)*100))
w = csv.DictWriter(open("archives/eta-framing-xp/outputs/eta-f1-significance.csv", "w"), fieldnames=out[0].keys())
w.writeheader(); w.writerows(out)
for o in out: print(o)
