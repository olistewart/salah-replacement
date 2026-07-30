"""
Section 8d: Visuals - diagnostics.

Where Salah's own last-two-seasons profile would land (sanity check
against the candidate-pool methodology), a minutes-vs-similarity plot
(the direct answer to 'did removing the minutes threshold surface
anyone new'), and per-feature distributions for the top 15 vs. the rest.
"""

# Filter Salah's data for the candidate seasons (last two seasons)
salah_df_last_two_seasons = salah_df[salah_df["season"].isin(CANDIDATE_SEASONS)].copy()

# Build a target vector for Salah based on these two seasons
# Using the CANDIDATE_WEIGHTS to be consistent with candidate profile generation
salah_target_last_two_seasons = build_target_vector(salah_df_last_two_seasons, CANDIDATE_WEIGHTS, "Mohamed Salah (last two seasons)")

# Scale this new target vector
salah_target_last_two_seasons_scaled = scaler.transform(pd.DataFrame([salah_target_last_two_seasons[CLUSTER_FEATURES].values], columns=CLUSTER_FEATURES))

# Predict the cluster for Salah based on his last two seasons
salah_cluster_last_two_seasons = kmeans.predict(salah_target_last_two_seasons_scaled)[0]

print(f"Mohamed Salah's profile for the last two seasons belongs to Cluster: {salah_cluster_last_two_seasons}")
print("Salah target profile (last two seasons):\n", salah_target_last_two_seasons)
print("Corresponding cluster summary:\n", cluster_summary.loc[salah_cluster_last_two_seasons])


def minutes_vs_similarity(ranked_df):
    """Direct visual answer to the old minutes-threshold problem: shows
    whether a high ranking is backed by a big sample or a small one, instead
    of hiding low-minute players from the analysis entirely."""
    color_map = {"High": "#2a6f97", "Medium": "#89c2d9", "Low": "#e07a5f"}
    fig, ax = plt.subplots(figsize=(8, 6))
    for rel, group in ranked_df.groupby("reliability"):
        ax.scatter(group["total_minutes"], group["similarity_to_salah"], label=rel,
                   color=color_map.get(rel, "#999"), alpha=0.75, s=55, edgecolors="white")
    ax.set_xlabel("Total minutes in candidate window")
    ax.set_ylabel("Similarity to Salah target")
    ax.set_title("Similarity vs. sample size -- nobody silently excluded")
    ax.legend(title="Reliability")
    fig.tight_layout()
    return fig

minutes_vs_similarity(ranked)
plt.show()


# Feature-by-feature distribution across the top 15 vs. the rest, Salah marked
top15_names = ranked.head(15)["player_name"].tolist()
plot_data = candidate_profiles.copy()
plot_data["group"] = np.where(plot_data["player_name"].isin(top15_names), "Top 15 shortlist", "Rest of pool")

fig, axes = plt.subplots(3, 3, figsize=(14, 11))
for ax, feature in zip(axes.flat, CLUSTER_FEATURES):
    for group, color in [("Rest of pool", "#cccccc"), ("Top 15 shortlist", "#2a6f97")]:
        subset = plot_data[plot_data["group"] == group][feature]
        ax.hist(subset, bins=20, alpha=0.6, label=group, color=color, density=True)
    ax.axvline(salah_target[feature], color="red", linestyle="--", linewidth=2, label="Salah target")
    ax.set_title(FEATURE_LABELS.get(feature, feature), fontsize=10)
axes.flat[0].legend(fontsize=8)
plt.tight_layout()
plt.show()
