# ==============================================================================
# process_capability.R  —  TheQualityVault.com
# Process Capability Calculator (normal data) — base R only, no packages needed
#
#   Within sigma : m = 1  -> MR-bar / 1.128      m = 2..10 -> R-bar / d2(m)
#   Overall sigma: sample standard deviation s
#   Cp, Cpk, CPU, CPL (within) · Pp, Ppk, PPU, PPL (overall) · Cpm
#   Expected PPM (within / overall), observed PPM, Z.bench, Anderson-Darling test
#
# Gives the same numbers as the Excel workbook and process_capability.py.
#
# Quick start (from the folder holding example_data.csv):
#   source("process_capability.R")
#   demo()
#   d <- read.csv("my_data.csv")
#   r <- capability(d$measurement, lsl = 9.95, usl = 10.05, target = 10, subgroup_size = 5)
#   print_capability(r); plot_capability(r, file = "capability.png")
# ==============================================================================

D2 <- c(`2` = 1.128, `3` = 1.693, `4` = 2.059, `5` = 2.326, `6` = 2.534,
        `7` = 2.704, `8` = 2.847, `9` = 2.970, `10` = 3.078)

NAVY <- "#1A2B5F"; GOLD <- "#C9A84C"; RED <- "#C0392B"

sigma_within <- function(x, m = 1) {
  if (m == 1) return(mean(abs(diff(x))) / 1.128)
  if (!(m %in% 2:10)) stop("Subgroup size must be 1 to 10.")
  k <- length(x) %/% m                         # complete subgroups only
  if (k < 1) stop("Not enough data for one complete subgroup.")
  g <- matrix(x[1:(k * m)], nrow = k, byrow = TRUE)
  mean(apply(g, 1, max) - apply(g, 1, min)) / D2[[as.character(m)]]
}

anderson_darling <- function(x) {
  n <- length(x)
  z <- (sort(x) - mean(x)) / sd(x)
  F <- pnorm(z)
  i <- seq_len(n)
  a2 <- -n - sum((2 * i - 1) * (log(F) + log(1 - rev(F)))) / n
  a <- a2 * (1 + 0.75 / n + 2.25 / n^2)
  p <- if (a >= 0.6) exp(1.2937 - 5.709 * a + 0.0186 * a^2)
       else if (a >= 0.34) exp(0.9177 - 4.279 * a - 1.38 * a^2)
       else if (a >= 0.2) 1 - exp(-8.318 + 42.796 * a - 59.938 * a^2)
       else 1 - exp(-13.436 + 101.14 * a - 223.73 * a^2)
  list(stat = a2, p = min(max(p, 0), 1))
}

capability <- function(x, lsl, usl, target = NULL, subgroup_size = 1) {
  x <- suppressWarnings(as.numeric(x)); x <- x[!is.na(x)]
  if (length(x) < 2) stop("Need at least 2 measurements.")
  if (usl <= lsl) stop("USL must be greater than LSL.")
  if (is.null(target)) target <- (lsl + usl) / 2
  m <- as.integer(subgroup_size)
  mu <- mean(x); s <- sd(x); sw <- sigma_within(x, m); tol <- usl - lsl
  cpu <- (usl - mu) / (3 * sw); cpl <- (mu - lsl) / (3 * sw)
  ppu <- (usl - mu) / (3 * s);  ppl <- (mu - lsl) / (3 * s)
  pw_l <- pnorm((lsl - mu) / sw) * 1e6; pw_u <- pnorm((usl - mu) / sw, lower.tail = FALSE) * 1e6
  po_l <- pnorm((lsl - mu) / s) * 1e6;  po_u <- pnorm((usl - mu) / s, lower.tail = FALSE) * 1e6
  ad <- anderson_darling(x)
  r <- list(
    x = x, n = length(x), subgroup_size = m, lsl = lsl, usl = usl, target = target,
    mean = mu, sd_overall = s, sd_within = sw,
    cp = tol / (6 * sw), cpu = cpu, cpl = cpl, cpk = min(cpu, cpl),
    pp = tol / (6 * s), ppu = ppu, ppl = ppl, ppk = min(ppu, ppl),
    cpm = tol / (6 * sqrt(s^2 + (mu - target)^2)),
    ppm_within_lsl = pw_l, ppm_within_usl = pw_u, ppm_within = pw_l + pw_u,
    ppm_overall_lsl = po_l, ppm_overall_usl = po_u, ppm_overall = po_l + po_u,
    ppm_observed = sum(x < lsl | x > usl) / length(x) * 1e6,
    z_bench = qnorm((po_l + po_u) / 1e6, lower.tail = FALSE),
    ad_stat = ad$stat, ad_p = ad$p)
  r$verdict <- if (r$ad_p < 0.05) "Data are NOT normal (AD p < 0.05) - indices may be misleading" else
               if (r$ppk >= 1.33) "CAPABLE - Ppk >= 1.33" else
               if (r$ppk >= 1.0) "MARGINAL - 1.00 <= Ppk < 1.33" else "NOT CAPABLE - Ppk < 1.00"
  class(r) <- "capability"
  r
}

print_capability <- function(r) {
  f <- function(v, d = 3) formatC(v, format = "f", digits = d)
  cat("\n", strrep("=", 60), "\n  Process Capability Report  -  TheQualityVault.com\n", strrep("=", 60), "\n", sep = "")
  cat(sprintf("  n = %d    subgroup size = %d\n", r$n, r$subgroup_size))
  cat(sprintf("  LSL = %g   Target = %g   USL = %g\n", r$lsl, r$target, r$usl))
  cat("  Mean            :", f(r$mean, 5), "\n")
  cat("  StDev (overall) :", f(r$sd_overall, 5), "\n")
  cat("  StDev (within)  :", f(r$sd_within, 5), "\n")
  cat("  Cp ", f(r$cp), "  CPL", f(r$cpl), "  CPU", f(r$cpu), "  Cpk", f(r$cpk), "\n")
  cat("  Pp ", f(r$pp), "  PPL", f(r$ppl), "  PPU", f(r$ppu), "  Ppk", f(r$ppk), "\n")
  cat("  Cpm", f(r$cpm), "\n")
  cat("  Expected PPM within :", f(r$ppm_within, 1), "\n")
  cat("  Expected PPM overall:", f(r$ppm_overall, 1), "\n")
  cat("  Observed PPM        :", f(r$ppm_observed, 1), "\n")
  cat("  Z.bench (overall)   :", f(r$z_bench), "\n")
  cat("  Anderson-Darling    : A2 =", f(r$ad_stat, 4), "  p =", f(r$ad_p, 4), "\n")
  cat("  Verdict             :", r$verdict, "\n", strrep("=", 60), "\n\n", sep = "")
  invisible(r)
}

plot_capability <- function(r, file = NULL) {
  if (!is.null(file)) png(file, width = 1500, height = 600, res = 120)
  op <- par(mfrow = c(1, 2), mar = c(4.5, 4.5, 3, 1)); on.exit(par(op))
  lo <- min(r$lsl, r$x); hi <- max(r$usl, r$x); pad <- 0.08 * (hi - lo)
  br <- seq(lo, hi, length.out = 21)
  g <- seq(lo - pad, hi + pad, length.out = 400)
  yl <- max(hist(r$x, breaks = br, plot = FALSE)$density, dnorm(r$mean, r$mean, r$sd_within))
  hist(r$x, breaks = br, freq = FALSE, col = adjustcolor(NAVY, 0.7), border = "white",
       xlim = range(g), ylim = c(0, yl * 1.1), main = "Capability Histogram", xlab = "Measurement")
  lines(g, dnorm(g, r$mean, r$sd_overall), col = GOLD, lwd = 2.5)
  lines(g, dnorm(g, r$mean, r$sd_within), col = NAVY, lwd = 1.8, lty = 2)
  abline(v = c(r$lsl, r$usl), col = RED, lwd = 2); abline(v = r$target, col = "grey50", lty = 3)
  mtext(c("LSL", "USL"), side = 3, at = c(r$lsl, r$usl), col = RED, font = 2)
  legend("topleft", c("Overall fit", "Within fit"), col = c(GOLD, NAVY), lwd = 2, lty = c(1, 2), bty = "n")
  plot.new(); title("Summary")
  txt <- c(sprintf("n = %d (subgroup %d)", r$n, r$subgroup_size),
           sprintf("Mean = %.4f", r$mean),
           sprintf("StDev overall = %.4f   within = %.4f", r$sd_overall, r$sd_within), "",
           sprintf("Cp = %.2f    Cpk = %.2f", r$cp, r$cpk),
           sprintf("Pp = %.2f    Ppk = %.2f", r$pp, r$ppk),
           sprintf("Cpm = %.2f", r$cpm), "",
           sprintf("PPM within = %.0f   overall = %.0f", r$ppm_within, r$ppm_overall),
           sprintf("Observed PPM = %.0f   Z.bench = %.2f", r$ppm_observed, r$z_bench),
           sprintf("AD normality p = %.3f", r$ad_p), "", r$verdict)
  text(0, seq(0.95, 0.95 - 0.07 * (length(txt) - 1), by = -0.07), txt, adj = 0, family = "mono", cex = 0.85)
  if (!is.null(file)) { dev.off(); message("Plot saved to ", file) }
  invisible(r)
}

demo <- function() {
  d <- read.csv("example_data.csv")
  r <- capability(d$diameter_mm, lsl = 9.95, usl = 10.05, target = 10.00, subgroup_size = 5)
  print_capability(r)
  plot_capability(r, file = "capability_example_R.png")
  invisible(r)
}

if (sys.nframe() == 0) demo()   # runs when called with: Rscript process_capability.R
