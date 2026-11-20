# Repairable Systems & Replacement Age — TheQualityVault.com

For a fleet of repairable units: how failures build up with age (mean cumulative function), whether
units wear out (power-law NHPP fitted by maximum likelihood, with staggered start dates and retirements),
which units fail far more than the rest (bad actors), the replacement age with the lowest long-run cost,
and a keep / plan / replace recommendation for every unit still in service. Data can be entered as dates
or ages. Excel, Python and R give identical results.

## Files
| File | What it is |
|---|---|
| Repairable_Systems_Replacement_Age.xlsx | Tabs: How to Use, Example (40 pumps, dates), Blank Template (2,000 events, 600 units), Python Code, R Code. No macros. |
| repairable_systems.py | Python version (numpy, pandas, scipy, matplotlib) |
| repairable_systems.R | R version (base R only) |
| example_data.csv | One row per event: unit, event (I/S/F/E/R), date, age |
| repairable_systems_example_python.png / repairable_systems_example_R.png | Example output charts |

## Event codes
I installed · S records start (optional) · F failure, repaired · E end of observation, still in service · R retired.
Every unit needs one E or R row; units that never failed still count. Give each row a date or an age.

## Example (40 pumps, records 2016–2025, replacement 45,000, repair 6,000, 3-year look-ahead)
| Measure | Value |
|---|---|
| Units / failures | 40 (32 in service, 8 retired) / 89 |
| β (MLE) and 95% bounds | 2.05 (1.72 – 2.44) → wear-out |
| Laplace U / p | 2.29 / 0.022 |
| Optimum replacement age T* | 16.6 years |
| Lowest cost per pump-year | 5,290 |
| Replace now / plan within 3 years | 4 / 5 pumps |
| Bad actor | PMP-18: 16 failures vs 4.7 expected |

## Run
    python repairable_systems.py demo
    python repairable_systems.py --csv fleet.csv --replace-cost 45000 --repair-cost 6000 --horizon 3 --export units.csv
    Rscript repairable_systems.R

## Method
MCF (Nelson) with log-scale Poisson bounds. ρ(t) = λβt^(β−1), each unit observed from age a to b:
λ = N/Σ(b^β − a^β); β solves N/β + Σ ln t − N·Σ(b^β ln b − a^β ln a)/Σ(b^β − a^β) = 0; bounds on β from the
profile-likelihood information. Laplace U = Σ(t − (a+b)/2)/√(Σ n(b−a)²/12). Bad actor: Poisson P(X ≥ n).
Minimal repair with replacement at age T: C(T) = (Cp + Cr·λT^β)/T, T* = [Cp/(Cr·λ(β−1))]^(1/β) for β > 1
(Barlow–Hunter). Assumes the units are alike – analyse different models, duties or sites separately.
