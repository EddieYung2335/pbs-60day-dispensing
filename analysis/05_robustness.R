# Robustness, all fixed in advance before results were seen.
#   1. Placebo switch 12 months early, using only pre-policy data. Expect null.
#   2. Supply multiplier 1.8 and 1.9 instead of 2.0.
#   3. Government cost with and without under-co-payment scripts.
source("analysis/00_prep.R")
suppressPackageStartupMessages({ library(did); library(readr); library(dplyr) })

set.seed(20230901)

d_raw <- prep_panel()
SWITCH_T <- month_to_t(202309)

collapse <- function(data, multiplier) {
  data |>
    group_by(gid, t) |>
    summarise(scripts_30 = sum(scripts_30), scripts_60 = sum(scripts_60),
              g = first(g), .groups = "drop") |>
    mutate(log_supply = log(scripts_30 + multiplier * scripts_60 + 1))
}

fit <- function(data, control_group = "notyettreated") {
  att <- att_gt(yname = "log_supply", tname = "t", idname = "gid", gname = "g",
                data = data, control_group = control_group, clustervars = "gid",
                est_method = "reg", allow_unbalanced_panel = TRUE,
                base_period = "universal")
  aggte(att, type = "simple", na.rm = TRUE)
}

rows <- list()

# Placebo: pretend the switch happened 12 months early, and drop all real
# post-policy data so the true policy cannot leak into the estimate.
placebo <- collapse(d_raw, 2.0) |>
  filter(t < SWITCH_T) |>
  mutate(g = ifelse(g > 0, g - 12L, 0L)) |>
  filter(g == 0 | g < SWITCH_T)
pl <- fit(placebo)
rows[[length(rows) + 1]] <- tibble(
  check = "placebo_switch_202209", estimate = pl$overall.att, se = pl$overall.se,
  ci_lo = pl$overall.att - 1.96 * pl$overall.se,
  ci_hi = pl$overall.att + 1.96 * pl$overall.se,
  verdict = ifelse(pl$overall.att - 1.96 * pl$overall.se <= 0 &
                     pl$overall.att + 1.96 * pl$overall.se >= 0,
                   "PASS - null as expected", "FAIL - effect on a fake date")
)

for (mult in c(1.8, 1.9)) {
  f <- fit(collapse(d_raw, mult))
  rows[[length(rows) + 1]] <- tibble(
    check = sprintf("multiplier_%.1f", mult), estimate = f$overall.att,
    se = f$overall.se, ci_lo = f$overall.att - 1.96 * f$overall.se,
    ci_hi = f$overall.att + 1.96 * f$overall.se, verdict = "sensitivity"
  )
}

# Government cost per supply-month, excluding under-co-payment scripts.
# Those rows carry zero government contribution by construction, so including
# them makes a shift in patient mix look like a cost effect.
cost_check <- function(data, keep_under) {
  sub <- data |>
    filter(keep_under | script_type == "ABOVE CO-PAYMENT") |>
    group_by(gid, t) |>
    summarise(y = sum(govt_contrib) / pmax(sum(supply_months), 1),
              g = first(g), .groups = "drop")
  att <- att_gt(yname = "y", tname = "t", idname = "gid", gname = "g",
                data = sub, control_group = "notyettreated", clustervars = "gid",
                est_method = "reg", allow_unbalanced_panel = TRUE,
                base_period = "universal")
  aggte(att, type = "simple", na.rm = TRUE)
}

for (keep in c(TRUE, FALSE)) {
  f <- cost_check(d_raw, keep)
  rows[[length(rows) + 1]] <- tibble(
    check = ifelse(keep, "govt_cost_all_scripts", "govt_cost_above_copay_only"),
    estimate = f$overall.att, se = f$overall.se,
    ci_lo = f$overall.att - 1.96 * f$overall.se,
    ci_hi = f$overall.att + 1.96 * f$overall.se,
    verdict = "sensitivity"
  )
}

out <- bind_rows(rows)
print(out)
write_csv(out, "reports/robustness.csv")

cat("\nGATE: the placebo row must read PASS. An effect on a date when nothing",
    "\nhappened means the design is fitting noise.\n")
