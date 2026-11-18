# ==============================================================================
# bartlett_test.R  —  TheQualityVault.com
# Bartlett's Test
#
# Tests whether k normal populations have equal variances (more powerful than Levene when data
# are normal, but sensitive to non-normality).
#
# Same results as the Excel workbook (Bartlett_Test.xlsx) and bartlett_test.py.  Base R only.
#
#   source("bartlett_test.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, c("A", "B", "C")))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, alpha = 0.05) {
  gs <- lapply(cols, function(c) num(d[[c]])); g <- factor(rep(cols, lengths(gs)), levels = cols)
  b <- bartlett.test(unlist(gs), g); p <- b$p.value; N <- length(g); k <- length(cols)
  list(`Groups k` = k, N = N, `Pooled variance` = sum((lengths(gs) - 1) * sapply(gs, var)) / (N - k),
       `Chi-square` = unname(b$statistic), DF = k - 1, `P-value` = p,
       conclusion = if (p < alpha) sprintf("p = %.4f < %g -> reject H0: the variances differ.", p, alpha)
                    else sprintf("p = %.4f >= %g -> fail to reject H0: no evidence the variances differ.", p, alpha))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  Bartlett's Test  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
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
