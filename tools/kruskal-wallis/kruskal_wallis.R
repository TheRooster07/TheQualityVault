# ==============================================================================
# kruskal_wallis.R  —  TheQualityVault.com
# Kruskal-Wallis Test
#
# Rank-based test that k independent samples come from the same distribution (non-parametric
# one-way ANOVA). H statistic with tie correction, chi-square p-value.
#
# Same results as the Excel workbook (Kruskal_Wallis.xlsx) and kruskal_wallis.py.  Base R only.
#
#   source("kruskal_wallis.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, c("A", "B", "C")))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, alpha = 0.05) {
  gs <- lapply(cols, function(c) num(d[[c]])); g <- factor(rep(cols, lengths(gs)), levels = cols)
  k <- kruskal.test(unlist(gs), g); p <- k$p.value
  list(`Groups k` = length(cols), N = length(g), `H (tie-corrected)` = unname(k$statistic), DF = length(cols) - 1, `P-value` = p,
       conclusion = if (p < alpha) sprintf("p = %.4f < %g -> reject H0: at least one group differs.", p, alpha)
                    else sprintf("p = %.4f >= %g -> fail to reject H0: no evidence the groups differ.", p, alpha))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  Kruskal-Wallis Test  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
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
