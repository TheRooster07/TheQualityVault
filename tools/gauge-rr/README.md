# Gauge R&R (ANOVA Method) — TheQualityVault.com

Crossed Gauge R&R study analysed by two-way ANOVA (AIAG MSA): variance components,
%Contribution, %Study Variation, %Tolerance and number of distinct categories (ndc).
Excel, Python and R give identical results.

## Files
| File | What it is |
|---|---|
| Gauge_RR_ANOVA.xlsx | Excel tool — tabs: How to Use, Example, Blank Template, Python Code, R Code. Up to 20 parts × 4 operators × 4 trials. No macros. |
| gauge_rr.py | Python version (numpy, pandas, scipy, matplotlib) |
| gauge_rr.R | R version (base R only) |
| example_data.csv | Example study in long format: part, operator, trial, measurement (10 × 3 × 3) |
| gauge_rr_example_python.png / gauge_rr_example_R.png | Example output charts |

## Example results (tolerance 3.0)
| Measure | Value |
|---|---|
| %Study Var — Total Gage R&R | 21.2 % |
| %Tolerance — Total Gage R&R | 17.3 % |
| %Contribution — Total Gage R&R | 4.5 % |
| ndc | 6 |
| Part × Operator | not significant (p = 0.70) — pooled |
| Verdict | Marginal |

## Run
    python gauge_rr.py demo
    python gauge_rr.py --csv my_study.csv --part part --operator operator --value measurement --tolerance 3.0 --save grr.png
    Rscript gauge_rr.R

## Notes
Study must be balanced. Study variation = 6 × SD. Interaction pooled when p ≥ alpha (default 0.05).
In the Excel chart helper columns, N/A values are deliberate — they hide unused parts on the interaction chart.
