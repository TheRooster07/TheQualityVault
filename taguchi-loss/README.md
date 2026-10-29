# Taguchi Loss Function Toolkit — TheQualityVault.com

Calculate Taguchi quality loss for Nominal-Is-Best, Larger-Is-Better and
Smaller-Is-Better characteristics — single value or full batch — in Python or R.
The Excel, Python and R versions give identical results.

## Files

| File | What it is |
|---|---|
| `taguchi_loss.py` | Python library + command line (numpy, pandas, matplotlib) |
| `taguchi_loss.R` | R version — base R only, no packages needed |
| `taguchi_loss_calculator.xlsx` | Excel workbook — NIB, LIB, SIB sheets with live formulas and charts |
| `example_data.csv` | 30 units: `fill_weight_g`, `bond_strength_mpa`, `leak_rate_ccm` |
| `taguchi_example_python.png` / `taguchi_example_R.png` | Output of the worked example |

## Formulas

| Type | Loss | Constant |
|---|---|---|
| Nominal-Is-Best | L(y) = k(y − m)² | k = A₀ / Δ² |
| Larger-Is-Better | L(y) = k / y² | k = A₀ · m² |
| Smaller-Is-Better | L(y) = k · y² | k = A₀ / m² |

For NIB batches the average loss splits into **spread** k·σ² and **off-target** k·(ȳ − m)²,
telling you whether to reduce variation or simply re-centre the process.

## Python

```
pip install numpy pandas matplotlib          # openpyxl too, for Excel files
python taguchi_loss.py demo                  # worked example
python taguchi_loss.py nib --target 500 --delta 10 --A0 2.50 --y 506
python taguchi_loss.py nib --target 500 --delta 10 --A0 2.50 --csv example_data.csv --column fill_weight_g --save nib.png --export nib_results.csv
python taguchi_loss.py lib --m 80 --A0 400 --csv example_data.csv --column bond_strength_mpa --plot
python taguchi_loss.py sib --m 5 --A0 300 --excel mydata.xlsx --column 0 --sheet 0
```

## R

```r
# terminal
Rscript taguchi_loss.R demo

# R / RStudio
source("taguchi_loss.R")
nib <- taguchi_calc("nib", target = 500, delta = 10, A0 = 2.50)
taguchi_eval(nib, 506)
b <- taguchi_from_csv(nib, "example_data.csv", "fill_weight_g")
print(b); taguchi_plot(nib, b); taguchi_export_csv(b, "nib_results.csv")
```

## Worked example results (Excel, Python and R)

| Characteristic | Type | Spec / A₀ | Mean | E[L] per unit | Batch of 30 |
|---|---|---|---|---|---|
| Fill weight (g) | NIB | 500 ± 10, $2.50 | 502.49 | $0.3819 | $11.46 |
| Bond strength (MPa) | LIB | ≥ 80, $400 | 96.20 | $284.71 | $8,541.19 |
| Leak rate (ccm) | SIB | ≤ 5, $300 | 2.06 | $80.42 | $2,412.74 |

Live calculator: https://thequalityvault.com/taguchi-loss/
