"""
hypothesis_advisor.py  —  TheQualityVault.com
=============================================
Hypothesis Test Advisor: answer a few questions about your data and get the right
test, then (optionally) run it.

    python hypothesis_advisor.py              # interactive questions
    python hypothesis_advisor.py demo         # worked example (two filling machines)

In code:
    from hypothesis_advisor import recommend, run_test
    rec = recommend(compare="mean", groups=2, paired=False, normal=True, equal_var=False)
    print(rec["test"])                        # 2-Sample t-Test (Welch)
    print(run_test(rec["key"], a, b))         # runs it with scipy

The decision logic is identical to the Excel workbook and hypothesis_advisor.R.
Dependencies: numpy, pandas, scipy
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

TESTS = {
    "t1": "1-Sample t-Test", "wil1": "1-Sample Wilcoxon Signed Rank",
    "tpair": "Paired t-Test", "wilpair": "Wilcoxon Signed Rank (paired differences)",
    "t2pool": "2-Sample t-Test (pooled)", "t2welch": "2-Sample t-Test (Welch)", "mw": "Mann-Whitney U",
    "anova1": "One-Way ANOVA", "welchanova": "Welch's ANOVA", "kw": "Kruskal-Wallis",
    "mood": "Mood's Median Test", "anova2": "Two-Way ANOVA", "friedman": "Friedman Test",
    "chivar1": "1-Variance Chi-Square Test", "bonett1": "1-Variance Test (Bonett)",
    "ftest": "F-Test for Equal Variances", "levene": "Levene's Test (Brown-Forsythe)",
    "bartlett": "Bartlett's Test", "prop1": "1-Proportion Test (exact binomial)",
    "prop2": "2-Proportion Test / Fisher's Exact", "mcnemar": "McNemar's Test",
    "chiassoc": "Chi-Square Test of Association", "pearson": "Pearson Correlation + Regression",
    "spearman": "Spearman Rank Correlation", "chigof": "Chi-Square Goodness of Fit",
    "ad": "Anderson-Darling Normality Test",
}


def recommend(compare: str, groups: int = 2, paired: bool = False, normal: bool = True,
              equal_var: bool | None = None, factors: int = 1, outliers: bool = False,
              continuous_fit: bool = True) -> dict:
    """
    compare  : 'mean'  (means/medians of a continuous Y)
               'variance'  (spread of a continuous Y)
               'proportion' (pass/fail, counts, categories)
               'relationship' (two continuous variables)
               'fit'  (does data follow a distribution / expected proportions)
    groups   : 1 (vs a target), 2, or 3+ (any number ≥ 3)
    paired   : same units measured twice / matched pairs (2 groups only)
    normal   : data roughly normal, OR at least 30 per group for means
    equal_var: True / False / None (not sure → treated as False)
    factors  : for 3+ groups, number of factors (1 or 2)
    outliers : for 3+ non-normal groups – are there extreme outliers?
    """
    g = 3 if groups >= 3 else int(groups)
    c = compare.lower()
    if c == "mean":
        if g == 1:
            k = "t1" if normal else "wil1"
        elif g == 2:
            if paired:
                k = "tpair" if normal else "wilpair"
            elif normal:
                k = "t2pool" if equal_var else "t2welch"
            else:
                k = "mw"
        else:
            if factors >= 2:
                k = "anova2" if normal else "friedman"
            elif normal:
                k = "anova1" if equal_var else "welchanova"
            else:
                k = "mood" if outliers else "kw"
    elif c == "variance":
        k = {1: "chivar1" if normal else "bonett1", 2: "ftest" if normal else "levene",
             3: "bartlett" if normal else "levene"}[g]
    elif c == "proportion":
        k = {1: "prop1", 2: "mcnemar" if paired else "prop2", 3: "chiassoc"}[g]
    elif c == "relationship":
        k = "pearson" if normal else "spearman"
    elif c == "fit":
        k = "ad" if continuous_fit else "chigof"
    else:
        raise ValueError("compare must be mean, variance, proportion, relationship or fit")
    return {"key": k, "test": TESTS[k]}


def run_test(key: str, *samples, mu0: float = 0.0, p0: float = 0.5, alpha: float = 0.05) -> str:
    """Run the recommended test on numeric samples (lists/arrays). Returns a plain-English result."""
    s = [np.asarray(pd.to_numeric(pd.Series(x), errors="coerce").dropna(), float) for x in samples]
    res = None
    if key == "t1":
        res = stats.ttest_1samp(s[0], mu0)
    elif key == "wil1":
        res = stats.wilcoxon(s[0] - mu0, correction=True, method="approx")
    elif key == "tpair":
        res = stats.ttest_rel(s[0], s[1])
    elif key == "wilpair":
        res = stats.wilcoxon(s[0], s[1], correction=True, method="approx")
    elif key in ("t2pool", "t2welch"):
        res = stats.ttest_ind(s[0], s[1], equal_var=(key == "t2pool"))
    elif key == "mw":
        res = stats.mannwhitneyu(s[0], s[1], alternative="two-sided", method="asymptotic")
    elif key == "anova1":
        res = stats.f_oneway(*s)
    elif key == "welchanova":
        k = len(s); n = np.array([len(x) for x in s]); m = np.array([x.mean() for x in s])
        v = np.array([x.var(ddof=1) for x in s]); w = n / v; mw = (w * m).sum() / w.sum()
        a = (w * (m - mw) ** 2).sum() / (k - 1)
        lam = ((1 - w / w.sum()) ** 2 / (n - 1)).sum()
        F = a / (1 + 2 * (k - 2) * lam / (k ** 2 - 1)); df2 = (k ** 2 - 1) / (3 * lam)
        return _say("Welch's ANOVA", F, stats.f.sf(F, k - 1, df2), alpha, "there is a difference")
    elif key == "kw":
        res = stats.kruskal(*s)
    elif key == "mood":
        st, p, _, _ = stats.median_test(*s)
        return _say(TESTS["mood"], st, p, alpha, "there is a difference")
    elif key == "ftest":
        F = s[0].var(ddof=1) / s[1].var(ddof=1); d1, d2 = len(s[0]) - 1, len(s[1]) - 1
        p = 2 * min(stats.f.cdf(F, d1, d2), stats.f.sf(F, d1, d2))
        return _say(TESTS["ftest"], F, p, alpha, "variances differ")
    elif key == "levene":
        res = stats.levene(*s, center="median")
    elif key == "bartlett":
        res = stats.bartlett(*s)
    elif key in ("pearson", "spearman"):
        res = (stats.pearsonr if key == "pearson" else stats.spearmanr)(s[0], s[1])
        return _say(TESTS[key], res[0], res[1], alpha, "the variables are related")
    elif key == "ad":
        x = s[0]; n = len(x); z = np.sort((x - x.mean()) / x.std(ddof=1)); F = stats.norm.cdf(z)
        i = np.arange(1, n + 1)
        a2 = -n - np.sum((2 * i - 1) * (np.log(F) + np.log(1 - F[::-1]))) / n
        a = a2 * (1 + 0.75 / n + 2.25 / n ** 2)
        p = (np.exp(1.2937 - 5.709 * a + 0.0186 * a * a) if a >= 0.6 else
             np.exp(0.9177 - 4.279 * a - 1.38 * a * a) if a >= 0.34 else
             1 - np.exp(-8.318 + 42.796 * a - 59.938 * a * a) if a >= 0.2 else
             1 - np.exp(-13.436 + 101.14 * a - 223.73 * a * a))
        return _say(TESTS["ad"], a2, p, alpha, "the data are not normal")
    else:
        return (f"{TESTS[key]}: pass counts to scipy directly, e.g. stats.binomtest, stats.fisher_exact, "
                f"stats.chi2_contingency or stats.chisquare.")
    claim = "variances differ" if key in ("levene", "bartlett") else "there is a difference"
    return _say(TESTS[key], float(res[0]), float(res[1]), alpha, claim)


def _say(name, stat, p, alpha, claim):
    verdict = (f"p = {p:.4f} < {alpha} → reject H0: evidence that {claim}." if p < alpha else
               f"p = {p:.4f} ≥ {alpha} → fail to reject H0: no evidence that {claim}.")
    return f"{name}: statistic = {stat:.4f}.  {verdict}"


def _ask(q, options):
    print(f"\n{q}")
    for i, o in enumerate(options, 1):
        print(f"  {i}. {o}")
    while True:
        a = input("  > ").strip()
        if a.isdigit() and 1 <= int(a) <= len(options):
            return int(a) - 1


def interactive():
    print("\nHypothesis Test Advisor — TheQualityVault.com")
    comp = ["mean", "variance", "proportion", "relationship", "fit"][_ask(
        "What do you want to test?", ["Means / medians (continuous Y)", "Variation / spread (continuous Y)",
                                      "Proportions or counts (attribute Y)", "Relationship between two continuous variables",
                                      "Fit to a distribution / expected proportions"])]
    kw = {"compare": comp}
    if comp in ("mean", "variance", "proportion"):
        kw["groups"] = [1, 2, 3][_ask("How many groups?", ["1 (compare with a target)", "2", "3 or more"])]
    if kw.get("groups") == 2 and comp in ("mean", "proportion"):
        kw["paired"] = _ask("Are the two samples paired (same units measured twice)?", ["Yes", "No"]) == 0
    if comp in ("mean", "variance", "relationship"):
        kw["normal"] = _ask("Is the data roughly normal (or n ≥ 30 per group for means)?", ["Yes", "No"]) == 0
    if comp == "mean" and kw.get("groups", 1) >= 2 and not kw.get("paired") and kw["normal"]:
        kw["equal_var"] = _ask("Are the group variances equal?", ["Yes", "No / not sure"]) == 0
    if comp == "mean" and kw.get("groups") == 3:
        kw["factors"] = [1, 2][_ask("How many factors (X variables)?", ["1", "2"])]
        if not kw["normal"] and kw["factors"] == 1:
            kw["outliers"] = _ask("Are there extreme outliers?", ["Yes", "No"]) == 0
    if comp == "fit":
        kw["continuous_fit"] = _ask("What kind of data?", ["Continuous measurements", "Counts in categories"]) == 0
    print(f"\n  ➜ Recommended: {recommend(**kw)['test']}\n")


def run_demo():
    """Two filling machines – is the mean fill weight different? 12 bottles each."""
    a = [500.4, 501.2, 499.8, 500.9, 501.5, 500.2, 499.6, 501.0, 500.7, 500.1, 501.3, 500.5]
    b = [501.8, 502.6, 500.9, 503.1, 502.2, 501.5, 503.4, 502.0, 501.1, 502.8, 502.4, 501.7]
    print("\nScenario: compare mean fill weight of Machine A vs Machine B (12 bottles each)")
    print(" ", run_test("ad", a), "  (Machine A)")
    print(" ", run_test("ad", b), "  (Machine B)")
    print(" ", run_test("ftest", a, b))
    F = np.var(a, ddof=1) / np.var(b, ddof=1)
    p_f = 2 * min(stats.f.cdf(F, 11, 11), stats.f.sf(F, 11, 11))
    rec = recommend("mean", groups=2, paired=False, normal=True, equal_var=bool(p_f >= 0.05))
    print(f"\n  ➜ Recommended: {rec['test']}")
    print(" ", run_test(rec["key"], a, b))
    print(f"  Mean A = {np.mean(a):.3f} g   Mean B = {np.mean(b):.3f} g\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_demo()
    else:
        interactive()
