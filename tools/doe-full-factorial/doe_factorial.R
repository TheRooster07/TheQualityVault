# ==============================================================================
# doe_factorial.R  —  TheQualityVault.com
# 2-level Full Factorial DOE: design generator + analysis. Base R only.
#
#   design(): 2^k design (k = 2-5) with replicates and randomised run order
#   analyze(): effects, coefficients, ANOVA for main effects + two-factor
#              interactions (higher-order interactions pooled into error)
#   Effect = mean(Y at +1) - mean(Y at -1); SS = N * effect^2 / 4
#
# Same numbers as the Excel workbook and doe_factorial.py.
#   source("doe_factorial.R"); demo()
#   d <- design(list(Temp = c(150, 180), Pressure = c(2, 4)), reps = 2, seed = 7)
# ==============================================================================

LETTERS5 <- c("A", "B", "C", "D", "E")
NAVY <- "#1A2B5F"; GOLD <- "#C9A84C"; RED <- "#C0392B"

design <- function(factors, reps = 1, seed = NULL) {
  k <- length(factors); if (k < 2 || k > 5) stop("Use 2 to 5 factors.")
  n <- 2^k
  coded <- sapply(0:(k - 1), function(j) ifelse(((0:(n - 1)) %/% 2^j) %% 2 == 0, -1, 1))
  coded <- coded[rep(1:n, reps), , drop = FALSE]
  d <- data.frame(StdOrder = 1:(n * reps), Rep = rep(1:reps, each = n))
  if (!is.null(seed)) set.seed(seed)
  d$RunOrder <- sample(nrow(d))
  for (j in 1:k) d[[LETTERS5[j]]] <- coded[, j]
  for (j in 1:k) d[[names(factors)[j]]] <- ifelse(coded[, j] == -1, factors[[j]][1], factors[[j]][2])
  d
}

terms <- function(k) c(LETTERS5[1:k], apply(combn(LETTERS5[1:k], 2), 2, paste, collapse = ""))

analyze <- function(d, response = "Y", k = sum(LETTERS5 %in% names(d))) {
  y <- as.numeric(d[[response]]); N <- length(y)
  tt <- terms(k)
  eff <- t(sapply(tt, function(t) {
    x <- Reduce(`*`, lapply(strsplit(t, "")[[1]], function(c) d[[c]]))
    e <- mean(y[x == 1]) - mean(y[x == -1])
    c(Effect = e, Coef = e / 2, SS = N * e^2 / 4)
  }))
  eff <- as.data.frame(eff)
  ss_tot <- sum((y - mean(y))^2); df_res <- N - 1 - nrow(eff)
  ss_res <- ss_tot - sum(eff$SS); ms_res <- if (df_res > 0) ss_res / df_res else NA
  eff$DF <- 1
  eff$F <- if (df_res > 0) eff$SS / ms_res else NA
  eff$P <- if (df_res > 0) pf(eff$F, 1, df_res, lower.tail = FALSE) else NA
  list(effects = eff, mean = mean(y), ss_total = ss_tot, ss_res = ss_res, df_res = df_res,
       ms_res = ms_res, r2 = 1 - ss_res / ss_tot, N = N, k = k, data = d, response = response)
}

print_doe <- function(r, names = NULL) {
  e <- r$effects
  if (!is.null(names)) rownames(e) <- ifelse(rownames(e) %in% names(names),
                                             paste0(rownames(e), " (", names[rownames(e)], ")"), rownames(e))
  cat("\n", strrep("=", 70), "\n  2-Level Full Factorial Analysis  -  TheQualityVault.com\n", strrep("=", 70), "\n", sep = "")
  cat(sprintf("  Runs N = %d   Factors k = %d   Grand mean = %.4f\n", r$N, r$k, r$mean))
  cat("  Model: main effects + two-factor interactions (higher-order pooled into error)\n\n")
  print(round(e, 4))
  cat(sprintf("\n  Residual: SS = %.4f   DF = %d   MS = %.4f\n", r$ss_res, r$df_res, r$ms_res))
  cat(sprintf("  Total SS = %.4f    R2 = %.2f%%\n", r$ss_total, 100 * r$r2))
  if (r$df_res > 0) cat("  Significant at 0.05:", paste(rownames(r$effects)[r$effects$P < 0.05], collapse = ", "), "\n")
  cat(strrep("=", 70), "\n\n")
  invisible(r)
}

plot_doe <- function(r, names = NULL, file = NULL) {
  if (!is.null(file)) png(file, width = 1500, height = 1000, res = 120)
  op <- par(mfrow = c(2, 2), mar = c(4.5, 6, 3, 1)); on.exit(par(op))
  e <- sort(abs(r$effects$Effect)); nm <- rownames(r$effects)[order(abs(r$effects$Effect))]
  sig <- if (r$df_res > 0) r$effects[nm, "P"] < 0.05 else rep(FALSE, length(nm))
  barplot(e, names.arg = nm, horiz = TRUE, las = 1, col = ifelse(sig, RED, NAVY),
          main = "Pareto of |Effects| (red = p < 0.05)")
  d <- r$data; y <- d[[r$response]]
  m <- sapply(LETTERS5[1:r$k], function(f) tapply(y, d[[f]], mean))
  matplot(1:2, m, type = "b", pch = 19, lty = 1, lwd = 2, xaxt = "n", xlab = "", ylab = "Mean response",
          main = "Main Effects", col = c(NAVY, GOLD, RED, "darkgreen", "purple")[1:r$k])
  axis(1, at = 1:2, labels = c("Low (-1)", "High (+1)")); abline(h = r$mean, lty = 3, col = "grey50")
  legend("topleft", if (is.null(names)) LETTERS5[1:r$k] else unname(names[LETTERS5[1:r$k]]),
         col = c(NAVY, GOLD, RED, "darkgreen", "purple")[1:r$k], lty = 1, pch = 19, bty = "n", cex = 0.8)
  two <- rownames(r$effects)[nchar(rownames(r$effects)) == 2]
  top <- two[which.max(abs(r$effects[two, "Effect"]))]; f1 <- substr(top, 1, 1); f2 <- substr(top, 2, 2)
  im <- tapply(y, list(d[[f1]], d[[f2]]), mean)
  matplot(1:2, im, type = "b", pch = 19, lty = 1, lwd = 2, col = c(NAVY, GOLD), xaxt = "n",
          xlab = f1, ylab = "Mean response", main = paste("Largest interaction:", top))
  axis(1, at = 1:2, labels = c("-1", "+1"))
  legend("topleft", paste(f2, c("= -1", "= +1")), col = c(NAVY, GOLD), lty = 1, pch = 19, bty = "n", cex = 0.8)
  fit <- r$mean + Reduce(`+`, lapply(rownames(r$effects), function(t)
    r$effects[t, "Coef"] * Reduce(`*`, lapply(strsplit(t, "")[[1]], function(c) d[[c]]))))
  plot(fit, y - fit, pch = 19, col = NAVY, xlab = "Fitted", ylab = "Residual", main = "Residuals vs Fitted")
  abline(h = 0, col = RED)
  if (!is.null(file)) { dev.off(); message("Plot saved to ", file) }
  invisible(r)
}

demo <- function() {
  d <- read.csv("example_data.csv")
  nm <- c(A = "Temperature", B = "Pressure", C = "Time")
  r <- analyze(d, "Yield", k = 3)
  print_doe(r, nm); plot_doe(r, nm, file = "doe_example_R.png")
  invisible(r)
}

if (sys.nframe() == 0) demo()
