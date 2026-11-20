"""
repairable_systems.py  —  TheQualityVault.com
=============================================
Repairable systems analysis for a fleet, and the repair-or-replace decision.

Data (CSV, one row per event):  unit, event, date, age      – give a date OR an age on each row
    I  installed (new)                 – sets age 0 when you work in dates
    S  records start (optional)        – only if history before this point is unknown
    F  failure, repaired and returned to service
    E  end of observation, still in service
    R  retired / removed from service
  Units with no failures still count: give them an I (or S) row and an E or R row.
  With dates, age = (date − install date) / days-per-unit (365.25 → years). Without an I row,
  the S date is taken as age 0.

Analysis
  · Mean cumulative function (MCF, Nelson): average failures per unit by age, staggered entry and
    retirement allowed; 95% bounds on the log scale (Poisson variance).
  · Power-law NHPP  ρ(t) = λβt^(β−1), fitted by maximum likelihood with each unit observed from age a
    to age b:  λ = N / Σ(b^β − a^β);  β solves N/β + Σ ln t − N·Σ(b^β ln b − a^β ln a)/Σ(b^β − a^β) = 0.
    Bounds on β from the profile-likelihood information (log scale).
  · Laplace trend test across the fleet:  U = Σ(t − (a+b)/2) / √(Σ n(b−a)²/12).
  · Bad actors: units with more failures than the model predicts (Poisson upper-tail p-value).
  · Economics (minimal repair, planned replacement at age T):  cost rate C(T) = (Cp + Cr·λT^β) / T.
    With β > 1 the optimum replacement age is T* = [Cp / (Cr·λ(β−1))]^(1/β).
    Each unit still in service gets expected failures and repair cost over the next H time units
    and a keep / plan / replace recommendation.

The Excel workbook and repairable_systems.R give identical numbers.

Quick start
-----------
    python repairable_systems.py demo
    python repairable_systems.py --csv fleet.csv --replace-cost 45000 --repair-cost 6000 --horizon 3

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


def prepare(df, days_per_unit=365.25):
    """Return (events with an 'age' column, unit table)."""
    d = df.copy()
    d.columns = [c.strip().lower() for c in d.columns]
    d["unit"] = d["unit"].astype(str).str.strip()
    d["event"] = d["event"].astype(str).str.strip().str.upper().str[0]
    age = pd.to_numeric(d["age"], errors="coerce") if "age" in d else pd.Series(np.nan, index=d.index)
    date = pd.to_datetime(d["date"], errors="coerce") if "date" in d else pd.Series(pd.NaT, index=d.index)
    origin = {}
    for u, g in d.assign(_date=date).groupby("unit", sort=False):
        i = g[(g.event == "I") & g._date.notna()]
        s = g[(g.event == "S") & g._date.notna()]
        origin[u] = i._date.iloc[0] if len(i) else (s._date.iloc[0] if len(s) else pd.NaT)
    from_date = (date - d["unit"].map(origin)).dt.days / days_per_unit
    d["age"] = age.where(age.notna(), from_date)
    d.loc[(d.event == "I") & d.age.isna(), "age"] = 0.0
    if d.age.isna().any():
        raise ValueError("Rows with no usable date or age: " + ", ".join(d.loc[d.age.isna(), "unit"].unique()))
    units = []
    for u, g in d.groupby("unit", sort=False):
        s = g[g.event == "S"]; e = g[g.event.isin(["E", "R"])]
        if len(e) != 1:
            raise ValueError(f"Unit {u}: needs exactly one E (in service) or R (retired) row.")
        a = float(s.age.iloc[0]) if len(s) else 0.0
        b = float(e.age.iloc[0])
        f = g[g.event == "F"].age
        if (f <= a).any() or (f > b).any() or b <= a:
            raise ValueError(f"Unit {u}: failures must fall after the start and on/before the end of observation.")
        units.append(dict(unit=u, start=a, end=b, failures=len(f), status="Retired" if e.event.iloc[0] == "R" else "In service"))
    return d, pd.DataFrame(units)


def analyze(df, replace_cost=None, repair_cost=None, horizon=3.0, alpha=0.05, flag_p=0.01, days_per_unit=365.25):
    d, U = prepare(df, days_per_unit)
    t = d.loc[d.event == "F", "age"].to_numpy(float)
    N, K = len(t), len(U)
    if N < 3:
        raise ValueError("Need at least 3 failures.")
    a, b, n = U.start.to_numpy(), U.end.to_numpy(), U.failures.to_numpy()
    sa = np.where(a > 0, a, 1.0)
    lt = float(np.log(t).sum())

    def sums(B):
        S0 = (b ** B - (a > 0) * sa ** B).sum()
        S1 = (b ** B * np.log(b) - (a > 0) * sa ** B * np.log(sa)).sum()
        S2 = (b ** B * np.log(b) ** 2 - (a > 0) * sa ** B * np.log(sa) ** 2).sum()
        return S0, S1, S2
    g = lambda B: N / B + lt - N * sums(B)[1] / sums(B)[0]
    beta = optimize.brentq(g, 0.01, 20, xtol=1e-14)
    S0, S1, S2 = sums(beta)
    lam = N / S0
    info = N / beta ** 2 + N * (S2 * S0 - S1 ** 2) / S0 ** 2
    se = 1 / math.sqrt(info)
    z = stats.norm.ppf(1 - alpha / 2)
    b_lo, b_hi = beta * math.exp(-z * se / beta), beta * math.exp(z * se / beta)

    mid = dict(zip(U.unit, (U.start + U.end) / 2))
    num = float((d.loc[d.event == "F", "age"] - d.loc[d.event == "F", "unit"].map(mid)).sum())
    Ul = num / math.sqrt(float((n * (b - a) ** 2).sum() / 12))
    p_trend = 2 * (1 - stats.norm.cdf(abs(Ul)))

    # MCF at each failure age (all failures at or before t; ties share one value)
    risk = np.array([((a < x) & (x <= b)).sum() for x in t])
    mcf = np.array([(1 / risk[t <= x]).sum() for x in t])
    var = np.array([(1 / risk[t <= x] ** 2).sum() for x in t])
    o = np.argsort(t, kind="stable")
    M = pd.DataFrame({"age": t, "at_risk": risk, "mcf": mcf,
                      "lower": mcf * np.exp(-z * np.sqrt(var) / mcf),
                      "upper": mcf * np.exp(z * np.sqrt(var) / mcf)}).iloc[o].reset_index(drop=True)

    U["expected"] = lam * (b ** beta - (a > 0) * sa ** beta)
    U["p_excess"] = [1 - stats.poisson.cdf(k - 1, e) if k > 0 else 1.0 for k, e in zip(n, U.expected)]
    U["bad_actor"] = (U.p_excess < flag_p) & (U.failures >= 2)

    r = dict(K=K, N=N, in_service=int((U.status == "In service").sum()), retired=int((U.status == "Retired").sum()),
             exposure=float((b - a).sum()), beta=beta, lam=lam, se=se, beta_lo=b_lo, beta_hi=b_hi, alpha=alpha,
             U=Ul, p_trend=p_trend, units=U, mcf=M, events=d, horizon=horizon,
             Cp=replace_cost, Cr=repair_cost, flag_p=flag_p)
    r["rate_per_unit"] = N / r["exposure"]
    if replace_cost and repair_cost:
        cost = lambda T: (replace_cost + repair_cost * lam * T ** beta) / T
        r["cost"] = cost
        if beta > 1:
            Ts = (replace_cost / (repair_cost * lam * (beta - 1))) ** (1 / beta)
            r["T_star"], r["C_star"] = Ts, cost(Ts)
        else:
            r["T_star"] = r["C_star"] = float("nan")
    ins = U.status == "In service"
    t0 = U.end.where(ins)
    U["next_failures"] = (lam * ((t0 + horizon) ** beta - t0 ** beta)).where(ins)
    U["next_repair_cost"] = U.next_failures * repair_cost if repair_cost else np.nan
    U["advice"] = [_advice(r, row) for row in U.itertuples()]
    return r


def _advice(r, u):
    if u.status != "In service":
        return "Retired"
    if u.bad_actor:
        return "Bad actor – find the cause; replace early if it can't be fixed"
    Ts = r.get("T_star")
    if Ts is None or (isinstance(Ts, float) and math.isnan(Ts)):
        return "Keep repairing" if r["beta"] <= 1 or Ts is not None else "Enter costs for a replace decision"
    if u.end >= Ts:
        return "Replace – past the optimum age"
    if u.end + r["horizon"] >= Ts:
        return f"Plan replacement in about {Ts - u.end:.1f}"
    return "Keep repairing"


def pattern(r) -> str:
    lo, hi = r["beta_lo"], r["beta_hi"]
    if lo > 1:
        return "WEAR-OUT: failures come faster as units age (β > 1). Replacement at the right age saves money."
    if hi < 1:
        return "IMPROVING: failures get further apart with age (β < 1). Keep repairing."
    return "NO CLEAR AGE EFFECT: β is not significantly different from 1 – the failure rate is steady; repairing is fine."


def summary(r) -> str:
    L = lambda k, v: f"  {k:<44}{v:>14}"
    u = r["units"]
    lines = ["", "=" * 62, "  Repairable Systems & Replacement Age  —  TheQualityVault.com", "=" * 62,
             L("Units (in service / retired)", f"{r['K']} ({r['in_service']} / {r['retired']})"),
             L("Failures", r["N"]), L("Observed unit-time", f"{r['exposure']:,.2f}"),
             L("Failures per unit per time unit (average)", f"{r['rate_per_unit']:.4f}"),
             L("Shape β (MLE)", f"{r['beta']:.4f}"), L("Scale λ", f"{r['lam']:.6g}"),
             L(f"β {100 * (1 - r['alpha']):.0f}% lower bound", f"{r['beta_lo']:.4f}"),
             L(f"β {100 * (1 - r['alpha']):.0f}% upper bound", f"{r['beta_hi']:.4f}"),
             L("Laplace U", f"{r['U']:.4f}"), L("Laplace p-value (two-sided)", f"{r['p_trend']:.4f}")]
    if r.get("Cp"):
        Ts = r["T_star"]
        lines += [L("Replacement cost / repair cost", f"{r['Cp']:,.0f} / {r['Cr']:,.0f}"),
                  L("Optimum replacement age T*", "none (β ≤ 1)" if math.isnan(Ts) else f"{Ts:,.2f}"),
                  L("Lowest cost per unit per time unit", "—" if math.isnan(Ts) else f"{r['C_star']:,.2f}"),
                  L("In-service units past T*", "—" if math.isnan(Ts) else int(((u.status == 'In service') & (u.end >= Ts)).sum()))]
    lines += [L("Bad actors flagged", int(u.bad_actor.sum())), "  " + pattern(r), "=" * 62]
    show = u[(u.status == "In service")].sort_values("end", ascending=False).head(12)
    lines.append(f"  {'Unit':<8}{'Age':>8}{'Fails':>7}{'Next ' + format(r['horizon'], 'g') + ' fails':>14}  Advice")
    for x in show.itertuples():
        lines.append(f"  {x.unit:<8}{x.end:>8.2f}{x.failures:>7}{x.next_failures:>14.2f}  {x.advice}")
    for x in u[u.bad_actor].itertuples():
        lines.append(f"  ! Bad actor {x.unit}: {x.failures} failures vs {x.expected:.2f} expected (p = {x.p_excess:.4f})")
    return "\n".join(lines + [""])


def plot(r, show=True) -> plt.Figure:
    M = r["mcf"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.2))
    a1.step(M.age, M.mcf, where="post", color=NAVY, lw=1.8, label="MCF (observed)")
    a1.fill_between(M.age, M.lower, M.upper, step="post", color=NAVY, alpha=0.12, label=f"{100 * (1 - r['alpha']):.0f}% bounds")
    tg = np.linspace(0, r["units"].end.max(), 200)
    a1.plot(tg, r["lam"] * tg ** r["beta"], color=GOLD, lw=2.2, label=f"Power-law fit  β = {r['beta']:.2f}")
    a1.set_xlabel("Age"); a1.set_ylabel("Cumulative failures per unit")
    a1.set_title("Mean cumulative function", fontweight="bold"); a1.legend(fontsize=8, loc="upper left")
    if r.get("Cp") and not math.isnan(r["T_star"]):
        Ts = r["T_star"]; T = np.linspace(Ts * 0.25, Ts * 3, 300)
        a2.plot(T, r["cost"](T), color=GOLD, lw=2.2, label="Cost per unit per time unit")
        a2.axvline(Ts, color=RED, ls="--", lw=1.4, label=f"Optimum T* = {Ts:.1f}")
        a2.set_ylim(0, r["cost"](T).max() * 1.05)
        a2.set_xlabel("Replacement age T"); a2.set_ylabel("Cost per unit per time unit")
        a2.set_title("Repair-or-replace cost curve", fontweight="bold"); a2.legend(fontsize=8)
    else:
        u = r["units"]
        a2.bar(u.unit, u.failures, color=[RED if x else NAVY for x in u.bad_actor])
        a2.plot(u.unit, u.expected, "o", color=GOLD, label="Expected")
        a2.set_title("Failures per unit (red = bad actor)", fontweight="bold"); a2.tick_params(axis="x", rotation=90, labelsize=6)
    fig.suptitle("Repairable Systems — TheQualityVault.com      " + pattern(r).split(":")[0],
                 fontsize=10.5, fontweight="bold", color=NAVY)
    fig.tight_layout()
    if show:
        plt.show()
    return fig


def run_demo(show=True):
    """40 pumps (in dates): replacement 45,000, repair 6,000 incl. downtime, 3-year look-ahead."""
    d = pd.read_csv(Path(__file__).with_name("example_data.csv"))
    r = analyze(d, replace_cost=45000, repair_cost=6000, horizon=3)
    print(summary(r))
    plot(r, show=False).savefig("repairable_systems_example_python.png", dpi=130, bbox_inches="tight")
    print("  → Plot saved to repairable_systems_example_python.png")
    if show:
        plt.show()
    return r


def _cli():
    p = argparse.ArgumentParser(description="Repairable systems & replacement age — TheQualityVault.com")
    p.add_argument("--csv", type=Path, required=True, help="Columns: unit, event, date and/or age")
    p.add_argument("--replace-cost", type=float); p.add_argument("--repair-cost", type=float)
    p.add_argument("--horizon", type=float, default=3.0); p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--flag-p", type=float, default=0.01, help="Bad-actor p-value threshold")
    p.add_argument("--days-per-unit", type=float, default=365.25, help="For dates: 365.25 = years, 1 = days")
    p.add_argument("--save", type=Path); p.add_argument("--export", type=Path, help="Write the unit table to CSV")
    a = p.parse_args()
    r = analyze(pd.read_csv(a.csv), a.replace_cost, a.repair_cost, a.horizon, a.alpha, a.flag_p, a.days_per_unit)
    print(summary(r))
    if a.save:
        plot(r, show=False).savefig(a.save, dpi=150, bbox_inches="tight")
    if a.export:
        r["units"].to_csv(a.export, index=False)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo(show="--no-show" not in sys.argv)
    else:
        _cli()
