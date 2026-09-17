"""Diagnostics for checks_findings.md."""
import pandas as pd

from src.config import PROCESSED


def january_effect(panel):
    """Government cost per script by calendar month.

    The safety net resets each January, so government cost drops across all
    medicines including controls. Any model without calendar-month fixed
    effects will attribute part of that drop to the policy.
    """
    df = panel.copy()
    df["month_of_year"] = df["month"] % 100
    grouped = df.groupby("month_of_year").agg(
        govt=("govt_contrib", "sum"),
        scripts=("scripts_total", "sum"),
        years=("month", "nunique"),
    )
    grouped["mean_govt_per_script"] = grouped["govt"] / grouped["scripts"]
    grouped["mean_scripts"] = grouped["scripts"] / grouped["years"]
    return grouped.reset_index()[
        ["month_of_year", "mean_govt_per_script", "mean_scripts"]
    ]


def summary(panel, cohort):
    stages = cohort["stage"].value_counts().sort_index()
    lines = [
        f"panel rows: {len(panel):,}",
        f"months: {panel['month'].min()} to {panel['month'].max()}",
        "groups by stage:",
    ]
    for stage, n in stages.items():
        label = "never eligible" if stage == 0 else f"Stage {stage}"
        lines.append(f"  {label}: {n:,}")
    return "\n".join(lines)


def main():
    panel = pd.read_parquet(PROCESSED / "panel.parquet")
    cohort = pd.read_parquet(PROCESSED / "cohort.parquet")
    print(summary(panel, cohort))
    print()
    print(january_effect(panel).to_string(index=False))


if __name__ == "__main__":
    main()
