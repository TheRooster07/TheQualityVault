"""
bartlett_test.py  —  TheQualityVault.com
=======================================
Bartlett's Test

Tests whether k normal populations have equal variances (more powerful than Levene when data
are normal, but sensitive to non-normality).

The Excel workbook (Bartlett_Test.xlsx) and bartlett_test.R give the same results.

Run
---
    python bartlett_test.py demo
    python bartlett_test.py --csv my_data.csv --cols "Line 1" "Line 2" "Line 3"

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
    r = stats.bartlett(*groups); p = float(r.pvalue)
    k = len(groups); N = sum(len(g) for g in groups)
    sp2 = sum((len(g) - 1) * g.var(ddof=1) for g in groups) / (N - k)
    return {"Groups k": k, "N": N, "Pooled variance": sp2, "Chi-square": float(r.statistic), "DF": k - 1, "P-value": p,
            "conclusion": (f"p = {p:.4f} < {alpha} → reject H0: the variances differ." if p < alpha else
                           f"p = {p:.4f} ≥ {alpha} → fail to reject H0: no evidence the variances differ.")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  Bartlett's Test  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="Bartlett's Test — TheQualityVault.com")
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
