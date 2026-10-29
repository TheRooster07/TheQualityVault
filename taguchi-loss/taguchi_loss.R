# =============================================================================
# taguchi_loss.R  —  TheQualityVault.com
# Taguchi Quality Loss Function — all three characteristics (base R only)
#
#   Nominal-Is-Best  (NIB): L(y) = k (y - m)^2   k = A0 / delta^2
#   Larger-Is-Better (LIB): L(y) = k / y^2       k = A0 * m^2
#   Smaller-Is-Better(SIB): L(y) = k * y^2       k = A0 / m^2
#
# For a batch, NIB average loss splits into two parts:
#   E[L] = k*sigma^2 + k*(ybar - m)^2      (spread loss + off-target loss)
#
# Gives the same numbers as the companion Python file taguchi_loss.py.
#
# Quick start
#   From a terminal:   Rscript taguchi_loss.R demo
#   Inside R/RStudio:  source("taguchi_loss.R")
#                      nib <- taguchi_calc("nib", target = 500, delta = 10, A0 = 2.50)
#                      taguchi_eval(nib, 506)
#                      b <- taguchi_from_csv(nib, "example_data.csv", "fill_weight_g")
#                      print(b); taguchi_plot(nib, b)
#
# No packages required. Excel import uses readxl if installed
# (install.packages("readxl")).
# =============================================================================

.TQ_LABELS <- c(nib = "Nominal-Is-Best", lib = "Larger-Is-Better",
                sib = "Smaller-Is-Better")
.TQ_COLS <- list(nib = "#1F4E79", lib = "#2E7D32", sib = "#BF360C")

# ── Core functions ────────────────────────────────────────────────────────────

#' Loss constant k.  ref = tolerance delta (NIB) or reference m (LIB/SIB)
taguchi_k <- function(method, A0, ref) {
  method <- match.arg(method, c("nib", "lib", "sib"))
  if (A0 <= 0)  stop("A0 must be positive")
  if (ref <= 0) stop("Reference / tolerance value must be positive")
  switch(method,
         nib = A0 / ref^2,
         lib = A0 * ref^2,
         sib = A0 / ref^2)
}

#' Individual loss L(y); target only used for NIB
taguchi_loss <- function(method, k, y, target = 0) {
  y <- as.numeric(y)
  switch(method,
         nib = k * (y - target)^2,
         lib = ifelse(y > 0, k / y^2, Inf),
         sib = k * y^2,
         stop("Unknown method: ", method))
}

#' Create a calculator.
#'   NIB: taguchi_calc("nib", target, delta, A0)
#'   LIB: taguchi_calc("lib", m = , A0 = )
#'   SIB: taguchi_calc("sib", m = , A0 = )
taguchi_calc <- function(method, A0, target = NULL, delta = NULL, m = NULL) {
  method <- match.arg(method, c("nib", "lib", "sib"))
  if (method == "nib") {
    if (is.null(target) || is.null(delta)) stop("NIB needs target and delta")
    ref <- delta
  } else {
    if (is.null(m)) stop("LIB/SIB need m")
    ref <- m
    target <- if (method == "lib") m else 0
  }
  structure(list(method = method, A0 = A0, ref = ref, target = target,
                 k = taguchi_k(method, A0, ref)),
            class = "taguchi_calc")
}

print.taguchi_calc <- function(x, ...) {
  cat(sprintf("Taguchi %s calculator: k = %.6f, A0 = $%.2f, ref = %g\n",
              .TQ_LABELS[[x$method]], x$k, x$A0, x$ref))
  invisible(x)
}

# ── Status rules (same thresholds as the Python version) ─────────────────────

.status_single <- function(calc, y, lv) {
  A0 <- calc$A0; ref <- calc$ref
  switch(calc$method,
    nib = {
      dev <- abs(y - calc$target)
      if (dev > ref) "OUT OF TOLERANCE"
      else if (dev > 0.5 * ref) "CAUTION - outer half of tolerance band"
      else "WITHIN TOLERANCE"
    },
    lib = {
      if (y <= 0) "INVALID - y must be > 0"
      else if (lv > A0) "CRITICAL - loss > A0 (y below reference)"
      else if (lv > 0.5 * A0) "CAUTION - loss > 50% of A0"
      else "GOOD"
    },
    sib = {
      if (y < 0) "INVALID - y must be >= 0"
      else if (y > ref) "OUT OF TOLERANCE - y exceeds boundary m"
      else if (lv > 0.5 * A0) "CAUTION - loss > 50% of A0"
      else "GOOD"
    })
}

.status_batch <- function(calc, x, el) {
  A0 <- calc$A0; ref <- calc$ref
  if (el > A0) return("CRITICAL - E[L] > A0")
  if (el > 0.5 * A0) return("CAUTION - E[L] > 50% of A0")
  if (calc$method == "nib" && abs(mean(x) - calc$target) > 0.5 * ref)
    return("BIAS WARNING - mean significantly off-target")
  if (calc$method == "lib" && mean(x) < ref)
    return("MEAN BELOW REFERENCE - process output is low")
  if (calc$method == "sib" && mean(x) > ref)
    return("MEAN EXCEEDS TOLERANCE - process output too high")
  "ACCEPTABLE"
}

# ── Single value ─────────────────────────────────────────────────────────────

taguchi_eval <- function(calc, y) {
  lv <- taguchi_loss(calc$method, calc$k, y, calc$target)
  structure(list(calc = calc, y = y, loss = lv, pct_A0 = lv / calc$A0 * 100,
                 status = .status_single(calc, y, lv)),
            class = "taguchi_single")
}

print.taguchi_single <- function(x, ...) {
  c <- x$calc; line <- strrep("=", 55)
  cat("\n", line, "\n  Taguchi Loss - ", .TQ_LABELS[[c$method]], "\n", line, "\n", sep = "")
  cat(sprintf("  A0              : $%s\n", format(c$A0, nsmall = 4, big.mark = ",")))
  cat(sprintf("  k               : %s\n", formatC(c$k, format = "f", digits = 6, big.mark = ",")))
  cat(sprintf("  y (measured)    : %.4f\n", x$y))
  if (c$method == "nib") {
    cat(sprintf("  Target m        : %.4f\n", c$target))
    cat(sprintf("  Tolerance delta : %.4f\n", c$ref))
    cat(sprintf("  Deviation (y-m) : %+.4f\n", x$y - c$target))
  } else {
    cat(sprintf("  Reference m     : %.4f\n", c$ref))
  }
  cat(sprintf("  L(y)            : $%s\n", formatC(x$loss, format = "f", digits = 4, big.mark = ",")))
  cat(sprintf("  L(y) / A0       : %.2f%%\n", x$pct_A0))
  cat(sprintf("  Status          : %s\n%s\n\n", x$status, line))
  invisible(x)
}

# ── Batch ────────────────────────────────────────────────────────────────────

taguchi_batch <- function(calc, data) {
  x <- suppressWarnings(as.numeric(data))
  x <- x[!is.na(x)]
  if (length(x) == 0) stop("Batch data is empty after removing NA values.")
  losses <- taguchi_loss(calc$method, calc$k, x, calc$target)
  el <- mean(losses)
  var_l <- bias_l <- NA_real_
  if (calc$method == "nib") {
    pop_var <- mean((x - mean(x))^2)           # population variance
    var_l  <- calc$k * pop_var
    bias_l <- calc$k * (mean(x) - calc$target)^2
  }
  structure(list(calc = calc, n = length(x), mean = mean(x),
                 sd = if (length(x) > 1) sd(x) else 0,
                 min = min(x), max = max(x),
                 expected_loss = el, total_loss = sum(losses),
                 variance_loss = var_l, bias_loss = bias_l,
                 losses = losses, data = x,
                 status = .status_batch(calc, x, el)),
            class = "taguchi_batch")
}

print.taguchi_batch <- function(x, ...) {
  c <- x$calc; line <- strrep("=", 55)
  f4 <- function(v) formatC(v, format = "f", digits = 4, big.mark = ",")
  cat("\n", line, "\n  Taguchi Batch Loss - ", .TQ_LABELS[[c$method]], "\n", line, "\n", sep = "")
  cat(sprintf("  n               : %d\n", x$n))
  cat(sprintf("  Mean  ybar      : %s\n", f4(x$mean)))
  cat(sprintf("  Std dev s       : %s\n", f4(x$sd)))
  cat(sprintf("  Min / Max       : %s / %s\n", f4(x$min), f4(x$max)))
  cat(sprintf("  A0              : $%s\n", f4(c$A0)))
  cat(sprintf("  k               : %s\n", formatC(c$k, format = "f", digits = 6, big.mark = ",")))
  cat(sprintf("  E[L]  (avg loss): $%s\n", f4(x$expected_loss)))
  if (!is.na(x$variance_loss)) {
    pv <- if (x$expected_loss > 0) x$variance_loss / x$expected_loss * 100 else 0
    cat(sprintf("    from spread    : $%s  (%.0f%%)\n", f4(x$variance_loss), pv))
    cat(sprintf("    from off-target: $%s  (%.0f%%)\n", f4(x$bias_loss), 100 - pv))
  }
  cat(sprintf("  Total batch loss: $%s\n", f4(x$total_loss)))
  cat(sprintf("  E[L] / A0       : %.2f%%\n", x$expected_loss / c$A0 * 100))
  cat(sprintf("  Status          : %s\n%s\n\n", x$status, line))
  invisible(x)
}

# ── Import / export ──────────────────────────────────────────────────────────

taguchi_from_csv <- function(calc, path, column = 1) {
  if (!file.exists(path)) stop("CSV not found: ", path)
  df <- read.csv(path, stringsAsFactors = FALSE)
  taguchi_batch(calc, df[[column]])
}

taguchi_from_excel <- function(calc, path, column = 1, sheet = 1) {
  if (!requireNamespace("readxl", quietly = TRUE))
    stop("Excel import needs the readxl package: install.packages('readxl')")
  df <- as.data.frame(readxl::read_excel(path, sheet = sheet))
  taguchi_batch(calc, df[[column]])
}

taguchi_export_csv <- function(batch, path = "taguchi_batch_results.csv") {
  write.csv(data.frame(index = seq_len(batch$n), y = batch$data, loss = batch$losses),
            path, row.names = FALSE)
  cat(sprintf("  -> Exported %d rows to %s\n", batch$n, path))
  invisible(path)
}

# ── Plotting (base graphics) ─────────────────────────────────────────────────

.curve_x <- function(calc) {
  switch(calc$method,
         nib = seq(calc$target - 2 * calc$ref, calc$target + 2 * calc$ref, length.out = 400),
         lib = seq(calc$ref * 0.2, calc$ref * 2.5, length.out = 400),
         sib = seq(0, calc$ref * 1.5, length.out = 400))
}

#' Loss curve; pass a taguchi_single to mark a point, or a taguchi_batch for E[L]
taguchi_plot_curve <- function(calc, point = NULL, batch = NULL) {
  x <- .curve_x(calc); y <- taguchi_loss(calc$method, calc$k, x, calc$target)
  col <- .TQ_COLS[[calc$method]]
  ylim <- c(0, max(min(max(y), calc$A0 * 4), calc$A0 * 1.2))
  plot(x, y, type = "l", lwd = 2.2, col = col, ylim = ylim,
       xlab = "Process output y", ylab = "Loss L(y) ($)",
       main = .TQ_LABELS[[calc$method]])
  abline(h = calc$A0, lty = 2, col = "#C0392B")
  if (calc$method == "nib") {
    abline(v = calc$target, lty = 3, col = "grey50")
    abline(v = calc$target + c(-1, 1) * calc$ref, lty = 3, col = "grey70")
  } else {
    abline(v = calc$ref, lty = 3, col = "grey50")
  }
  leg <- c("L(y)", sprintf("A0 = $%.2f", calc$A0)); lc <- c(col, "#C0392B"); lt <- c(1, 2)
  if (!is.null(batch)) {
    abline(h = batch$expected_loss, lty = 4, col = "#E67E22")
    leg <- c(leg, sprintf("E[L] = $%.2f", batch$expected_loss)); lc <- c(lc, "#E67E22"); lt <- c(lt, 4)
  }
  if (!is.null(point)) {
    points(point$y, point$loss, pch = 19, cex = 1.4, col = "#C0392B")
    leg <- c(leg, sprintf("y = %g, L = $%.2f", point$y, point$loss)); lc <- c(lc, "#C0392B"); lt <- c(lt, NA)
  }
  legend("top", legend = leg, col = lc, lty = lt, pch = ifelse(is.na(lt), 19, NA),
         bty = "n", cex = 0.8)
}

taguchi_plot_batch <- function(batch) {
  c <- batch$calc; col <- .TQ_COLS[[c$method]]
  plot(seq_len(batch$n), batch$losses, pch = 19, col = adjustcolor(col, 0.75),
       ylim = c(0, max(batch$losses, c$A0) * 1.05),
       xlab = "Measurement #", ylab = "Loss L(y) ($)",
       main = sprintf("Individual losses (n = %d)", batch$n))
  abline(h = batch$expected_loss, lty = 4, lwd = 1.8, col = "#E67E22")
  abline(h = c$A0, lty = 2, col = "#C0392B")
  legend("topright", c(sprintf("E[L] = $%.2f", batch$expected_loss), sprintf("A0 = $%.2f", c$A0)),
         col = c("#E67E22", "#C0392B"), lty = c(4, 2), bty = "n", cex = 0.8)
}

#' Side-by-side curve + individual losses. file = "out.png" saves instead of showing.
taguchi_plot <- function(calc, batch, file = NULL) {
  if (!is.null(file)) { png(file, width = 1300, height = 500, res = 110); on.exit(dev.off()) }
  op <- par(mfrow = c(1, 2)); on.exit(par(op), add = TRUE)
  taguchi_plot_curve(calc, batch = batch)
  taguchi_plot_batch(batch)
  if (!is.null(file)) cat("  -> Plot saved to", file, "\n")
}

# ── Worked example ───────────────────────────────────────────────────────────
# NIB fill weight: target 500 g, delta 10 g, A0 $2.50 per pack
# LIB bond strength: minimum 80 MPa, A0 $400 per assembly
# SIB leak rate: limit 5 ccm, A0 $300 per unit

taguchi_demo <- function(csv = "example_data.csv", png_file = "taguchi_example_R.png") {
  df <- read.csv(csv)
  nib <- taguchi_calc("nib", target = 500, delta = 10, A0 = 2.50)
  lib <- taguchi_calc("lib", m = 80, A0 = 400)
  sib <- taguchi_calc("sib", m = 5, A0 = 300)

  r_nib <- taguchi_eval(nib, 506); b_nib <- taguchi_batch(nib, df$fill_weight_g)
  r_lib <- taguchi_eval(lib, 85);  b_lib <- taguchi_batch(lib, df$bond_strength_mpa)
  r_sib <- taguchi_eval(sib, 3.2); b_sib <- taguchi_batch(sib, df$leak_rate_ccm)

  cat("\n", strrep("=", 58), "\n  TAGUCHI LOSS FUNCTION - WORKED EXAMPLE (R)\n", strrep("=", 58), "\n", sep = "")
  cat("\n[1] NOMINAL-IS-BEST - fill weight (g)\n");   print(r_nib); print(b_nib)
  cat("[2] LARGER-IS-BETTER - bond strength (MPa)\n"); print(r_lib); print(b_lib)
  cat("[3] SMALLER-IS-BETTER - leak rate (ccm)\n");    print(r_sib); print(b_sib)

  png(png_file, width = 1650, height = 1000, res = 120)
  par(mfrow = c(2, 3), oma = c(0, 0, 2, 0))
  taguchi_plot_curve(nib, point = r_nib)
  taguchi_plot_curve(lib, point = r_lib)
  taguchi_plot_curve(sib, point = r_sib)
  taguchi_plot_batch(b_nib); taguchi_plot_batch(b_lib); taguchi_plot_batch(b_sib)
  mtext("Taguchi Loss Functions - Worked Example", outer = TRUE, font = 2, cex = 1.2)
  dev.off()
  cat("  -> Plot saved to", png_file, "\n")
  invisible(list(nib = b_nib, lib = b_lib, sib = b_sib))
}

# Run the worked example when called as:  Rscript taguchi_loss.R demo
if (!interactive() && identical(commandArgs(trailingOnly = TRUE)[1], "demo")) {
  taguchi_demo()
}
