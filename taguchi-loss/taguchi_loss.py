"""
taguchi_loss.py  —  TheQualityVault.com
=======================================
Taguchi Quality Loss Function — all three characteristics
  • Nominal-Is-Best  (NIB): L(y) = k(y - m)²   k = A₀ / Δ²
  • Larger-Is-Better (LIB): L(y) = k / y²      k = A₀ · m²
  • Smaller-Is-Better(SIB): L(y) = k · y²      k = A₀ / m²

For a batch, the average loss for NIB splits into two parts:
    E[L] = k·σ² + k·(ȳ - m)²     (variance loss + bias loss)
which tells you whether to reduce spread or re-centre the process.

Supports single values, lists/arrays, CSV and Excel files, plots, and CSV export.
A companion R version (taguchi_loss.R) gives identical numbers.

Quick start
-----------
    python taguchi_loss.py demo                       # runs the worked example
    python taguchi_loss.py nib --target 500 --delta 10 --A0 2.50 --y 506
    python taguchi_loss.py nib --target 500 --delta 10 --A0 2.50 \
        --csv example_data.csv --column fill_weight_g --save nib.png

Dependencies: numpy, pandas, matplotlib   (pip install numpy pandas matplotlib)
Excel import also needs: openpyxl          (pip install openpyxl)
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional, Sequence

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "figure.dpi": 120,
})

Method = Literal["nib", "lib", "sib"]

_COLOURS = {
    "nib": {"primary": "#1F4E79", "accent": "#C0392B", "el": "#E67E22"},
    "lib": {"primary": "#2E7D32", "accent": "#C0392B", "el": "#E67E22"},
    "sib": {"primary": "#BF360C", "accent": "#1F4E79", "el": "#E67E22"},
}
_LABELS = {
    "nib": "Nominal-Is-Best",
    "lib": "Larger-Is-Better",
    "sib": "Smaller-Is-Better",
}


# ══════════════════════════════════════════════════════════════════════════════
# Core loss functions
# ══════════════════════════════════════════════════════════════════════════════

def loss_constant(method: Method, A0: float, ref: float) -> float:
    """
    Loss constant k.

    A0  : monetary loss at the reference / tolerance boundary
    ref : NIB → tolerance Δ;  LIB/SIB → reference/boundary value m
    """
    if A0 <= 0:
        raise ValueError("A0 must be positive")
    if ref <= 0:
        raise ValueError("Reference / tolerance value must be positive")
    if method == "nib":
        return A0 / ref ** 2          # k = A₀ / Δ²
    if method == "lib":
        return A0 * ref ** 2          # k = A₀ · m²
    if method == "sib":
        return A0 / ref ** 2          # k = A₀ / m²
    raise ValueError(f"Unknown method '{method}'. Use 'nib', 'lib', or 'sib'.")


def loss(method: Method, k: float,
         y: float | np.ndarray,
         target: float = 0.0) -> float | np.ndarray:
    """Individual quality loss L(y). `target` is only used for NIB."""
    y = np.asarray(y, dtype=float)
    if method == "nib":
        return k * (y - target) ** 2
    if method == "lib":
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(y > 0, k / y ** 2, np.inf)
    if method == "sib":
        return k * y ** 2
    raise ValueError(f"Unknown method '{method}'")


# ══════════════════════════════════════════════════════════════════════════════
# Result dataclasses
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SingleResult:
    method: Method
    A0: float
    k: float
    y: float
    target: float
    ref: float
    loss_value: float
    loss_pct_A0: float
    status: str

    def summary(self) -> str:
        lines = [
            f"\n{'='*55}",
            f"  Taguchi Loss — {_LABELS[self.method]}",
            f"{'='*55}",
            f"  A₀              : ${self.A0:,.4f}",
            f"  k               : {self.k:,.6f}",
            f"  y (measured)    : {self.y:,.4f}",
        ]
        if self.method == "nib":
            lines.append(f"  Target m        : {self.target:,.4f}")
            lines.append(f"  Tolerance Δ     : {self.ref:,.4f}")
            lines.append(f"  Deviation (y-m) : {self.y - self.target:+,.4f}")
        else:
            lines.append(f"  Reference m     : {self.ref:,.4f}")
        lines += [
            f"  L(y)            : ${self.loss_value:,.4f}",
            f"  L(y) / A₀       : {self.loss_pct_A0:.2f}%",
            f"  Status          : {self.status}",
            f"{'='*55}\n",
        ]
        return "\n".join(lines)


@dataclass
class BatchResult:
    method: Method
    A0: float
    k: float
    ref: float
    target: float
    n: int
    mean: float
    std: float
    min_val: float
    max_val: float
    expected_loss: float
    total_loss: float
    individual_losses: np.ndarray = field(repr=False)
    data: np.ndarray = field(repr=False)
    status: str = ""
    variance_loss: Optional[float] = None   # NIB only: k·σ²  (population σ)
    bias_loss: Optional[float] = None       # NIB only: k·(ȳ − m)²

    def summary(self) -> str:
        lines = [
            f"\n{'='*55}",
            f"  Taguchi Batch Loss — {_LABELS[self.method]}",
            f"{'='*55}",
            f"  n               : {self.n}",
            f"  Mean  ȳ         : {self.mean:,.4f}",
            f"  Std dev s       : {self.std:,.4f}",
            f"  Min / Max       : {self.min_val:,.4f} / {self.max_val:,.4f}",
            f"  A₀              : ${self.A0:,.4f}",
            f"  k               : {self.k:,.6f}",
            f"  E[L]  (avg loss): ${self.expected_loss:,.4f}",
        ]
        if self.variance_loss is not None:
            pv = self.variance_loss / self.expected_loss * 100 if self.expected_loss else 0
            lines += [
                f"    from spread    : ${self.variance_loss:,.4f}  ({pv:.0f}%)",
                f"    from off-target: ${self.bias_loss:,.4f}  ({100 - pv:.0f}%)",
            ]
        lines += [
            f"  Total batch loss: ${self.total_loss:,.4f}",
            f"  E[L] / A₀       : {self.expected_loss/self.A0*100:.2f}%",
            f"  Status          : {self.status}",
            f"{'='*55}\n",
        ]
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# Calculator classes
# ══════════════════════════════════════════════════════════════════════════════

class TaguchiBase:
    """Base calculator — subclassed by NIB, LIB, SIB."""

    method: Method = "nib"

    def __init__(self, A0: float, ref: float, target: float = 0.0):
        self.A0 = float(A0)
        self.ref = float(ref)
        self.target = float(target)
        self.k = loss_constant(self.method, self.A0, self.ref)

    # ── single point ────────────────────────────────────────────────────────

    def evaluate(self, y: float) -> SingleResult:
        lv = float(loss(self.method, self.k, y, self.target))
        return SingleResult(
            method=self.method, A0=self.A0, k=self.k,
            y=float(y), target=self.target, ref=self.ref,
            loss_value=lv, loss_pct_A0=lv / self.A0 * 100,
            status=self._status_single(y, lv),
        )

    def _status_single(self, y: float, lv: float) -> str:
        if lv > self.A0:
            return "⚠  CRITICAL — loss exceeds A₀"
        if lv > 0.5 * self.A0:
            return "⚡  CAUTION — loss >50% of A₀"
        return "✅  GOOD"

    # ── batch ────────────────────────────────────────────────────────────────

    def evaluate_batch(self, data: Sequence[float] | np.ndarray) -> BatchResult:
        arr = np.asarray(data, dtype=float)
        arr = arr[~np.isnan(arr)]
        if len(arr) == 0:
            raise ValueError("Batch data is empty after removing NaN values.")
        losses = loss(self.method, self.k, arr, self.target)
        el = float(np.mean(losses))
        mean = float(np.mean(arr))
        std = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
        var_l = bias_l = None
        if self.method == "nib":
            var_l = float(self.k * np.var(arr))            # population variance
            bias_l = float(self.k * (mean - self.target) ** 2)
        return BatchResult(
            method=self.method, A0=self.A0, k=self.k,
            ref=self.ref, target=self.target,
            n=len(arr), mean=mean, std=std,
            min_val=float(np.min(arr)), max_val=float(np.max(arr)),
            expected_loss=el, total_loss=float(np.sum(losses)),
            individual_losses=losses, data=arr,
            status=self._status_batch(arr, el),
            variance_loss=var_l, bias_loss=bias_l,
        )

    def _status_batch(self, arr: np.ndarray, el: float) -> str:
        if el > self.A0:
            return "⚠  CRITICAL — E[L] exceeds A₀"
        if el > 0.5 * self.A0:
            return "⚡  CAUTION — E[L] >50% of A₀"
        return "✅  ACCEPTABLE"

    # ── import helpers ───────────────────────────────────────────────────────

    def from_csv(self, filepath: str | Path, column: str | int = 0) -> BatchResult:
        """Load one column of measurements from a CSV file (first row = header)."""
        fp = Path(filepath)
        if not fp.exists():
            raise FileNotFoundError(f"CSV not found: {fp}")
        return self.from_dataframe(pd.read_csv(fp), column)

    def from_excel(self, filepath: str | Path, column: str | int = 0,
                   sheet: str | int = 0) -> BatchResult:
        """Load one column from an Excel sheet (.xlsx needs openpyxl)."""
        fp = Path(filepath)
        if not fp.exists():
            raise FileNotFoundError(f"Excel file not found: {fp}")
        return self.from_dataframe(pd.read_excel(fp, sheet_name=sheet), column)

    def from_dataframe(self, df: pd.DataFrame, column: str | int = 0) -> BatchResult:
        col = df.columns[column] if isinstance(column, int) else column
        data = pd.to_numeric(df[col], errors="coerce").dropna().to_numpy()
        return self.evaluate_batch(data)

    # ── plotting ─────────────────────────────────────────────────────────────

    def plot_curve(self, ax: plt.Axes | None = None, show: bool = True,
                   result: SingleResult | None = None) -> plt.Figure:
        fig, ax = _get_ax(ax)
        col = _COLOURS[self.method]
        x = self._curve_x()
        ax.plot(x, loss(self.method, self.k, x, self.target),
                color=col["primary"], linewidth=2.2, label="L(y)")
        ax.axhline(self.A0, color=col["accent"], linewidth=1.5,
                   linestyle="--", label=f"A₀ = ${self.A0:,.2f}")
        if result is not None:
            ax.scatter([result.y], [result.loss_value], color=col["accent"], s=80,
                       zorder=5, label=f"y={result.y:.3f}  L=${result.loss_value:,.2f}")
        self._decorate_ax(ax)
        fig.tight_layout()
        if show:
            plt.show()
        return fig

    def plot_batch(self, result: BatchResult, ax: plt.Axes | None = None,
                   show: bool = True) -> plt.Figure:
        fig, ax = _get_ax(ax)
        self._scatter_losses(ax, result)
        ax.set_title(f"{_LABELS[self.method]} — Individual Losses  (n={result.n})",
                     fontsize=12, fontweight="bold")
        fig.tight_layout()
        if show:
            plt.show()
        return fig

    def plot_combined(self, result: BatchResult, show: bool = True) -> plt.Figure:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
        col = _COLOURS[self.method]
        x = self._curve_x()
        ax1.plot(x, loss(self.method, self.k, x, self.target),
                 color=col["primary"], linewidth=2.2, label="L(y)")
        ax1.axhline(self.A0, color=col["accent"], linewidth=1.5,
                    linestyle="--", label=f"A₀ = ${self.A0:,.2f}")
        ax1.axhline(result.expected_loss, color=col["el"], linewidth=1.5,
                    linestyle="-.", label=f"E[L] = ${result.expected_loss:,.2f}")
        self._decorate_ax(ax1)
        self._scatter_losses(ax2, result)
        ax2.set_title(f"Individual Losses  (n={result.n})", fontsize=12, fontweight="bold")
        fig.suptitle(f"Taguchi Loss — {_LABELS[self.method]}", fontsize=13, fontweight="bold")
        fig.tight_layout()
        if show:
            plt.show()
        return fig

    def _scatter_losses(self, ax: plt.Axes, result: BatchResult) -> None:
        col = _COLOURS[self.method]
        ax.scatter(range(1, result.n + 1), result.individual_losses,
                   color=col["primary"], alpha=0.75, s=28)
        ax.axhline(result.expected_loss, color=col["el"], linewidth=1.8,
                   linestyle="-.", label=f"E[L] = ${result.expected_loss:,.2f}")
        ax.axhline(self.A0, color=col["accent"], linewidth=1.5,
                   linestyle="--", label=f"A₀ = ${self.A0:,.2f}")
        ax.set_xlabel("Measurement #", fontsize=11)
        ax.set_ylabel("Loss L(y)  ($)", fontsize=11)
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.2f"))
        ax.legend(fontsize=9)

    # ── export ───────────────────────────────────────────────────────────────

    def export_batch_csv(self, result: BatchResult,
                         filepath: str | Path = "taguchi_batch_results.csv") -> Path:
        fp = Path(filepath)
        pd.DataFrame({
            "index": range(1, result.n + 1),
            "y": result.data,
            "loss": result.individual_losses,
        }).to_csv(fp, index=False)
        print(f"  → Exported {result.n} rows to {fp}")
        return fp

    def _curve_x(self) -> np.ndarray:
        raise NotImplementedError

    def _decorate_ax(self, ax: plt.Axes) -> None:
        raise NotImplementedError


# ── Nominal-Is-Best ──────────────────────────────────────────────────────────

class NominalIsBest(TaguchiBase):
    """NIB: target m, tolerance Δ (loss = A₀ when |y − m| = Δ)."""
    method: Method = "nib"

    def __init__(self, target: float, delta: float, A0: float):
        super().__init__(A0=A0, ref=delta, target=target)
        self.delta = self.ref

    def _status_single(self, y: float, lv: float) -> str:
        dev = abs(y - self.target)
        if dev > self.ref:
            return "⚠  OUT OF TOLERANCE"
        if dev > 0.5 * self.ref:
            return "⚡  CAUTION — outer half of tolerance band"
        return "✅  WITHIN TOLERANCE"

    def _status_batch(self, arr: np.ndarray, el: float) -> str:
        bias = abs(float(np.mean(arr)) - self.target)
        if el > self.A0:
            return "⚠  CRITICAL — E[L] > A₀"
        if el > 0.5 * self.A0:
            return "⚡  CAUTION — E[L] > 50% of A₀"
        if bias > 0.5 * self.ref:
            return "⚡  BIAS WARNING — mean significantly off-target"
        return "✅  ACCEPTABLE"

    def _curve_x(self) -> np.ndarray:
        return np.linspace(self.target - 2 * self.ref, self.target + 2 * self.ref, 400)

    def _decorate_ax(self, ax: plt.Axes) -> None:
        ax.axvline(self.target, color="#888", linewidth=1.0, linestyle=":",
                   label=f"Target m={self.target:g}")
        for sign in (+1, -1):
            ax.axvline(self.target + sign * self.ref, color="#aaa", linewidth=0.8, linestyle=":")
        ax.set_xlabel("Process Output y", fontsize=11)
        ax.set_ylabel("Loss L(y)  ($)", fontsize=11)
        ax.set_title("Nominal-Is-Best  L(y) = k(y−m)²", fontsize=12, fontweight="bold")
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.2f"))
        ax.legend(fontsize=9)


# ── Larger-Is-Better ─────────────────────────────────────────────────────────

class LargerIsBetter(TaguchiBase):
    """LIB: reference / minimum acceptable value m (loss = A₀ at y = m)."""
    method: Method = "lib"

    def __init__(self, m: float, A0: float):
        super().__init__(A0=A0, ref=m, target=m)

    def _status_single(self, y: float, lv: float) -> str:
        if y <= 0:
            return "⛔  INVALID — y must be > 0"
        if lv > self.A0:
            return "⚠  CRITICAL — loss > A₀ (y below reference)"
        if lv > 0.5 * self.A0:
            return "⚡  CAUTION — loss > 50% of A₀"
        return "✅  GOOD"

    def _status_batch(self, arr: np.ndarray, el: float) -> str:
        if el > self.A0:
            return "⚠  CRITICAL — E[L] > A₀"
        if el > 0.5 * self.A0:
            return "⚡  CAUTION — E[L] > 50% of A₀"
        if float(np.mean(arr)) < self.ref:
            return "⚡  MEAN BELOW REFERENCE — process output is low"
        return "✅  ACCEPTABLE"

    def _curve_x(self) -> np.ndarray:
        return np.linspace(self.ref * 0.2, self.ref * 2.5, 400)

    def _decorate_ax(self, ax: plt.Axes) -> None:
        ax.axvline(self.ref, color="#888", linewidth=1.0, linestyle=":",
                   label=f"Reference m={self.ref:g}")
        ax.set_xlabel("Process Output y  (higher = better)", fontsize=11)
        ax.set_ylabel("Loss L(y)  ($)", fontsize=11)
        ax.set_title("Larger-Is-Better  L(y) = k / y²", fontsize=12, fontweight="bold")
        ax.set_ylim(0, self.A0 * 4)       # keep the curve readable near m
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.2f"))
        ax.legend(fontsize=9)


# ── Smaller-Is-Better ────────────────────────────────────────────────────────

class SmallerIsBetter(TaguchiBase):
    """SIB: boundary m (loss = A₀ at y = m); ideal is y = 0."""
    method: Method = "sib"

    def __init__(self, m: float, A0: float):
        super().__init__(A0=A0, ref=m, target=0.0)

    def _status_single(self, y: float, lv: float) -> str:
        if y < 0:
            return "⛔  INVALID — y must be ≥ 0"
        if y > self.ref:
            return "⚠  OUT OF TOLERANCE — y exceeds boundary m"
        if lv > 0.5 * self.A0:
            return "⚡  CAUTION — loss > 50% of A₀"
        return "✅  GOOD"

    def _status_batch(self, arr: np.ndarray, el: float) -> str:
        if el > self.A0:
            return "⚠  CRITICAL — E[L] > A₀"
        if el > 0.5 * self.A0:
            return "⚡  CAUTION — E[L] > 50% of A₀"
        if float(np.mean(arr)) > self.ref:
            return "⚠  MEAN EXCEEDS TOLERANCE — process output too high"
        return "✅  ACCEPTABLE"

    def _curve_x(self) -> np.ndarray:
        return np.linspace(0, self.ref * 1.5, 400)

    def _decorate_ax(self, ax: plt.Axes) -> None:
        ax.axvline(self.ref, color="#888", linewidth=1.0, linestyle=":",
                   label=f"Boundary m={self.ref:g}")
        ax.set_xlabel("Process Output y  (lower = better)", fontsize=11)
        ax.set_ylabel("Loss L(y)  ($)", fontsize=11)
        ax.set_title("Smaller-Is-Better  L(y) = k · y²", fontsize=12, fontweight="bold")
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.2f"))
        ax.legend(fontsize=9)


def make_calculator(method: Method, **kwargs) -> TaguchiBase:
    """Factory. NIB kwargs: target, delta, A0 · LIB/SIB kwargs: m, A0"""
    classes = {"nib": NominalIsBest, "lib": LargerIsBetter, "sib": SmallerIsBetter}
    if method not in classes:
        raise ValueError(f"Unknown method '{method}'")
    return classes[method](**kwargs)


def _get_ax(ax: plt.Axes | None) -> tuple[plt.Figure, plt.Axes]:
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))
    else:
        fig = ax.get_figure()
    return fig, ax


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def _build_cli() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Taguchi Quality Loss Function calculator — TheQualityVault.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (using the included example_data.csv)
----------------------------------------------
python taguchi_loss.py demo
python taguchi_loss.py nib --target 500 --delta 10 --A0 2.50 --y 506
python taguchi_loss.py nib --target 500 --delta 10 --A0 2.50 --csv example_data.csv --column fill_weight_g --save nib.png
python taguchi_loss.py lib --m 80 --A0 400 --csv example_data.csv --column bond_strength_mpa --plot
python taguchi_loss.py sib --m 5 --A0 300 --csv example_data.csv --column leak_rate_ccm --export sib_results.csv
""",
    )
    sub = p.add_subparsers(dest="method", required=True)

    nib = sub.add_parser("nib", help="Nominal-Is-Best")
    nib.add_argument("--target", type=float, required=True, help="Target value m")
    nib.add_argument("--delta", type=float, required=True, help="Tolerance Δ")
    nib.add_argument("--A0", type=float, required=True, help="Loss at tolerance ($)")
    _add_common(nib)

    lib = sub.add_parser("lib", help="Larger-Is-Better")
    lib.add_argument("--m", type=float, required=True, help="Reference value m")
    lib.add_argument("--A0", type=float, required=True, help="Loss at reference ($)")
    _add_common(lib)

    sib = sub.add_parser("sib", help="Smaller-Is-Better")
    sib.add_argument("--m", type=float, required=True, help="Tolerance boundary m")
    sib.add_argument("--A0", type=float, required=True, help="Loss at boundary ($)")
    _add_common(sib)
    return p


def _add_common(p: argparse.ArgumentParser) -> None:
    g = p.add_mutually_exclusive_group()
    g.add_argument("--y", type=float, help="Single measurement value")
    g.add_argument("--csv", type=Path, help="Path to CSV file")
    g.add_argument("--excel", type=Path, help="Path to Excel file (.xlsx)")
    p.add_argument("--column", default=0, help="Column name or 0-based index")
    p.add_argument("--sheet", default=0, help="Sheet name or 0-based index (Excel)")
    p.add_argument("--plot", action="store_true", help="Show plot on screen")
    p.add_argument("--save", type=Path, help="Save plot to an image file (e.g. out.png)")
    p.add_argument("--export", type=Path, help="Export batch results to CSV path")


def _as_int_if_possible(v):
    try:
        return int(v)
    except (ValueError, TypeError):
        return v


def _run_cli(args: argparse.Namespace) -> None:
    if args.method == "nib":
        calc = NominalIsBest(target=args.target, delta=args.delta, A0=args.A0)
    elif args.method == "lib":
        calc = LargerIsBetter(m=args.m, A0=args.A0)
    else:
        calc = SmallerIsBetter(m=args.m, A0=args.A0)

    col = _as_int_if_possible(args.column)
    want_fig = args.plot or args.save
    fig = None

    if args.csv or args.excel:
        result = (calc.from_csv(args.csv, column=col) if args.csv else
                  calc.from_excel(args.excel, column=col,
                                  sheet=_as_int_if_possible(args.sheet)))
        print(result.summary())
        if args.export:
            calc.export_batch_csv(result, args.export)
        if want_fig:
            fig = calc.plot_combined(result, show=False)
    elif args.y is not None:
        result = calc.evaluate(args.y)
        print(result.summary())
        if want_fig:
            fig = calc.plot_curve(result=result, show=False)
    else:
        print(f"\n  k = {calc.k:.6f}  (A₀={calc.A0}, ref={calc.ref})")
        if want_fig:
            fig = calc.plot_curve(show=False)

    if fig is not None:
        if args.save:
            fig.savefig(args.save, dpi=150, bbox_inches="tight")
            print(f"  → Plot saved to {args.save}")
        if args.plot:
            plt.show()


# ══════════════════════════════════════════════════════════════════════════════
# Worked example — python taguchi_loss.py demo
# ══════════════════════════════════════════════════════════════════════════════

def run_demo(csv_path: str | Path | None = None, show: bool = True) -> None:
    """
    Worked example using example_data.csv (30 parts per characteristic):
      NIB  fill weight      target 500 g, Δ = 10 g,  A₀ = $2.50 per pack
      LIB  bond strength    minimum 80 MPa,          A₀ = $400 per assembly
      SIB  leak rate        limit 5 ccm,             A₀ = $300 per unit
    """
    csv_path = Path(csv_path or Path(__file__).with_name("example_data.csv"))
    df = pd.read_csv(csv_path)

    print("\n" + "═" * 58)
    print("  TAGUCHI LOSS FUNCTION — WORKED EXAMPLE")
    print("═" * 58)

    nib = NominalIsBest(target=500, delta=10, A0=2.50)
    lib = LargerIsBetter(m=80, A0=400)
    sib = SmallerIsBetter(m=5, A0=300)

    r_nib, r_lib, r_sib = nib.evaluate(506), lib.evaluate(85), sib.evaluate(3.2)
    b_nib = nib.from_dataframe(df, "fill_weight_g")
    b_lib = lib.from_dataframe(df, "bond_strength_mpa")
    b_sib = sib.from_dataframe(df, "leak_rate_ccm")

    print("\n[1] NOMINAL-IS-BEST — fill weight (g)")
    print(r_nib.summary(), b_nib.summary())
    print("[2] LARGER-IS-BETTER — bond strength (MPa)")
    print(r_lib.summary(), b_lib.summary())
    print("[3] SMALLER-IS-BETTER — leak rate (ccm)")
    print(r_sib.summary(), b_sib.summary())

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    fig.suptitle("Taguchi Loss Functions — Worked Example", fontsize=14, fontweight="bold")
    nib.plot_curve(ax=axes[0, 0], show=False, result=r_nib)
    lib.plot_curve(ax=axes[0, 1], show=False, result=r_lib)
    sib.plot_curve(ax=axes[0, 2], show=False, result=r_sib)
    nib.plot_batch(b_nib, ax=axes[1, 0], show=False)
    lib.plot_batch(b_lib, ax=axes[1, 1], show=False)
    sib.plot_batch(b_sib, ax=axes[1, 2], show=False)
    fig.tight_layout()
    fig.savefig("taguchi_example_python.png", dpi=130, bbox_inches="tight")
    print("  → Plot saved to taguchi_example_python.png")
    if show:
        plt.show()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo(show="--no-show" not in sys.argv)
    else:
        _run_cli(_build_cli().parse_args())
