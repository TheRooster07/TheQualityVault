"""
crow_amsaa.py  —  TheQualityVault.com
=====================================
Crow-AMSAA reliability growth (NHPP power-law model) for one system or several
identical systems tested at the same time.

  Model      expected cumulative failures per system  N(t) = λ·t^β
             failure intensity                         ρ(t) = λ·β·t^(β−1)
             instantaneous MTBF                        1 / ρ(t)
  MLE        β̂ solves N/β + Σ ln t_i − N·Σ_q T_q^β ln T_q / Σ_q T_q^β = 0,   λ̂ = N / Σ_q T_q^β̂
             (N = total failures, T_q = end of test for system q). One system, or all
             systems ending together:  β̂ = N / Σ ln(T / t_i)
  Note       the χ² bounds on β are exact for one system or equal end times, approximate otherwise
  Unbiased   β̄ = (N−1)/N·β̂  time-terminated       β̄ = (N−2)/N·β̂  failure-terminated
  β bounds   2Nβ/β̂ ~ χ²(2N)  time-terminated      χ²(2(N−1))  failure-terminated
  Trend      Laplace test U ~ N(0,1);  U < 0 → failures getting further apart (growth)
  Plan       time for the instantaneous MTBF to reach a target = (λβ·MTBF)^(1/(1−β))

Data layout (CSV): one row per event
    system, time, event          event = F (failure) or E (end of test for that system)
  · A system with an E row is time-terminated at that time.
  · A single system with no E row is failure-terminated at its last failure.

The Excel workbook and crow_amsaa.R give identical numbers.

Quick start
-----------
    python crow_amsaa.py demo
    python crow_amsaa.py --csv my_test.csv --target-mtbf 150 --at 2500 --save growth.png

Dependencies: numpy, pandas, scipy, matplotlib
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats
import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False,
                            "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3})
NAVY, GOLD, RED = "#1A2B5F", "#C9A84C", "#C0392B"


def analyze(system, time, event, alpha=0.05, at=None, target_mtbf=None, future=None) -> dict:
    d = pd.DataFrame({"system": [str(s).strip() for s in system],
                      "time": pd.to_numeric(pd.Series(list(time)), errors="coerce"),
                      "event": [str(e).strip().upper()[:1] for e in event]}).dropna(subset=["time"])
    if (d.time <= 0).any():
        raise ValueError("All times must be greater than zero.")
    fails = d[d.event == "F"]
    systems = list(dict.fromkeys(d.system))
    K, N = len(systems), len(fails)
    if N < 3:
        raise ValueError("Need at least 3 failures.")
    end = {}
    for s in systems:
        e = d[(d.system == s) & (d.event == "E")]
        end[s] = e.time.iloc[0] if len(e) else d[d.system == s].time.max()
    ft = K == 1 and not (d.event == "E").any()          # failure-terminated (single system only)
    T = np.array([end[s] for s in systems])

    # MLE: β solves  N/β + Σ ln t_i − N·Σ T_q^β ln T_q / Σ T_q^β = 0   (g is strictly decreasing)
    # With one system, or equal end times, this is the textbook β̂ = N / Σ ln(T/t_i).
    sum_ln_t, lnT = float(np.log(fails.time).sum()), np.log(T)
    g = lambda b: N / b + sum_ln_t - N * float((T ** b * lnT).sum() / (T ** b).sum())
    beta = optimize.brentq(g, 1e-3, 20, xtol=1e-14)
    lam = N / float((T ** beta).sum())
    beta_unb = (N - 2) / N * beta if ft else (N - 1) / N * beta
    df = 2 * (N - 1) if ft else 2 * N
    b_lo = beta * stats.chi2.ppf(alpha / 2, df) / (2 * N)
    b_hi = beta * stats.chi2.ppf(1 - alpha / 2, df) / (2 * N)

    # Laplace trend test (for failure-terminated data the final failure is left out)
    m = N - (1 if ft else 0)
    num = float(fails.time.sum()) - (T[0] if ft else 0) - sum(
        (len(fails[fails.system == s]) - (1 if ft else 0)) * end[s] / 2 for s in systems)
    den = math.sqrt(sum((len(fails[fails.system == s]) - (1 if ft else 0)) * end[s] ** 2 / 12 for s in systems))
    U = num / den
    p_trend = 2 * (1 - stats.norm.cdf(abs(U)))

    t_eval = at if at else float(T.max())
    rho = lambda t: lam * beta * t ** (beta - 1)
    out = dict(K=K, N=N, ft=ft, T=T, end=end, systems=systems, fails=fails, alpha=alpha,
               beta=beta, lam=lam, beta_unb=beta_unb, beta_lo=b_lo, beta_hi=b_hi, df=df,
               growth=1 - beta, U=U, p_trend=p_trend, m=m, t_eval=t_eval,
               total_time=float(T.sum()), cum_mtbf_obs=float(T.sum()) / N,
               inst_mtbf=1 / rho(t_eval), cum_mtbf_model=t_eval ** (1 - beta) / lam,
               intensity=rho(t_eval), target=target_mtbf, future=future)
    if target_mtbf:
        out["t_target"] = (lam * beta * target_mtbf) ** (1 / (1 - beta)) if beta < 1 else float("nan")
    if future:
        out["n_future"] = lam * future ** beta
        out["n_add"] = lam * (future ** beta - t_eval ** beta)
        out["mtbf_future"] = 1 / rho(future)

    # Mean cumulative function (Nelson-Aalen) for the plot: failures per system vs age
    ft_sorted = fails.sort_values("time")
    at_risk = np.array([(T >= t).sum() for t in ft_sorted.time])
    out["mcf_t"] = ft_sorted.time.to_numpy()
    out["mcf"] = np.cumsum(1 / at_risk)
    return out


def verdict(r) -> str:
    a = r["alpha"]
    if r["p_trend"] < a and r["U"] < 0:
        return f"Reliability is GROWING: failures are getting further apart (Laplace p = {r['p_trend']:.4f} < {a})."
    if r["p_trend"] < a and r["U"] > 0:
        return f"Reliability is GETTING WORSE: failures are coming closer together (Laplace p = {r['p_trend']:.4f} < {a})."
    return f"No significant trend (Laplace p = {r['p_trend']:.4f} ≥ {a}): treat the failure rate as constant (β ≈ 1)."


def summary(r: dict) -> str:
    L = lambda k, v: f"  {k:<40}{v:>16}"
    g = lambda v, f="{:,.4f}": f.format(v)
    lines = ["", "=" * 60, "  Crow-AMSAA Reliability Growth  —  TheQualityVault.com", "=" * 60,
             L("Systems", r["K"]), L("Failures N", r["N"]),
             L("Test type", "failure-terminated" if r["ft"] else "time-terminated"),
             L("Total test time (all systems)", g(r["total_time"], "{:,.1f}")),
             L("Shape β (MLE)", g(r["beta"])),
             L("Scale λ", g(r["lam"], "{:.6g}")),
             L("β unbiased", g(r["beta_unb"])),
             L(f"β {100 * (1 - r['alpha']):.0f}% lower bound", g(r["beta_lo"])),
             L(f"β {100 * (1 - r['alpha']):.0f}% upper bound", g(r["beta_hi"])),
             L("Growth rate α = 1 − β", g(r["growth"])),
             L("Laplace U", g(r["U"])), L("Laplace p-value (two-sided)", g(r["p_trend"])),
             L("Evaluated at age t", g(r["t_eval"], "{:,.1f}")),
             L("Failure intensity at t (per system)", g(r["intensity"], "{:.6g}")),
             L("Instantaneous MTBF at t", g(r["inst_mtbf"], "{:,.2f}")),
             L("Cumulative MTBF (model) at t", g(r["cum_mtbf_model"], "{:,.2f}")),
             L("Cumulative MTBF (observed)", g(r["cum_mtbf_obs"], "{:,.2f}"))]
    if r.get("target"):
        tt = r["t_target"]
        lines.append(L(f"Age to reach MTBF {r['target']:g}", "not reached (β ≥ 1)" if math.isnan(tt) else g(tt, "{:,.1f}")))
    if r.get("future"):
        lines += [L(f"Expected failures per system by {r['future']:g}", g(r["n_future"], "{:,.2f}")),
                  L(f"Additional failures per system to {r['future']:g}", g(r["n_add"], "{:,.2f}")),
                  L(f"Instantaneous MTBF at {r['future']:g}", g(r["mtbf_future"], "{:,.2f}"))]
    lines += ["  " + verdict(r), "=" * 60, ""]
    return "\n".join(lines)


def plot(r: dict, show=True) -> plt.Figure:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.2))
    tmax = max(r["T"].max(), r.get("future") or 0)
    tg = np.geomspace(r["mcf_t"].min() * 0.8, tmax * 1.1, 200)
    a1.loglog(r["mcf_t"], r["mcf"], "o", color=NAVY, label="Observed (cumulative failures per system)")
    a1.loglog(tg, r["lam"] * tg ** r["beta"], color=GOLD, lw=2, label=f"Crow-AMSAA fit  β = {r['beta']:.3f}")
    a1.set_xlabel("Test time per system (log)"); a1.set_ylabel("Cumulative failures per system (log)")
    a1.set_title("Cumulative failures — log-log", fontweight="bold"); a1.legend(fontsize=8, loc="upper left")
    tl = np.linspace(r["mcf_t"].min(), tmax * 1.05, 300)
    a2.plot(tl, 1 / (r["lam"] * r["beta"] * tl ** (r["beta"] - 1)), color=GOLD, lw=2, label="Instantaneous MTBF (model)")
    a2.plot(tl, tl ** (1 - r["beta"]) / r["lam"], color=RED, lw=1.5, ls="--", label="Cumulative MTBF (model)")
    a2.plot(r["mcf_t"], r["mcf_t"] / r["mcf"], "o", color=NAVY, ms=4, label="Cumulative MTBF (observed)")
    if r.get("target"):
        a2.axhline(r["target"], color="grey", ls=":", lw=1.2, label=f"Target MTBF {r['target']:g}")
    a2.set_xlabel("Test time per system"); a2.set_ylabel("MTBF")
    a2.set_title("MTBF growth", fontweight="bold"); a2.legend(fontsize=8, loc="upper left")
    fig.suptitle("Crow-AMSAA Reliability Growth — TheQualityVault.com      " + verdict(r).split(":")[0],
                 fontsize=10.5, fontweight="bold", color=NAVY)
    fig.tight_layout()
    if show:
        plt.show()
    return fig


def export(r: dict, path) -> None:
    pd.DataFrame({"time": r["mcf_t"], "cumulative_failures_per_system": r["mcf"],
                  "model_cumulative_failures": r["lam"] * r["mcf_t"] ** r["beta"],
                  "instantaneous_mtbf_model": 1 / (r["lam"] * r["beta"] * r["mcf_t"] ** (r["beta"] - 1))}
                 ).to_csv(path, index=False)


def run_demo(show=True):
    """Three prototypes on a reliability growth test; target MTBF 350 h; projection to 2,500 h."""
    d = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    r = analyze(d["system"], d["time"], d["event"], target_mtbf=350, future=2500)
    print(summary(r))
    plot(r, show=False).savefig("crow_amsaa_example_python.png", dpi=130, bbox_inches="tight")
    print("  → Plot saved to crow_amsaa_example_python.png")
    if show:
        plt.show()
    return r


def _cli():
    p = argparse.ArgumentParser(description="Crow-AMSAA reliability growth — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--system", default="system"); p.add_argument("--time", default="time")
    p.add_argument("--event", default="event", help="Column with F (failure) / E (end of test)")
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--at", type=float, help="Age at which to report MTBF (default: longest test time)")
    p.add_argument("--target-mtbf", type=float); p.add_argument("--future", type=float, help="Project to this age")
    p.add_argument("--save", type=Path); p.add_argument("--export", type=Path)
    a = p.parse_args()
    d = pd.read_csv(a.csv)
    sysc = d[a.system] if a.system in d else ["1"] * len(d)
    evc = d[a.event] if a.event in d else ["F"] * len(d)
    r = analyze(sysc, d[a.time], evc, a.alpha, a.at, a.target_mtbf, a.future)
    print(summary(r))
    if a.save:
        plot(r, show=False).savefig(a.save, dpi=150, bbox_inches="tight")
    if a.export:
        export(r, a.export)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo(show="--no-show" not in sys.argv)
    else:
        _cli()
