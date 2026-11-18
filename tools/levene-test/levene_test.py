"""
levene_test.py  —  TheQualityVault.com
=====================================
Levene's Test (Brown-Forsythe)

Tests whether 2 or more groups have equal variances. Brown-Forsythe version: one-way ANOVA on
the absolute deviations from each group's median – robust to non-normal data.

The Excel workbook (Levene_Test.xlsx) and levene_test.R give the same results.

Run
---
    python levene_test.py demo
    python levene_test.py --csv my_data.csv --cols "Line 1" "Line 2" "Line 3"

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
    z = [np.abs(g - np.median(g)) for g in groups]
    k, N, ssb, ssw, W, p = _anova(z)
    chk = stats.levene(*groups, center="median")
    assert abs(chk.statistic - W) < 1e-9
    return {"Groups k": k, "N": N, "W (F)": W, "DF1": k - 1, "DF2": N - k, "P-value": p,
            "conclusion": (f"p = {p:.4f} < {alpha} → reject H0: the variances differ." if p < alpha else
                           f"p = {p:.4f} ≥ {alpha} → fail to reject H0: no evidence the variances differ.")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  Levene's Test (Brown-Forsythe)  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="Levene's Test (Brown-Forsythe) — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)

    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Line 1', 'Line 2', 'Line 3'], **{})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
