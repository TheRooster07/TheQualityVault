"""
doe_factorial.py  —  TheQualityVault.com
========================================
2-level Full Factorial DOE: design generator + analysis

  • Builds a 2^k design (k = 2–5 factors) with replicates and a randomised run order
  • Analyses the response: effects, coefficients and ANOVA for all main effects and
    two-factor interactions (three-factor and higher interactions are pooled into error)
  • Plots: Pareto of |effects|, main-effects plots, interaction plot of the largest 2FI

Effect = mean(Y at +1) − mean(Y at −1);  coefficient = effect / 2;  SS = N·effect² / 4.
The Excel workbook and doe_factorial.R give identical numbers.

Quick start
-----------
    python doe_factorial.py demo
    python doe_factorial.py design --factors Temp:150:180 Pressure:2:4 Time:10:20 --reps 2 --seed 7 --out plan.csv
    python doe_factorial.py analyze --csv plan_with_results.csv --response Y --save doe.png

Dependencies: numpy, pandas, scipy, matplotlib
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False,
                            "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3})
NAVY, GOLD, RED = "#1A2B5F", "#C9A84C", "#C0392B"
LETTERS = "ABCDE"


def design(factors: dict[str, tuple[float, float]], reps: int = 1, seed: int | None = None) -> pd.DataFrame:
    """factors = {'Temp': (150, 180), ...} in order A, B, C …  Returns std order + run order + coded + actual."""
    k = len(factors)
    if not 2 <= k <= 5:
        raise ValueError("Use 2 to 5 factors.")
    n = 2 ** k
    rows = []
    for rep in range(1, reps + 1):
        for i in range(n):
            coded = [(-1 if (i >> j) % 2 == 0 else 1) for j in range(k)]   # Yates standard order
            rows.append([len(rows) + 1, rep] + coded)
    cols = ["StdOrder", "Rep"] + [LETTERS[j] for j in range(k)]
    d = pd.DataFrame(rows, columns=cols)
    rng = np.random.default_rng(seed)
    d.insert(1, "RunOrder", rng.permutation(len(d)) + 1)
    for j, (name, (lo, hi)) in enumerate(factors.items()):
        d[name] = np.where(d[LETTERS[j]] == -1, lo, hi)
    return d


def terms(k: int) -> list[str]:
    return list(LETTERS[:k]) + ["".join(p) for p in itertools.combinations(LETTERS[:k], 2)]


def analyze(d: pd.DataFrame, response: str = "Y", k: int | None = None) -> dict:
    k = k or sum(c in d.columns for c in LETTERS)
    y = d[response].astype(float).to_numpy()
    N = len(y)
    rows = []
    for t in terms(k):
        x = np.prod([d[c].to_numpy() for c in t], axis=0)
        eff = y[x == 1].mean() - y[x == -1].mean()
        rows.append((t, eff, eff / 2, N * eff ** 2 / 4))
    eff = pd.DataFrame(rows, columns=["Term", "Effect", "Coef", "SS"]).set_index("Term")
    ss_tot = ((y - y.mean()) ** 2).sum()
    df_res = N - 1 - len(eff)
    ss_res = ss_tot - eff["SS"].sum()
    ms_res = ss_res / df_res if df_res > 0 else np.nan
    eff["DF"] = 1
    eff["F"] = eff["SS"] / ms_res if df_res > 0 else np.nan
    eff["P"] = stats.f.sf(eff["F"], 1, df_res) if df_res > 0 else np.nan
    return {"effects": eff, "mean": y.mean(), "ss_total": ss_tot, "ss_res": ss_res, "df_res": df_res,
            "ms_res": ms_res, "r2": 1 - ss_res / ss_tot, "N": N, "k": k, "data": d, "response": response}


def summary(res: dict, names: dict | None = None) -> str:
    names = names or {}
    e = res["effects"].copy()
    e.index = [t + (f" ({names[t]})" if t in names else "") for t in e.index]
    pd.set_option("display.float_format", lambda v: f"{v:,.4f}")
    lines = ["", "=" * 70, "  2-Level Full Factorial Analysis  —  TheQualityVault.com", "=" * 70,
             f"  Runs N = {res['N']}   Factors k = {res['k']}   Grand mean = {res['mean']:.4f}",
             "  Model: main effects + two-factor interactions (higher-order pooled into error)", "",
             e.to_string(), "",
             f"  Residual: SS = {res['ss_res']:.4f}   DF = {res['df_res']}   MS = {res['ms_res']:.4f}",
             f"  Total SS = {res['ss_total']:.4f}    R² = {res['r2'] * 100:.2f}%"]
    if res["df_res"] > 0:
        sig = [t for t, p in res["effects"]["P"].items() if p < 0.05]
        lines.append(f"  Significant at 0.05: {', '.join(sig) if sig else 'none'}")
    else:
        lines.append("  No residual degrees of freedom – add replicates to get p-values.")
    lines += ["=" * 70, ""]
    return "\n".join(lines)


def plot(res: dict, names: dict | None = None, show: bool = True) -> plt.Figure:
    names = names or {}
    d, y, k = res["data"], res["response"], res["k"]
    e = res["effects"]["Effect"].abs().sort_values(ascending=True)
    fig = plt.figure(figsize=(14, 8.5))
    ax = fig.add_subplot(2, 2, 1)
    cols = [RED if res["df_res"] > 0 and res["effects"].loc[t, "P"] < 0.05 else NAVY for t in e.index]
    ax.barh([f"{t} {names.get(t, '')}" for t in e.index], e.values, color=cols)
    ax.set_title("Pareto of |Effects| (red = p < 0.05)", fontweight="bold")
    ax = fig.add_subplot(2, 2, 2)
    for j in range(k):
        f = LETTERS[j]; m = d.groupby(f)[y].mean()
        ax.plot([f"{f} −", f"{f} +"], m.loc[[-1, 1]].values, marker="o", lw=2, label=names.get(f, f))
    ax.axhline(res["mean"], color="grey", ls=":", lw=1)
    ax.set_title("Main Effects (mean response)", fontweight="bold"); ax.legend(fontsize=8)
    two = [t for t in res["effects"].index if len(t) == 2]
    top = max(two, key=lambda t: abs(res["effects"].loc[t, "Effect"]))
    ax = fig.add_subplot(2, 2, 3)
    for lvl, colr in ((-1, NAVY), (1, GOLD)):
        m = d[d[top[1]] == lvl].groupby(top[0])[y].mean()
        ax.plot(["−1", "+1"], m.loc[[-1, 1]].values, marker="o", lw=2, color=colr,
                label=f"{names.get(top[1], top[1])} = {lvl:+d}")
    ax.set_xlabel(names.get(top[0], top[0])); ax.legend(fontsize=8)
    ax.set_title(f"Largest interaction: {top}", fontweight="bold")
    ax = fig.add_subplot(2, 2, 4)
    fitted = res["mean"] + sum(res["effects"].loc[t, "Coef"] * np.prod([d[c] for c in t], axis=0)
                               for t in res["effects"].index)
    ax.scatter(fitted, d[y] - fitted, color=NAVY); ax.axhline(0, color=RED, lw=1)
    ax.set_xlabel("Fitted"); ax.set_ylabel("Residual"); ax.set_title("Residuals vs Fitted", fontweight="bold")
    fig.suptitle("2-Level Full Factorial — TheQualityVault.com", fontsize=13, fontweight="bold", color=NAVY)
    fig.tight_layout()
    if show:
        plt.show()
    return fig


EXAMPLE = {"Temperature": (150, 180), "Pressure": (2, 4), "Time": (10, 20)}


def run_demo(show=True):
    """Chemical yield: 3 factors × 2 replicates (16 runs). Data in example_data.csv."""
    d = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    names = dict(zip(LETTERS, EXAMPLE))
    res = analyze(d, "Yield", k=3)
    print(summary(res, names))
    plot(res, names, show=False).savefig("doe_example_python.png", dpi=130, bbox_inches="tight")
    print("  → Plot saved to doe_example_python.png")
    if show:
        plt.show()
    return res


def _cli():
    p = argparse.ArgumentParser(description="2-level full factorial DOE — TheQualityVault.com")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("design"); g.add_argument("--factors", nargs="+", required=True, help="Name:low:high …")
    g.add_argument("--reps", type=int, default=1); g.add_argument("--seed", type=int); g.add_argument("--out", type=Path, required=True)
    a = sub.add_parser("analyze"); a.add_argument("--csv", type=Path, required=True)
    a.add_argument("--response", default="Y"); a.add_argument("--save", type=Path)
    args = p.parse_args()
    if args.cmd == "design":
        f = {s.split(":")[0]: (float(s.split(":")[1]), float(s.split(":")[2])) for s in args.factors}
        d = design(f, args.reps, args.seed); d[" Y"] = ""
        d.sort_values("RunOrder").to_csv(args.out, index=False)
        print(f"  → {len(d)} runs written to {args.out} (sorted by run order). Fill in the response column.")
    else:
        d = pd.read_csv(args.csv); res = analyze(d, args.response)
        print(summary(res))
        if args.save:
            plot(res, show=False).savefig(args.save, dpi=150, bbox_inches="tight")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo(show="--no-show" not in sys.argv)
    else:
        _cli()
