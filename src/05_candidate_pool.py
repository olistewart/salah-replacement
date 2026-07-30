"""
Section 5: Candidate pool (last two seasons, threshold-free).

Every attacking player across the Big-5 leagues in the last two completed
seasons, no minutes cutoff -- low-sample players stay in the pool with a
'Low' reliability flag rather than being silently excluded.
"""

CANDIDATE_WEIGHTS = {CANDIDATE_SEASONS[0]: 1.0, CANDIDATE_SEASONS[1]: 1.0}
print("Candidate seasons:", CANDIDATE_SEASONS, "weights:", CANDIDATE_WEIGHTS)


def build_candidate_profiles(df: pd.DataFrame, candidate_seasons: list, season_weights: dict,
                              exclude_names=None) -> pd.DataFrame:
    exclude_names = exclude_names or []
    pool = df[df["is_attacking"] & df["season"].isin(candidate_seasons) & ~df["player_name"].isin(exclude_names)].copy()
    pool["recency_weight"] = pool["season"].map(season_weights)
    pool["combined_weight"] = pool["time"] * pool["recency_weight"]
    pool = pool.sort_values(["player_name", "season"])

    rows = []
    for player, group in pool.groupby("player_name"):
        total_minutes = group["time"].sum()
        total_weight = group["combined_weight"].sum()
        latest = group.iloc[-1]
        row = {
            "player_name": player,
            "total_minutes": total_minutes,
            "seasons_count": group["season"].nunique(),
            "last_team": latest["team_title"],
            "last_league": latest["league"],
            "last_position": latest["position"],
            "reliability": reliability_flag(total_minutes),
        }
        for f in CLUSTER_FEATURES:
            row[f] = (group[f] * group["combined_weight"]).sum() / total_weight
        rows.append(row)
    return pd.DataFrame(rows)


candidate_profiles = build_candidate_profiles(df, CANDIDATE_SEASONS, CANDIDATE_WEIGHTS, exclude_names=["Mohamed Salah"])
candidate_profiles.to_csv(data_path("salah_replacement_candidates_current.csv"), index=False)

print(candidate_profiles.shape)
print(candidate_profiles["reliability"].value_counts())
