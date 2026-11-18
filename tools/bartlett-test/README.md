# Bartlett's Test — TheQualityVault.com

Tests whether k normal populations have equal variances (more powerful than Levene when data are normal, but sensitive to non-normality).

## Files
| File | What it is |
|---|---|
| Bartlett_Test.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| bartlett_test.py | Python version (numpy, pandas, scipy) |
| bartlett_test.R | R version (base R only) |
| example_data.csv | Example data: fill weights from 3 lines (same data as the Levene example). |

## Example output (Excel, Python and R agree)
    Bartlett's Test  —  TheQualityVault.com
    Groups k                                       3
    N                                             42
    Pooled variance                          1.69688
    Chi-square                               6.39126
    DF                                             2
    P-value                                0.0409408
    p = 0.0409 < 0.05 → reject H0: the variances differ.

## Run
    python bartlett_test.py demo
    python bartlett_test.py --csv my_data.csv --cols "Line 1" "Line 2" "Line 3"
    Rscript bartlett_test.R
