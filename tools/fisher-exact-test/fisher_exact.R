# ==============================================================================
# fisher_exact.R  —  TheQualityVault.com
# Fisher's Exact Test
#
# Exact test of association for a 2 × 2 table – use instead of chi-square when counts are small
# (any expected count below 5). Reports two-sided and one-sided p-values and the odds ratio.
# Tables larger than 2 × 2: the R version tries an exact test; Excel and Python return N/A with the reason.
#
# Same results as the Excel workbook (Fisher_Exact_Test.xlsx) and fisher_exact.py.  Base R only.
#
#   source("fisher_exact.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, names(d)))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, alpha = 0.05) {
  m <- as.matrix(d[, cols[-1]]); rownames(m) <- d[[cols[1]]]; m[is.na(m)] <- 0
  na <- function(cause) list(Rows = nrow(m), Columns = ncol(m), `Odds ratio` = "N/A", `P-value (two-sided)` = "N/A",
                             conclusion = paste("N/A -", cause))
  if (nrow(m) < 2 || ncol(m) < 2) return(na("enter at least a 2 x 2 table."))
  if (all(dim(m) == 2)) {
    p2 <- fisher.test(m)$p.value
    pl <- fisher.test(m, alternative = "less")$p.value; pg <- fisher.test(m, alternative = "greater")$p.value
    orr <- if (m[1, 2] * m[2, 1] > 0) (m[1, 1] * m[2, 2]) / (m[1, 2] * m[2, 1]) else Inf
    return(list(Rows = 2, Columns = 2, N = sum(m), `Odds ratio` = orr, `P-value (two-sided)` = p2,
                `P-value (less)` = pl, `P-value (greater)` = pg,
                conclusion = if (p2 < alpha) sprintf("p = %.4f < %g -> reject H0: the row and column variables are associated.", p2, alpha)
                             else sprintf("p = %.4f >= %g -> fail to reject H0: no evidence of association.", p2, alpha)))
  }
  r <- tryCatch(fisher.test(m, workspace = 2e7), error = function(e) e)
  if (inherits(r, "error"))
    return(na(paste0("the ", nrow(m), " x ", ncol(m), " table is too large for an exact test (", trimws(gsub("[[:space:]]+", " ", conditionMessage(r))),
                     "). Merge categories or use the chi-square test.")))
  p2 <- r$p.value
  list(Rows = nrow(m), Columns = ncol(m), N = sum(m), `Odds ratio` = "N/A (only for 2 x 2)", `P-value (two-sided)` = p2,
       conclusion = if (p2 < alpha) sprintf("Exact r x c test: p = %.4f < %g -> reject H0: the variables are associated.", p2, alpha)
                    else sprintf("Exact r x c test: p = %.4f >= %g -> fail to reject H0: no evidence of association.", p2, alpha))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  Fisher's Exact Test  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
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
