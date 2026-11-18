# ==============================================================================
# wilcoxon_signed_rank.R  —  TheQualityVault.com
# Wilcoxon Signed Rank Test
#
# Tests whether the median of paired differences is zero (two columns) or whether one sample's
# median equals a target (one column). Zero differences are dropped; normal approximation with
# tie and continuity corrections.
#
# Same results as the Excel workbook (Wilcoxon_Signed_Rank.xlsx) and wilcoxon_signed_rank.py.  Base R only.
#
#   source("wilcoxon_signed_rank.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, c("Before", "After")))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, m0 = 0, alpha = 0.05) {
  if (length(cols) > 1) {
    a <- suppressWarnings(as.numeric(d[[cols[1]]])); b <- suppressWarnings(as.numeric(d[[cols[2]]]))
    ok <- !is.na(a) & !is.na(b); dd <- a[ok] - b[ok]
  } else dd <- num(d[[cols[1]]]) - m0
  dd <- round(dd, 10)
  dd <- dd[dd != 0]
  w <- wilcox.test(dd, exact = FALSE, correct = TRUE); p <- w$p.value
  list(`Non-zero differences` = length(dd), `Median difference` = median(dd), `W+` = unname(w$statistic), `P-value` = p,
       conclusion = if (p < alpha) sprintf("p = %.4f < %g -> reject H0: the median difference is not zero.", p, alpha)
                    else sprintf("p = %.4f >= %g -> fail to reject H0: no evidence of a difference.", p, alpha))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  Wilcoxon Signed Rank Test  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
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
