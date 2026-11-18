# ==============================================================================
# levene_test.R  —  TheQualityVault.com
# Levene's Test (Brown-Forsythe)
#
# Tests whether 2 or more groups have equal variances. Brown-Forsythe version: one-way ANOVA on
# the absolute deviations from each group's median – robust to non-normal data.
#
# Same results as the Excel workbook (Levene_Test.xlsx) and levene_test.py.  Base R only.
#
#   source("levene_test.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, c("A", "B", "C")))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, alpha = 0.05) {
  gs <- lapply(cols, function(c) num(d[[c]]))
  z <- unlist(lapply(gs, function(g) abs(g - median(g))))
  g <- factor(rep(cols, lengths(gs)), levels = cols)
  s <- summary(aov(z ~ g))[[1]]; p <- s[1, "Pr(>F)"]
  list(`Groups k` = length(cols), N = length(z), `W (F)` = s[1, "F value"], DF1 = s[1, "Df"], DF2 = s[2, "Df"], `P-value` = p,
       conclusion = if (p < alpha) sprintf("p = %.4f < %g -> reject H0: the variances differ.", p, alpha)
                    else sprintf("p = %.4f >= %g -> fail to reject H0: no evidence the variances differ.", p, alpha))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  Levene's Test (Brown-Forsythe)  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
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
