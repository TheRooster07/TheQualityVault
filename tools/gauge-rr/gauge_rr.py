"""
gauge_rr.py  —  TheQualityVault.com
===================================
Gauge R&R — crossed study, ANOVA method (AIAG MSA)

  Two-way ANOVA:  Part, Operator, Part × Operator, Repeatability
  If the Part × Operator p-value ≥ alpha (default 0.05) the interaction is pooled
  into repeatability and the reduced model is used.

  Variance components (with interaction)
      Repeatability   = MS_repeat
      Part × Operator = (MS_int − MS_repeat) / r
      Operator        = (MS_op  − MS_int) / (p·r)
      Part-to-part    = (MS_part − MS_int) / (o·r)        (negative estimates → 0)
  Reproducibility = Operator + Part × Operator;  Total GR&R = Repeatability + Reproducibility

  Reports %Contribution, %Study Variation (6·SD), %Tolerance and the number of
  distinct categories ndc = floor(1.41 · SD_part / SD_GRR).
  AIAG guidance: %Study Var or %Tol < 10 % acceptable · 10–30 % marginal · > 30 % unacceptable; ndc ≥ 5.

Input: a long table with one row per measurement — columns for part, operator and value.
The Excel workbook and gauge_rr.R give identical numbers.

Quick start
-----------
    python gauge_rr.py demo
    python gauge_rr.py --csv example_data.csv --part part --operator operator \
        --value measurement --tolerance 3.0 --save grr.png

Dependencies: numpy, pandas, scipy, matplotlib
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False,
                            "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3})
NAVY, GOLD, RED, BLUE = "#1A2B5F", "#C9A84C", "#C0392B", "#4472C4"


@dataclass
class GRRResult:
    anova_full: pd.DataFrame
    anova_reduced: pd.DataFrame | None
    interaction_used: bool
    components: pd.DataFrame
    ndc: int
    p: int
    o: int
    r: int
    tolerance: float | None
    data: pd.DataFrame

    def verdict(self) -> str:
        pct = self.components.loc["Total Gage R&R", "%Study Var"]
        if pct < 10:
            v = "ACCEPTABLE – %Study Var < 10%"
        elif pct <= 30:
            v = "MARGINAL – 10–30% %Study Var; may be acceptable depending on use and cost"
        else:
            v = "UNACCEPTABLE – %Study Var > 30%; improve the measurement system"
        if self.ndc < 5:
            v += f"  ·  ndc = {self.ndc} (< 5: gauge cannot separate parts well)"
        return v

    def summary(self) -> str:
        pd.set_option("display.float_format", lambda v: f"{v:,.5f}")
        out = ["", "=" * 72, "  Gauge R&R (ANOVA method)  —  TheQualityVault.com", "=" * 72,
               f"  Parts = {self.p}   Operators = {self.o}   Trials = {self.r}   "
               f"Tolerance = {self.tolerance if self.tolerance else 'not given'}",
               "", "  Two-way ANOVA with interaction", self.anova_full.to_string()]
        if self.anova_reduced is not None:
            out += ["", "  Interaction not significant – pooled into repeatability (reduced model)",
                    self.anova_reduced.to_string()]
        pd.set_option("display.float_format", lambda v: f"{v:,.4f}")
        out += ["", "  Variance components", self.components.to_string(),
                "", f"  Number of distinct categories (ndc) = {self.ndc}",
                f"  Verdict: {self.verdict()}", "=" * 72, ""]
        return "\n".join(out)


def _p(fval, d1, d2):
    return float(stats.f.sf(fval, d1, d2)) if np.isfinite(fval) else float("nan")


def gauge_rr(df: pd.DataFrame, part: str, operator: str, value: str,
             tolerance: float | None = None, alpha: float = 0.05) -> GRRResult:
    d = df[[part, operator, value]].dropna().copy()
    d.columns = ["part", "operator", "y"]
    d["y"] = d["y"].astype(float)
    cells = d.groupby(["part", "operator"])["y"]
    counts = cells.size()
    p, o = d["part"].nunique(), d["operator"].nunique()
    if counts.nunique() != 1 or len(counts) != p * o:
        raise ValueError("Study must be balanced: every operator measures every part the same number of times.")
    r = int(counts.iloc[0])
    if r < 2:
        raise ValueError("Need at least 2 trials per operator per part.")

    gm = d["y"].mean()
    ss_total = ((d["y"] - gm) ** 2).sum()
    ss_part = o * r * ((d.groupby("part")["y"].mean() - gm) ** 2).sum()
    ss_op = p * r * ((d.groupby("operator")["y"].mean() - gm) ** 2).sum()
    ss_rep = ((d["y"] - cells.transform("mean")) ** 2).sum()
    ss_int = ss_total - ss_part - ss_op - ss_rep

    df_p, df_o = p - 1, o - 1
    df_i, df_r = df_p * df_o, p * o * (r - 1)
    ms_p, ms_o, ms_i, ms_r = ss_part / df_p, ss_op / df_o, ss_int / df_i, ss_rep / df_r
    f_p, f_o, f_i = ms_p / ms_i, ms_o / ms_i, ms_i / ms_r
    full = pd.DataFrame({
        "DF": [df_p, df_o, df_i, df_r, p * o * r - 1],
        "SS": [ss_part, ss_op, ss_int, ss_rep, ss_total],
        "MS": [ms_p, ms_o, ms_i, ms_r, np.nan],
        "F": [f_p, f_o, f_i, np.nan, np.nan],
        "P": [_p(f_p, df_p, df_i), _p(f_o, df_o, df_i), _p(f_i, df_i, df_r), np.nan, np.nan],
    }, index=["Part", "Operator", "Part × Operator", "Repeatability", "Total"])

    use_int = full.loc["Part × Operator", "P"] < alpha
    reduced = None
    if use_int:
        v_rep = ms_r
        v_int = max((ms_i - ms_r) / r, 0.0)
        v_op = max((ms_o - ms_i) / (p * r), 0.0)
        v_part = max((ms_p - ms_i) / (o * r), 0.0)
    else:
        df_pool = df_i + df_r
        ms_pool = (ss_int + ss_rep) / df_pool
        fp2, fo2 = ms_p / ms_pool, ms_o / ms_pool
        reduced = pd.DataFrame({
            "DF": [df_p, df_o, df_pool, p * o * r - 1],
            "SS": [ss_part, ss_op, ss_int + ss_rep, ss_total],
            "MS": [ms_p, ms_o, ms_pool, np.nan],
            "F": [fp2, fo2, np.nan, np.nan],
            "P": [_p(fp2, df_p, df_pool), _p(fo2, df_o, df_pool), np.nan, np.nan],
        }, index=["Part", "Operator", "Repeatability", "Total"])
        v_rep, v_int = ms_pool, 0.0
        v_op = max((ms_o - ms_pool) / (p * r), 0.0)
        v_part = max((ms_p - ms_pool) / (o * r), 0.0)

    v_repro = v_op + v_int
    v_grr = v_rep + v_repro
    v_tot = v_grr + v_part
    names = ["Total Gage R&R", "  Repeatability", "  Reproducibility", "    Operator",
             "    Part × Operator", "Part-to-Part", "Total Variation"]
    var = np.array([v_grr, v_rep, v_repro, v_op, v_int, v_part, v_tot])
    sd = np.sqrt(var)
    comp = pd.DataFrame({"VarComp": var, "%Contribution": var / v_tot * 100, "StdDev": sd,
                         "StudyVar (6·SD)": 6 * sd, "%Study Var": sd / sd[-1] * 100}, index=names)
    if tolerance:
        comp["%Tolerance"] = 6 * sd / tolerance * 100
    comp.index = [n.strip() for n in names]
    ndc = int(math.floor(1.41 * sd[5] / sd[0])) if sd[0] > 0 else 0
    return GRRResult(full, reduced, bool(use_int), comp, ndc, p, o, r, tolerance, d)


def plot_grr(res: GRRResult, show: bool = True) -> plt.Figure:
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))
    c = res.components
    keys = ["Total Gage R&R", "Repeatability", "Reproducibility", "Part-to-Part"]
    cols = ["%Contribution", "%Study Var"] + (["%Tolerance"] if "%Tolerance" in c else [])
    x = np.arange(len(keys)); w = 0.8 / len(cols)
    ax = axes[0, 0]
    for i, (col, colr) in enumerate(zip(cols, [NAVY, GOLD, BLUE])):
        ax.bar(x + i * w - 0.4 + w / 2, c.loc[keys, col], w, label=col, color=colr)
    ax.axhline(10, color="green", ls=":", lw=1); ax.axhline(30, color=RED, ls=":", lw=1)
    ax.set_xticks(x, ["Gage R&R", "Repeat", "Reprod", "Part-to-Part"])
    ax.set_ylabel("Percent"); ax.set_title("Components of Variation", fontweight="bold"); ax.legend(fontsize=8)

    d = res.data
    ax = axes[0, 1]
    parts = sorted(d["part"].unique(), key=lambda v: (str(type(v)), v))
    ax.boxplot([d.loc[d["part"] == pt, "y"] for pt in parts],
               patch_artist=True, boxprops=dict(facecolor="#DCE3F2"))
    ax.set_xticks(range(1, len(parts) + 1), [str(pt) for pt in parts])
    ax.set_title("Measurement by Part", fontweight="bold"); ax.set_xlabel("Part")

    ax = axes[1, 0]
    ops = sorted(d["operator"].unique(), key=str)
    ax.boxplot([d.loc[d["operator"] == op, "y"] for op in ops],
               patch_artist=True, boxprops=dict(facecolor="#F3E9CC"))
    ax.set_xticks(range(1, len(ops) + 1), [str(op) for op in ops])
    ax.set_title("Measurement by Operator", fontweight="bold"); ax.set_xlabel("Operator")

    ax = axes[1, 1]
    m = d.groupby(["part", "operator"])["y"].mean().unstack()
    m = m.loc[parts]
    for op, colr in zip(m.columns, [NAVY, GOLD, BLUE, RED, "green"]):
        ax.plot([str(pt) for pt in m.index], m[op], marker="o", label=str(op), color=colr)
    ax.set_title("Part × Operator Interaction", fontweight="bold"); ax.set_xlabel("Part")
    ax.legend(title="Operator", fontsize=8)
    fig.suptitle(f"Gauge R&R (ANOVA) — TheQualityVault.com      {res.verdict()}",
                 fontsize=11, fontweight="bold", color=NAVY)
    fig.tight_layout()
    if show:
        plt.show()
    return fig


def _cli(argv=None):
    a = argparse.ArgumentParser(description="Gauge R&R (ANOVA) — TheQualityVault.com")
    a.add_argument("--csv", type=Path, required=True)
    a.add_argument("--part", default="part"); a.add_argument("--operator", default="operator")
    a.add_argument("--value", default="measurement")
    a.add_argument("--tolerance", type=float, default=None, help="USL − LSL (optional)")
    a.add_argument("--alpha", type=float, default=0.05, help="Alpha to remove interaction (default 0.05)")
    a.add_argument("--save", type=Path); a.add_argument("--plot", action="store_true")
    args = a.parse_args(argv)
    res = gauge_rr(pd.read_csv(args.csv), args.part, args.operator, args.value, args.tolerance, args.alpha)
    print(res.summary())
    if args.save or args.plot:
        fig = plot_grr(res, show=False)
        if args.save:
            fig.savefig(args.save, dpi=150, bbox_inches="tight"); print(f"  → Plot saved to {args.save}")
        if args.plot:
            plt.show()


def run_demo(show=True):
    """10 parts × 3 operators × 3 trials, tolerance 3.0."""
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    res = gauge_rr(df, "part", "operator", "measurement", tolerance=3.0)
    print(res.summary())
    plot_grr(res, show=False).savefig("gauge_rr_example_python.png", dpi=130, bbox_inches="tight")
    print("  → Plot saved to gauge_rr_example_python.png")
    if show:
        plt.show()
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo(show="--no-show" not in sys.argv)
    else:
        _cli()
