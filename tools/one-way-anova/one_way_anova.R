# ==============================================================================
# one_way_anova.R  —  TheQualityVault.com
# One-Way ANOVA
#
# Tests whether the means of k groups are all equal (one factor). Reports the ANOVA table,
# R², pooled standard deviation and group confidence intervals. Python/R also print Tukey comparisons.
#
# Same results as the Excel workbook (One_Way_ANOVA.xlsx) and one_way_anova.py.  Base R only.
#
#   source("one_way_anova.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, c("A", "B", "C")))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, alpha = 0.05) {
  y <- unlist(lapply(cols, function(c) num(d[[c]])))
  g <- factor(rep(cols, sapply(cols, function(c) length(num(d[[c]])))), levels = cols)
  fit <- aov(y ~ g); s <- summary(fit)[[1]]
  print(TukeyHSD(fit, conf.level = 1 - alpha))
  p <- s[1, "Pr(>F)"]
  list(`Groups k` = nlevels(g), N = length(y), `SS Factor` = s[1, "Sum Sq"], `SS Error` = s[2, "Sum Sq"],
       `DF Factor` = s[1, "Df"], `DF Error` = s[2, "Df"], F = s[1, "F value"], `P-value` = p,
       `R-sq` = s[1, "Sum Sq"] / sum(s[, "Sum Sq"]), `Pooled StDev` = sqrt(s[2, "Mean Sq"]),
       conclusion = if (p < alpha) sprintf("p = %.4f < %g -> reject H0: at least one mean differs.", p, alpha)
                    else sprintf("p = %.4f >= %g -> fail to reject H0: no evidence the means differ.", p, alpha))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  One-Way ANOVA  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
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
