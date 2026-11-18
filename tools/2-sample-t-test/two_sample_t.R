# ==============================================================================
# two_sample_t.R  —  TheQualityVault.com
# 2-Sample t-Test
#
# Compares the means of two independent samples. Reports both the pooled (equal variances)
# and the Welch (unequal variances) t-test with confidence intervals for the difference.
#
# Same results as the Excel workbook (2_Sample_t_Test.xlsx) and two_sample_t.py.  Base R only.
#
#   source("two_sample_t.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, c("Line 1", "Line 2")))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, alternative = "two-sided", alpha = 0.05) {
  alternative <- sub("-", ".", alternative)
  a <- num(d[[cols[1]]]); b <- num(d[[cols[2]]])
  tp <- t.test(a, b, var.equal = TRUE, alternative = alternative)
  tw <- t.test(a, b, alternative = alternative)
  cp <- t.test(a, b, var.equal = TRUE, conf.level = 1 - alpha)$conf.int
  cw <- t.test(a, b, conf.level = 1 - alpha)$conf.int
  p <- tw$p.value
  list(n1 = length(a), n2 = length(b), `Mean 1` = mean(a), `Mean 2` = mean(b), `StDev 1` = sd(a), `StDev 2` = sd(b),
       Difference = mean(a) - mean(b), `t (pooled)` = unname(tp$statistic), `DF (pooled)` = unname(tp$parameter),
       `P-value (pooled)` = tp$p.value, `CI lower (pooled)` = cp[1], `CI upper (pooled)` = cp[2],
       `t (Welch)` = unname(tw$statistic), `DF (Welch)` = unname(tw$parameter), `P-value (Welch)` = p,
       `CI lower (Welch)` = cw[1], `CI upper (Welch)` = cw[2],
       conclusion = if (p < alpha) sprintf("Welch p = %.4f < %g -> reject H0: the means differ.", p, alpha)
                    else sprintf("Welch p = %.4f >= %g -> fail to reject H0: no evidence the means differ.", p, alpha))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  2-Sample t-Test  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
  for (k in setdiff(names(res), "conclusion")) {
    v <- res[[k]]
    cat(sprintf("  %-34s%14s\n", k, if (is.numeric(v)) format(signif(v, 6), big.mark = ",") else v))
  }
  cat("  ", res$conclusion, "\n", strrep("=", 62), "\n\n", sep = "")
  invisible(res)
}

demo <- function() {
  d <- read.csv("example_data.csv", check.names = FALSE)
  report(analyze(d, c("Line 1 (s)", "Line 2 (s)")))
}

if (sys.nframe() == 0) demo()
