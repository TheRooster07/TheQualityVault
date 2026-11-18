"""
weibull.py  —  TheQualityVault.com
==================================
2-parameter Weibull life-data analysis with suspensions (right-censored units)

  Median Rank Regression (MRR, X on Y)
      • Johnson's adjusted ranks for suspensions, Benard's median rank F = (j − 0.3)/(N + 0.4)
      • x = ln(t), y = ln(−ln(1 − F)); regress x on y  →  β = 1/slope, η = exp(intercept)
  Maximum Likelihood (MLE)
      • β solves  Σt^β·ln t / Σt^β − 1/β − (1/r)·Σ_fail ln t = 0   (sums over ALL units)
      • η = (Σ t^β / r)^(1/β)
  Outputs: β, η, R² (MRR), B1/B10/B50 life, MTTF = η·Γ(1+1/β), reliability R(t) = exp(−(t/η)^β)

The Excel workbook and weibull.R give identical numbers.

Quick start
-----------
    python weibull.py demo
    python weibull.py --csv my_life_data.csv --time hours --status status --at 1000 --save weibull.png
      (status column: F = failure, S = suspension / still running)

Dependencies: numpy, pandas, scipy, matplotlib
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize
import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False,
                            "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3})
NAVY, GOLD, RED = "#1A2B5F", "#C9A84C", "#C0392B"


def _prep(times, status):
    t = np.asarray(times, float)
    f = np.array([str(s).strip().upper().startswith("F") for s in status])
    order = np.lexsort((~f, t))            # sort by time; failures before suspensions at ties
    return t[order], f[order]


def mrr(times, status) -> dict:
    t, f = _prep(times, status)
    N = len(t)
    adj, prev = [], 0.0
    for i in range(N):
        if f[i]:
            prev = prev + (N + 1 - prev) / (1 + (N - i))     # Johnson: reverse rank = N − i (0-based)
            adj.append(prev)
        else:
            adj.append(np.nan)
    adj = np.array(adj)
    F = (adj - 0.3) / (N + 0.4)
    x = np.log(t[f]); y = np.log(-np.log(1 - F[f]))
    b, a = np.polyfit(y, x, 1)                # x = a + b·y
    beta, eta = 1 / b, math.exp(a)
    r2 = np.corrcoef(x, y)[0, 1] ** 2
    return {"beta": beta, "eta": eta, "r2": r2, "t": t, "fail": f, "F": F, "x": x, "y": y}


def mle(times, status) -> dict:
    t, f = _prep(times, status)
    r = f.sum()
    lt = np.log(t)

    def g(b):
        tb = t ** b
        return (tb * lt).sum() / tb.sum() - 1 / b - lt[f].mean()
    beta = optimize.brentq(g, 0.05, 20, xtol=1e-12)
    eta = ((t ** beta).sum() / r) ** (1 / beta)
    return {"beta": beta, "eta": eta}


def life(beta, eta, p):        # time by which fraction p has failed
    return eta * (-math.log(1 - p)) ** (1 / beta)


def report(times, status, at: float | None = None) -> dict:
    m, l = mrr(times, status), mle(times, status)
    out = {"n": len(m["t"]), "failures": int(m["fail"].sum()), "mrr": m, "mle": l, "at": at}
    for key, fit in (("mrr", m), ("mle", l)):
        b, e = fit["beta"], fit["eta"]
        fit.update(B1=life(b, e, .01), B10=life(b, e, .10), B50=life(b, e, .50),
                   MTTF=e * math.gamma(1 + 1 / b), R_at=(math.exp(-(at / e) ** b) if at else None))
    return out


def shape_text(beta):
    if beta < 0.95:
        return "β < 1 → decreasing failure rate (infant mortality: quality, assembly, burn-in issues)"
    if beta <= 1.05:
        return "β ≈ 1 → constant failure rate (random failures)"
    return "β > 1 → increasing failure rate (wear-out: plan preventive replacement)"


def summary(r: dict) -> str:
    m, l = r["mrr"], r["mle"]
    row = lambda k, fmt="{:,.1f}": f"  {k:<26}{fmt.format(m[k] if k in m else 0):>14}{fmt.format(l[k]):>14}"
    lines = ["", "=" * 60, "  Weibull Analysis  —  TheQualityVault.com", "=" * 60,
             f"  Units = {r['n']}   Failures = {r['failures']}   Suspensions = {r['n'] - r['failures']}",
             f"  {'':<26}{'MRR (X on Y)':>14}{'MLE':>14}",
             row("beta", "{:.4f}"), row("eta"), row("B1"), row("B10"), row("B50"), row("MTTF")]
    if r["at"]:
        lines.append(f"  {'R(' + format(r['at'], 'g') + ')':<26}{m['R_at']:>14.4f}{l['R_at']:>14.4f}")
    lines += [f"  R² (MRR fit)              {m['r2']:>14.4f}", f"  {shape_text(m['beta'])}", "=" * 60, ""]
    return "\n".join(lines)


def plot(r: dict, show=True) -> plt.Figure:
    m, l = r["mrr"], r["mle"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.2))
    a1.scatter(m["x"], m["y"], color=NAVY, zorder=3, label="Failures (median ranks)")
    xs = np.linspace(min(m["x"]) - 0.3, max(m["x"]) + 0.3, 50)
    a1.plot(xs, m["beta"] * (xs - math.log(m["eta"])), color=GOLD, lw=2, label=f"MRR β={m['beta']:.2f} η={m['eta']:,.0f}")
    a1.plot(xs, l["beta"] * (xs - math.log(l["eta"])), color=RED, lw=1.5, ls="--", label=f"MLE β={l['beta']:.2f} η={l['eta']:,.0f}")
    pt = [0.01, 0.05, 0.1, 0.2, 0.5, 0.632, 0.9, 0.99]
    a1.set_yticks([math.log(-math.log(1 - p)) for p in pt], [f"{p:.0%}" if p != .632 else "63.2%" for p in pt])
    tt = [v for v in [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]
          if min(xs) <= math.log(v) <= max(xs)]
    a1.set_xticks([math.log(v) for v in tt], [f"{v:,}" for v in tt])
    a1.set_xlabel("Time (log scale)"); a1.set_ylabel("Unreliability F(t)")
    a1.set_title("Weibull Probability Plot", fontweight="bold"); a1.legend(fontsize=8, loc="upper left")
    tg = np.linspace(0, max(m["t"]) * 1.5, 300)
    for fit, colr, lab in ((m, GOLD, "MRR"), (l, RED, "MLE")):
        a2.plot(tg, np.exp(-(tg / fit["eta"]) ** fit["beta"]), color=colr, lw=2, label=f"Reliability R(t) – {lab}")
    a2.set_xlabel("Time"); a2.set_ylabel("Reliability"); a2.set_ylim(0, 1.02)
    a2.set_title("Reliability Curve", fontweight="bold"); a2.legend(fontsize=8)
    fig.suptitle("Weibull Analysis — TheQualityVault.com      " + shape_text(m["beta"]),
                 fontsize=10.5, fontweight="bold", color=NAVY)
    fig.tight_layout()
    if show:
        plt.show()
    return fig


def run_demo(show=True):
    """20 pump bearings: 15 failures, 5 suspensions (still running). Reliability at 1,000 h."""
    d = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    r = report(d["hours"], d["status"], at=1000)
    print(summary(r))
    plot(r, show=False).savefig("weibull_example_python.png", dpi=130, bbox_inches="tight")
    print("  → Plot saved to weibull_example_python.png")
    if show:
        plt.show()
    return r


def _cli():
    p = argparse.ArgumentParser(description="Weibull analysis — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--time", default="hours"); p.add_argument("--status", default="status",
                                                              help="Column with F (failure) / S (suspension)")
    p.add_argument("--at", type=float, help="Time at which to report reliability")
    p.add_argument("--save", type=Path)
    a = p.parse_args()
    d = pd.read_csv(a.csv)
    r = report(d[a.time], d[a.status], a.at)
    print(summary(r))
    if a.save:
        plot(r, show=False).savefig(a.save, dpi=150, bbox_inches="tight")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo(show="--no-show" not in sys.argv)
    else:
        _cli()
