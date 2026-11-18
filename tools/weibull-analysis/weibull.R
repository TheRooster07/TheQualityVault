# ==============================================================================
# weibull.R  —  TheQualityVault.com
# 2-parameter Weibull life-data analysis with suspensions. Base R only.
#
#   MRR (X on Y): Johnson's adjusted ranks, Benard median ranks,
#                 x = ln t, y = ln(-ln(1-F)), x = a + b*y -> beta = 1/b, eta = exp(a)
#   MLE: beta solves sum(t^b ln t)/sum(t^b) - 1/b - mean(ln t_fail) = 0,
#        eta = (sum(t^beta)/r)^(1/beta)
#   B1/B10/B50 life, MTTF = eta*gamma(1+1/beta), R(t) = exp(-(t/eta)^beta)
#
# Same numbers as the Excel workbook and weibull.py.
#   source("weibull.R"); demo()
#   d <- read.csv("my_data.csv"); r <- weibull_report(d$hours, d$status, at = 1000)
# ==============================================================================

NAVY <- "#1A2B5F"; GOLD <- "#C9A84C"; RED <- "#C0392B"

prep <- function(times, status) {
  f <- toupper(substr(trimws(as.character(status)), 1, 1)) == "F"
  o <- order(times, !f)                       # failures before suspensions at ties
  list(t = as.numeric(times)[o], f = f[o])
}

weibull_mrr <- function(times, status) {
  p <- prep(times, status); t <- p$t; f <- p$f; N <- length(t)
  adj <- rep(NA_real_, N); prev <- 0
  for (i in seq_len(N)) if (f[i]) { prev <- prev + (N + 1 - prev) / (1 + (N - i + 1)); adj[i] <- prev }
  F <- (adj - 0.3) / (N + 0.4)
  x <- log(t[f]); y <- log(-log(1 - F[f]))
  fit <- lm(x ~ y)
  list(beta = 1 / unname(coef(fit)[2]), eta = exp(unname(coef(fit)[1])), r2 = cor(x, y)^2,
       t = t, fail = f, x = x, y = y)
}

weibull_mle <- function(times, status) {
  p <- prep(times, status); t <- p$t; f <- p$f; r <- sum(f); lt <- log(t)
  g <- function(b) sum(t^b * lt) / sum(t^b) - 1 / b - mean(lt[f])
  beta <- uniroot(g, c(0.05, 20), tol = 1e-12)$root
  list(beta = beta, eta = (sum(t^beta) / r)^(1 / beta))
}

blife <- function(beta, eta, p) eta * (-log(1 - p))^(1 / beta)

weibull_report <- function(times, status, at = NULL) {
  m <- weibull_mrr(times, status); l <- weibull_mle(times, status)
  add <- function(z) {
    z$B1 <- blife(z$beta, z$eta, .01); z$B10 <- blife(z$beta, z$eta, .10); z$B50 <- blife(z$beta, z$eta, .50)
    z$MTTF <- z$eta * gamma(1 + 1 / z$beta)
    z$R_at <- if (!is.null(at)) exp(-(at / z$eta)^z$beta) else NA
    z
  }
  list(n = length(m$t), failures = sum(m$fail), mrr = add(m), mle = add(l), at = at)
}

shape_text <- function(b) if (b < 0.95) "beta < 1 -> infant mortality (decreasing failure rate)" else
  if (b <= 1.05) "beta ~ 1 -> random failures (constant failure rate)" else
  "beta > 1 -> wear-out (increasing failure rate): plan preventive replacement"

print_weibull <- function(r) {
  m <- r$mrr; l <- r$mle
  cat("\n", strrep("=", 60), "\n  Weibull Analysis  -  TheQualityVault.com\n", strrep("=", 60), "\n", sep = "")
  cat(sprintf("  Units = %d   Failures = %d   Suspensions = %d\n", r$n, r$failures, r$n - r$failures))
  cat(sprintf("  %-24s%14s%14s\n", "", "MRR (X on Y)", "MLE"))
  for (k in c("beta", "eta", "B1", "B10", "B50", "MTTF"))
    cat(sprintf("  %-24s%14.4f%14.4f\n", k, m[[k]], l[[k]]))
  if (!is.null(r$at)) cat(sprintf("  %-24s%14.4f%14.4f\n", paste0("R(", r$at, ")"), m$R_at, l$R_at))
  cat(sprintf("  R2 (MRR fit)            %14.4f\n  %s\n%s\n\n", m$r2, shape_text(m$beta), strrep("=", 60)))
  invisible(r)
}

plot_weibull <- function(r, file = NULL) {
  if (!is.null(file)) png(file, width = 1500, height = 620, res = 120)
  op <- par(mfrow = c(1, 2), mar = c(4.5, 4.5, 3, 1)); on.exit(par(op))
  m <- r$mrr; l <- r$mle
  xs <- seq(min(m$x) - 0.3, max(m$x) + 0.3, length.out = 50)
  pt <- c(.01, .05, .1, .2, .5, .632, .9, .99)
  plot(m$x, m$y, pch = 19, col = NAVY, xlab = "Time (log scale)", ylab = "Unreliability F(t)",
       main = "Weibull Probability Plot", xaxt = "n", yaxt = "n",
       ylim = range(c(m$y, log(-log(1 - c(.01, .99))))))
  axis(2, at = log(-log(1 - pt)), labels = paste0(pt * 100, "%"), las = 1, cex.axis = 0.8)
  tt <- c(10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000)
  axis(1, at = log(tt), labels = format(tt, big.mark = ",", scientific = FALSE))
  lines(xs, m$beta * (xs - log(m$eta)), col = GOLD, lwd = 2)
  lines(xs, l$beta * (xs - log(l$eta)), col = RED, lwd = 1.5, lty = 2)
  legend("topleft", c(sprintf("MRR beta=%.2f eta=%.0f", m$beta, m$eta), sprintf("MLE beta=%.2f eta=%.0f", l$beta, l$eta)),
         col = c(GOLD, RED), lty = c(1, 2), lwd = 2, bty = "n", cex = 0.8)
  tg <- seq(0, max(m$t) * 1.5, length.out = 300)
  plot(tg, exp(-(tg / m$eta)^m$beta), type = "l", lwd = 2, col = GOLD, ylim = c(0, 1),
       xlab = "Time", ylab = "Reliability", main = "Reliability Curve")
  lines(tg, exp(-(tg / l$eta)^l$beta), lwd = 2, col = RED, lty = 2)
  legend("topright", c("MRR", "MLE"), col = c(GOLD, RED), lty = c(1, 2), lwd = 2, bty = "n")
  if (!is.null(file)) { dev.off(); message("Plot saved to ", file) }
  invisible(r)
}

demo <- function() {
  d <- read.csv("example_data.csv")
  r <- weibull_report(d$hours, d$status, at = 1000)
  print_weibull(r); plot_weibull(r, file = "weibull_example_R.png")
  invisible(r)
}

if (sys.nframe() == 0) demo()
