"""
one_sample_t.py  —  TheQualityVault.com
======================================
1-Sample t-Test

Tests whether the mean of one sample differs from a target value mu0.
t = (x̄ − mu0) / (s/√n), df = n − 1. Reports t, p-value and a confidence interval for the mean.

The Excel workbook (1_Sample_t_Test.xlsx) and one_sample_t.R give the same results.

Run
---
    python one_sample_t.py demo
    python one_sample_t.py --csv my_data.csv --cols weight_mg --mu0 250 --alternative two-sided

Dependencies: numpy, pandas, scipy
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

def analyze(df, cols, mu0, alternative="two-sided", alpha=0.05, **_):
    x = _num(df[cols[0]])
    n, m, s = len(x), x.mean(), x.std(ddof=1)
    r = stats.ttest_1samp(x, mu0, alternative=alternative)
    h = stats.t.ppf(1 - alpha / 2, n - 1) * s / math.sqrt(n)
    p = float(r.pvalue)
    return {"n": n, "Mean": m, "StDev": s, "SE Mean": s / math.sqrt(n), "t": float(r.statistic), "DF": n - 1,
            "P-value": p, "CI lower": m - h, "CI upper": m + h,
            "conclusion": (f"p = {p:.4f} < {alpha} → reject H0: the mean differs from {mu0:g}." if p < alpha else
                           f"p = {p:.4f} ≥ {alpha} → fail to reject H0: no evidence the mean differs from {mu0:g}.")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  1-Sample t-Test  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="1-Sample t-Test — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--mu0", type=float, required=True)
    p.add_argument("--alternative", default="two-sided", choices=["two-sided", "less", "greater"])
    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Tablet weight (mg)'], **{'mu0': 250.0, 'alternative': 'two-sided'})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
