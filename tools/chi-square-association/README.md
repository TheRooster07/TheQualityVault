# Chi-Square Test of Association — TheQualityVault.com

Tests independence in an r × c table of counts (e.g. defect type × shift). Reports chi-square, p-value, expected counts and how many cells have expected counts below 5.

## Files
| File | What it is |
|---|---|
| Chi_Square_Association.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| chi_square_association.py | Python version (numpy, pandas, scipy) |
| chi_square_association.R | R version (base R only) |
| example_data.csv | Example data: defect type by shift (3 × 3). |

## Example output (Excel, Python and R agree)
    Expected counts:
    Shift 1  Shift 2  Shift 3
    Defect type
    Scratch        19.73    21.67    23.60
    Dent           17.61    19.33    21.06
    Misalign       13.66    15.00    16.34
    Chi-Square Test of Association  —  TheQualityVault.com
    Rows                                           3
    Columns                                        3
    N                                            168
    Chi-square                               11.0056
    DF                                             4
    P-value                                0.0265009
    Cells expected < 5                             0
    p = 0.0265 < 0.05 → reject H0: the variables are associated.

## Run
    python chi_square_association.py demo
    python chi_square_association.py --csv my_data.csv --cols "Defect type" "Shift 1" "Shift 2" "Shift 3"
    Rscript chi_square_association.R
