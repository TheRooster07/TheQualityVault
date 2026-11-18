# ==============================================================================
# gauge_rr.R  —  TheQualityVault.com
# Gauge R&R — crossed study, ANOVA method (AIAG MSA). Base R only.
#
# Two-way ANOVA (Part, Operator, Part x Operator, Repeatability). If the
# interaction p-value >= alpha (default 0.05) it is pooled into repeatability.
# Reports variance components, %Contribution, %Study Var (6*SD), %Tolerance
# and ndc = floor(1.41 * SD_part / SD_GRR).
# AIAG: < 10% acceptable, 10-30% marginal, > 30% unacceptable; ndc >= 5.
#
# Same numbers as the Excel workbook and gauge_rr.py.
#
#   source("gauge_rr.R"); demo()
#   d <- read.csv("my_study.csv")
#   r <- gauge_rr(d$part, d$operator, d$measurement, tolerance = 3)
#   print_grr(r); plot_grr(r, file = "grr.png")
# ==============================================================================

NAVY <- "#1A2B5F"; GOLD <- "#C9A84C"; RED <- "#C0392B"; BLUE <- "#4472C4"

gauge_rr <- function(part, operator, y, tolerance = NULL, alpha = 0.05) {
  d <- data.frame(part = factor(part), operator = factor(operator), y = as.numeric(y))
  d <- d[complete.cases(d), ]
  tab <- table(d$part, d$operator)
  if (length(unique(as.vector(tab))) != 1) stop("Study must be balanced.")
  p <- nlevels(d$part); o <- nlevels(d$operator); r <- tab[1, 1]
  if (r < 2) stop("Need at least 2 trials per operator per part.")
  gm <- mean(d$y)
  ss_total <- sum((d$y - gm)^2)
  ss_part <- o * r * sum((tapply(d$y, d$part, mean) - gm)^2)
  ss_op <- p * r * sum((tapply(d$y, d$operator, mean) - gm)^2)
  cellm <- ave(d$y, d$part, d$operator)
  ss_rep <- sum((d$y - cellm)^2)
  ss_int <- ss_total - ss_part - ss_op - ss_rep
  df_p <- p - 1; df_o <- o - 1; df_i <- df_p * df_o; df_r <- p * o * (r - 1)
  ms_p <- ss_part / df_p; ms_o <- ss_op / df_o; ms_i <- ss_int / df_i; ms_r <- ss_rep / df_r
  f_p <- ms_p / ms_i; f_o <- ms_o / ms_i; f_i <- ms_i / ms_r
  full <- data.frame(
    DF = c(df_p, df_o, df_i, df_r, p * o * r - 1),
    SS = c(ss_part, ss_op, ss_int, ss_rep, ss_total),
    MS = c(ms_p, ms_o, ms_i, ms_r, NA),
    F = c(f_p, f_o, f_i, NA, NA),
    P = c(pf(f_p, df_p, df_i, lower.tail = FALSE), pf(f_o, df_o, df_i, lower.tail = FALSE),
          pf(f_i, df_i, df_r, lower.tail = FALSE), NA, NA),
    row.names = c("Part", "Operator", "Part x Operator", "Repeatability", "Total"))
  use_int <- full["Part x Operator", "P"] < alpha
  reduced <- NULL
  if (use_int) {
    v_rep <- ms_r; v_int <- max((ms_i - ms_r) / r, 0)
    v_op <- max((ms_o - ms_i) / (p * r), 0); v_part <- max((ms_p - ms_i) / (o * r), 0)
  } else {
    df_pool <- df_i + df_r; ms_pool <- (ss_int + ss_rep) / df_pool
    reduced <- data.frame(
      DF = c(df_p, df_o, df_pool, p * o * r - 1),
      SS = c(ss_part, ss_op, ss_int + ss_rep, ss_total),
      MS = c(ms_p, ms_o, ms_pool, NA),
      F = c(ms_p / ms_pool, ms_o / ms_pool, NA, NA),
      P = c(pf(ms_p / ms_pool, df_p, df_pool, lower.tail = FALSE),
            pf(ms_o / ms_pool, df_o, df_pool, lower.tail = FALSE), NA, NA),
      row.names = c("Part", "Operator", "Repeatability", "Total"))
    v_rep <- ms_pool; v_int <- 0
    v_op <- max((ms_o - ms_pool) / (p * r), 0); v_part <- max((ms_p - ms_pool) / (o * r), 0)
  }
  v_repro <- v_op + v_int; v_grr <- v_rep + v_repro; v_tot <- v_grr + v_part
  var <- c(v_grr, v_rep, v_repro, v_op, v_int, v_part, v_tot)
  sd <- sqrt(var)
  comp <- data.frame(VarComp = var, PctContribution = var / v_tot * 100, StdDev = sd,
                     StudyVar = 6 * sd, PctStudyVar = sd / sd[7] * 100,
                     row.names = c("Total Gage R&R", "Repeatability", "Reproducibility", "Operator",
                                   "Part x Operator", "Part-to-Part", "Total Variation"))
  if (!is.null(tolerance)) comp$PctTolerance <- 6 * sd / tolerance * 100
  ndc <- if (sd[1] > 0) floor(1.41 * sd[6] / sd[1]) else 0
  pct <- comp["Total Gage R&R", "PctStudyVar"]
  verdict <- if (pct < 10) "ACCEPTABLE - %Study Var < 10%" else
             if (pct <= 30) "MARGINAL - 10-30% %Study Var" else "UNACCEPTABLE - %Study Var > 30%"
  if (ndc < 5) verdict <- paste0(verdict, "  |  ndc = ", ndc, " (< 5)")
  structure(list(anova_full = full, anova_reduced = reduced, interaction_used = use_int,
                 components = comp, ndc = ndc, p = p, o = o, r = r, tolerance = tolerance,
                 verdict = verdict, data = d), class = "grr")
}

print_grr <- function(x) {
  cat("\n", strrep("=", 72), "\n  Gauge R&R (ANOVA method)  -  TheQualityVault.com\n", strrep("=", 72), "\n", sep = "")
  cat(sprintf("  Parts = %d   Operators = %d   Trials = %d   Tolerance = %s\n\n",
              x$p, x$o, x$r, ifelse(is.null(x$tolerance), "not given", x$tolerance)))
  cat("  Two-way ANOVA with interaction\n"); print(signif(x$anova_full, 6))
  if (!is.null(x$anova_reduced)) {
    cat("\n  Interaction not significant - pooled into repeatability (reduced model)\n")
    print(signif(x$anova_reduced, 6))
  }
  cat("\n  Variance components\n"); print(round(x$components, 4))
  cat("\n  Number of distinct categories (ndc) =", x$ndc, "\n")
  cat("  Verdict:", x$verdict, "\n", strrep("=", 72), "\n\n", sep = "")
  invisible(x)
}

plot_grr <- function(x, file = NULL) {
  if (!is.null(file)) png(file, width = 1500, height = 1000, res = 120)
  op <- par(mfrow = c(2, 2), mar = c(4.5, 4.5, 3, 1)); on.exit(par(op))
  c <- x$components[c("Total Gage R&R", "Repeatability", "Reproducibility", "Part-to-Part"), ]
  cols <- c("PctContribution", "PctStudyVar", if (!is.null(x$tolerance)) "PctTolerance")
  barplot(t(as.matrix(c[, cols])), beside = TRUE, col = c(NAVY, GOLD, BLUE)[seq_along(cols)],
          names.arg = c("Gage R&R", "Repeat", "Reprod", "Part"), ylab = "Percent",
          main = "Components of Variation", legend.text = sub("Pct", "%", cols),
          args.legend = list(bty = "n", cex = 0.8))
  abline(h = c(10, 30), lty = 3, col = c("darkgreen", RED))
  boxplot(y ~ part, data = x$data, col = "#DCE3F2", main = "Measurement by Part", xlab = "Part", ylab = "")
  boxplot(y ~ operator, data = x$data, col = "#F3E9CC", main = "Measurement by Operator", xlab = "Operator", ylab = "")
  m <- tapply(x$data$y, list(x$data$part, x$data$operator), mean)
  matplot(m, type = "b", pch = 19, lty = 1, col = c(NAVY, GOLD, BLUE, RED, "darkgreen")[1:ncol(m)],
          xaxt = "n", xlab = "Part", ylab = "Mean", main = "Part x Operator Interaction")
  axis(1, at = seq_len(nrow(m)), labels = rownames(m))
  legend("topleft", colnames(m), col = c(NAVY, GOLD, BLUE, RED, "darkgreen")[1:ncol(m)], lty = 1, pch = 19, bty = "n", cex = 0.8)
  if (!is.null(file)) { dev.off(); message("Plot saved to ", file) }
  invisible(x)
}

demo <- function() {
  d <- read.csv("example_data.csv")
  r <- gauge_rr(d$part, d$operator, d$measurement, tolerance = 3.0)
  print_grr(r); plot_grr(r, file = "gauge_rr_example_R.png")
  invisible(r)
}

if (sys.nframe() == 0) demo()
