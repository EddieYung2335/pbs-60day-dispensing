# arrow library can read parquet files 
# dplyr gives table verbs: mutate, filter, left join, select
suppressPackageStartupMessages({
  library(arrow); library(dplyr)
})

MONTH_ORIGIN = 202007 # t = 1

# Turn every month into counter t
month_to_t <- function(yyyymm) {
  year = yyyymm %/% 100  # Divide 100 and throw away the remainder 
  month = yyyymm %% 100  # Divide 100 and only keeping the remainder
  oy <- MONTH_ORIGIN %/% 100 
  om <- MONTH_ORIGIN %% 100 
  # For example 2021008 
  # (2021 - 2020) * 12 = 1 * 12 = 12 
  # (8 - 7) + 1 = 1 + 1 = 2 
  # 12 + 2 = 14
  (year - oy) * 12 + (month - om) + 1 
}

prep_panel <- function(root = ".") {
  panel  <- read_parquet(file.path(root, "data/processed/panel.parquet"))
  cohort <- read_parquet(file.path(root, "data/processed/cohort.parquet"))
  ctrls  <- read_parquet(file.path(root, "data/processed/matched_controls.parquet"))

  # Assign an id to the group_key, because the model we want to use later do not read long name 
  ids <- tibble(group_key = sort(unique(panel$group_key))) |>
    mutate(gid = row_number())

  panel |>
    left_join(cohort |> select(group_key, stage, switch_month), by = "group_key") |>
    left_join(ids, by = "group_key") |>
    
    mutate(
           t = month_to_t(month),
           g = ifelse(is.na(switch_month), 0L, as.integer(month_to_t(switch_month))),
                 month_of_year = factor(month %% 100),
          log_scripts = log(scripts_total + 1),
          log_supply  = log(supply_months + 1),
          govt_per_supply    = govt_contrib / pmax(supply_months, 1),
          patient_per_supply = patient_contrib / pmax(supply_months, 1),
          arm_b = group_key %in% ctrls$group_key[ctrls$role == "matched_control"]
    ) |>
    filter(!is.na(gid))
}







