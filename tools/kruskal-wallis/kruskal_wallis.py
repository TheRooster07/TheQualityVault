"""
kruskal_wallis.py  —  TheQualityVault.com
========================================
Kruskal-Wallis Test

Rank-based test that k independent samples come from the same distribution (non-parametric
one-way ANOVA). H statistic with tie correction, chi-square p-value.

The Excel workbook (Kruskal_Wallis.xlsx) and kruskal_wallis.R give the same results.

Run
---
    python kruskal_wallis.py demo
    python kruskal_wallis.py --csv my_data.csv --cols "Method A" "Method B" "Method C"

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
    groups = [_num(df[c]) for c in cols]
    r = stats.kruskal(*groups); p = float(r.pvalue)
    return {"Groups k": len(groups), "N": sum(len(g) for g in groups), "H (tie-corrected)": float(r.statistic),
            "DF": len(groups) - 1, "P-value": p,
            "conclusion": (f"p = {p:.4f} < {alpha} → reject H0: at least one group differs." if p < alpha else
                           f"p = {p:.4f} ≥ {alpha} → fail to reject H0: no evidence the groups differ.")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  Kruskal-Wallis Test  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="Kruskal-Wallis Test — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)

    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Method A', 'Method B', 'Method C'], **{})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
