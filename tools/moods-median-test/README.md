# Mood's Median Test — TheQualityVault.com

Counts how many values in each group lie above / at-or-below the grand median and runs a chi-square test on that table. Very robust to outliers.

## Files
| File | What it is |
|---|---|
| Moods_Median_Test.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| moods_median.py | Python version (numpy, pandas, scipy) |
| moods_median.R | R version (base R only) |
| example_data.csv | Example data: cycle times on three shifts, with two outliers. |

## Example output (Excel, Python and R agree)
    Mood's Median Test  —  TheQualityVault.com
    Groups k                                       3
    Grand median                                32.4
    Chi-square                               2.97849
    DF                                             2
    P-value                                 0.225543
    p = 0.2255 ≥ 0.05 → fail to reject H0: no evidence the medians differ.

## Run
    python moods_median.py demo
    python moods_median.py --csv my_data.csv --cols "Shift 1" "Shift 2" "Shift 3"
    Rscript moods_median.R
