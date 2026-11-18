# Linear Regression (simple and multiple) — TheQualityVault.com

Ordinary least-squares regression of one response on 1–5 predictors: coefficients, standard errors, t and p-values, R², adjusted R², standard error of the regression and the model F-test.

## Files
| File | What it is |
|---|---|
| Regression.xlsx | Tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| regression.py | Python version (numpy, pandas, scipy) |
| regression.R | R version (base R only) |
| example_data.csv | Example data: weld strength vs temperature, pressure and humidity (25 welds). |

## Example output (Excel, Python and R agree)
    Intercept      coef     9.250862  SE   5.428694  t    1.704  p 0.1031
    Temp           coef     0.181875  SE   0.025763  t    7.060  p 0.0000
    Pressure       coef     3.001068  SE   0.297975  t   10.072  p 0.0000
    Humidity       coef     0.082208  SE   0.066891  t    1.229  p 0.2327
    Linear Regression (simple and multiple)  —  TheQualityVault.com
    n                                             25
    Predictors k                                   3
    R-sq                                    0.929994
    R-sq (adj)                              0.919994
    S                                        1.50161
    F                                         92.992
    P-value (model)                      2.73925e-12
    Coef X1                                 0.181875
    P X1                                 5.75295e-07
    Model p = 0.0000 < 0.05 → the model explains a significant part of the variation (R² = 93.0%).

## Run
    python regression.py demo
    python regression.py --csv my_data.csv --cols Y X1 X2 X3
    Rscript regression.R
