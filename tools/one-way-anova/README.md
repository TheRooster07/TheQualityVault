# One-Way ANOVA — TheQualityVault.com

Tests whether the means of k groups are all equal (one factor). Reports the ANOVA table, R², pooled standard deviation and group confidence intervals. Python/R also print Tukey comparisons.

## Files
| File | What it is |
|---|---|
| One_Way_ANOVA.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| one_way_anova.py | Python version (numpy, pandas, scipy) |
| one_way_anova.R | R version (base R only) |
| example_data.csv | Example data: tensile strength from 4 suppliers, 8 samples each. |

## Example output (Excel, Python and R agree)
    Supplier A           n=8    mean=51.2500  CI=(49.6081, 52.8919)
    Supplier B           n=8    mean=54.6500  CI=(53.0081, 56.2919)
    Supplier C           n=8    mean=52.5125  CI=(50.8706, 54.1544)
    Supplier D           n=8    mean=56.0750  CI=(54.4331, 57.7169)
    Tukey HSD pairwise comparisons:
    Pairwise Group Comparisons (95.0% Confidence Interval)
    Comparison  Statistic  p-value  Lower CI  Upper CI
    (0 - 1)     -3.400     0.027    -6.495    -0.305
    (0 - 2)     -1.263     0.684    -4.358     1.833
    (0 - 3)     -4.825     0.001    -7.920    -1.730
    (1 - 0)      3.400     0.027     0.305     6.495
    (1 - 2)      2.138     0.257    -0.958     5.233
    (1 - 3)     -1.425     0.597    -4.520     1.670
    (2 - 0)      1.263     0.684    -1.833     4.358
    (2 - 1)     -2.138     0.257    -5.233     0.958
    (2 - 3)     -3.562     0.019    -6.658    -0.467
    (3 - 0)      4.825     0.001     1.730     7.920
    (3 - 1)      1.425     0.597    -1.670     4.520
    (3 - 2)      3.562     0.019     0.467     6.658
    One-Way ANOVA  —  TheQualityVault.com
    Groups k                                       4
    N                                             32
    SS Factor                                111.451
    SS Error                                 143.924
    DF Factor                                      3
    DF Error                                      28
    F                                         7.2275
    P-value                              0.000972411
    R-sq                                    0.436421
    Pooled StDev                             2.26719
    p = 0.0010 < 0.05 → reject H0: at least one mean differs.

## Run
    python one_way_anova.py demo
    python one_way_anova.py --csv my_data.csv --cols "Supplier A" "Supplier B" "Supplier C"
    Rscript one_way_anova.R
