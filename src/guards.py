"""Flag drug groups whose 60-day classification may be wrong.

Guards flag; they never drop. A human reads checks_findings.md and decides.
"""
import pandas as pd

NO_SUBSTITUTION = "no_substitution"
POSSIBLE_RELISTING = "possible_relisting"
LOW_UPTAKE = "low_uptake"

LOW_UPTAKE_SHARE = 0.05


def _group_frames(con):
    """Per treated group: monthly 30-day and 60-day scripts.

    A code first dispensed on or after the group's switch month is the 60-day
    listing; anything older is the 30-day sibling it substitutes for.

    Args:
        con: DuckDB connection holding item_months, item_first, group_stage.

    Returns:
        DataFrame with group_key, switch_month, month, scripts_60, scripts_30.
    """
    return con.execute(
        """
        SELECT g.group_key,
               g.switch_month,
               im.month,
               SUM(CASE WHEN f.first_month >= g.switch_month THEN im.scripts ELSE 0 END) AS scripts_60,
               SUM(CASE WHEN f.first_month <  g.switch_month THEN im.scripts ELSE 0 END) AS scripts_30
        FROM group_stage g
        JOIN item_first f  ON f.group_key = g.group_key
        JOIN item_months im ON im.item_code = f.item_code
        WHERE g.stage > 0
        GROUP BY 1, 2, 3
        ORDER BY 1, 3
        """
    ).df()


def _months_before(switch, n):
    """n calendar months strictly before switch, as YYYYMM ints."""
    year, month = divmod(switch, 100)
    out = []
    for _ in range(n):
        month -= 1
        if month == 0:
            year, month = year - 1, 12
        out.append(year * 100 + month)
    return sorted(out)


def _months_from(switch, n):
    """switch plus the n-1 months after it, as YYYYMM ints."""
    year, month = divmod(switch, 100)
    out = [switch]
    for _ in range(n - 1):
        month += 1
        if month == 13:
            year, month = year + 1, 1
        out.append(year * 100 + month)
    return out


def run_guards(con, window=6):
    """Apply every misclassification guard to every treated group.

    Args:
        con: DuckDB connection holding item_months, item_first, group_stage.
        window: months of history compared either side of the switch month.

    Returns:
        DataFrame with group_key, guard, detail. One row per flagged group per
        guard. Empty frame means nothing was flagged.
    """
    df = _group_frames(con)
    flags = []
    for group_key, g in df.groupby("group_key"):
        switch = int(g["switch_month"].iloc[0])
        pre = g[g["month"].isin(_months_before(switch, window))]
        post = g[g["month"].isin(_months_from(switch, window))]
        if pre.empty or post.empty:
            continue

        pre_30 = pre["scripts_30"].mean()
        post_30 = post["scripts_30"].mean()
        post_60 = post["scripts_60"].mean()

        # Guard 1: genuine 60-day listing shifts volume; a new brand adds volume.
        if post_60 > 0 and post_30 >= pre_30:
            flags.append((group_key, NO_SUBSTITUTION,
                          f"30-day mean {pre_30:.0f} -> {post_30:.0f}, did not fall"))

        # Guard 3: substitution leaves the 30-day code alive; relisting kills it.
        if pre_30 > 0 and post_30 == 0:
            flags.append((group_key, POSSIBLE_RELISTING,
                          f"30-day scripts fell to zero after {switch}"))

        # Guard 4: near-zero uptake suggests the sibling was matched wrongly.
        total_post = post_30 + post_60
        if total_post > 0 and post_60 / total_post < LOW_UPTAKE_SHARE:
            flags.append((group_key, LOW_UPTAKE,
                          f"60-day share {post_60 / total_post:.1%} of group volume"))

    return pd.DataFrame(flags, columns=["group_key", "guard", "detail"])
