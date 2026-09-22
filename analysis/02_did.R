source("analysis/00_prep.R")
suppressPackageStartupMessages({ library(did); library(readr); library(dplyr) })

set.seed(20230901)

d <- prep_panel() |>
  group_by(gid, t) |>
  summarise(across(c(scripts_total, supply_months, govt_contrib, patient_contrib), sum),
            g = first(g), stage = first(stage), arm_b = first(arm_b),
            month_of_year = first(month_of_year), .groups = "drop") |>
  mutate(log_supply = log(supply_months + 1),
         log_scripts = log(scripts_total + 1))


run_cs <- function(data, yname, control_group) {
att <- att_gt(
  yname = yname, tname = "t", idname = "gid", gname = "g",
  data = data, control_group = control_group,
  clustervars = "gid", est_method = "reg",
  allow_unbalanced_panel = TRUE, base_period = "universal"
)
agg <- aggte(att, type = "simple", na.rm = TRUE)
tibble(
    outcome = yname,
    control_arm = control_group,
    estimate = agg$overall.att,
    se = agg$overall.se,
    ci_lo = agg$overall.att - 1.96 * agg$overall.se,
    ci_hi = agg$overall.att + 1.96 * agg$overall.se,
    n_groups = length(unique(data$gid))
  )
}

# Arm A: not-yet-treated. All groups, later stages act as controls.
arm_a_supply  <- run_cs(d, "log_supply",  "notyettreated")
arm_a_scripts <- run_cs(d, "log_scripts", "notyettreated")

# Arm B: matched never-eligible only. Stage 1 treated plus matched controls.
d_b <- d |> filter(stage == 1 | (stage == 0 & arm_b))
arm_b_supply  <- run_cs(d_b, "log_supply",  "nevertreated")
arm_b_scripts <- run_cs(d_b, "log_scripts", "nevertreated")

out <- bind_rows(arm_a_supply, arm_a_scripts, arm_b_supply, arm_b_scripts)
print(out)
write_csv(out, "reports/estimates_primary.csv")

cat("\nInterpretation: estimates are in log points. Multiply by 100 for approximate percent.\n")

# Cross-check: Sun-Abraham interaction-weighted estimator. Different estimator,
# same design. Material disagreement with Callaway-Sant'Anna is itself a finding.
# Calendar-month fixed effects enter explicitly here (spec 9.5) - the January
# safety-net reset moves all groups, treated and control alike.
suppressPackageStartupMessages(library(fixest))

d_sa <- d |>
  mutate(
    month_of_year = factor(((t - 1 + 6) %% 12) + 1),  # t = 1 is July 2020
    cohort_g = ifelse(g == 0, 10000, g)               # fixest wants a large value for never-treated
  )

sa <- feols(
  log_supply ~ sunab(cohort_g, t) | gid + month_of_year,
  data = d_sa, cluster = ~gid
)
sa_att <- summary(sa, agg = "att")
print(sa_att)

sa_row <- tibble(
  outcome = "log_supply",
  control_arm = "sunab (never-treated implicit)",
  estimate = coef(sa_att)[[1]],
  se = se(sa_att)[[1]],
  ci_lo = coef(sa_att)[[1]] - 1.96 * se(sa_att)[[1]],
  ci_hi = coef(sa_att)[[1]] + 1.96 * se(sa_att)[[1]],
  n_groups = length(unique(d_sa$gid))
)
write_csv(bind_rows(out, sa_row), "reports/estimates_primary.csv")

cat("\nCallaway-Sant'Anna vs Sun-Abraham gap: ",
    sprintf("%.4f log points\n", abs(arm_a_supply$estimate - sa_row$estimate)))

