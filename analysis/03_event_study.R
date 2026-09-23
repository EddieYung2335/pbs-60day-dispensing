# Event study: coefficients from -12 to +12 months around each group's switch.
# The pre-period coefficients are the load-bearing part. Flat leads support
# parallel trends; sloped leads do not, and that must be reported.
source("analysis/00_prep.R")
suppressPackageStartupMessages({
  library(did); library(ggplot2); library(readr); library(dplyr)
})

set.seed(20230901)

d <- prep_panel() |>
  group_by(gid, t) |>
  summarise(supply_months = sum(supply_months), g = first(g),
            stage = first(stage), arm_b = first(arm_b), .groups = "drop") |>
  mutate(log_supply = log(supply_months + 1))

event_study <- function(data, control_group, label, from_t = NULL) {
  if (!is.null(from_t)) data <- data |> filter(t >= from_t)
  att <- att_gt(yname = "log_supply", tname = "t", idname = "gid", gname = "g",
                data = data, control_group = control_group, clustervars = "gid",
                est_method = "reg", allow_unbalanced_panel = TRUE,
                base_period = "universal")
  dyn <- aggte(att, type = "dynamic", min_e = -12, max_e = 12, na.rm = TRUE)
  tibble(event_time = dyn$egt, estimate = dyn$att.egt, se = dyn$se.egt) |>
    mutate(ci_lo = estimate - 1.96 * se, ci_hi = estimate + 1.96 * se,
           outcome = "log_supply", control_arm = label)
}

d_b <- d |> filter(stage == 1 | (stage == 0 & arm_b))

es <- bind_rows(
  event_study(d,   "notyettreated", "notyettreated"),
  event_study(d_b, "nevertreated",  "nevertreated")
)
write_csv(es, "reports/event_study.csv")

# Second specification: drop the first 24 months of the series, so no comparison
# reaches back into the COVID-era volatility of 2020-21. Stage 1 switches at
# t = 39, so this still leaves 24 pre-period months. Run once, reported whatever
# the result, never re-tuned until it passes.
# Result: identical to the full series. The leads that fail the gate sit at
# t = 27 to 33 for Stage 1, already inside the trimmed window, so this remedy
# cannot reach them. Kept so the attempt is reproducible rather than asserted.
es_trim <- bind_rows(
  event_study(d,   "notyettreated", "notyettreated", from_t = 15),
  event_study(d_b, "nevertreated",  "nevertreated",  from_t = 15)
) |> mutate(window = "from 2021-09")
write_csv(bind_rows(es |> mutate(window = "full series"), es_trim),
          "reports/event_study.csv")

p <- ggplot(es |> filter(!is.na(se)), aes(event_time, estimate, colour = control_arm)) +
  geom_hline(yintercept = 0, linetype = "dotted") +
  geom_vline(xintercept = -0.5, linetype = "dashed") +
  geom_pointrange(aes(ymin = ci_lo, ymax = ci_hi), position = position_dodge(0.4)) +
  labs(title = "Effect on supply-months, by months since 60-day eligibility",
       subtitle = "Coefficients left of the dashed line test parallel trends",
       x = "Months relative to switch", y = "Log points", colour = "Control arm") +
  theme_minimal()

ggsave("reports/figures/event_study_supply.png", p, width = 9, height = 5, dpi = 150)

# Gate. base_period = "universal" makes event_time -1 the reference, so its
# coefficient is zero by construction and is excluded from the counts below.
# More than about 2 of 12 significant leads means parallel trends is not
# supported and the headline must be reported as descriptive, not causal.
report_gate <- function(tbl, label) {
  cat(sprintf("\n%s\n", label))
  pre <- tbl |> filter(event_time < 0, event_time != -1)
  for (arm in unique(pre$control_arm)) {
    a <- pre |> filter(control_arm == arm)
    sig <- a |> filter(ci_lo > 0 | ci_hi < 0)
    cat(sprintf("  %-14s %d of %d leads significant%s\n", arm, nrow(sig), nrow(a),
                if (nrow(sig) > 0)
                  paste0("  (at ", paste(sig$event_time, collapse = ", "), ")") else ""))
  }
}

report_gate(es, "Pre-trend test, full series:")
report_gate(es_trim, "Pre-trend test, from 2021-09:")
cat("\nGate: more than about 2 of 11 significant leads means parallel trends",
    "is not supported.\n")
