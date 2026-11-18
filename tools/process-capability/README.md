# Process Capability Calculator — TheQualityVault.com

Cp, Cpk, Pp, Ppk, Cpm, expected and observed PPM, Z.bench and an Anderson-Darling
normality check — in Excel, Python and R. All three give identical results.

## Files
| File | What it is |
|---|---|
| Process_Capability_Calculator.xlsx | Excel tool — tabs: How to Use, Example, Blank Template, Python Code, R Code. Formulas only, no macros. |
| process_capability.py | Python version (numpy, pandas, scipy, matplotlib) |
| process_capability.R | R version (base R, no packages) |
| example_data.csv | Example data: 125 shaft diameters (mm), 25 subgroups of 5 |
| capability_example_python.png / capability_example_R.png | Example output charts |

## Example (spec 10.00 ± 0.05 mm, subgroup size 5)
| Index | Value |
|---|---|
| Cp / Cpk | 1.46 / 1.31 |
| Pp / Ppk | 1.30 / 1.17 |
| Cpm | 1.21 |
| Expected PPM (overall) | 237 |
| Anderson-Darling p | 0.767 (normal) |
| Verdict | Marginal — reduce variation or re-centre |

## Run
    python process_capability.py demo
    python process_capability.py --csv my_data.csv --column 0 --lsl 9.95 --usl 10.05 --subgroup-size 5 --save cap.png
    Rscript process_capability.R            # runs the demo

## Method
σ within = MR-bar/1.128 (individuals) or R-bar/d2 (subgroups 2–10, complete subgroups only).
σ overall = sample standard deviation. Anderson-Darling p-value per D'Agostino & Stephens (1986).
Indices assume a stable, normally distributed process — check a control chart first.
