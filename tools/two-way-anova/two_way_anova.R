# ==============================================================================
# two_way_anova.R  —  TheQualityVault.com
# Two-Way ANOVA
#
# Balanced two-factor ANOVA with interaction: tests factor A, factor B and A × B.
# Input is a long table: one row per observation with the A level, B level and response.
#
# Same results as the Excel workbook (Two_Way_ANOVA.xlsx) and two_way_anova.py.  Base R only.
#
#   source("two_way_anova.R"); demo()
#   d <- read.csv("my_data.csv"); report(analyze(d, c("A", "B", "Y")))
# ==============================================================================

num <- function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] }

analyze <- function(d, cols, alpha = 0.05) {
  d <- d[complete.cases(d[cols]), ]
  A <- factor(d[[cols[1]]]); B <- factor(d[[cols[2]]]); y <- as.numeric(d[[cols[3]]])
  s <- summary(aov(y ~ A * B))[[1]]
  sig <- c("A", "B", "AxB")[s[1:3, "Pr(>F)"] < alpha]
  list(`Levels A` = nlevels(A), `Levels B` = nlevels(B), Replicates = length(y) / (nlevels(A) * nlevels(B)),
       `SS A` = s[1, 2], `SS B` = s[2, 2], `SS AxB` = s[3, 2], `SS Error` = s[4, 2],
       `F A` = s[1, 4], `P A` = s[1, 5], `F B` = s[2, 4], `P B` = s[2, 5], `F AxB` = s[3, 4], `P AxB` = s[3, 5],
       `R-sq` = sum(s[1:3, 2]) / sum(s[, 2]),
       conclusion = if (length(sig)) paste0("Significant at ", alpha, ": ", paste(sig, collapse = ", "), " -> those effects matter.")
                    else paste0("-> No factor or interaction is significant at ", alpha, "."))
}


report <- function(res) {
  cat("\n", strrep("=", 62), "\n  Two-Way ANOVA  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
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
