source("analysis/00_prep.R")
suppressPackageStartupMessages({ library(ggplot2); library(readr) })
# outputs land here; recursive = TRUE builds reports/ on the way
dir.create("reports/figures", recursive = TRUE, showWarnings = FALSE)

d <- prep_panel()
s1 <- d |> filter(stage == 1)

pre  <- s1 |> filter(month >= 202209, month <= 202308) |>
  summarise(scripts = sum(scripts_total)) |> pull(scripts)
post <- s1 |> filter(month >= 202309, month <= 202408) |>
  summarise(scripts = sum(scripts_total)) |> pull(scripts)

pct <- 100 * (post - pre) / pre
cat(sprintf("Stage 1 scripts, 12 months before: %s\n", format(pre, big.mark = ",")))
cat(sprintf("Stage 1 scripts, 12 months after:  %s\n", format(post, big.mark = ",")))
cat(sprintf("Naive change: %.1f%%\n", pct))

write_csv(
  tibble(outcome = "scripts_naive_pct_change", estimate = pct,
         se = NA_real_, ci_lo = NA_real_, ci_hi = NA_real_,
         control_arm = "none (before/after only)"),
  "reports/estimates_naive.csv"
)

monthly <- s1 |> group_by(month) |>
  summarise(scripts = sum(scripts_total), supply = sum(supply_months), .groups = "drop") |>
  mutate(date = as.Date(paste0(month %/% 100, "-", sprintf("%02d", month %% 100), "-01")))

p <- ggplot(monthly, aes(date)) +
  geom_line(aes(y = scripts, colour = "Prescriptions")) +
  geom_line(aes(y = supply,  colour = "Supply-months")) +
  geom_vline(xintercept = as.Date("2023-09-01"), linetype = "dashed") +
  labs(title = "Stage 1 medicines: prescriptions fell, supply did not",
       subtitle = "Dashed line: 60-day dispensing begins, 1 September 2023",
       x = NULL, y = NULL, colour = NULL) +
  theme_minimal()

ggsave("reports/figures/naive_scripts.png", p, width = 9, height = 5, dpi = 150)




