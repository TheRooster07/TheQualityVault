"""
chi_square_gof.py  —  TheQualityVault.com
========================================
Chi-Square Goodness of Fit

Tests whether observed counts in k categories match expected proportions (e.g. equal, or a
historical mix). Reports chi-square, p-value and each category's contribution.

The Excel workbook (Chi_Square_Goodness_of_Fit.xlsx) and chi_square_gof.R give the same results.

Run
---
    python chi_square_gof.py demo
    python chi_square_gof.py --csv my_data.csv --cols Category Observed Expected

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
    d = df[cols].dropna()
    o = d[cols[1]].astype(float).to_numpy(); w = d[cols[2]].astype(float).to_numpy()
    e = o.sum() * w / w.sum()
    r = stats.chisquare(o, e); p = float(r.pvalue)
    for c, oi, ei in zip(d[cols[0]], o, e):
        print(f"  {str(c):<16} observed {oi:>8.0f}  expected {ei:>9.2f}  contribution {(oi - ei) ** 2 / ei:>8.3f}")
    return {"Categories k": len(o), "N": o.sum(), "Chi-square": float(r.statistic), "DF": len(o) - 1, "P-value": p,
            "Smallest expected count": e.min(),
            "conclusion": (f"p = {p:.4f} < {alpha} → reject H0: the counts do not follow the expected proportions." if p < alpha else
                           f"p = {p:.4f} ≥ {alpha} → fail to reject H0: counts are consistent with the expected proportions.")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  Chi-Square Goodness of Fit  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="Chi-Square Goodness of Fit — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)

    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Day', 'Defects observed', 'Expected proportion'], **{})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
