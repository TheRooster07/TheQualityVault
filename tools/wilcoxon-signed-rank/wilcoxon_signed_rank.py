"""
wilcoxon_signed_rank.py  —  TheQualityVault.com
==============================================
Wilcoxon Signed Rank Test

Tests whether the median of paired differences is zero (two columns) or whether one sample's
median equals a target (one column). Zero differences are dropped; normal approximation with
tie and continuity corrections.

The Excel workbook (Wilcoxon_Signed_Rank.xlsx) and wilcoxon_signed_rank.R give the same results.

Run
---
    python wilcoxon_signed_rank.py demo
    python wilcoxon_signed_rank.py --csv my_data.csv --cols Before After      (or --cols x --m0 10 for one sample)

Dependencies: numpy, pandas, scipy
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

def analyze(df, cols, m0=0.0, alpha=0.05, **_):
    if len(cols) > 1:
        d2 = df[cols].apply(pd.to_numeric, errors="coerce").dropna()
        d = (d2[cols[0]] - d2[cols[1]]).to_numpy(float)
    else:
        d = _num(df[cols[0]]) - m0
    d = np.round(d, 10)
    d = d[d != 0]
    r = stats.wilcoxon(d, correction=True, method="approx")
    ranks = stats.rankdata(np.abs(d))
    wplus = float(ranks[d > 0].sum())
    p = float(r.pvalue)
    return {"Non-zero differences": len(d), "Median difference": float(np.median(d)), "W+": wplus, "P-value": p,
            "conclusion": (f"p = {p:.4f} < {alpha} → reject H0: the median difference is not zero." if p < alpha else
                           f"p = {p:.4f} ≥ {alpha} → fail to reject H0: no evidence of a difference.")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  Wilcoxon Signed Rank Test  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="Wilcoxon Signed Rank Test — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--m0", type=float, default=0.0, help="target median (one-sample mode)")
    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Before (s)', 'After (s)'], **{'m0': 0.0})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
