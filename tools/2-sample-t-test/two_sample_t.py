"""
two_sample_t.py  —  TheQualityVault.com
======================================
2-Sample t-Test

Compares the means of two independent samples. Reports both the pooled (equal variances)
and the Welch (unequal variances) t-test with confidence intervals for the difference.

The Excel workbook (2_Sample_t_Test.xlsx) and two_sample_t.R give the same results.

Run
---
    python two_sample_t.py demo
    python two_sample_t.py --csv my_data.csv --cols "Line 1" "Line 2" --alternative two-sided

Dependencies: numpy, pandas, scipy
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

def analyze(df, cols, alternative="two-sided", alpha=0.05, **_):
    a, b = _num(df[cols[0]]), _num(df[cols[1]])
    n1, n2 = len(a), len(b)
    v1, v2 = a.var(ddof=1), b.var(ddof=1)
    d = a.mean() - b.mean()
    pooled = stats.ttest_ind(a, b, equal_var=True, alternative=alternative)
    welch = stats.ttest_ind(a, b, equal_var=False, alternative=alternative)
    dfp = n1 + n2 - 2
    sp = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / dfp)
    sep = sp * math.sqrt(1 / n1 + 1 / n2)
    sew = math.sqrt(v1 / n1 + v2 / n2)
    dfw = sew ** 4 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
    p = float(welch.pvalue)
    return {"n1": n1, "n2": n2, "Mean 1": a.mean(), "Mean 2": b.mean(), "StDev 1": math.sqrt(v1), "StDev 2": math.sqrt(v2),
            "Difference": d, "t (pooled)": float(pooled.statistic), "DF (pooled)": dfp, "P-value (pooled)": float(pooled.pvalue),
            "CI lower (pooled)": d - stats.t.ppf(1 - alpha / 2, dfp) * sep, "CI upper (pooled)": d + stats.t.ppf(1 - alpha / 2, dfp) * sep,
            "t (Welch)": float(welch.statistic), "DF (Welch)": dfw, "P-value (Welch)": p,
            "CI lower (Welch)": d - stats.t.ppf(1 - alpha / 2, dfw) * sew, "CI upper (Welch)": d + stats.t.ppf(1 - alpha / 2, dfw) * sew,
            "conclusion": (f"Welch p = {p:.4f} < {alpha} → reject H0: the means differ." if p < alpha else
                           f"Welch p = {p:.4f} ≥ {alpha} → fail to reject H0: no evidence the means differ.")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  2-Sample t-Test  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="2-Sample t-Test — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--alternative", default="two-sided", choices=["two-sided", "less", "greater"])
    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Line 1 (s)', 'Line 2 (s)'], **{'alternative': 'two-sided'})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
