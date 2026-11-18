# Weibull Life Data Analysis — TheQualityVault.com

2-parameter Weibull fit with suspensions (units still running): shape β, characteristic life η,
B1/B10/B50 life, MTTF and reliability at a chosen time — by median rank regression (MRR) and
maximum likelihood (MLE). Excel, Python and R give identical results.

## Files
| File | What it is |
|---|---|
| Weibull_Analysis.xlsx | Tabs: How to Use, Example (20 pump bearings, 15 failures, 5 suspensions), Blank Template (200 units), Python Code, R Code. No macros. |
| weibull.py | Python version (numpy, pandas, scipy, matplotlib) |
| weibull.R | R version (base R only) |
| example_data.csv | unit, hours, status (F = failed, S = suspended) |
| weibull_example_python.png / weibull_example_R.png | Probability plot and reliability curve |

## Example results
| | MRR | MLE |
|---|---|---|
| β | 2.683 | 2.644 |
| η (hours) | 2,178 | 2,197 |
| B10 life | 941 | 938 |
| MTTF | 1,937 | 1,952 |
| R(1,000 h) | 0.883 | 0.883 |
β > 1 → wear-out; plan preventive replacement.

## Run
    python weibull.py demo
    python weibull.py --csv my_data.csv --time hours --status status --at 1000 --save weibull.png
    Rscript weibull.R

## Notes
MRR: Johnson adjusted ranks, Benard median ranks, regression of x = ln t on y.  MLE: profile likelihood solved by bisection.
In the Excel chart-helper columns, N/A values are deliberate (they keep unused rows off the probability plot).
