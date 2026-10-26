# Purpose: A/B readout for ETA-E3 (two-proportion z-test, 95% CI, bounce rate, SRM check, sample-size check, segment overlap)
# Serves: M1, M2, M3, M4, M5
# Reads: archives/eta-ranges-xp/raw-data/mixpanel-etaranges-dashboard-counts-2026-10-26.csv (Q1)
# Writes: archives/eta-ranges-xp/outputs/ab-readout-2026-10-26.csv
# Run with: python3 archives/eta-ranges-xp/scripts/2026-10-26-aggregate-ab-readout-v2.py

import math
import pandas as pd

SRC = "archives/eta-ranges-xp/raw-data/mixpanel-etaranges-dashboard-counts-2026-10-26.csv"
OUT = "archives/eta-ranges-xp/outputs/ab-readout-2026-10-26.csv"
Z_A, Z_B = 1.96, 0.84   # 95% confidence, 80% power (PRD)
MDE_PP = 1.0            # PRD MDE


def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def ztest(n_c, x_c, n_t, x_t):
    p_c, p_t = x_c / n_c, x_t / n_t
    diff = p_t - p_c
    p_pool = (x_c + x_t) / (n_c + n_t)
    se_pool = math.sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_t))
    z = diff / se_pool
    p = 2 * (1 - norm_cdf(abs(z)))
    se = math.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    return p_c, p_t, diff, diff - Z_A * se, diff + Z_A * se, p


def n_per_arm(p, delta):
    return math.ceil(2 * (Z_A + Z_B) ** 2 * p * (1 - p) / delta ** 2)


def main():
    df = pd.read_csv(SRC)
    rows = []
    for (seg, stage), g in df[df.stage != "SRM_uniques"].groupby(["segment", "stage"], sort=False):
        c = g[g.variant == "control"].iloc[0]
        t = g[g.variant == "test"].iloc[0]
        p_c, p_t, d, lo, hi, p = ztest(c.users_start, c.users_end, t.users_start, t.users_end)
        for name, r, rate in (("control", c, p_c), ("test", t, p_t)):
            rows.append(dict(segment=seg, stage=stage, variant=name, users=int(r.users_start),
                             conversions=int(r.users_end), rate_pct=round(rate * 100, 2), bounce_pct=round((1 - rate) * 100, 2),
                             diff_vs_control_pp=None if name == "control" else round(d * 100, 2),
                             ci95_low_pp=None if name == "control" else round(lo * 100, 2),
                             ci95_high_pp=None if name == "control" else round(hi * 100, 2),
                             p_value=None if name == "control" else round(p, 4)))
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))

    # SRM: actual split vs planned 50/50 (chi-square, 1 df)
    s = df[df.stage == "SRM_uniques"].set_index("variant").users_start
    tot = s.sum()
    exp = tot / 2
    chi = sum((s[v] - exp) ** 2 / exp for v in ("control", "test"))
    p_srm = 1 - math.erf(math.sqrt(chi / 2))
    print(f"\nSRM: control={s['control']} test={s['test']} chi2={chi:.3f} p={p_srm:.4f}")

    # Sample size for MDE and observed effect, using overall control rate
    o = out[(out.segment == "overall") & (out.variant == "control")].iloc[0]
    base = o.rate_pct / 100
    n_mde = n_per_arm(base, MDE_PP / 100)
    print(f"\nBaseline (control) rate {o.rate_pct}%; n per arm for {MDE_PP}pp MDE = {n_mde}; have control={o.users}")
    ov = out[(out.segment == "overall") & (out.variant == "test")].iloc[0]
    obs = ov.diff_vs_control_pp / 100
    if obs != 0:
        n_obs = n_per_arm(base, abs(obs))
        print(f"Observed effect {ov.diff_vs_control_pp}pp; n per arm to detect it at 80% power = {n_obs}; "
              f"multiple of current arm size = {n_obs / o.users:.1f}x")
    # Smallest effect detectable with current n (80% power)
    mde_now = (Z_A + Z_B) * math.sqrt(2 * base * (1 - base) / o.users)
    print(f"Smallest effect detectable at current n per arm (80% power) = {mde_now*100:.2f}pp")
    # Segment overlap: NU + RU viewers vs overall viewers, per variant
    print()
    for v in ("control", "test"):
        seg = df[(df.stage == "OS_to_OP") & (df.variant == v)].set_index("segment").users_start
        print(f"Overlap {v}: NU+RU={seg['NU'] + seg['RU']} overall={seg['overall']} extra={seg['NU'] + seg['RU'] - seg['overall']}")
    # Upper bound of the overall M1 interval as a share of the PRD target
    ub = ov.ci95_high_pp
    print(f"Upper bound {ub}pp is {ub / MDE_PP * 100:.0f}% of the {MDE_PP}pp target")


if __name__ == "__main__":
    main()
