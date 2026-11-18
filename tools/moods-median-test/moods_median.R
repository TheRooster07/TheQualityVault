# ==============================================================================
# moods_median.R  —  TheQualityVault.com
# Mood's Median Test
#
# Counts how many values in each group lie above / at-or-below the grand median and runs a
# chi-square test on that table. Very robust to outliers.
#
# Same results as the Excel workbook (Moods_Median_Test.xlsx) and moods_median.py.  Base R only.
#
#   source("moods_median.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, c("A", "B", "C")))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, alpha = 0.05) {
  gs <- lapply(cols, function(c) num(d[[c]])); y <- unlist(gs); g <- factor(rep(cols, lengths(gs)), levels = cols)
  med <- median(y); tb <- table(y > med, g)
  ct <- suppressWarnings(chisq.test(tb, correct = FALSE)); p <- ct$p.value
  list(`Groups k` = length(cols), `Grand median` = med, `Chi-square` = unname(ct$statistic), DF = length(cols) - 1, `P-value` = p,
       conclusion = if (p < alpha) sprintf("p = %.4f < %g -> reject H0: the medians differ.", p, alpha)
                    else sprintf("p = %.4f >= %g -> fail to reject H0: no evidence the medians differ.", p, alpha))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  Mood's Median Test  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
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
