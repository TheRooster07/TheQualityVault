"""
one_way_anova.py  —  TheQualityVault.com
=======================================
One-Way ANOVA

Tests whether the means of k groups are all equal (one factor). Reports the ANOVA table,
R², pooled standard deviation and group confidence intervals. Python/R also print Tukey comparisons.

The Excel workbook (One_Way_ANOVA.xlsx) and one_way_anova.R give the same results.

Run
---
    python one_way_anova.py demo
    python one_way_anova.py --csv my_data.csv --cols "Supplier A" "Supplier B" "Supplier C"

Dependencies: numpy, pandas, scipy
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

def _anova(groups):
    k = len(groups); N = sum(len(g) for g in groups); gm = np.concatenate(groups).mean()
    ssb = sum(len(g) * (g.mean() - gm) ** 2 for g in groups); ssw = sum(((g - g.mean()) ** 2).sum() for g in groups)
    F = (ssb / (k - 1)) / (ssw / (N - k))
    return k, N, ssb, ssw, F, float(stats.f.sf(F, k - 1, N - k))

def analyze(df, cols, alpha=0.05, **_):
    groups = [_num(df[c]) for c in cols]
    k, N, ssb, ssw, F, p = _anova(groups)
    sp = math.sqrt(ssw / (N - k))
    for c, g in zip(cols, groups):
        h = stats.t.ppf(1 - alpha / 2, N - k) * sp / math.sqrt(len(g))
        print(f"  {c:<20} n={len(g):<4} mean={g.mean():.4f}  CI=({g.mean() - h:.4f}, {g.mean() + h:.4f})")
    try:
        print("\n  Tukey HSD pairwise comparisons:\n", stats.tukey_hsd(*groups))
    except AttributeError:
        pass
    return {"Groups k": k, "N": N, "SS Factor": ssb, "SS Error": ssw, "DF Factor": k - 1, "DF Error": N - k,
            "F": F, "P-value": p, "R-sq": ssb / (ssb + ssw), "Pooled StDev": sp,
            "conclusion": (f"p = {p:.4f} < {alpha} → reject H0: at least one mean differs." if p < alpha else
                           f"p = {p:.4f} ≥ {alpha} → fail to reject H0: no evidence the means differ.")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  One-Way ANOVA  —  TheQualityVault.com")
    print("=" * 62)
    for k, v in res.items():
        if k == "conclusion":
            continue
        print(f"  {k:<34}{v:>14,.6g}" if isinstance(v, (int, float, np.floating, np.integer)) else f"  {k:<34}{v!s:>14}")
    print("  " + res["conclusion"])
    print("=" * 62 + "\n")


def _num(s):
    return pd.to_numeric(s, errors="coerce").dropna().to_numpy(float)


def main(argv=None):
    p = argparse.ArgumentParser(description="One-Way ANOVA — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)

    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Supplier A', 'Supplier B', 'Supplier C', 'Supplier D'], **{})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
