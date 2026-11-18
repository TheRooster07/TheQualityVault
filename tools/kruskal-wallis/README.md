# Kruskal-Wallis Test — TheQualityVault.com

Rank-based test that k independent samples come from the same distribution (non-parametric one-way ANOVA). H statistic with tie correction, chi-square p-value.

## Files
| File | What it is |
|---|---|
| Kruskal_Wallis.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| kruskal_wallis.py | Python version (numpy, pandas, scipy) |
| kruskal_wallis.R | R version (base R only) |
| example_data.csv | Example data: processing times for three methods (skewed). |

## Example output (Excel, Python and R agree)
    Kruskal-Wallis Test  —  TheQualityVault.com
    Groups k                                       3
    N                                             30
    H (tie-corrected)                           11.9
    DF                                             2
    P-value                               0.00260578
    p = 0.0026 < 0.05 → reject H0: at least one group differs.

## Run
    python kruskal_wallis.py demo
    python kruskal_wallis.py --csv my_data.csv --cols "Method A" "Method B" "Method C"
    Rscript kruskal_wallis.R
