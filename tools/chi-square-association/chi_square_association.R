# ==============================================================================
# chi_square_association.R  —  TheQualityVault.com
# Chi-Square Test of Association
#
# Tests independence in an r × c table of counts (e.g. defect type × shift). Reports chi-square,
# p-value, expected counts and how many cells have expected counts below 5.
#
# Same results as the Excel workbook (Chi_Square_Association.xlsx) and chi_square_association.py.  Base R only.
#
#   source("chi_square_association.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, names(d)))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, alpha = 0.05) {
  m <- as.matrix(d[, cols[-1]]); rownames(m) <- d[[cols[1]]]; m[is.na(m)] <- 0
  ct <- suppressWarnings(chisq.test(m, correct = FALSE)); p <- ct$p.value
  cat("  Expected counts:\n"); print(round(ct$expected, 2))
  list(Rows = nrow(m), Columns = ncol(m), N = sum(m), `Chi-square` = unname(ct$statistic), DF = unname(ct$parameter),
       `P-value` = p, `Cells expected < 5` = sum(ct$expected < 5),
       conclusion = if (p < alpha) sprintf("p = %.4f < %g -> reject H0: the variables are associated.", p, alpha)
                    else sprintf("p = %.4f >= %g -> fail to reject H0: no evidence of association.", p, alpha))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  Chi-Square Test of Association  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
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
