"""
chi_square_association.py  —  TheQualityVault.com
================================================
Chi-Square Test of Association

Tests independence in an r × c table of counts (e.g. defect type × shift). Reports chi-square,
p-value, expected counts and how many cells have expected counts below 5.

The Excel workbook (Chi_Square_Association.xlsx) and chi_square_association.R give the same results.

Run
---
    python chi_square_association.py demo
    python chi_square_association.py --csv my_data.csv --cols "Defect type" "Shift 1" "Shift 2" "Shift 3"

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
    chi, p, dof, exp = stats.chi2_contingency(t.to_numpy(float), correction=False)
    print("  Expected counts:\n" + pd.DataFrame(exp, index=t.index, columns=t.columns).round(2).to_string())
    p = float(p)
    return {"Rows": t.shape[0], "Columns": t.shape[1], "N": float(t.to_numpy().sum()), "Chi-square": float(chi), "DF": int(dof),
            "P-value": p, "Cells expected < 5": int((exp < 5).sum()),
            "conclusion": (f"p = {p:.4f} < {alpha} → reject H0: the variables are associated." if p < alpha else
                           f"p = {p:.4f} ≥ {alpha} → fail to reject H0: no evidence of association.")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  Chi-Square Test of Association  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="Chi-Square Test of Association — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)

    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Defect type', 'Shift 1', 'Shift 2', 'Shift 3'], **{})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
