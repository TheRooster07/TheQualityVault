# Paired t-Test — TheQualityVault.com

Tests whether the mean of paired differences (first − second) differs from a hypothesised difference (usually 0). Each row is one unit measured twice.

## Files
| File | What it is |
|---|---|
| Paired_t_Test.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| paired_t.py | Python version (numpy, pandas, scipy) |
| paired_t.R | R version (base R only) |
| example_data.csv | Example data: set-up time for 15 machines before and after a SMED workshop. |

## Example output (Excel, Python and R agree)
    Paired t-Test  —  TheQualityVault.com
    Pairs                                         15
    Mean difference                          2.61333
    StDev difference                          1.8392
    t                                        5.50314
    DF                                            14
    P-value                              7.77915e-05
    CI lower                                 1.59482
    CI upper                                 3.63185
    p = 0.0001 < 0.05 → reject H0: the mean difference is not 0.

## Run
    python paired_t.py demo
    python paired_t.py --csv my_data.csv --cols Before After --mu0 0
    Rscript paired_t.R
