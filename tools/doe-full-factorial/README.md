# DOE — 2-Level Full Factorial Designer — TheQualityVault.com

Plan and analyse 2^k full factorial experiments (2–5 factors, 1–3 replicates): design matrix in
standard order, randomised run order, effects, coefficients, ANOVA (main effects + two-factor
interactions), R² and a Pareto of effects. Excel, Python and R give identical results.

## Files
| File | What it is |
|---|---|
| DOE_Full_Factorial_Designer.xlsx | Tabs: How to Use, Example (yield vs Temperature/Pressure/Time, 16 runs), Blank Template, Python Code, R Code. No macros. |
| doe_factorial.py | Python: `design()` + `analyze()` + plots (Pareto, main effects, interaction, residuals) |
| doe_factorial.R | R version (base R only) |
| example_data.csv | Example design with results (std order, run order, coded + actual levels, Yield) |
| doe_example_python.png / doe_example_R.png | Example output charts |

## Example result
Temperature effect +9.46, Pressure +4.96, Temperature×Pressure +4.90 (all p < 0.0001); Time not significant. R² = 98.3 %.

## Run
    python doe_factorial.py demo
    python doe_factorial.py design --factors Temp:150:180 Pressure:2:4 Time:10:20 --reps 2 --seed 7 --out plan.csv
    python doe_factorial.py analyze --csv plan_with_results.csv --response Y --save doe.png
    Rscript doe_factorial.R
