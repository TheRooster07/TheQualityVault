# Wilcoxon Signed Rank Test — TheQualityVault.com

Tests whether the median of paired differences is zero (two columns) or whether one sample's median equals a target (one column). Zero differences are dropped; normal approximation with tie and continuity corrections.

## Files
| File | What it is |
|---|---|
| Wilcoxon_Signed_Rank.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| wilcoxon_signed_rank.py | Python version (numpy, pandas, scipy) |
| wilcoxon_signed_rank.R | R version (base R only) |
| example_data.csv | Example data: cycle time of 14 operators before and after a new fixture. |

## Example output (Excel, Python and R agree)
    Wilcoxon Signed Rank Test  —  TheQualityVault.com
    Non-zero differences                          14
    Median difference                            1.6
    W+                                           104
    P-value                                0.0013592
    p = 0.0014 < 0.05 → reject H0: the median difference is not zero.

## Run
    python wilcoxon_signed_rank.py demo
    python wilcoxon_signed_rank.py --csv my_data.csv --cols Before After      (or --cols x --m0 10 for one sample)
    Rscript wilcoxon_signed_rank.R
