# ==============================================================================
# chi_square_gof.R  —  TheQualityVault.com
# Chi-Square Goodness of Fit
#
# Tests whether observed counts in k categories match expected proportions (e.g. equal, or a
# historical mix). Reports chi-square, p-value and each category's contribution.
#
# Same results as the Excel workbook (Chi_Square_Goodness_of_Fit.xlsx) and chi_square_gof.py.  Base R only.
#
#   source("chi_square_gof.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, c("Category", "Observed", "Expected")))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, alpha = 0.05) {
  d <- d[complete.cases(d[cols]), ]
  o <- as.numeric(d[[cols[2]]]); w <- as.numeric(d[[cols[3]]])
  ct <- chisq.test(o, p = w, rescale.p = TRUE); p <- ct$p.value
  print(data.frame(Category = d[[cols[1]]], Observed = o, Expected = round(ct$expected, 2),
                   Contribution = round((o - ct$expected)^2 / ct$expected, 3)))
  list(`Categories k` = length(o), N = sum(o), `Chi-square` = unname(ct$statistic), DF = length(o) - 1, `P-value` = p,
       `Smallest expected count` = min(ct$expected),
       conclusion = if (p < alpha) sprintf("p = %.4f < %g -> reject H0: the counts do not follow the expected proportions.", p, alpha)
                    else sprintf("p = %.4f >= %g -> fail to reject H0: counts are consistent with the expected proportions.", p, alpha))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  Chi-Square Goodness of Fit  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
  for (k in setdiff(names(res), "conclusion")) {
    v <- res[[k]]
    cat(sprintf("  %-34s%14s\n", k, if (is.numeric(v)) format(signif(v, 6), big.mark = ",") else v))
  }
  cat("  ", res$conclusion, "\n", strrep("=", 62), "\n\n", sep = "")
  invisible(res)
}

demo <- function() {
  d <- read.csv("example_data.csv", check.names = FALSE)
  report(analyze(d, names(d)))
}

if (sys.nframe() == 0) demo()
