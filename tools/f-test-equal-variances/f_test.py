"""
f_test.py  —  TheQualityVault.com
================================
F-Test for Equal Variances

Tests whether two normal populations have the same variance. F = s1² / s2².
Two-sided p-value and a confidence interval for the variance ratio.

The Excel workbook (F_Test_Equal_Variances.xlsx) and f_test.R give the same results.

Run
---
    python f_test.py demo
    python f_test.py --csv my_data.csv --cols "Machine A" "Machine B"

Dependencies: numpy, pandas, scipy
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

def analyze(df, cols, alpha=0.05, **_):
    a, b = _num(df[cols[0]]), _num(df[cols[1]])
    d1, d2 = len(a) - 1, len(b) - 1
    F = a.var(ddof=1) / b.var(ddof=1)
    p = 2 * min(stats.f.cdf(F, d1, d2), stats.f.sf(F, d1, d2))
    return {"n1": len(a), "n2": len(b), "StDev 1": a.std(ddof=1), "StDev 2": b.std(ddof=1), "F": F, "DF1": d1, "DF2": d2,
            "P-value": p, "Ratio CI lower": F / stats.f.ppf(1 - alpha / 2, d1, d2), "Ratio CI upper": F * stats.f.ppf(1 - alpha / 2, d2, d1),
            "conclusion": (f"p = {p:.4f} < {alpha} → reject H0: the variances differ." if p < alpha else
                           f"p = {p:.4f} ≥ {alpha} → fail to reject H0: no evidence the variances differ.")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  F-Test for Equal Variances  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="F-Test for Equal Variances — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)

    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Machine A', 'Machine B'], **{})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
