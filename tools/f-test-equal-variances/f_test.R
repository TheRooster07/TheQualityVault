# ==============================================================================
# f_test.R  —  TheQualityVault.com
# F-Test for Equal Variances
#
# Tests whether two normal populations have the same variance. F = s1² / s2².
# Two-sided p-value and a confidence interval for the variance ratio.
#
# Same results as the Excel workbook (F_Test_Equal_Variances.xlsx) and f_test.py.  Base R only.
#
#   source("f_test.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, c("Machine A", "Machine B")))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, alpha = 0.05) {
  a <- num(d[[cols[1]]]); b <- num(d[[cols[2]]])
  v <- var.test(a, b, conf.level = 1 - alpha); p <- v$p.value
  list(n1 = length(a), n2 = length(b), `StDev 1` = sd(a), `StDev 2` = sd(b), F = unname(v$statistic),
       DF1 = length(a) - 1, DF2 = length(b) - 1, `P-value` = p, `Ratio CI lower` = v$conf.int[1], `Ratio CI upper` = v$conf.int[2],
       conclusion = if (p < alpha) sprintf("p = %.4f < %g -> reject H0: the variances differ.", p, alpha)
                    else sprintf("p = %.4f >= %g -> fail to reject H0: no evidence the variances differ.", p, alpha))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  F-Test for Equal Variances  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
  for (k in setdiff(names(res), "conclusion")) {
    v <- res[[k]]
    cat(sprintf("  %-34s%14s\n", k, if (is.numeric(v)) format(signif(v, 6), big.mark = ",") else v))
  }
  cat("  ", res$conclusion, "\n", strrep("=", 62), "\n\n", sep = "")
  invisible(res)
}

demo <- function() {
  d <- read.csv("example_data.csv", check.names = FALSE)
  report(analyze(d, c("Machine A", "Machine B")))
}

if (sys.nframe() == 0) demo()
