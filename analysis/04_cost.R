# Secondary outcomes: cost per month of therapy, separately for concessional
# and general patients. The outcome is dollars per supply-month, not a log, so
# estimates read as dollars and are not comparable to the log-point figures in
# reports/estimates_primary.csv.
source("analysis/00_prep.R")
suppressPackageStartupMessages({
  library(did); library(readr); library(dplyr); library(purrr); library(ggplot2)
})

set.seed(20230901)

d <- prep_panel()

# One row per group-month: cost per supply-month, plus the numerator and
# denominator so a volume-weighted figure can be rebuilt from the same rows.
cost_panel <- function(data, yname, ptype) {
  data |>
    filter(patient_type == ptype) |>
    group_by(gid, t) |>
    summarise(y = sum(.data[[yname]]) / pmax(sum(supply_months), 1),
              num = sum(.data[[yname]]), den = sum(supply_months),
              g = first(g), .groups = "drop")
}

fit_cost <- function(data, yname, ptype, control_group) {
  sub <- cost_panel(data, yname, ptype)
  att <- att_gt(yname = "y", tname = "t", idname = "gid", gname = "g",
                data = sub, control_group = control_group, clustervars = "gid",
                est_method = "reg", allow_unbalanced_panel = TRUE,
                base_period = "universal")
  agg <- aggte(att, type = "simple", na.rm = TRUE)
  tibble(outcome = yname, patient_type = ptype, control_arm = control_group,
         estimate = agg$overall.att, se = agg$overall.se,
         ci_lo = agg$overall.att - 1.96 * agg$overall.se,
         ci_hi = agg$overall.att + 1.96 * agg$overall.se)
}

grid <- expand.grid(
  yname = c("patient_contrib", "govt_contrib"),
  ptype = c("concessional", "general"),
  stringsAsFactors = FALSE
)

out <- pmap_dfr(grid, function(yname, ptype)
  fit_cost(d, yname, ptype, "notyettreated"))

print(out)
write_csv(out, "reports/estimates_cost.csv")

# Patient effects are single dollars, government effects are hundreds, so a
# shared y axis would flatten the patient panel to a line at zero.
p <- ggplot(out, aes(patient_type, estimate)) +
  geom_hline(yintercept = 0, linetype = "dotted") +
  geom_pointrange(aes(ymin = ci_lo, ymax = ci_hi)) +
  facet_wrap(~outcome, scales = "free_y") +
  labs(title = "Change in cost per supply-month after 60-day eligibility",
       subtitle = paste("Dollars per month of therapy, averaged across drug-form groups.",
                        "Bars are 95% confidence intervals."),
       x = NULL, y = "Dollars per supply-month") +
  theme_minimal()

ggsave("reports/figures/cost_by_patient_type.png", p, width = 9, height = 5, dpi = 150)

cat("\nOutcome is dollars per supply-month. A negative estimate means the cost of",
    "\na month of therapy fell relative to medicines that had not yet switched.\n")

# Pre-switch baselines for the treated groups. att_gt averages across drug-form
# groups without weighting by volume, so the comparable baseline is each group's
# own pre-period mean, averaged unweighted across groups (group_mean). The
# volume-weighted figure is what a budget line would show. The gap between the
# two, and between median and group-month mean, is the skew findings.md warns
# about when reading the government-cost estimates.
baseline <- pmap_dfr(grid, function(yname, ptype) {
  pre <- cost_panel(d, yname, ptype) |> filter(g > 0, t < g)
  per_group <- pre |> group_by(gid) |> summarise(m = mean(y), .groups = "drop")
  tibble(outcome = yname, patient_type = ptype,
         group_mean = mean(per_group$m),
         group_month_median = median(pre$y),
         group_month_mean = mean(pre$y),
         group_month_max = max(pre$y),
         volume_weighted = sum(pre$num) / sum(pre$den))
})

print(baseline, width = Inf)
write_csv(baseline, "reports/cost_baseline.csv")

cat("\nGovernment-cost estimates are unweighted averages across groups and are",
    "\ndominated by high-cost specialty medicines. See findings.md.\n")
