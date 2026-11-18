# 2-Sample t-Test — TheQualityVault.com

Compares the means of two independent samples. Reports both the pooled (equal variances) and the Welch (unequal variances) t-test with confidence intervals for the difference.

## Files
| File | What it is |
|---|---|
| 2_Sample_t_Test.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| two_sample_t.py | Python version (numpy, pandas, scipy) |
| two_sample_t.R | R version (base R only) |
| example_data.csv | Example data: cycle times on two production lines (15 and 18 observations). |

## Example output (Excel, Python and R agree)
    2-Sample t-Test  —  TheQualityVault.com
    n1                                            15
    n2                                            18
    Mean 1                                   41.3267
    Mean 2                                   45.4889
    StDev 1                                  2.70488
    StDev 2                                   3.6556
    Difference                              -4.16222
    t (pooled)                              -3.65118
    DF (pooled)                                   31
    P-value (pooled)                     0.000953063
    CI lower (pooled)                        -6.4872
    CI upper (pooled)                       -1.83724
    t (Welch)                               -3.75269
    DF (Welch)                               30.6244
    P-value (Welch)                      0.000732613
    CI lower (Welch)                        -6.42543
    CI upper (Welch)                        -1.89901
    Welch p = 0.0007 < 0.05 → reject H0: the means differ.

## Run
    python two_sample_t.py demo
    python two_sample_t.py --csv my_data.csv --cols "Line 1" "Line 2" --alternative two-sided
    Rscript two_sample_t.R
