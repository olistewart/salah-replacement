"""
Section 11: League translation model (v2) -- the recommended version.

Upgrades over v1: minutes-weighted (harmonic mean before/after),
cluster-aware (role-specific) ratios with a pooled fallback, weighted
regression instead of a flat ratio where there's enough data (>=10
weighted-equivalent transfers), and a properly z-scored fallback
distribution-transfer for league pairs with too little signal.
"""

def _weighted_median(values, weights):
    d = pd.DataFrame({"v": values, "w": weights}).dropna()
    if d.empty:
        return np.nan
    d = d.sort_values("v")
    cum = d["w"].cumsum()
    cutoff = d["w"].sum() / 2.0
    hit = d.loc[cum >= cutoff]
    return hit["v"].iloc[0] if not hit.empty else np.nan


def find_league_transfers(df: pd.DataFrame) -> pd.DataFrame:
    """Players who moved between two Big-5 leagues across consecutive
    seasons, with a reliability weight (harmonic mean of before/after
    minutes) attached to each observation."""
    d = df[df["is_attacking"]].sort_values(["player_name", "season"])
    rows = []
    for player, group in d.groupby("player_name"):
        group = group.sort_values("season")
        for i in range(len(group) - 1):
            before, after = group.iloc[i], group.iloc[i + 1]
            if before["league"] == after["league"] or after["season"] - before["season"] != 1:
                continue
            m1, m2 = before["time"], after["time"]
            weight = (2 * m1 * m2 / (m1 + m2)) if (m1 + m2) > 0 else 0.0
            row = {
                "player_name": player, "from_league": before["league"], "to_league": after["league"],
                "from_season": before["season"], "to_season": after["season"], "weight": weight,
            }
            for f in CLUSTER_FEATURES:
                row[f"{f}_before"], row[f"{f}_after"] = before[f], after[f]
                denom = before[f] if pd.notna(before[f]) and before[f] > 1e-6 else np.nan
                row[f"{f}_ratio"] = after[f] / denom if pd.notna(denom) else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def tag_transfer_clusters(transfers: pd.DataFrame, scaler, kmeans) -> pd.DataFrame:
    """Assign each transfer's pre-move cluster using the SAME fitted
    scaler/kmeans as the main candidate-pool clustering, so cluster IDs are
    directly comparable to Salah's own cluster elsewhere in the notebook."""
    transfers = transfers.copy()
    if transfers.empty:
        transfers["from_cluster"] = pd.Series(dtype="Int64")
        return transfers
    before_cols = [f"{f}_before" for f in CLUSTER_FEATURES]
    X_before = transfers[before_cols].rename(columns=lambda c: c.replace("_before", ""))
    X_scaled = scaler.transform(X_before[CLUSTER_FEATURES])
    transfers["from_cluster"] = kmeans.predict(X_scaled)
    return transfers


transfers = find_league_transfers(df)
transfers = tag_transfer_clusters(transfers, scaler, kmeans)
print(f"Observed {len(transfers)} cross-league transfers in the dataset window")
print(transfers[["player_name", "from_league", "to_league", "from_cluster", "weight"]].head(10))


MIN_REGRESSION_N = 10  # weighted-equivalent transfers needed to trust a regression fit
MIN_RATIO_N = 5        # weighted-equivalent transfers needed to trust a weighted-median ratio


def _fit_group_translation(group: pd.DataFrame) -> dict:
    """For one (from_league, to_league[, cluster]) group of transfers,
    return per-feature regression coeffs (if enough data), weighted-median
    ratios, and the effective sample size."""
    out = {"n_transfers": len(group), "total_weight": group["weight"].sum()}

    for f in CLUSTER_FEATURES:
        b, a, w = group[f"{f}_before"], group[f"{f}_after"], group["weight"]
        valid = b.notna() & a.notna() & (w > 0)
        if valid.sum() >= MIN_REGRESSION_N:
            slope, intercept = np.polyfit(b[valid], a[valid], deg=1, w=w[valid])
            out[f"{f}_slope"], out[f"{f}_intercept"] = slope, intercept
        else:
            out[f"{f}_slope"], out[f"{f}_intercept"] = np.nan, np.nan
        out[f"{f}_ratio"] = _weighted_median(group.loc[valid, f"{f}_ratio"], w[valid])
    return out


def build_translation_tables(transfers: pd.DataFrame):
    """Returns (cluster_specific_table, pooled_table). Cluster-specific is
    keyed by (from_league, to_league, from_cluster); pooled ignores cluster."""
    if transfers.empty:
        empty = pd.DataFrame(columns=["from_league", "to_league", "n_transfers"])
        return empty, empty

    cluster_rows = []
    for (fl, tl, cl), g in transfers.groupby(["from_league", "to_league", "from_cluster"]):
        cluster_rows.append({"from_league": fl, "to_league": tl, "from_cluster": cl, **_fit_group_translation(g)})
    cluster_table = pd.DataFrame(cluster_rows)

    pooled_rows = []
    for (fl, tl), g in transfers.groupby(["from_league", "to_league"]):
        pooled_rows.append({"from_league": fl, "to_league": tl, **_fit_group_translation(g)})
    pooled_table = pd.DataFrame(pooled_rows)

    def _tier(n):
        if n >= MIN_REGRESSION_N:
            return f"Regression (n>={MIN_REGRESSION_N})"
        if n >= MIN_RATIO_N:
            return f"Weighted-median ratio ({MIN_RATIO_N}<=n<{MIN_REGRESSION_N})"
        return f"Insufficient (n<{MIN_RATIO_N}) -- falls back to league-strength proxy"

    cluster_table["tier"] = cluster_table["n_transfers"].apply(_tier)
    pooled_table["tier"] = pooled_table["n_transfers"].apply(_tier)
    return cluster_table, pooled_table


translation_by_cluster, translation_pooled = build_translation_tables(transfers)

print("=== Pooled (all attackers) league-pair table ===")
print(translation_pooled[["from_league", "to_league", "n_transfers", "tier"]] if not translation_pooled.empty else "No transfers observed.")
print("\n=== Cluster-specific table (role-aware) ===")
print(translation_by_cluster[["from_league", "to_league", "from_cluster", "n_transfers", "tier"]] if not translation_by_cluster.empty else "No transfers observed.")

# Diagnostic: how much of the model actually rests on real signal vs. fallback?
if not translation_by_cluster.empty:
    tier_counts = translation_by_cluster["tier"].value_counts()
    print("\nCluster-specific cells by tier:\n", tier_counts)


def league_strength_index(df: pd.DataFrame) -> pd.Series:
    """Composite league-strength proxy: z-score EVERY cluster feature
    across the dataset first (fixes the old version, which averaged raw
    per-90 columns on very different scales -- key_passes_per90 (~2.0) was
    silently dominating npxG_per90 (~0.4) in a plain mean), then average the
    standardized scores."""
    attackers = df[df["is_attacking"]].dropna(subset=CLUSTER_FEATURES).copy()
    means, stds = attackers[CLUSTER_FEATURES].mean(), attackers[CLUSTER_FEATURES].std().replace(0, 1)
    z = (attackers[CLUSTER_FEATURES] - means) / stds
    z["league"] = attackers["league"].values
    return z.groupby("league")[CLUSTER_FEATURES].mean().mean(axis=1).sort_values(ascending=False)


def _league_feature_stats(df: pd.DataFrame) -> dict:
    """Per-league mean/std for every cluster feature -- the basis for the
    fallback distribution-transfer (see translate_player_stats)."""
    attackers = df[df["is_attacking"]].dropna(subset=CLUSTER_FEATURES)
    return {
        "mean": attackers.groupby("league")[CLUSTER_FEATURES].mean(),
        "std": attackers.groupby("league")[CLUSTER_FEATURES].std().replace(0, 1),
    }


strength_index = league_strength_index(df)
league_feature_stats = _league_feature_stats(df)

print("League strength index (composite, z-scored):")
print(strength_index)


def translate_player_stats(player_row: pd.Series, target_league: str, translation_by_cluster: pd.DataFrame,
                            translation_pooled: pd.DataFrame, league_feature_stats: dict) -> dict:
    """Project a player's per-90 numbers into a different league, trying
    the most specific reliable estimate first:
      1. cluster-specific regression / weighted-median ratio
      2. pooled (all-attacker) regression / weighted-median ratio
      3. fallback: re-express the player's z-score in the 'from' league's
         attacking population against the 'to' league's population
         (a proper distribution transfer, not a single blunt multiplier).
    """
    from_league = player_row["last_league"]
    if from_league == target_league:
        return {**{f: player_row[f] for f in CLUSTER_FEATURES}, "method": "same_league",
                "confidence": "N/A", "granularity": "N/A"}

    cluster = player_row.get("cluster", np.nan)

    def _apply_tier_row(row, granularity):
        if row["n_transfers"] >= MIN_REGRESSION_N:
            result = {f: row[f"{f}_slope"] * player_row[f] + row[f"{f}_intercept"] for f in CLUSTER_FEATURES}
            return {**result, "method": "weighted_regression", "confidence": f"n={int(row['n_transfers'])}", "granularity": granularity}
        if row["n_transfers"] >= MIN_RATIO_N:
            result = {f: player_row[f] * row[f"{f}_ratio"] for f in CLUSTER_FEATURES if pd.notna(row[f"{f}_ratio"])}
            for f in CLUSTER_FEATURES:
                result.setdefault(f, player_row[f])
            return {**result, "method": "weighted_median_ratio", "confidence": f"n={int(row['n_transfers'])}", "granularity": granularity}
        return None

    if pd.notna(cluster) and not translation_by_cluster.empty:
        match = translation_by_cluster[
            (translation_by_cluster["from_league"] == from_league) &
            (translation_by_cluster["to_league"] == target_league) &
            (translation_by_cluster["from_cluster"] == cluster)
        ]
        if not match.empty:
            result = _apply_tier_row(match.iloc[0], f"cluster {cluster}-specific")
            if result:
                return result

    if not translation_pooled.empty:
        match = translation_pooled[(translation_pooled["from_league"] == from_league) & (translation_pooled["to_league"] == target_league)]
        if not match.empty:
            result = _apply_tier_row(match.iloc[0], "pooled (all attackers)")
            if result:
                return result

    # Fallback: distribution transfer using per-league feature mean/std
    means, stds = league_feature_stats["mean"], league_feature_stats["std"]
    if from_league in means.index and target_league in means.index:
        result = {}
        for f in CLUSTER_FEATURES:
            z = (player_row[f] - means.loc[from_league, f]) / stds.loc[from_league, f]
            result[f] = means.loc[target_league, f] + z * stds.loc[target_league, f]
        return {**result, "method": "distribution_transfer_fallback",
                "confidence": "Low -- league-population proxy, not player-specific", "granularity": "league-pair only"}

    return {**{f: player_row[f] for f in CLUSTER_FEATURES}, "method": "no_adjustment_insufficient_data", "confidence": "None", "granularity": "N/A"}


# Example: project a Ligue 1 candidate's numbers into the Premier League
ligue1_candidates = ranked[ranked["last_league"] == "Ligue 1"]
if not ligue1_candidates.empty:
    example_player = ligue1_candidates.iloc[0]
    projection = translate_player_stats(example_player, "Premier League", translation_by_cluster, translation_pooled, league_feature_stats)
    print(f"{example_player['player_name']} (Ligue 1, cluster {example_player['cluster']}) projected into the Premier League:")
    for k, v in projection.items():
        print(f"  {k}: {v}")
else:
    print("No Ligue 1 players in the current shortlist to demo with -- re-run against the full candidate pool.")


selected_players_for_translation_v2 = candidate_profiles[candidate_profiles['player_name'].isin(selected_pca_names)].copy()

comparison_data_v2 = []
for idx, player_row in selected_players_for_translation_v2.iterrows():
    player_name = player_row['player_name']
    current_league = player_row['last_league']
    player_cluster = player_row['cluster'] # Get the player's cluster

    # Get original stats
    original_stats = {f: player_row[f] for f in CLUSTER_FEATURES}

    # Get translated stats using the v2 function
    translated_projection_v2 = translate_player_stats(
        player_row,
        "Premier League",
        translation_by_cluster,
        translation_pooled,
        league_feature_stats
    )
    translated_stats_v2 = {f: translated_projection_v2[f] for f in CLUSTER_FEATURES}

    # Prepare data for comparison
    row_data_v2 = {
        'Player': player_name,
        'Current_League': current_league,
        'Cluster': player_cluster,
        'Translation_Method': translated_projection_v2['method'],
        'Confidence': translated_projection_v2['confidence'],
        'Granularity': translated_projection_v2['granularity']
    }

    for feature in CLUSTER_FEATURES:
        row_data_v2[f'{feature}_Original'] = original_stats[feature]
        row_data_v2[f'{feature}_Translated_PL'] = translated_stats_v2[feature]
        row_data_v2[f'{feature}_Ratio'] = translated_stats_v2[feature] / original_stats[feature] if original_stats[feature] != 0 else np.nan

    comparison_data_v2.append(row_data_v2)

comparison_df_v2 = pd.DataFrame(comparison_data_v2)

print("\n--- Translations using League Translation Model (v2) ---")
print(comparison_df_v2.set_index(['Player', 'Current_League', 'Cluster', 'Translation_Method', 'Confidence', 'Granularity']).T.round(3))
