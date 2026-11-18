# Two-Way ANOVA — TheQualityVault.com

Balanced two-factor ANOVA with interaction: tests factor A, factor B and A × B. Input is a long table: one row per observation with the A level, B level and response.

## Files
| File | What it is |
|---|---|
| Two_Way_ANOVA.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| two_way_anova.py | Python version (numpy, pandas, scipy) |
| two_way_anova.R | R version (base R only) |
| example_data.csv | Example data: output of 3 machines on 2 shifts, 4 runs per combination. |

## Example output (Excel, Python and R agree)
    Two-Way ANOVA  —  TheQualityVault.com
    Levels A                                       3
    Levels B                                       2
    Replicates                                     4
    SS A                                     95.0077
    SS B                                       29.04
    SS AxB                                   10.0016
    SS Error                                 49.2286
    F A                                      17.3694
    P A                                  6.28473e-05
    F B                                      10.6182
    P B                                   0.00436234
    F AxB                                    1.82849
    P AxB                                   0.189265
    R-sq                                    0.731399
    Significant at 0.05: A, B → those effects matter.

## Run
    python two_way_anova.py demo
    python two_way_anova.py --csv my_data.csv --cols Machine Shift Output
    Rscript two_way_anova.R
