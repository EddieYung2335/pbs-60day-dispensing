import pandas as pd

from src.controls import assign_strata, match_controls


def test_stratum_combines_atc1_and_volume_decile():
    # 18 low-volume fillers make 20 groups: neighbours sit 0.05 apart in pct
    # rank, so the top two (1.00, 0.95) can share decile 10. With 3 groups
    # they sit 0.33 apart and can never share a decile.
    fillers = [f"F{i} | F" for i in range(18)]
    cohort = pd.DataFrame(
        [("A | X", 1, "C10AA05"), ("B | Y", 0, "C07AB02"), ("C | Z", 0, "N06AB03")]
        + [(f, 0, "J01CA04") for f in fillers],
        columns=["group_key", "stage", "atc5"],
    )
    volumes = pd.Series(
        [1000.0, 900.0, 10.0] + [20.0 + i for i in range(18)],
        index=["A | X", "B | Y", "C | Z"] + fillers,
    )
    strata = assign_strata(cohort, volumes)
    assert strata.loc["A | X", "atc1"] == "C"
    assert strata.loc["C | Z", "atc1"] == "N"
    # similar volume and same ATC-1 must land in the same stratum
    assert strata.loc["A | X", "stratum"] == strata.loc["B | Y", "stratum"]
    # very different volume must land in a different decile
    assert strata.loc["C | Z", "decile"] != strata.loc["A | X", "decile"]


def test_only_never_eligible_groups_become_controls():
    cohort = pd.DataFrame(
        [("A | X", 1, "C10AA05"), ("B | Y", 0, "C07AB02"), ("D | W", 2, "C08CA01")],
        columns=["group_key", "stage", "atc5"],
    )
    panel = pd.DataFrame(
        [
            (g, m, "concessional", 100.0)
            for g in ["A | X", "B | Y", "D | W"]
            for m in [202301, 202302, 202303]
        ],
        columns=["group_key", "month", "patient_type", "supply_months"],
    )
    out = match_controls(panel, cohort)
    controls = set(out[out["role"] == "matched_control"]["group_key"])
    assert controls == {"B | Y"}  # stage 2 group is not a never-eligible control
