# Mann-Whitney U Test — TheQualityVault.com

Rank-based test that two independent samples come from the same distribution (often read as 'equal medians'). Normal approximation with tie correction and continuity correction.

## Files
| File | What it is |
|---|---|
| Mann_Whitney_U.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| mann_whitney.py | Python version (numpy, pandas, scipy) |
| mann_whitney.R | R version (base R only) |
| example_data.csv | Example data: repair turnaround times for two vendors (skewed). |

## Example output (Excel, Python and R agree)
    Mann-Whitney U Test  —  TheQualityVault.com
    n1                                            12
    n2                                            14
    Median 1                                    2.05
    Median 2                                     5.1
    U (sample 1)                                  55
    P-value                                 0.142134
    p = 0.1421 ≥ 0.05 → fail to reject H0: no evidence the distributions differ.

## Run
    python mann_whitney.py demo
    python mann_whitney.py --csv my_data.csv --cols "Vendor A" "Vendor B"
    Rscript mann_whitney.R
