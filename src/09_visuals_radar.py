"""
Section 8b: Visuals - radar plots, Salah vs. each selected candidate.

Combined radar (all manually-selected candidates + Salah on one chart)
plus individual radar plots per candidate. `selected_pca_names` (defined
in 08_visuals_pca.py) drives who's included -- edit that list to compare
different players.
"""

def _maybe_download(path):
    """Triggers a browser download when running in Google Colab; no-op elsewhere
    (e.g. running these scripts locally or in the repo's own environment)."""
    try:
        from google.colab import files as _colab_files
        _colab_files.download(path)
    except ImportError:
        pass



FEATURE_LABELS = {
    "npg_per90": "Non-pen goals /90", "npxG_per90": "Non-pen xG /90", "shots_per90": "Shots /90",
    "assists_per90": "Assists /90", "xA_per90": "xA /90", "key_passes_per90": "Key passes /90",
    "xGChain_per90": "xG Chain /90", "xGBuildup_per90": "xG Buildup /90", "xG_per_shot": "xG per shot",
}

# Define distinct colors for candidates. Use a palette that offers enough variety.
# Moved outside the function so it can be accessed globally if needed.
DEFAULT_CANDIDATE_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

def radar_chart(players_df, target, name_col="player_name", features=None, global_min=None, global_max=None, player_colors_override_map=None):
    features = features or CLUSTER_FEATURES

    # Ensure players_df has a clean, sequential index for direct iloc access
    players_df_for_norm = players_df[features].reset_index(drop=True)

    all_rows = pd.concat([
        players_df_for_norm,
        pd.DataFrame([target[features].values], columns=features),
    ], ignore_index=True)

    if global_min is None or global_max is None:
        mins, maxs = all_rows.min(), all_rows.max()
    else:
        mins = global_min[features]
        maxs = global_max[features]

    normed = (all_rows - mins) / (maxs - mins).replace(0, 1)

    labels = [FEATURE_LABELS.get(f, f) for f in features]
    angles = np.linspace(0, 2 * np.pi, len(features), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

    # Plot Salah target first, ensuring it's always visible and on top
    salah_values = normed.iloc[len(players_df_for_norm)].tolist(); salah_values += salah_values[:1]
    ax.plot(angles, salah_values, linewidth=3, linestyle="--", color="black", label="Salah 2017-25", zorder=10)

    # Plot candidates after Salah target, with fill having lower zorder than line
    for i in range(len(players_df_for_norm)):
        player_name = players_df.iloc[i][name_col]
        values = normed.iloc[i].tolist(); values += values[:1]

        # Use override color if provided, otherwise cycle through default colors
        if player_colors_override_map and player_name in player_colors_override_map:
            color = player_colors_override_map[player_name]
        else:
            color = DEFAULT_CANDIDATE_COLORS[i % len(DEFAULT_CANDIDATE_COLORS)] # Cycle through colors

        ax.plot(angles, values, linewidth=2, label=player_name, color=color, zorder=5)
        ax.fill(angles, values, alpha=0.1, color=color, zorder=1) # Fill has lower zorder

    ax.set_xticks(angles[:-1]); ax.set_xticklabels(labels, fontsize=9)
    ax.set_yticklabels([])#; ax.set_title(title, fontsize=13, pad=20)
    ax.legend(loc="upper right", frameon=True, framealpha=0.6, bbox_to_anchor=(1.35, 1.1), fontsize=9)
    fig.tight_layout()
    return fig


# Calculate global min/max from the entire candidate pool (X DataFrame)
global_min_features = X[CLUSTER_FEATURES].min()
global_max_features = X[CLUSTER_FEATURES].max()

# Filter the ranked DataFrame for the selected players
manual_top_candidates_for_radar = ranked[ranked['player_name'].isin(selected_pca_names)]
print("Manually selected candidates for radar plot:", manual_top_candidates_for_radar["player_name"].tolist())

# Call for the combined plot (no override map needed here, it uses the default cycling)
radar_chart(manual_top_candidates_for_radar, salah_target, global_min=global_min_features, global_max=global_max_features)
plt.savefig("combined_radar_plot.png")
_maybe_download("combined_radar_plot.png")
plt.show()


# Create a mapping of player names to their assigned colors from the combined plot
player_color_map_for_individuals = {}
for i, (_, row) in enumerate(manual_top_candidates_for_radar.iterrows()):
    player_name = row['player_name']
    player_color_map_for_individuals[player_name] = DEFAULT_CANDIDATE_COLORS[i % len(DEFAULT_CANDIDATE_COLORS)]

for _, player_row in manual_top_candidates_for_radar.iterrows():
    player_name = player_row['player_name']
    # Create a DataFrame for a single player
    single_player_df = pd.DataFrame([player_row])

    print(f"Radar plot: {player_name} vs. Salah 2017-25")
    radar_chart(
        single_player_df,
        salah_target,
        #title=f"{player_name} vs. Salah target",
        global_min=global_min_features,
        global_max=global_max_features,
        player_colors_override_map=player_color_map_for_individuals # Pass the color map here
    )
    plt.show()
    plt.savefig(f"{player_name}_radar_plot.png")
    _maybe_download(f"{player_name}_radar_plot.png")
