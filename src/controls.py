import pandas as pd
import numpy as np

from src.config import PROCESSED

PRE_END = 202308  # This is the last month in stage one


def assign_strata(cohort, volumes):
    df = cohort.set_index("group_key").copy()
    df["atc1"] = df["atc5"].str[0].fillna("Z")
    df["volume"] = volumes.reindex(df.index).fillna(0.0)
    # pct=True gives each group its position as a fraction from 0 - 1
    ranks = df["volume"].rank(pct=True, method="average")
    # rank * 10 for example 0.34 * 10  = 3.4
    # np.ceil(rank * 10) = ceil(3.4) = 4
    # .clip(1, 10) keeps the result between 1 and 10
    df["decile"] = np.ceil(ranks * 10).clip(1, 10).astype(int)
    df["stratum"] = df["atc1"] + "-" + df["decile"].astype(str)
    return df[["atc1", "decile", "stratum", "volume"]]


def match_controls(panel, cohort, pre_end=PRE_END):
    pre = panel[panel["month"] <= pre_end]
    # volumes = average supply_months per group_key over pre
    # supply_months = S_60 * 2 + S_30
    volumes = pre.groupby("group_key")["supply_months"].mean()
    assign_strata(cohort, volumes)


def main():
    panel = pd.read_parquet(PROCESSED / "panel.parquet")
    cohort = pd.read_parquet(PROCESSED / "cohort.parquet")
    match_controls(panel, cohort)


if __name__ == "__main__":
    main()
