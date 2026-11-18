# Fisher's Exact Test — TheQualityVault.com

Exact test of association for a 2 × 2 table of counts. Use it instead of the chi-square test when
counts are small (any expected count below 5). Reports two-sided and one-sided p-values and the odds ratio.

## Files
| File | What it is |
|---|---|
| Fisher_Exact_Test.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| fisher_exact.py | Python version (scipy) |
| fisher_exact.R | R version (base R) – also tests larger r × c tables exactly |
| example_data.csv | Pass / fail counts for two suppliers |

## When the result is N/A (cause is always stated)
| Version | N/A when |
|---|---|
| Excel | table larger than 2 × 2; counts not whole numbers ≥ 0; 2 × 2 counts so large that more than 1,001 tables would have to be enumerated |
| Python | table larger than 2 × 2 (scipy supports 2 × 2 only) |
| R | table too large for fisher.test's exact algorithm (error message reported) |

## Example output (Excel, Python and R agree)
      Fisher's Exact Test  —  TheQualityVault.com
      Rows                                           2
      Columns                                        2
      N                                             95
      Odds ratio                               5.44737
      P-value (two-sided)                    0.0273174
      P-value (less)                          0.996594
      P-value (greater)                      0.0230911
      p = 0.0273 < 0.05 → reject H0: the row and column variables are associated.
    

## Run
    python fisher_exact.py demo
    python fisher_exact.py --csv my_table.csv --cols Label Col1 Col2
    Rscript fisher_exact.R
