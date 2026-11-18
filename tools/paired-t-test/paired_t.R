# ==============================================================================
# paired_t.R  —  TheQualityVault.com
# Paired t-Test
#
# Tests whether the mean of paired differences (first − second) differs from a hypothesised
# difference (usually 0). Each row is one unit measured twice.
#
# Same results as the Excel workbook (Paired_t_Test.xlsx) and paired_t.py.  Base R only.
#
#   source("paired_t.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, c("Before", "After"), mu0 = 0))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, mu0 = 0, alternative = "two-sided", alpha = 0.05) {
  alternative <- sub("-", ".", alternative)
  a <- suppressWarnings(as.numeric(d[[cols[1]]])); b <- suppressWarnings(as.numeric(d[[cols[2]]]))
  ok <- !is.na(a) & !is.na(b); diff <- a[ok] - b[ok]
  tt <- t.test(diff, mu = mu0, alternative = alternative)
  ci <- t.test(diff, mu = mu0, conf.level = 1 - alpha)$conf.int; p <- tt$p.value
  list(Pairs = length(diff), `Mean difference` = mean(diff), `StDev difference` = sd(diff), t = unname(tt$statistic),
       DF = length(diff) - 1, `P-value` = p, `CI lower` = ci[1], `CI upper` = ci[2],
       conclusion = if (p < alpha) sprintf("p = %.4f < %g -> reject H0: the mean difference is not %g.", p, alpha, mu0)
                    else sprintf("p = %.4f >= %g -> fail to reject H0: no evidence of a difference.", p, alpha))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  Paired t-Test  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
  for (k in setdiff(names(res), "conclusion")) {
    v <- res[[k]]
    cat(sprintf("  %-34s%14s\n", k, if (is.numeric(v)) format(signif(v, 6), big.mark = ",") else v))
  }
  cat("  ", res$conclusion, "\n", strrep("=", 62), "\n\n", sep = "")
  invisible(res)
}

demo <- function() {
  d <- read.csv("example_data.csv", check.names = FALSE)
  report(analyze(d, c("Before (min)", "After (min)"), mu0 = 0))
}

if (sys.nframe() == 0) demo()
