# ==============================================================================
# repairable_systems.R  —  TheQualityVault.com
# Repairable systems analysis for a fleet and the repair-or-replace decision. Base R only.
#
# Data, one row per event: unit, event, date, age (give a date OR an age on each row)
#   I installed · S records start (optional) · F failure, repaired · E end, still in service · R retired
#   With dates, age = (date - install date) / days_per_unit (365.25 -> years); no I row -> S date is age 0.
#
#   MCF (Nelson) with log-scale bounds; power-law NHPP fitted by MLE with each unit observed from a to b:
#     lambda = N / sum(b^beta - a^beta);  beta solves
#     N/beta + sum(ln t) - N*sum(b^beta ln b - a^beta ln a)/sum(b^beta - a^beta) = 0
#   Laplace trend test; bad actors (Poisson upper tail); cost rate C(T) = (Cp + Cr*lambda*T^beta)/T,
#   optimum replacement age T* = (Cp/(Cr*lambda*(beta-1)))^(1/beta) when beta > 1.
# Same numbers as the Excel workbook and repairable_systems.py.
#   source("repairable_systems.R"); demo()
#   r <- repairable(read.csv("fleet.csv"), replace_cost = 45000, repair_cost = 6000, horizon = 3)
# ==============================================================================

NAVY <- "#1A2B5F"; GOLD <- "#C9A84C"; RED <- "#C0392B"

rs_prepare <- function(df, days_per_unit = 365.25) {
  names(df) <- tolower(trimws(names(df)))
  d <- data.frame(unit = trimws(as.character(df$unit)),
                  event = toupper(substr(trimws(as.character(df$event)), 1, 1)), stringsAsFactors = FALSE)
  age <- if (!is.null(df$age)) suppressWarnings(as.numeric(df$age)) else rep(NA_real_, nrow(d))
  dt <- if (!is.null(df$date)) as.Date(as.character(df$date), optional = TRUE) else as.Date(rep(NA, nrow(d)))
  units <- unique(d$unit)
  origin <- sapply(units, function(u) {
    i <- which(d$unit == u & d$event == "I" & !is.na(dt)); s <- which(d$unit == u & d$event == "S" & !is.na(dt))
    if (length(i)) as.numeric(dt[i[1]]) else if (length(s)) as.numeric(dt[s[1]]) else NA_real_
  })
  from_date <- (as.numeric(dt) - origin[d$unit]) / days_per_unit
  d$age <- ifelse(!is.na(age), age, from_date)
  d$age[d$event == "I" & is.na(d$age)] <- 0
  if (any(is.na(d$age))) stop("Rows with no usable date or age: ", paste(unique(d$unit[is.na(d$age)]), collapse = ", "))
  U <- do.call(rbind, lapply(units, function(u) {
    g <- d[d$unit == u, ]; e <- g[g$event %in% c("E", "R"), ]
    if (nrow(e) != 1) stop("Unit ", u, ": needs exactly one E (in service) or R (retired) row.")
    a <- if (any(g$event == "S")) g$age[g$event == "S"][1] else 0; b <- e$age
    f <- g$age[g$event == "F"]
    if (any(f <= a) || any(f > b) || b <= a) stop("Unit ", u, ": failures must fall after the start and on/before the end.")
    data.frame(unit = u, start = a, end = b, failures = length(f),
               status = if (e$event == "R") "Retired" else "In service", stringsAsFactors = FALSE)
  }))
  list(events = d, units = U)
}

repairable <- function(df, replace_cost = NULL, repair_cost = NULL, horizon = 3, alpha = 0.05,
                       flag_p = 0.01, days_per_unit = 365.25) {
  p <- rs_prepare(df, days_per_unit); d <- p$events; U <- p$units
  t <- d$age[d$event == "F"]; N <- length(t); K <- nrow(U)
  if (N < 3) stop("Need at least 3 failures.")
  a <- U$start; b <- U$end; n <- U$failures; m <- a > 0; sa <- ifelse(m, a, 1); lt <- sum(log(t))
  sums <- function(B) c(sum(b^B - m * sa^B), sum(b^B * log(b) - m * sa^B * log(sa)),
                        sum(b^B * log(b)^2 - m * sa^B * log(sa)^2))
  g <- function(B) { s <- sums(B); N / B + lt - N * s[2] / s[1] }
  beta <- uniroot(g, c(0.01, 20), tol = 1e-14)$root
  s <- sums(beta); lam <- N / s[1]
  se <- 1 / sqrt(N / beta^2 + N * (s[3] * s[1] - s[2]^2) / s[1]^2)
  z <- qnorm(1 - alpha / 2)
  mid <- setNames((U$start + U$end) / 2, U$unit)
  Ul <- sum(t - mid[d$unit[d$event == "F"]]) / sqrt(sum(n * (b - a)^2) / 12)
  risk <- sapply(t, function(x) sum(a < x & x <= b))
  mcf <- sapply(t, function(x) sum(1 / risk[t <= x])); v <- sapply(t, function(x) sum(1 / risk[t <= x]^2))
  o <- order(t)
  M <- data.frame(age = t, at_risk = risk, mcf = mcf, lower = mcf * exp(-z * sqrt(v) / mcf),
                  upper = mcf * exp(z * sqrt(v) / mcf))[o, ]
  U$expected <- lam * (b^beta - m * sa^beta)
  U$p_excess <- ifelse(n > 0, 1 - ppois(n - 1, U$expected), 1)
  U$bad_actor <- U$p_excess < flag_p & n >= 2
  r <- list(K = K, N = N, in_service = sum(U$status == "In service"), retired = sum(U$status == "Retired"),
            exposure = sum(b - a), beta = beta, lam = lam, se = se, alpha = alpha,
            beta_lo = beta * exp(-z * se / beta), beta_hi = beta * exp(z * se / beta),
            U = Ul, p_trend = 2 * (1 - pnorm(abs(Ul))), mcf = M, horizon = horizon,
            Cp = replace_cost, Cr = repair_cost)
  r$rate_per_unit <- N / r$exposure
  r$T_star <- NULL
  if (!is.null(replace_cost) && !is.null(repair_cost)) {
    r$cost <- function(T) (replace_cost + repair_cost * lam * T^beta) / T
    r$T_star <- if (beta > 1) (replace_cost / (repair_cost * lam * (beta - 1)))^(1 / beta) else NaN
    r$C_star <- if (beta > 1) r$cost(r$T_star) else NaN
  }
  ins <- U$status == "In service"
  U$next_failures <- ifelse(ins, lam * ((b + horizon)^beta - b^beta), NA)
  U$next_repair_cost <- if (!is.null(repair_cost)) U$next_failures * repair_cost else NA
  U$advice <- sapply(seq_len(K), function(i) {
    if (!ins[i]) return("Retired")
    if (U$bad_actor[i]) return("Bad actor – find the cause; replace early if it can't be fixed")
    if (is.null(r$T_star)) return(if (beta <= 1) "Keep repairing" else "Enter costs for a replace decision")
    if (is.nan(r$T_star)) return("Keep repairing")
    if (b[i] >= r$T_star) return("Replace – past the optimum age")
    if (b[i] + horizon >= r$T_star) return(sprintf("Plan replacement in about %.1f", r$T_star - b[i]))
    "Keep repairing"
  })
  r$units <- U
  class(r) <- "repairable"; r
}

rs_pattern <- function(r) {
  if (r$beta_lo > 1) "WEAR-OUT: failures come faster as units age (beta > 1). Replacement at the right age saves money." else
  if (r$beta_hi < 1) "IMPROVING: failures get further apart with age (beta < 1). Keep repairing." else
  "NO CLEAR AGE EFFECT: beta is not significantly different from 1 - the failure rate is steady; repairing is fine."
}

print.repairable <- function(x, ...) {
  r <- x; U <- r$units; L <- function(k, v) cat(sprintf("  %-44s%14s\n", k, v))
  cl <- sprintf("%.0f%%", 100 * (1 - r$alpha))
  cat("\n", strrep("=", 62), "\n  Repairable Systems & Replacement Age  -  TheQualityVault.com\n", strrep("=", 62), "\n", sep = "")
  L("Units (in service / retired)", sprintf("%d (%d / %d)", r$K, r$in_service, r$retired)); L("Failures", r$N)
  L("Observed unit-time", formatC(r$exposure, format = "f", digits = 2, big.mark = ","))
  L("Failures per unit per time unit (average)", sprintf("%.4f", r$rate_per_unit))
  L("Shape beta (MLE)", sprintf("%.4f", r$beta)); L("Scale lambda", formatC(r$lam, format = "g", digits = 6))
  L(paste("beta", cl, "lower bound"), sprintf("%.4f", r$beta_lo)); L(paste("beta", cl, "upper bound"), sprintf("%.4f", r$beta_hi))
  L("Laplace U", sprintf("%.4f", r$U)); L("Laplace p-value (two-sided)", sprintf("%.4f", r$p_trend))
  if (!is.null(r$Cp)) {
    L("Replacement cost / repair cost", sprintf("%s / %s", formatC(r$Cp, format = "d", big.mark = ","), formatC(r$Cr, format = "d", big.mark = ",")))
    L("Optimum replacement age T*", if (is.nan(r$T_star)) "none (beta <= 1)" else formatC(r$T_star, format = "f", digits = 2, big.mark = ","))
    L("Lowest cost per unit per time unit", if (is.nan(r$T_star)) "-" else formatC(r$C_star, format = "f", digits = 2, big.mark = ","))
    L("In-service units past T*", if (is.nan(r$T_star)) "-" else sum(U$status == "In service" & U$end >= r$T_star))
  }
  L("Bad actors flagged", sum(U$bad_actor)); cat("  ", rs_pattern(r), "\n", strrep("=", 62), "\n", sep = "")
  s <- U[U$status == "In service", ]; s <- head(s[order(-s$end), ], 12)
  cat(sprintf("  %-8s%8s%7s%14s  %s\n", "Unit", "Age", "Fails", paste("Next", r$horizon, "fails"), "Advice"))
  for (i in seq_len(nrow(s))) cat(sprintf("  %-8s%8.2f%7d%14.2f  %s\n", s$unit[i], s$end[i], s$failures[i], s$next_failures[i], s$advice[i]))
  for (i in which(U$bad_actor)) cat(sprintf("  ! Bad actor %s: %d failures vs %.2f expected (p = %.4f)\n",
                                            U$unit[i], U$failures[i], U$expected[i], U$p_excess[i]))
  cat("\n"); invisible(r)
}

plot_repairable <- function(r, file = NULL) {
  if (!is.null(file)) png(file, width = 1500, height = 620, res = 120)
  op <- par(mfrow = c(1, 2), mar = c(4.5, 4.5, 3, 1)); on.exit(par(op))
  M <- r$mcf; tg <- seq(0, max(r$units$end), length.out = 200)
  plot(M$age, M$mcf, type = "s", col = NAVY, lwd = 2, ylim = c(0, max(M$upper, r$lam * max(tg)^r$beta)),
       xlim = c(0, max(tg)), xlab = "Age", ylab = "Cumulative failures per unit", main = "Mean cumulative function")
  lines(M$age, M$lower, type = "s", col = "grey60", lty = 2); lines(M$age, M$upper, type = "s", col = "grey60", lty = 2)
  lines(tg, r$lam * tg^r$beta, col = GOLD, lwd = 2.5)
  legend("topleft", c("MCF (observed)", sprintf("%.0f%% bounds", 100 * (1 - r$alpha)), sprintf("Power-law fit  beta = %.2f", r$beta)),
         col = c(NAVY, "grey60", GOLD), lty = c(1, 2, 1), lwd = c(2, 1, 2.5), bty = "n", cex = 0.8)
  if (!is.null(r$T_star) && !is.nan(r$T_star)) {
    T <- seq(r$T_star * 0.25, r$T_star * 3, length.out = 300); C <- r$cost(T)
    plot(T, C, type = "l", col = GOLD, lwd = 2.5, ylim = c(0, max(C) * 1.05), xlab = "Replacement age T",
         ylab = "Cost per unit per time unit", main = "Repair-or-replace cost curve")
    abline(v = r$T_star, col = RED, lty = 2, lwd = 1.5)
    legend("topright", c("Cost per unit per time unit", sprintf("Optimum T* = %.1f", r$T_star)),
           col = c(GOLD, RED), lty = c(1, 2), lwd = 2, bty = "n", cex = 0.8)
  } else {
    U <- r$units; barplot(U$failures, names.arg = U$unit, col = ifelse(U$bad_actor, RED, NAVY), las = 2,
                          cex.names = 0.5, main = "Failures per unit (red = bad actor)")
  }
  if (!is.null(file)) dev.off()
  invisible(r)
}

demo <- function() {
  # 40 pumps (in dates): replacement 45,000, repair 6,000 incl. downtime, 3-year look-ahead.
  r <- repairable(read.csv("example_data.csv", stringsAsFactors = FALSE), replace_cost = 45000, repair_cost = 6000, horizon = 3)
  print(r)
  plot_repairable(r, "repairable_systems_example_R.png")
  cat("  -> Plot saved to repairable_systems_example_R.png\n")
  invisible(r)
}

if (!interactive() && sys.nframe() == 0) demo()
