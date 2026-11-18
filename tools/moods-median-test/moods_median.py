"""
moods_median.py  —  TheQualityVault.com
======================================
Mood's Median Test

Counts how many values in each group lie above / at-or-below the grand median and runs a
chi-square test on that table. Very robust to outliers.

The Excel workbook (Moods_Median_Test.xlsx) and moods_median.R give the same results.

Run
---
    python moods_median.py demo
    python moods_median.py --csv my_data.csv --cols "Shift 1" "Shift 2" "Shift 3"

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
    st, p, med, tbl = stats.median_test(*groups, correction=False)
    p = float(p)
    return {"Groups k": len(groups), "Grand median": float(med), "Chi-square": float(st), "DF": len(groups) - 1, "P-value": p,
            "conclusion": (f"p = {p:.4f} < {alpha} → reject H0: the medians differ." if p < alpha else
                           f"p = {p:.4f} ≥ {alpha} → fail to reject H0: no evidence the medians differ.")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  Mood's Median Test  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="Mood's Median Test — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)

    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Shift 1', 'Shift 2', 'Shift 3'], **{})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
