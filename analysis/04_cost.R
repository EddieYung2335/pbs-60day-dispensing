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

fit_cost <- function(data, yname, ptype, control_group) {
  sub <- data |>
    filter(patient_type == ptype) |>
    group_by(gid, t) |>
    summarise(y = sum(.data[[yname]]) / pmax(sum(supply_months), 1),
              g = first(g), .groups = "drop")
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

# att_gt averages across drug-form groups without weighting by volume, and cost
# per supply-month is heavily skewed: the pre-period group-month median is about
# $40 for concessional patients against a mean of $527. The government-cost
# estimates therefore describe the average group, which a handful of specialty
# medicines dominate, and are far larger than the volume-weighted cost per
# supply-month of roughly $19. Read them as a group average, not a budget figure.
cat("\nGovernment-cost estimates are unweighted averages across groups and are",
    "\ndominated by high-cost specialty medicines. See findings.md.\n")
