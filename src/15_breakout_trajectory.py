"""
Section 12: Breakout trajectory matching.

A complementary signal to the static similarity score: does a candidate's
own season-over-season growth SHAPE resemble Salah's own Roma-to-Liverpool
breakout arc (2015-2017)? Surfaces rising/undervalued targets that a
snapshot similarity score alone would miss.
"""

TRAJECTORY_FEATURES = ["npg_per90", "npxG_per90", "assists_per90", "xA_per90","xGChain_per90", "key_passes_per90"]


def compute_growth_vector(player_df: pd.DataFrame, features: list) -> tuple:
    """Average season-over-season delta across whatever consecutive
    seasons are available (only real, back-to-back seasons count -- a gap
    year doesn't count as a 'transition'). Returns (pd.Series of avg deltas,
    n_transitions)."""
    d = player_df.sort_values("season")
    deltas = []
    seasons = d["season"].tolist()
    for i in range(len(d) - 1):
        if seasons[i + 1] - seasons[i] != 1:
            continue
        deltas.append(d.iloc[i + 1][features].values - d.iloc[i][features].values)
    if not deltas:
        return None, 0
    avg_delta = pd.Series(np.mean(deltas, axis=0), index=features)
    return avg_delta, len(deltas)


def trajectory_reliability(n_transitions: int) -> str:
    if n_transitions >= 3:
        return "High"
    if n_transitions == 2:
        return "Medium"
    return "Low"


# --- Salah's breakout template: Roma (2015-2016) -> first Liverpool season (2017) ---
print("\n--- Mohamed Salah's data in df BEFORE filtering for breakout template ---")
salah_df_full_check = df[(df['player_name'] == 'Mohamed Salah') & (df['season'].isin([2015, 2016, 2017, 2018, 2019]))].sort_values('season')
print(salah_df_full_check[['season', 'team_title', 'league', 'time']])
print("--------------------------------------------------------------------------\n")

salah_breakout_df = df[(df["player_name"] == "Mohamed Salah") & (df["season"] <= 2017)].sort_values("season")
print("Salah's breakout-window rows (Roma -> first Liverpool season):")
print(salah_breakout_df[["season", "team_title", "league", "time"] + TRAJECTORY_FEATURES])

salah_template, salah_template_transitions = compute_growth_vector(salah_breakout_df, TRAJECTORY_FEATURES)
if salah_template is None:
    raise ValueError(
        "Could not build a Salah breakout template -- check that the Serie A 2015/2016 pull in Section 2 "
        "actually returned Salah's Roma seasons (Understat's Serie A archive needs to cover that far back)."
    )
print(f"\nSalah breakout template ({salah_template_transitions} season-transitions):")
print(salah_template)


salah_all_seasons_df = df[(df['player_name'] == 'Mohamed Salah')].sort_values('season')
print("Mohamed Salah's data in df, across all seasons:")
print(salah_all_seasons_df[['season', 'team_title', 'league', 'time'] + TRAJECTORY_FEATURES])


def build_trajectory_scores(df: pd.DataFrame, candidate_names: list, template: pd.Series,
                             features: list, window_seasons: list) -> pd.DataFrame:
    """For each candidate, compute their own recent growth vector (within
    window_seasons) and its cosine similarity to Salah's breakout template."""
    pool = df[df["is_attacking"] & df["player_name"].isin(candidate_names) & df["season"].isin(window_seasons)]
    rows = []
    for player, group in pool.groupby("player_name"):
        if group["season"].nunique() < 2:
            continue  # need at least one real transition
        growth, n_transitions = compute_growth_vector(group, features)
        if growth is None:
            continue
        sim = cosine_similarity(growth.values.reshape(1, -1), template.values.reshape(1, -1))[0, 0]
        rows.append({
            "player_name": player, "breakout_trajectory_score": sim, "n_transitions": n_transitions,
            "trajectory_reliability": trajectory_reliability(n_transitions),
            **{f"growth_{f}": growth[f] for f in features},
        })
    return pd.DataFrame(rows)


TRAJECTORY_WINDOW_SEASONS = list(range(min(CANDIDATE_SEASONS) - 3, max(CANDIDATE_SEASONS) + 1))  # a few extra seasons of history for growth shape
trajectory_df = build_trajectory_scores(df, candidate_profiles["player_name"].tolist(), salah_template,
                                         TRAJECTORY_FEATURES, TRAJECTORY_WINDOW_SEASONS)

ranked_full = ranked.merge(trajectory_df, on="player_name", how="left")
ranked_full.to_csv(data_path("salah_replacement_ranked_with_trajectory.csv"), index=False)

print(ranked_full[["player_name", "last_league", "similarity_to_salah", "breakout_trajectory_score", "trajectory_reliability"]]
      .sort_values("breakout_trajectory_score", ascending=False).head(15))

# --- The flagship chart: opportunity matrix ---


# --- The flagship chart: opportunity matrix ---
plot_df = ranked_full.dropna(subset=["breakout_trajectory_score"]).copy()

fig, ax = plt.subplots(figsize=(10, 8))
color_map = {"High": "#2a6f97", "Medium": "#89c2d9", "Low": "#e07a5f"}
for rel, group in plot_df.groupby("trajectory_reliability"):
    ax.scatter(group["similarity_to_salah"], group["breakout_trajectory_score"], label=f"{rel} trajectory reliability",
               color=color_map.get(rel, "#999"), alpha=0.75, s=60, edgecolors="white")

x_mid, y_mid = plot_df["similarity_to_salah"].median(), plot_df["breakout_trajectory_score"].median()
ax.axvline(x_mid, color="grey", linestyle=":", linewidth=1)
ax.axhline(y_mid, color="grey", linestyle=":", linewidth=1)

for _, row in plot_df.sort_values("breakout_trajectory_score", ascending=False).head(8).iterrows():
    ax.annotate(row["player_name"], (row["similarity_to_salah"], row["breakout_trajectory_score"]),
                fontsize=8, xytext=(4, 4), textcoords="offset points")
for _, row in plot_df.sort_values("similarity_to_salah", ascending=False).head(5).iterrows():
    ax.annotate(row["player_name"], (row["similarity_to_salah"], row["breakout_trajectory_score"]),
                fontsize=8, xytext=(4, 4), textcoords="offset points")

ax.set_xlabel("Similarity to Salah TODAY (static snapshot, Section 7)")
ax.set_ylabel("Breakout trajectory score (growth SHAPE vs. Salah's Roma->Liverpool arc)")
ax.set_title("Opportunity matrix: who matches Salah now vs. who's climbing the same curve")
ax.legend()
fig.tight_layout()
plt.show()

print("Top-right quadrant = matches Salah already AND still trending the right way -- the highest-conviction targets.")
print("Bottom-right = matches Salah's current output but has plateaued/declined recently -- worth a fitness/age check.")
print("Top-left = doesn't match Salah's current level yet, but is developing in the same shape -- the value/upside picks.")
