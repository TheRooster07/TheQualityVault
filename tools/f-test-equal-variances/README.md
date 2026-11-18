# F-Test for Equal Variances — TheQualityVault.com

Tests whether two normal populations have the same variance. F = s1² / s2². Two-sided p-value and a confidence interval for the variance ratio.

## Files
| File | What it is |
|---|---|
| F_Test_Equal_Variances.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| f_test.py | Python version (numpy, pandas, scipy) |
| f_test.R | R version (base R only) |
| example_data.csv | Example data: diameters from two machines, 16 parts each. |

## Example output (Excel, Python and R agree)
    F-Test for Equal Variances  —  TheQualityVault.com
    n1                                            16
    n2                                            16
    StDev 1                                  0.64167
    StDev 2                                  0.81608
    F                                       0.618241
    DF1                                           15
    DF2                                           15
    P-value                                 0.362003
    Ratio CI lower                           0.21601
    Ratio CI upper                           1.76946
    p = 0.3620 ≥ 0.05 → fail to reject H0: no evidence the variances differ.

## Run
    python f_test.py demo
    python f_test.py --csv my_data.csv --cols "Machine A" "Machine B"
    Rscript f_test.R
