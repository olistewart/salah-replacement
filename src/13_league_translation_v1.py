"""
Section 10: League translation model (v1).

First pass: median ratio of observed cross-league transfers per league
pair, falling back to a coarse league-strength-index proxy when a pair
has too few observed transfers. Superseded by v2 (14_league_translation_v2.py)
-- kept here since it's what the notebook actually ran and compared
against the v2 output, not because it's the recommended version to use.
"""

'''League Translation Model'''

# Cross-league transfers
def find_league_transfers(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["is_attacking"]].sort_values(["player_name", "season"])
    rows = []
    for player, group in d.groupby("player_name"):
        group = group.sort_values("season")
        for i in range(len(group) - 1):
            before, after = group.iloc[i], group.iloc[i + 1]
            if before["league"] == after["league"] or after["season"] - before["season"] != 1:
                continue
            row = {"player_name": player, "from_league": before["league"], "to_league": after["league"],
                   "from_season": before["season"], "to_season": after["season"]}
            for f in CLUSTER_FEATURES:
                row[f"{f}_before"], row[f"{f}_after"] = before[f], after[f]
                denom = before[f] if pd.notna(before[f]) and before[f] > 1e-6 else np.nan
                row[f"{f}_ratio"] = after[f] / denom if pd.notna(denom) else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def build_league_translation_table(transfers: pd.DataFrame, min_pair_transfers: int = 5) -> pd.DataFrame:
    if transfers.empty:
        return pd.DataFrame(columns=["from_league", "to_league", "n_transfers"] + CLUSTER_FEATURES)
    ratio_cols = [f"{f}_ratio" for f in CLUSTER_FEATURES]
    grouped = transfers.groupby(["from_league", "to_league"])
    summary = grouped[ratio_cols].median().reset_index()
    summary["n_transfers"] = grouped.size().values
    summary = summary.rename(columns={f"{f}_ratio": f for f in CLUSTER_FEATURES})
    summary["confidence"] = np.where(summary["n_transfers"] >= min_pair_transfers,
                                     f"Higher (>={min_pair_transfers} observed transfers)",
                                     f"Low (<{min_pair_transfers} observed transfers)")
    return summary


def league_strength_index(df: pd.DataFrame) -> pd.Series:
    attackers = df[df["is_attacking"]]
    idx_cols = ["npxG_per90", "xGChain_per90", "key_passes_per90"]
    return attackers.groupby("league")[idx_cols].mean().mean(axis=1).sort_values(ascending=False)


def translate_player_stats(player_row, target_league, translation_table, strength_index, min_pair_transfers=5):
    from_league = player_row["last_league"]
    if from_league == target_league:
        return {**{f: player_row[f] for f in CLUSTER_FEATURES}, "method": "same_league", "confidence": "N/A"}

    match = translation_table[(translation_table["from_league"] == from_league) &
                               (translation_table["to_league"] == target_league)]
    if not match.empty and match.iloc[0]["n_transfers"] >= min_pair_transfers:
        row = match.iloc[0]
        return {**{f: player_row[f] * row[f] for f in CLUSTER_FEATURES},
                "method": "empirical_transfer_pairs", "confidence": f"n={int(row['n_transfers'])} observed transfers"}

    if from_league in strength_index.index and target_league in strength_index.index:
        ratio = strength_index[target_league] / strength_index[from_league]
        return {**{f: player_row[f] * ratio for f in CLUSTER_FEATURES},
                "method": "league_strength_index_fallback",
                "confidence": "Low -- generic league-strength proxy, not player-specific"}

    return {**{f: player_row[f] for f in CLUSTER_FEATURES},
            "method": "no_adjustment_insufficient_data", "confidence": "None"}


transfers = find_league_transfers(df)
translation_table = build_league_translation_table(transfers, min_pair_transfers=5)
strength_index = league_strength_index(df)

print(f"Observed {len(transfers)} cross-league transfers in the dataset window")
print(translation_table)
print("\nLeague strength index (fallback proxy):")
print(strength_index)


# Example: project a Ligue 1 candidate's numbers into the Premier League
ligue1_candidates = ranked[ranked["last_league"] == "Ligue 1"]
if not ligue1_candidates.empty:
    example_player = ligue1_candidates.iloc[0]
    projection = translate_player_stats(example_player, "Premier League", translation_table, strength_index)
    print(f"{example_player['player_name']} (Ligue 1) projected into the Premier League:")
    for k, v in projection.items():
        print(f"  {k}: {v}")
else:
    print("No Ligue 1 players in the current shortlist to demo with -- re-run against the full candidate pool.")


selected_players_for_translation = candidate_profiles[candidate_profiles['player_name'].isin(selected_pca_names)].copy()

comparison_data = []
for idx, player_row in selected_players_for_translation.iterrows():
    player_name = player_row['player_name']
    current_league = player_row['last_league']

    # Get original stats
    original_stats = {f: player_row[f] for f in CLUSTER_FEATURES}

    # Get translated stats
    translated_projection = translate_player_stats(
        player_row,
        "Premier League",
        translation_table,
        strength_index
    )
    translated_stats = {f: translated_projection[f] for f in CLUSTER_FEATURES}

    # Prepare data for comparison
    row_data = {
        'Player': player_name,
        'Current_League': current_league,
        'Translation_Method': translated_projection['method'],
        'Confidence': translated_projection['confidence']
    }

    for feature in CLUSTER_FEATURES:
        row_data[f'{feature}_Original'] = original_stats[feature]
        row_data[f'{feature}_Translated_PL'] = translated_stats[feature]
        row_data[f'{feature}_Ratio'] = translated_stats[feature] / original_stats[feature] if original_stats[feature] != 0 else np.nan

    comparison_data.append(row_data)

comparison_df = pd.DataFrame(comparison_data)

print(comparison_df.set_index(['Player', 'Current_League', 'Translation_Method', 'Confidence']).T.round(3))


selected_players_for_translation_proxy = candidate_profiles[candidate_profiles['player_name'].isin(selected_pca_names)].copy()

comparison_data_proxy = []
for idx, player_row in selected_players_for_translation_proxy.iterrows():
    player_name = player_row['player_name']
    current_league = player_row['last_league']

    # Get original stats
    original_stats = {f: player_row[f] for f in CLUSTER_FEATURES}

    # Get translated stats, forcing fallback to league_strength_index by setting a high min_pair_transfers
    translated_projection_proxy = translate_player_stats(
        player_row,
        "Premier League",
        translation_table,
        strength_index,
        min_pair_transfers=1000 # Set a very high number to force fallback
    )
    translated_stats_proxy = {f: translated_projection_proxy[f] for f in CLUSTER_FEATURES}

    # Prepare data for comparison
    row_data_proxy = {
        'Player': player_name,
        'Current_League': current_league,
        'Translation_Method': translated_projection_proxy['method'],
        'Confidence': translated_projection_proxy['confidence']
    }

    for feature in CLUSTER_FEATURES:
        row_data_proxy[f'{feature}_Original'] = original_stats[feature]
        row_data_proxy[f'{feature}_Translated_PL_Proxy'] = translated_stats_proxy[feature]
        row_data_proxy[f'{feature}_Ratio_Proxy'] = translated_stats_proxy[feature] / original_stats[feature] if original_stats[feature] != 0 else np.nan

    comparison_data_proxy.append(row_data_proxy)

comparison_df_proxy = pd.DataFrame(comparison_data_proxy)

print("\n--- Translations using League Strength Index Proxy ---")
print(comparison_df_proxy.set_index(['Player', 'Current_League', 'Translation_Method', 'Confidence']).T.round(3))
