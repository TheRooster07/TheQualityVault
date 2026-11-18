# Chi-Square Goodness of Fit — TheQualityVault.com

Tests whether observed counts in k categories match expected proportions (e.g. equal, or a historical mix). Reports chi-square, p-value and each category's contribution.

## Files
| File | What it is |
|---|---|
| Chi_Square_Goodness_of_Fit.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| chi_square_gof.py | Python version (numpy, pandas, scipy) |
| chi_square_gof.R | R version (base R only) |
| example_data.csv | Example data: defects found on each weekday, tested against an even 20% per day. |

## Example output (Excel, Python and R agree)
    Mon              observed       34  expected     26.80  contribution    1.934
    Tue              observed       22  expected     26.80  contribution    0.860
    Wed              observed       19  expected     26.80  contribution    2.270
    Thu              observed       21  expected     26.80  contribution    1.255
    Fri              observed       38  expected     26.80  contribution    4.681
    Chi-Square Goodness of Fit  —  TheQualityVault.com
    Categories k                                   5
    N                                            134
    Chi-square                                    11
    DF                                             4
    P-value                                 0.026564
    Smallest expected count                     26.8
    p = 0.0266 < 0.05 → reject H0: the counts do not follow the expected proportions.

## Run
    python chi_square_gof.py demo
    python chi_square_gof.py --csv my_data.csv --cols Category Observed Expected
    Rscript chi_square_gof.R
