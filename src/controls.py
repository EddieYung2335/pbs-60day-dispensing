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
    strata = assign_strata(cohort, volumes)
    stage = cohort.set_index("group_key")["stage"]

    treated = strata[stage.reindex(strata.index) == 1]
    never = strata[stage.reindex(strata.index) == 0]

    # strata found in both treated and never
    keep_strata = set(treated["stratum"]) & set(never["stratum"])
    # A stage 1 med is kept if only its bucket contain at least one stage 0 medicine
    rows = [
        (g, s, "treated") for g, s in treated["stratum"].items() if s in keep_strata
    ]
    # A stage 0 medicine is kept only if its bucket also holds at least one Stage 1 medicine
    # for each stage 0 medicine g, with its bucket s:
    # if s is one of the 21 allowed buckets:
    # add (g, s, "matched_control") to the output
    # else: skip
    rows += [
        (g, s, "matched_control")
        for g, s in never["stratum"].items()
        if s in keep_strata
    ]
    return pd.DataFrame(rows, columns=["group_key", "stratum", "role"])


def main():
    panel = pd.read_parquet(PROCESSED / "panel.parquet")
    cohort = pd.read_parquet(PROCESSED / "cohort.parquet")
    out = match_controls(panel, cohort)
    out.to_parquet(PROCESSED / "matched_controls.parquet", index=False)
    counts = out["role"].value_counts()
    print(counts.to_string())
    print(f"strata used: {out['stratum'].nunique()}")
    unmatched = cohort[(cohort["stage"] == 1)]["group_key"].nunique() - counts.get(
        "treated", 0
    )
    print(f"Stage 1 groups with no available control: {unmatched}")


if __name__ == "__main__":
    main()
