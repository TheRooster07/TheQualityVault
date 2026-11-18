# ==============================================================================
# hypothesis_advisor.R  —  TheQualityVault.com
# Hypothesis Test Advisor: answer a few questions, get the right test, run it.
# Base R only. Same decision logic as the Excel workbook and hypothesis_advisor.py.
#
#   source("hypothesis_advisor.R")
#   recommend("mean", groups = 2, paired = FALSE, normal = TRUE, equal_var = FALSE)
#   run_test("t2welch", a, b)
#   demo()
# ==============================================================================

TESTS <- c(
  t1 = "1-Sample t-Test", wil1 = "1-Sample Wilcoxon Signed Rank",
  tpair = "Paired t-Test", wilpair = "Wilcoxon Signed Rank (paired differences)",
  t2pool = "2-Sample t-Test (pooled)", t2welch = "2-Sample t-Test (Welch)", mw = "Mann-Whitney U",
  anova1 = "One-Way ANOVA", welchanova = "Welch's ANOVA", kw = "Kruskal-Wallis",
  mood = "Mood's Median Test", anova2 = "Two-Way ANOVA", friedman = "Friedman Test",
  chivar1 = "1-Variance Chi-Square Test", bonett1 = "1-Variance Test (Bonett)",
  ftest = "F-Test for Equal Variances", levene = "Levene's Test (Brown-Forsythe)",
  bartlett = "Bartlett's Test", prop1 = "1-Proportion Test (exact binomial)",
  prop2 = "2-Proportion Test / Fisher's Exact", mcnemar = "McNemar's Test",
  chiassoc = "Chi-Square Test of Association", pearson = "Pearson Correlation + Regression",
  spearman = "Spearman Rank Correlation", chigof = "Chi-Square Goodness of Fit",
  ad = "Anderson-Darling Normality Test")

recommend <- function(compare, groups = 2, paired = FALSE, normal = TRUE, equal_var = NULL,
                      factors = 1, outliers = FALSE, continuous_fit = TRUE) {
  g <- if (groups >= 3) 3 else groups
  ev <- isTRUE(equal_var)
  k <- switch(tolower(compare),
    mean = if (g == 1) { if (normal) "t1" else "wil1" }
           else if (g == 2) { if (paired) { if (normal) "tpair" else "wilpair" }
                              else if (normal) { if (ev) "t2pool" else "t2welch" } else "mw" }
           else if (factors >= 2) { if (normal) "anova2" else "friedman" }
           else if (normal) { if (ev) "anova1" else "welchanova" }
           else if (outliers) "mood" else "kw",
    variance = c(if (normal) "chivar1" else "bonett1", if (normal) "ftest" else "levene",
                 if (normal) "bartlett" else "levene")[g],
    proportion = c("prop1", if (paired) "mcnemar" else "prop2", "chiassoc")[g],
    relationship = if (normal) "pearson" else "spearman",
    fit = if (continuous_fit) "ad" else "chigof",
    stop("compare must be mean, variance, proportion, relationship or fit"))
  list(key = k, test = unname(TESTS[k]))
}

ad_test <- function(x) {
  n <- length(x); z <- sort((x - mean(x)) / sd(x)); F <- pnorm(z); i <- seq_len(n)
  a2 <- -n - sum((2 * i - 1) * (log(F) + log(1 - rev(F)))) / n
  a <- a2 * (1 + 0.75 / n + 2.25 / n^2)
  p <- if (a >= 0.6) exp(1.2937 - 5.709 * a + 0.0186 * a^2) else
       if (a >= 0.34) exp(0.9177 - 4.279 * a - 1.38 * a^2) else
       if (a >= 0.2) 1 - exp(-8.318 + 42.796 * a - 59.938 * a^2) else
       1 - exp(-13.436 + 101.14 * a - 223.73 * a^2)
  list(statistic = a2, p.value = p)
}

say <- function(name, stat, p, alpha, claim) {
  v <- if (p < alpha) sprintf("p = %.4f < %g -> reject H0: evidence that %s.", p, alpha, claim)
       else sprintf("p = %.4f >= %g -> fail to reject H0: no evidence that %s.", p, alpha, claim)
  sprintf("%s: statistic = %.4f.  %s", name, stat, v)
}

run_test <- function(key, ..., mu0 = 0, alpha = 0.05) {
  s <- lapply(list(...), function(x) { x <- suppressWarnings(as.numeric(x)); x[!is.na(x)] })
  grp <- function() data.frame(y = unlist(s), g = factor(rep(seq_along(s), lengths(s))))
  r <- switch(key,
    t1 = t.test(s[[1]], mu = mu0), wil1 = wilcox.test(s[[1]], mu = mu0, exact = FALSE),
    tpair = t.test(s[[1]], s[[2]], paired = TRUE),
    wilpair = wilcox.test(s[[1]], s[[2]], paired = TRUE, exact = FALSE),
    t2pool = t.test(s[[1]], s[[2]], var.equal = TRUE), t2welch = t.test(s[[1]], s[[2]]),
    mw = wilcox.test(s[[1]], s[[2]], exact = FALSE),
    anova1 = oneway.test(y ~ g, grp(), var.equal = TRUE), welchanova = oneway.test(y ~ g, grp()),
    kw = kruskal.test(y ~ g, grp()), ftest = var.test(s[[1]], s[[2]]),
    bartlett = bartlett.test(y ~ g, grp()),
    levene = { d <- grp(); d$z <- abs(d$y - ave(d$y, d$g, FUN = median)); oneway.test(z ~ g, d, var.equal = TRUE) },
    pearson = cor.test(s[[1]], s[[2]]), spearman = cor.test(s[[1]], s[[2]], method = "spearman", exact = FALSE),
    ad = ad_test(s[[1]]),
    NULL)
  if (is.null(r)) return(paste0(TESTS[[key]], ": pass counts to binom.test, fisher.test, mcnemar.test or chisq.test."))
  st <- if (key %in% c("pearson", "spearman")) unname(r$estimate) else unname(r$statistic)
  say(TESTS[[key]], st, r$p.value, alpha,
      switch(key, ad = "the data are not normal", ftest = , levene = , bartlett = "variances differ",
             pearson = , spearman = "the variables are related", "there is a difference"))
}

demo <- function() {
  a <- c(500.4, 501.2, 499.8, 500.9, 501.5, 500.2, 499.6, 501.0, 500.7, 500.1, 501.3, 500.5)
  b <- c(501.8, 502.6, 500.9, 503.1, 502.2, 501.5, 503.4, 502.0, 501.1, 502.8, 502.4, 501.7)
  cat("\nScenario: compare mean fill weight of Machine A vs Machine B (12 bottles each)\n")
  cat(" ", run_test("ad", a), " (Machine A)\n")
  cat(" ", run_test("ad", b), " (Machine B)\n")
  cat(" ", run_test("ftest", a, b), "\n")
  rec <- recommend("mean", groups = 2, paired = FALSE, normal = TRUE,
                   equal_var = var.test(a, b)$p.value >= 0.05)
  cat("\n  -> Recommended:", rec$test, "\n ", run_test(rec$key, a, b), "\n")
  cat(sprintf("  Mean A = %.3f g   Mean B = %.3f g\n\n", mean(a), mean(b)))
}

if (sys.nframe() == 0) demo()
