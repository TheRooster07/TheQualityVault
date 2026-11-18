"""
regression.py  —  TheQualityVault.com
====================================
Linear Regression (simple and multiple)

Ordinary least-squares regression of one response on 1–5 predictors: coefficients, standard
errors, t and p-values, R², adjusted R², standard error of the regression and the model F-test.

The Excel workbook (Regression.xlsx) and regression.R give the same results.

Run
---
    python regression.py demo
    python regression.py --csv my_data.csv --cols Y X1 X2 X3

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
    d = df[cols].apply(pd.to_numeric, errors="coerce").dropna()
    y = d[cols[0]].to_numpy(float); X = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(float) for c in cols[1:]])
    n, p1 = X.shape; k = p1 - 1
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta; sse = resid @ resid; sst = ((y - y.mean()) ** 2).sum(); dfe = n - p1
    mse = sse / dfe; se = np.sqrt(np.diag(mse * np.linalg.inv(X.T @ X))); t = beta / se
    pv = 2 * stats.t.sf(np.abs(t), dfe)
    for name, b, s, tt, pp in zip(["Intercept"] + cols[1:], beta, se, t, pv):
        print(f"  {name:<14} coef {b:>12.6f}  SE {s:>10.6f}  t {tt:>8.3f}  p {pp:.4f}")
    F = ((sst - sse) / k) / mse; pF = float(stats.f.sf(F, k, dfe)); r2 = 1 - sse / sst
    out = {"n": n, "Predictors k": k, "R-sq": r2, "R-sq (adj)": 1 - (1 - r2) * (n - 1) / dfe, "S": math.sqrt(mse),
           "F": F, "P-value (model)": pF, "Coef X1": beta[1], "P X1": float(pv[1]),
           "conclusion": (f"Model p = {pF:.4f} < {alpha} → the model explains a significant part of the variation (R² = {r2:.1%})."
                          if pF < alpha else f"Model p = {pF:.4f} ≥ {alpha} → no evidence the X variables predict Y.")}
    return out


def report(res, alpha=0.05):
    print("\n" + "=" * 62)
    print("  Linear Regression (simple and multiple)  —  TheQualityVault.com")
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
    p = argparse.ArgumentParser(description="Linear Regression (simple and multiple) — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--cols", nargs="+", required=True, help="column names to use")
    p.add_argument("--alpha", type=float, default=0.05)

    a = p.parse_args(argv)
    df = pd.read_csv(a.csv)
    report(analyze(df, a.cols, **{k: v for k, v in vars(a).items() if k not in ("csv", "cols")}), a.alpha)


def demo():
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = analyze(df, ['Strength', 'Temp', 'Pressure', 'Humidity'], **{})
    report(res, 0.05)
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()
