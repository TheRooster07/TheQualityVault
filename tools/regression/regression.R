# ==============================================================================
# regression.R  —  TheQualityVault.com
# Linear Regression (simple and multiple)
#
# Ordinary least-squares regression of one response on 1–5 predictors: coefficients, standard
# errors, t and p-values, R², adjusted R², standard error of the regression and the model F-test.
#
# Same results as the Excel workbook (Regression.xlsx) and regression.py.  Base R only.
#
#   source("regression.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, c("Y", "X1", "X2")))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, alpha = 0.05) {
  d <- d[complete.cases(d[cols]), cols]
  f <- as.formula(paste0("`", cols[1], "` ~ ", paste0("`", cols[-1], "`", collapse = " + ")))
  m <- lm(f, data = d); s <- summary(m); print(round(coef(s), 6))
  fs <- s$fstatistic; pF <- pf(fs[1], fs[2], fs[3], lower.tail = FALSE)
  list(n = nrow(d), `Predictors k` = length(cols) - 1, `R-sq` = s$r.squared, `R-sq (adj)` = s$adj.r.squared, S = s$sigma,
       F = unname(fs[1]), `P-value (model)` = unname(pF), `Coef X1` = coef(m)[[2]], `P X1` = coef(s)[2, 4],
       conclusion = if (pF < alpha) sprintf("Model p = %.4f < %g -> the model explains a significant part of the variation (R2 = %.1f%%).", pF, alpha, 100 * s$r.squared)
                    else sprintf("Model p = %.4f >= %g -> no evidence the X variables predict Y.", pF, alpha))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  Linear Regression (simple and multiple)  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
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
