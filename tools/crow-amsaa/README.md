# Crow-AMSAA Reliability Growth — TheQualityVault.com

Tracks whether a design is getting more reliable as failures are found and fixed. Fits the Crow-AMSAA
(power-law NHPP) model by maximum likelihood for one system or several identical systems: shape β,
scale λ, bounds on β, Laplace trend test, instantaneous and cumulative MTBF, the test time needed to
reach a target MTBF, and a forecast of further failures. Excel, Python and R give identical results.

## Files
| File | What it is |
|---|---|
| Crow_AMSAA_Reliability_Growth.xlsx | Tabs: How to Use, Example (3 prototypes, 38 failures), Blank Template (300 rows), Python Code, R Code. Formulas only, no macros. |
| crow_amsaa.py | Python version (numpy, pandas, scipy, matplotlib) |
| crow_amsaa.R | R version (base R only) |
| example_data.csv | One row per event: system, time, event (F = failure, E = end of test) |
| crow_amsaa_example_python.png / crow_amsaa_example_R.png | Example output charts |

## Example (3 prototypes, tests ended at 1,800 / 1,650 / 1,500 h, target MTBF 350 h)
| Measure | Value |
|---|---|
| β (MLE) / unbiased | 0.528 / 0.515 |
| β 95% bounds | 0.374 – 0.709 |
| Laplace U / p | −3.60 / 0.0003 |
| Instantaneous MTBF at 1,800 h | 256.7 h |
| Cumulative MTBF (observed) | 130.3 h |
| Test time to reach 350 h MTBF | 3,475 h per system |
| Verdict | Reliability is growing |

## Run
    python crow_amsaa.py demo
    python crow_amsaa.py --csv my_test.csv --target-mtbf 350 --future 2500 --save growth.png
    Rscript crow_amsaa.R

## Method
N(t) = λ·t^β expected cumulative failures per system; instantaneous MTBF = 1/(λβt^(β−1)).
β solves N/β + Σ ln tᵢ − N·Σ T_q^β ln T_q / Σ T_q^β = 0 and λ = N / Σ T_q^β, where T_q is each system's
end of test. With one system, or equal end times, β = N / Σ ln(T/tᵢ). Unbiased β = (N−1)/N·β
(time-terminated) or (N−2)/N·β (failure-terminated); χ² bounds on β are exact for one system or equal end
times, approximate otherwise. A single system with no E row is treated as failure-terminated.
Reference: MIL-HDBK-189C. Grouped (interval) data is not supported in this version.
