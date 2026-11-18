# ==============================================================================
# mann_whitney.R  —  TheQualityVault.com
# Mann-Whitney U Test
#
# Rank-based test that two independent samples come from the same distribution (often read as
# 'equal medians'). Normal approximation with tie correction and continuity correction.
#
# Same results as the Excel workbook (Mann_Whitney_U.xlsx) and mann_whitney.py.  Base R only.
#
#   source("mann_whitney.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, c("Vendor A", "Vendor B")))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, alpha = 0.05) {
  a <- num(d[[cols[1]]]); b <- num(d[[cols[2]]])
  w <- wilcox.test(a, b, exact = FALSE, correct = TRUE); p <- w$p.value
  list(n1 = length(a), n2 = length(b), `Median 1` = median(a), `Median 2` = median(b), `U (sample 1)` = unname(w$statistic),
       `P-value` = p,
       conclusion = if (p < alpha) sprintf("p = %.4f < %g -> reject H0: the distributions differ.", p, alpha)
                    else sprintf("p = %.4f >= %g -> fail to reject H0: no evidence the distributions differ.", p, alpha))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  Mann-Whitney U Test  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
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
