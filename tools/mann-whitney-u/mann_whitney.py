"""
mann_whitney.py  —  TheQualityVault.com
======================================
Mann-Whitney U Test

Rank-based test that two independent samples come from the same distribution (often read as
'equal medians'). Normal approximation with tie correction and continuity correction.

The Excel workbook (Mann_Whitney_U.xlsx) and mann_whitney.R give the same results.

Run
---
    python mann_whitney.py demo
    python mann_whitney.py --csv my_data.csv --cols "Vendor A" "Vendor B"

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
    r = stats.mannwhitneyu(a, b, alternative="two-sided", method="asymptotic", use_continuity=True)
    p = float(r.pvalue)
    return {"n1": len(a), "n2": len(b), "Median 1": np.median(a), "Median 2": np.median(b), "U (sample 1)": float(r.statistic),
            "P-value": p,
            "conclusion": (f"p = {p:.4f} < {alpha} → reject H0: the distributions differ." if p < alpha else
                           f"p = {p:.4f} ≥ {alpha} → fail to reject H0: no evidence the distributions differ.")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  Mann-Whitney U Test  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="Mann-Whitney U Test — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)

    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Vendor A (days)', 'Vendor B (days)'], **{})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
