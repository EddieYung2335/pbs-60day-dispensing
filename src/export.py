"""Flatten the panel into CSVs Tableau Public can connect to directly."""
import pandas as pd

from src.config import PROCESSED, ROOT

STAGE_LABELS = {0: "Never eligible", 1: "Stage 1", 2: "Stage 2", 3: "Stage 3"}


def build_trend(panel, cohort):
    df = panel.merge(cohort[["group_key", "stage"]], on="group_key", how="left")
    df["group_set"] = df["stage"].map(STAGE_LABELS)
    out = df.groupby(["month", "group_set"], as_index=False).agg(
        scripts=("scripts_total", "sum"),
        supply_months=("supply_months", "sum"),
    )
    out["date"] = pd.to_datetime(
        out["month"].astype(str), format="%Y%m"
    ).dt.strftime("%Y-%m-%d")
    return out


def main():
    panel = pd.read_parquet(PROCESSED / "panel.parquet")
    cohort = pd.read_parquet(PROCESSED / "cohort.parquet")
    build_trend(panel, cohort).to_csv(PROCESSED / "dashboard_trend.csv", index=False)
    event = pd.read_csv(ROOT / "reports" / "event_study.csv")
    event.to_csv(PROCESSED / "dashboard_event.csv", index=False)
    print(f"wrote {PROCESSED / 'dashboard_trend.csv'}")
    print(f"wrote {PROCESSED / 'dashboard_event.csv'}")


if __name__ == "__main__":
    main()
