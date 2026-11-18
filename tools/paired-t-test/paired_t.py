"""
paired_t.py  —  TheQualityVault.com
==================================
Paired t-Test

Tests whether the mean of paired differences (first − second) differs from a hypothesised
difference (usually 0). Each row is one unit measured twice.

The Excel workbook (Paired_t_Test.xlsx) and paired_t.R give the same results.

Run
---
    python paired_t.py demo
    python paired_t.py --csv my_data.csv --cols Before After --mu0 0

Dependencies: numpy, pandas, scipy
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

def analyze(df, cols, mu0=0.0, alternative="two-sided", alpha=0.05, **_):
    d = df[cols].apply(pd.to_numeric, errors="coerce").dropna()
    diff = (d[cols[0]] - d[cols[1]]).to_numpy(float)
    n, m, s = len(diff), diff.mean(), diff.std(ddof=1)
    r = stats.ttest_1samp(diff, mu0, alternative=alternative)
    h = stats.t.ppf(1 - alpha / 2, n - 1) * s / math.sqrt(n)
    p = float(r.pvalue)
    return {"Pairs": n, "Mean difference": m, "StDev difference": s, "t": float(r.statistic), "DF": n - 1, "P-value": p,
            "CI lower": m - h, "CI upper": m + h,
            "conclusion": (f"p = {p:.4f} < {alpha} → reject H0: the mean difference is not {mu0:g}." if p < alpha else
                           f"p = {p:.4f} ≥ {alpha} → fail to reject H0: no evidence of a difference.")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  Paired t-Test  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="Paired t-Test — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--mu0", type=float, default=0.0)
    p.add_argument("--alternative", default="two-sided", choices=["two-sided", "less", "greater"])
    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Before (min)', 'After (min)'], **{'mu0': 0.0, 'alternative': 'two-sided'})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
