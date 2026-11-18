"""
fisher_exact.py  —  TheQualityVault.com
======================================
Fisher's Exact Test

Exact test of association for a 2 × 2 table – use instead of chi-square when counts are small
(any expected count below 5). Reports two-sided and one-sided p-values and the odds ratio.
Tables larger than 2 × 2: the R version tries an exact test; Excel and Python return N/A with the reason.

The Excel workbook (Fisher_Exact_Test.xlsx) and fisher_exact.R give the same results.

Run
---
    python fisher_exact.py demo
    python fisher_exact.py --csv my_data.csv --cols Supplier Pass Fail

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
    t = df[cols].dropna(how="all").set_index(cols[0]).apply(pd.to_numeric, errors="coerce").fillna(0)
    m = t.to_numpy(float)
    if m.shape != (2, 2):
        na = {"Rows": m.shape[0], "Columns": m.shape[1]}
        na.update({k: "N/A" for k in ("Odds ratio", "P-value (two-sided)", "P-value (less)", "P-value (greater)")})
        na["conclusion"] = (f"N/A – the table is {m.shape[0]} × {m.shape[1]}. scipy's exact test only supports 2 × 2 tables. "
                            "Use fisher_exact.R (fisher.test handles larger tables) or merge categories to 2 × 2.")
        return na
    m = m.astype(int)
    a, b, c, d = m.ravel()
    p2 = float(stats.fisher_exact(m, alternative="two-sided")[1])
    pl = float(stats.fisher_exact(m, alternative="less")[1])
    pg = float(stats.fisher_exact(m, alternative="greater")[1])
    orr = (a * d) / (b * c) if b * c > 0 else float("inf")
    return {"Rows": 2, "Columns": 2, "N": int(m.sum()), "Odds ratio": orr, "P-value (two-sided)": p2,
            "P-value (less)": pl, "P-value (greater)": pg,
            "conclusion": (f"p = {p2:.4f} < {alpha} → reject H0: the row and column variables are associated." if p2 < alpha else
                           f"p = {p2:.4f} ≥ {alpha} → fail to reject H0: no evidence of association.")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  Fisher's Exact Test  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="Fisher's Exact Test — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)

    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Supplier', 'Pass', 'Fail'], **{})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
