"""
process_capability.py  —  TheQualityVault.com
=============================================
Process Capability Calculator (normal data)

  Within (short-term) sigma
      subgroup size m = 1  :  sigma_w = MR-bar / 1.128        (moving range of 2)
      subgroup size m ≥ 2  :  sigma_w = R-bar  / d2(m)        (complete subgroups only)
  Overall (long-term) sigma  :  sample standard deviation s

  Cp  = (USL − LSL) / 6σw          Pp  = (USL − LSL) / 6s
  CPU = (USL − x̄) / 3σw            PPU = (USL − x̄) / 3s
  CPL = (x̄ − LSL) / 3σw            PPL = (x̄ − LSL) / 3s
  Cpk = min(CPU, CPL)              Ppk = min(PPU, PPL)
  Cpm = (USL − LSL) / 6·sqrt(s² + (x̄ − T)²)

  Expected PPM (within / overall), observed PPM, Z.bench,
  and an Anderson-Darling normality test.

The Excel workbook and the R version (process_capability.R) give identical numbers.

Quick start
-----------
    python process_capability.py demo
    python process_capability.py --csv example_data.csv --column diameter_mm \
        --lsl 9.95 --usl 10.05 --target 10.00 --subgroup-size 5 --save capability.png

Dependencies: numpy, pandas, scipy, matplotlib
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "figure.dpi": 120,
})

NAVY, GOLD, RED = "#1A2B5F", "#C9A84C", "#C0392B"

# d2 constants for subgroup sizes 2..10 (range method)
D2 = {2: 1.128, 3: 1.693, 4: 2.059, 5: 2.326, 6: 2.534,
      7: 2.704, 8: 2.847, 9: 2.970, 10: 3.078}


# ══════════════════════════════════════════════════════════════════════════════
# Core calculations
# ══════════════════════════════════════════════════════════════════════════════

def sigma_within(x: np.ndarray, m: int) -> float:
    """Short-term sigma from moving ranges (m = 1) or subgroup ranges (m = 2..10)."""
    if m == 1:
        mr = np.abs(np.diff(x))
        return float(mr.mean() / 1.128)
    if m not in D2:
        raise ValueError("Subgroup size must be 1 to 10.")
    k = len(x) // m                       # complete subgroups only
    if k < 1:
        raise ValueError("Not enough data for one complete subgroup.")
    groups = x[: k * m].reshape(k, m)
    rbar = float((groups.max(axis=1) - groups.min(axis=1)).mean())
    return rbar / D2[m]


def anderson_darling(x: np.ndarray) -> tuple[float, float]:
    """A² statistic (mean and s estimated) and p-value (D'Agostino & Stephens, 1986)."""
    n = len(x)
    z = (np.sort(x) - x.mean()) / x.std(ddof=1)
    F = stats.norm.cdf(z)
    i = np.arange(1, n + 1)
    a2 = -n - np.sum((2 * i - 1) * (np.log(F) + np.log(1 - F[::-1]))) / n
    a = a2 * (1 + 0.75 / n + 2.25 / n ** 2)
    if a >= 0.6:
        p = math.exp(1.2937 - 5.709 * a + 0.0186 * a ** 2)
    elif a >= 0.34:
        p = math.exp(0.9177 - 4.279 * a - 1.38 * a ** 2)
    elif a >= 0.2:
        p = 1 - math.exp(-8.318 + 42.796 * a - 59.938 * a ** 2)
    else:
        p = 1 - math.exp(-13.436 + 101.14 * a - 223.73 * a ** 2)
    return float(a2), float(min(max(p, 0.0), 1.0))


@dataclass
class CapabilityResult:
    n: int
    subgroup_size: int
    lsl: float
    usl: float
    target: float
    mean: float
    sd_overall: float
    sd_within: float
    cp: float
    cpu: float
    cpl: float
    cpk: float
    pp: float
    ppu: float
    ppl: float
    ppk: float
    cpm: float
    ppm_within_lsl: float
    ppm_within_usl: float
    ppm_overall_lsl: float
    ppm_overall_usl: float
    ppm_observed: float
    z_bench: float
    ad_stat: float
    ad_p: float

    @property
    def ppm_within(self) -> float:
        return self.ppm_within_lsl + self.ppm_within_usl

    @property
    def ppm_overall(self) -> float:
        return self.ppm_overall_lsl + self.ppm_overall_usl

    def verdict(self) -> str:
        if self.ad_p < 0.05:
            return "Data are NOT normal (AD p < 0.05) – indices may be misleading; transform or use a non-normal method."
        if self.ppk >= 1.33:
            return "CAPABLE – Ppk ≥ 1.33"
        if self.ppk >= 1.0:
            return "MARGINAL – 1.00 ≤ Ppk < 1.33; reduce variation or re-centre"
        return "NOT CAPABLE – Ppk < 1.00"

    def summary(self) -> str:
        r = self
        return "\n".join([
            "", "=" * 60, "  Process Capability Report  —  TheQualityVault.com", "=" * 60,
            f"  n = {r.n}    subgroup size = {r.subgroup_size}",
            f"  LSL = {r.lsl:g}   Target = {r.target:g}   USL = {r.usl:g}",
            f"  Mean            : {r.mean:.5f}",
            f"  StDev (overall) : {r.sd_overall:.5f}",
            f"  StDev (within)  : {r.sd_within:.5f}",
            "  ── Potential (within) ──────────────",
            f"  Cp  {r.cp:6.3f}   CPL {r.cpl:6.3f}   CPU {r.cpu:6.3f}   Cpk {r.cpk:6.3f}",
            "  ── Overall ─────────────────────────",
            f"  Pp  {r.pp:6.3f}   PPL {r.ppl:6.3f}   PPU {r.ppu:6.3f}   Ppk {r.ppk:6.3f}",
            f"  Cpm {r.cpm:6.3f}",
            "  ── PPM ─────────────────────────────",
            f"  Expected within  : {r.ppm_within:,.1f}  (<LSL {r.ppm_within_lsl:,.1f} | >USL {r.ppm_within_usl:,.1f})",
            f"  Expected overall : {r.ppm_overall:,.1f}  (<LSL {r.ppm_overall_lsl:,.1f} | >USL {r.ppm_overall_usl:,.1f})",
            f"  Observed         : {r.ppm_observed:,.1f}",
            f"  Z.bench (overall): {r.z_bench:.3f}",
            f"  Anderson-Darling : A² = {r.ad_stat:.4f}   p = {r.ad_p:.4f}",
            f"  Verdict          : {r.verdict()}",
            "=" * 60, "",
        ])


def capability(data, lsl: float, usl: float, target: Optional[float] = None,
               subgroup_size: int = 1) -> CapabilityResult:
    """Run the full capability analysis on a 1-D sequence of measurements (in time order)."""
    x = pd.to_numeric(pd.Series(data), errors="coerce").dropna().to_numpy(dtype=float)
    if len(x) < 2:
        raise ValueError("Need at least 2 measurements.")
    if usl <= lsl:
        raise ValueError("USL must be greater than LSL.")
    target = (lsl + usl) / 2 if target is None else target
    m = int(subgroup_size)
    mean, s = float(x.mean()), float(x.std(ddof=1))
    sw = sigma_within(x, m)
    tol = usl - lsl
    cpu, cpl = (usl - mean) / (3 * sw), (mean - lsl) / (3 * sw)
    ppu, ppl = (usl - mean) / (3 * s), (mean - lsl) / (3 * s)
    nd = stats.norm
    pw_l, pw_u = nd.cdf((lsl - mean) / sw) * 1e6, nd.sf((usl - mean) / sw) * 1e6
    po_l, po_u = nd.cdf((lsl - mean) / s) * 1e6, nd.sf((usl - mean) / s) * 1e6
    obs = ((x < lsl) | (x > usl)).sum() / len(x) * 1e6
    zb = float(nd.isf((po_l + po_u) / 1e6))
    a2, p = anderson_darling(x)
    return CapabilityResult(
        n=len(x), subgroup_size=m, lsl=lsl, usl=usl, target=target,
        mean=mean, sd_overall=s, sd_within=sw,
        cp=tol / (6 * sw), cpu=cpu, cpl=cpl, cpk=min(cpu, cpl),
        pp=tol / (6 * s), ppu=ppu, ppl=ppl, ppk=min(ppu, ppl),
        cpm=tol / (6 * math.sqrt(s ** 2 + (mean - target) ** 2)),
        ppm_within_lsl=pw_l, ppm_within_usl=pw_u,
        ppm_overall_lsl=po_l, ppm_overall_usl=po_u,
        ppm_observed=obs, z_bench=zb, ad_stat=a2, ad_p=p,
    ), x


# ══════════════════════════════════════════════════════════════════════════════
# Plot
# ══════════════════════════════════════════════════════════════════════════════

def plot_capability(r: CapabilityResult, x: np.ndarray, show: bool = True) -> plt.Figure:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"width_ratios": [1.6, 1]})
    lo, hi = min(r.lsl, x.min()), max(r.usl, x.max())
    pad = 0.08 * (hi - lo)
    ax1.hist(x, bins=20, range=(lo, hi), color=NAVY, alpha=0.75, edgecolor="white",
             density=True, label="Data")
    g = np.linspace(lo - pad, hi + pad, 400)
    ax1.plot(g, stats.norm.pdf(g, r.mean, r.sd_overall), color=GOLD, lw=2.2, label="Overall fit")
    ax1.plot(g, stats.norm.pdf(g, r.mean, r.sd_within), color=NAVY, lw=1.6, ls="--", label="Within fit")
    for v, lab in ((r.lsl, "LSL"), (r.usl, "USL")):
        ax1.axvline(v, color=RED, lw=2)
        ax1.text(v, ax1.get_ylim()[1] * 0.97, f" {lab}", color=RED, va="top", fontweight="bold")
    ax1.axvline(r.target, color="#888", lw=1.2, ls=":", label="Target")
    ax1.set_title("Capability Histogram", fontweight="bold")
    ax1.set_xlabel("Measurement")
    ax1.legend(fontsize=9, loc="center left")

    ax2.axis("off")
    txt = (f"n = {r.n}   (subgroup {r.subgroup_size})\n"
           f"Mean = {r.mean:.4f}\n"
           f"StDev overall = {r.sd_overall:.4f}\nStDev within  = {r.sd_within:.4f}\n\n"
           f"Cp  = {r.cp:.2f}    Cpk = {r.cpk:.2f}\n"
           f"Pp  = {r.pp:.2f}    Ppk = {r.ppk:.2f}\n"
           f"Cpm = {r.cpm:.2f}\n\n"
           f"PPM within  = {r.ppm_within:,.0f}\n"
           f"PPM overall = {r.ppm_overall:,.0f}\n"
           f"PPM observed = {r.ppm_observed:,.0f}\n"
           f"Z.bench = {r.z_bench:.2f}\n\n"
           f"AD normality p = {r.ad_p:.3f}\n\n{r.verdict()}")
    ax2.text(0.02, 0.98, txt, va="top", family="DejaVu Sans Mono", fontsize=10, wrap=True)
    fig.suptitle("Process Capability — TheQualityVault.com", fontsize=13, fontweight="bold", color=NAVY)
    fig.tight_layout()
    if show:
        plt.show()
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def _build_cli() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Process Capability Calculator — TheQualityVault.com")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", type=Path, help="CSV file (first row = header)")
    src.add_argument("--excel", type=Path, help="Excel file (.xlsx)")
    p.add_argument("--column", default=0, help="Column name or 0-based index of the measurements")
    p.add_argument("--sheet", default=0, help="Sheet name or index (Excel)")
    p.add_argument("--lsl", type=float, required=True)
    p.add_argument("--usl", type=float, required=True)
    p.add_argument("--target", type=float, default=None, help="Default: midpoint of specs")
    p.add_argument("--subgroup-size", type=int, default=1, help="1 (individuals) to 10")
    p.add_argument("--plot", action="store_true", help="Show the plot")
    p.add_argument("--save", type=Path, help="Save the plot to an image file")
    return p


def _col(df: pd.DataFrame, c):
    try:
        return df.iloc[:, int(c)]
    except (ValueError, TypeError):
        return df[c]


def main(argv=None) -> None:
    a = _build_cli().parse_args(argv)
    if a.csv:
        df = pd.read_csv(a.csv)
    else:
        sheet = int(a.sheet) if str(a.sheet).isdigit() else a.sheet
        df = pd.read_excel(a.excel, sheet_name=sheet)
    r, x = capability(_col(df, a.column), a.lsl, a.usl, a.target, a.subgroup_size)
    print(r.summary())
    if a.plot or a.save:
        fig = plot_capability(r, x, show=False)
        if a.save:
            fig.savefig(a.save, dpi=150, bbox_inches="tight")
            print(f"  → Plot saved to {a.save}")
        if a.plot:
            plt.show()


def run_demo(show: bool = True) -> CapabilityResult:
    """Worked example: shaft diameter, 25 subgroups of 5, specs 10.00 ± 0.05 mm."""
    df = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    r, x = capability(df["diameter_mm"], lsl=9.95, usl=10.05, target=10.00, subgroup_size=5)
    print(r.summary())
    fig = plot_capability(r, x, show=False)
    fig.savefig("capability_example_python.png", dpi=130, bbox_inches="tight")
    print("  → Plot saved to capability_example_python.png")
    if show:
        plt.show()
    return r


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo(show="--no-show" not in sys.argv)
    else:
        main()
