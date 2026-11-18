# Hypothesis Test Advisor — TheQualityVault.com

Answer up to 8 questions and get the right statistical test (26 covered), its null hypothesis,
assumptions, and the exact Excel, Python and R call. The Python and R scripts can also run the test.

## Files
| File | What it is |
|---|---|
| Hypothesis_Test_Advisor.xlsx | Tabs: How to Use, Example (two filling machines, with data and conclusion), Blank Template, Test Library, Python Code, R Code. No macros. |
| hypothesis_advisor.py | Python: interactive advisor + `recommend()` and `run_test()` (scipy) |
| hypothesis_advisor.R | R: `recommend()` and `run_test()` (base R) |

## Example
Machine A vs Machine B fill weight, 12 bottles each. Both normal (AD p = 0.95, 0.99), F-test p = 0.43 (equal variances)
→ 2-Sample t-Test (pooled), p = 0.00002 → Machine B fills about 1.5 g heavier.

## Run
    python hypothesis_advisor.py          # asks the questions
    python hypothesis_advisor.py demo
    Rscript hypothesis_advisor.R          # demo

The Excel decision logic was checked against the Python `recommend()` function on 60 random answer combinations.
