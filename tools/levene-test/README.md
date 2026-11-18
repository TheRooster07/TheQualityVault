# Levene's Test (Brown-Forsythe) — TheQualityVault.com

Tests whether 2 or more groups have equal variances. Brown-Forsythe version: one-way ANOVA on the absolute deviations from each group's median – robust to non-normal data.

## Files
| File | What it is |
|---|---|
| Levene_Test.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| levene_test.py | Python version (numpy, pandas, scipy) |
| levene_test.R | R version (base R only) |
| example_data.csv | Example data: fill weights from 3 lines with different consistency. |

## Example output (Excel, Python and R agree)
    Levene's Test (Brown-Forsythe)  —  TheQualityVault.com
    Groups k                                       3
    N                                             42
    W (F)                                    1.74391
    DF1                                            2
    DF2                                           39
    P-value                                 0.188194
    p = 0.1882 ≥ 0.05 → fail to reject H0: no evidence the variances differ.

## Run
    python levene_test.py demo
    python levene_test.py --csv my_data.csv --cols "Line 1" "Line 2" "Line 3"
    Rscript levene_test.R
