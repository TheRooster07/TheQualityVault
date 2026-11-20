# ==============================================================================
# crow_amsaa.R  —  TheQualityVault.com
# Crow-AMSAA reliability growth (NHPP power-law model). Base R only.
#
#   N(t) = lambda * t^beta      rho(t) = lambda*beta*t^(beta-1)      MTBF(t) = 1/rho(t)
#   MLE: beta solves N/b + sum(ln t_i) - N*sum(T^b ln T)/sum(T^b) = 0,  lambda = N/sum(T^beta)
#        (one system or equal end times: beta = N / sum(ln(T/t_i)))
#   Unbiased beta: (N-1)/N*beta time-terminated, (N-2)/N*beta failure-terminated
#   beta bounds: 2N*beta/beta_hat ~ chi-square(2N) [time] or chi-square(2(N-1)) [failure]
#   Laplace trend test U ~ N(0,1); U < 0 means reliability growth
#
# Data: one row per event - system, time, event (F = failure, E = end of test).
# A single system with no E row is failure-terminated at its last failure.
# Same numbers as the Excel workbook and crow_amsaa.py.
#   source("crow_amsaa.R"); demo()
#   d <- read.csv("my_test.csv"); r <- crow_amsaa(d$system, d$time, d$event, target_mtbf = 350)
# ==============================================================================

NAVY <- "#1A2B5F"; GOLD <- "#C9A84C"; RED <- "#C0392B"

crow_amsaa <- function(system, time, event, alpha = 0.05, at = NULL, target_mtbf = NULL, future = NULL) {
  d <- data.frame(system = trimws(as.character(system)), time = as.numeric(time),
                  event = toupper(substr(trimws(as.character(event)), 1, 1)), stringsAsFactors = FALSE)
  d <- d[!is.na(d$time), ]
  if (any(d$time <= 0)) stop("All times must be greater than zero.")
  f <- d[d$event == "F", ]
  systems <- unique(d$system); K <- length(systems); N <- nrow(f)
  if (N < 3) stop("Need at least 3 failures.")
  endt <- sapply(systems, function(s) {
    e <- d$time[d$system == s & d$event == "E"]
    if (length(e)) e[1] else max(d$time[d$system == s])
  })
  ft <- K == 1 && !any(d$event == "E")
  T <- as.numeric(endt); lnT <- log(T); slt <- sum(log(f$time))
  g <- function(b) N / b + slt - N * sum(T^b * lnT) / sum(T^b)
  beta <- uniroot(g, c(1e-3, 20), tol = 1e-14)$root
  lam <- N / sum(T^beta)
  beta_unb <- if (ft) (N - 2) / N * beta else (N - 1) / N * beta
  df <- if (ft) 2 * (N - 1) else 2 * N
  b_lo <- beta * qchisq(alpha / 2, df) / (2 * N); b_hi <- beta * qchisq(1 - alpha / 2, df) / (2 * N)

  nq <- sapply(systems, function(s) sum(f$system == s)) - ft
  num <- sum(f$time) - (if (ft) T[1] else 0) - sum(nq * T / 2)
  U <- num / sqrt(sum(nq * T^2 / 12)); p_trend <- 2 * (1 - pnorm(abs(U)))

  t_eval <- if (is.null(at)) max(T) else at
  rho <- function(t) lam * beta * t^(beta - 1)
  fs <- f[order(f$time), ]
  r <- list(K = K, N = N, ft = ft, T = T, alpha = alpha, beta = beta, lam = lam, beta_unb = beta_unb,
            beta_lo = b_lo, beta_hi = b_hi, growth = 1 - beta, U = U, p_trend = p_trend, t_eval = t_eval,
            total_time = sum(T), cum_mtbf_obs = sum(T) / N, inst_mtbf = 1 / rho(t_eval),
            cum_mtbf_model = t_eval^(1 - beta) / lam, intensity = rho(t_eval),
            target = target_mtbf, future = future,
            mcf_t = fs$time, mcf = cumsum(1 / sapply(fs$time, function(t) sum(T >= t))))
  if (!is.null(target_mtbf)) r$t_target <- if (beta < 1) (lam * beta * target_mtbf)^(1 / (1 - beta)) else NaN
  if (!is.null(future)) {
    r$n_future <- lam * future^beta; r$n_add <- lam * (future^beta - t_eval^beta); r$mtbf_future <- 1 / rho(future)
  }
  class(r) <- "crow_amsaa"; r
}

ca_verdict <- function(r) {
  if (r$p_trend < r$alpha && r$U < 0) sprintf("Reliability is GROWING: failures are getting further apart (Laplace p = %.4f < %g).", r$p_trend, r$alpha) else
  if (r$p_trend < r$alpha) sprintf("Reliability is GETTING WORSE: failures are coming closer together (Laplace p = %.4f < %g).", r$p_trend, r$alpha) else
  sprintf("No significant trend (Laplace p = %.4f >= %g): treat the failure rate as constant (beta ~ 1).", r$p_trend, r$alpha)
}

print.crow_amsaa <- function(x, ...) {
  r <- x; L <- function(k, v) cat(sprintf("  %-40s%16s\n", k, v))
  f4 <- function(v) formatC(v, format = "f", digits = 4, big.mark = ",")
  f2 <- function(v) formatC(v, format = "f", digits = 2, big.mark = ",")
  f1 <- function(v) formatC(v, format = "f", digits = 1, big.mark = ",")
  cl <- sprintf("%.0f%%", 100 * (1 - r$alpha))
  cat("\n", strrep("=", 60), "\n  Crow-AMSAA Reliability Growth  -  TheQualityVault.com\n", strrep("=", 60), "\n", sep = "")
  L("Systems", r$K); L("Failures N", r$N); L("Test type", if (r$ft) "failure-terminated" else "time-terminated")
  L("Total test time (all systems)", f1(r$total_time)); L("Shape beta (MLE)", f4(r$beta))
  L("Scale lambda", formatC(r$lam, format = "g", digits = 6)); L("beta unbiased", f4(r$beta_unb))
  L(paste("beta", cl, "lower bound"), f4(r$beta_lo)); L(paste("beta", cl, "upper bound"), f4(r$beta_hi))
  L("Growth rate alpha = 1 - beta", f4(r$growth)); L("Laplace U", f4(r$U)); L("Laplace p-value (two-sided)", f4(r$p_trend))
  L("Evaluated at age t", f1(r$t_eval)); L("Failure intensity at t (per system)", formatC(r$intensity, format = "g", digits = 6))
  L("Instantaneous MTBF at t", f2(r$inst_mtbf)); L("Cumulative MTBF (model) at t", f2(r$cum_mtbf_model))
  L("Cumulative MTBF (observed)", f2(r$cum_mtbf_obs))
  if (!is.null(r$target)) L(sprintf("Age to reach MTBF %g", r$target), if (is.nan(r$t_target)) "not reached (beta >= 1)" else f1(r$t_target))
  if (!is.null(r$future)) {
    L(sprintf("Expected failures per system by %g", r$future), f2(r$n_future))
    L(sprintf("Additional failures per system to %g", r$future), f2(r$n_add))
    L(sprintf("Instantaneous MTBF at %g", r$future), f2(r$mtbf_future))
  }
  cat("  ", ca_verdict(r), "\n", strrep("=", 60), "\n\n", sep = "")
  invisible(r)
}

plot_crow_amsaa <- function(r, file = NULL) {
  if (!is.null(file)) png(file, width = 1500, height = 620, res = 120)
  op <- par(mfrow = c(1, 2), mar = c(4.5, 4.5, 3, 1)); on.exit(par(op))
  tmax <- max(r$T, if (is.null(r$future)) 0 else r$future)
  tg <- exp(seq(log(min(r$mcf_t) * 0.8), log(tmax * 1.1), length.out = 200))
  plot(r$mcf_t, r$mcf, log = "xy", pch = 19, col = NAVY, xlab = "Test time per system (log)",
       ylab = "Cumulative failures per system (log)", main = "Cumulative failures - log-log",
       xlim = range(tg), ylim = range(c(r$mcf, r$lam * tg^r$beta)))
  lines(tg, r$lam * tg^r$beta, col = GOLD, lwd = 2.5)
  legend("topleft", c("Observed", sprintf("Crow-AMSAA fit  beta = %.3f", r$beta)), col = c(NAVY, GOLD),
         pch = c(19, NA), lty = c(NA, 1), lwd = c(NA, 2.5), bty = "n", cex = 0.8)
  tl <- seq(min(r$mcf_t), tmax * 1.05, length.out = 300)
  inst <- 1 / (r$lam * r$beta * tl^(r$beta - 1)); cumm <- tl^(1 - r$beta) / r$lam
  yl <- c(0, max(inst, if (is.null(r$target)) 0 else r$target) * 1.3)
  plot(tl, inst, type = "l", col = GOLD, lwd = 2.5, ylim = yl, xlab = "Test time per system", ylab = "MTBF",
       main = "MTBF growth")
  lines(tl, cumm, col = RED, lwd = 2, lty = 2); points(r$mcf_t, r$mcf_t / r$mcf, pch = 19, col = NAVY, cex = 0.7)
  if (!is.null(r$target)) abline(h = r$target, col = "grey50", lty = 3)
  legend("topleft", c("Instantaneous MTBF (model)", "Cumulative MTBF (model)", "Cumulative MTBF (observed)",
                      if (!is.null(r$target)) sprintf("Target MTBF %g", r$target)),
         col = c(GOLD, RED, NAVY, "grey50")[seq_len(3 + !is.null(r$target))],
         lty = c(1, 2, NA, 3)[seq_len(3 + !is.null(r$target))], pch = c(NA, NA, 19, NA)[seq_len(3 + !is.null(r$target))],
         lwd = 2, bty = "n", cex = 0.8)
  if (!is.null(file)) dev.off()
  invisible(r)
}

demo <- function() {
  # Three prototypes on a reliability growth test; target MTBF 350 h; projection to 2,500 h.
  d <- read.csv("example_data.csv", stringsAsFactors = FALSE)
  r <- crow_amsaa(d$system, d$time, d$event, target_mtbf = 350, future = 2500)
  print(r)
  plot_crow_amsaa(r, "crow_amsaa_example_R.png")
  cat("  -> Plot saved to crow_amsaa_example_R.png\n")
  invisible(r)
}

if (!interactive() && sys.nframe() == 0) demo()
