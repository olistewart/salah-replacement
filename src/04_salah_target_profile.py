"""
Section 4: Salah target profile (2017-2025, equal-weighted).

Builds the target vector every candidate gets compared against: Salah's
own per-90 output at Liverpool, each season weighted equally, most recent
in-progress season (2025-26) excluded.
"""

salah_df = df[
    (df["player_name"] == "Mohamed Salah") &
    (df["team_title"].str.contains("Liverpool", case=False, na=False))
].copy()

print(salah_df[["season", "team_title", "time"] + CLUSTER_FEATURES].sort_values("season"))

# Weighting across the full 2017-2026 window
# Drop 2025-26 season
seasons_present = sorted(salah_df["season"].dropna().unique())
seasons_present = seasons_present[:-1]
# For equal weighting, set each season's weight to 1.0.
# To manually set weights, you could do: salah_weights = {2017: 0.5, 2018: 0.7, 2019: 1.0, ...}
salah_weights = {s: 1.0 for s in seasons_present}
print("Season weights:", salah_weights)


def build_target_vector(player_df: pd.DataFrame, season_weights: dict, name: str) -> pd.Series:
    d = player_df[player_df["season"].isin(season_weights.keys())].copy()
    if d.empty:
        raise ValueError("No rows found for the requested seasons.")
    d["target_weight"] = d["season"].map(season_weights) * d["time"]
    total_weight = d["target_weight"].sum()
    target = {f: (d[f] * d["target_weight"]).sum() / total_weight for f in CLUSTER_FEATURES}
    return pd.Series(target, name=name)


salah_target = build_target_vector(salah_df, salah_weights, "Mohamed Salah target")
print(salah_target)
