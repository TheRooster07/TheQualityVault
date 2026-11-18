# 1-Sample t-Test — TheQualityVault.com

Tests whether the mean of one sample differs from a target value mu0. t = (x̄ − mu0) / (s/√n), df = n − 1. Reports t, p-value and a confidence interval for the mean.

## Files
| File | What it is |
|---|---|
| 1_Sample_t_Test.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| one_sample_t.py | Python version (numpy, pandas, scipy) |
| one_sample_t.R | R version (base R only) |
| example_data.csv | Example data: 20 tablet weights tested against the 250 mg target. |

## Example output (Excel, Python and R agree)
    1-Sample t-Test  —  TheQualityVault.com
    n                                             20
    Mean                                     251.335
    StDev                                    1.59251
    SE Mean                                 0.356095
    t                                          3.749
    DF                                            19
    P-value                               0.00135909
    CI lower                                  250.59
    CI upper                                  252.08
    p = 0.0014 < 0.05 → reject H0: the mean differs from 250.

## Run
    python one_sample_t.py demo
    python one_sample_t.py --csv my_data.csv --cols weight_mg --mu0 250 --alternative two-sided
    Rscript one_sample_t.R
