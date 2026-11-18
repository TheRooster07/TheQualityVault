"""
two_way_anova.py  —  TheQualityVault.com
=======================================
Two-Way ANOVA

Balanced two-factor ANOVA with interaction: tests factor A, factor B and A × B.
Input is a long table: one row per observation with the A level, B level and response.

The Excel workbook (Two_Way_ANOVA.xlsx) and two_way_anova.R give the same results.

Run
---
    python two_way_anova.py demo
    python two_way_anova.py --csv my_data.csv --cols Machine Shift Output

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
    d = df[cols].dropna(); d.columns = ["A", "B", "y"]; d["y"] = d["y"].astype(float)
    a, b = d["A"].nunique(), d["B"].nunique(); cnt = d.groupby(["A", "B"]).size()
    if len(cnt) != a * b or cnt.nunique() != 1:
        raise ValueError("Design must be balanced: same number of observations in every A × B cell.")
    r = int(cnt.iloc[0]); gm = d["y"].mean()
    ssa = b * r * ((d.groupby("A")["y"].mean() - gm) ** 2).sum()
    ssb = a * r * ((d.groupby("B")["y"].mean() - gm) ** 2).sum()
    sscell = r * ((d.groupby(["A", "B"])["y"].mean() - gm) ** 2).sum()
    sst = ((d["y"] - gm) ** 2).sum(); ssab = sscell - ssa - ssb; sse = sst - sscell
    dfa, dfb, dfab, dfe = a - 1, b - 1, (a - 1) * (b - 1), a * b * (r - 1)
    mse = sse / dfe
    fa, fb, fab = ssa / dfa / mse, ssb / dfb / mse, ssab / dfab / mse
    pa, pb, pab = (float(stats.f.sf(f, df1, dfe)) for f, df1 in ((fa, dfa), (fb, dfb), (fab, dfab)))
    sig = [n for n, p in (("A", pa), ("B", pb), ("A×B", pab)) if p < alpha]
    return {"Levels A": a, "Levels B": b, "Replicates": r, "SS A": ssa, "SS B": ssb, "SS AxB": ssab, "SS Error": sse,
            "F A": fa, "P A": pa, "F B": fb, "P B": pb, "F AxB": fab, "P AxB": pab, "R-sq": sscell / sst,
            "conclusion": ("Significant at " + str(alpha) + ": " + ", ".join(sig) + " → those effects matter." if sig
                           else "→ No factor or interaction is significant at " + str(alpha) + ".")}


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  Two-Way ANOVA  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="Two-Way ANOVA — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)

    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Machine', 'Shift', 'Output'], **{})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
