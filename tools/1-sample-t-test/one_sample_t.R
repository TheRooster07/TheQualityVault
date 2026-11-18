# ==============================================================================
# one_sample_t.R  —  TheQualityVault.com
# 1-Sample t-Test
#
# Tests whether the mean of one sample differs from a target value mu0.
# t = (x̄ − mu0) / (s/√n), df = n − 1. Reports t, p-value and a confidence interval for the mean.
#
# Same results as the Excel workbook (1_Sample_t_Test.xlsx) and one_sample_t.py.  Base R only.
#
#   source("one_sample_t.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, "weight_mg", mu0 = 250))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, col, mu0, alternative = "two-sided", alpha = 0.05) {
  alternative <- sub("-", ".", alternative)
  x <- num(d[[col]]); n <- length(x)
  tt <- t.test(x, mu = mu0, alternative = alternative)
  ci <- t.test(x, mu = mu0, conf.level = 1 - alpha)$conf.int
  p <- tt$p.value
  list(n = n, Mean = mean(x), StDev = sd(x), `SE Mean` = sd(x) / sqrt(n), t = unname(tt$statistic), DF = n - 1,
       `P-value` = p, `CI lower` = ci[1], `CI upper` = ci[2],
       conclusion = if (p < alpha) sprintf("p = %.4f < %g -> reject H0: the mean differs from %g.", p, alpha, mu0)
                    else sprintf("p = %.4f >= %g -> fail to reject H0: no evidence the mean differs from %g.", p, alpha, mu0))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  1-Sample t-Test  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
  for (k in setdiff(names(res), "conclusion")) {
    v <- res[[k]]
    cat(sprintf("  %-34s%14s\n", k, if (is.numeric(v)) format(signif(v, 6), big.mark = ",") else v))
  }
  cat("  ", res$conclusion, "\n", strrep("=", 62), "\n\n", sep = "")
  invisible(res)
}

demo <- function() {
  d <- read.csv("example_data.csv", check.names = FALSE)
  report(analyze(d, "Tablet weight (mg)", mu0 = 250))
}

if (sys.nframe() == 0) demo()
