"""
Section 8c: Visuals - stat-vs-stat scatters.

Simple two-feature scatters (easier to screenshot/explain than the full
9-D similarity score), plus one interactive Plotly version. An earlier
`feature_pair_scatter_plotly` experiment (highlighting multiple pairs
interactively) had a stray syntax error and never actually ran in the
original notebook -- dropped here in favour of the working matplotlib
version (`feature_pair_scatter`) and the working single-pair interactive
version below, consistent with this project's existing practice of
cutting dead-end code rather than keeping broken cells around.
"""

import matplotlib.cm as cm

# --- Simple stat-vs-stat scatters: which players sit closest to Salah on just two axes ---
# Complements the PCA/similarity views: easier to screenshot and explain, and sometimes
# surfaces players who are close on a specific trait pair but get buried in the 13-D similarity score.

def feature_pair_scatter(x_feat, y_feat, top_n=8, title=None, highlight_names=None):
    x_all = pd.concat([candidate_profiles[x_feat], pd.Series([salah_target[x_feat]])], ignore_index=True)
    y_all = pd.concat([candidate_profiles[y_feat], pd.Series([salah_target[y_feat]])], ignore_index=True)
    x_norm = (x_all - x_all.min()) / (x_all.max() - x_all.min())
    y_norm = (y_all - y_all.min()) / (y_all.max() - y_all.min())

    cand_x, cand_y = x_norm.iloc[:-1], y_norm.iloc[:-1]
    salah_x, salah_y = x_norm.iloc[-1], y_norm.iloc[-1]

    # Determine which players to highlight
    if highlight_names is not None and len(highlight_names) > 0:
        # Filter candidate_profiles by highlight_names to get their original indices
        players_to_annotate_df = candidate_profiles[candidate_profiles['player_name'].isin(highlight_names)]
    else:
        # Nearest-to-Salah in THIS pair specifically (min-max normalized so neither axis dominates)
        dist = np.sqrt((cand_x - salah_x) ** 2 + (cand_y - salah_y) ** 2)
        nearest_indices = dist.nsmallest(top_n).index
        players_to_annotate_df = candidate_profiles.iloc[nearest_indices]

    fig, ax = plt.subplots(figsize=(9, 7))
    ax.scatter(candidate_profiles[x_feat], candidate_profiles[y_feat],
               c=candidate_profiles["cluster"], cmap="viridis", alpha=0.55, s=45)
    ax.scatter(salah_target[x_feat], salah_target[y_feat], color="red", s=220,
               edgecolors="black", zorder=5, label="Salah 2017-25")

    # Plot highlighted players with a red border on top
    if highlight_names is not None and len(highlight_names) > 0:
        highlighted_plot_df = candidate_profiles[candidate_profiles['player_name'].isin(highlight_names)]

        # Get the viridis colormap and apply it for the highlighted players
        cmap = plt.get_cmap('viridis', K) # K is the number of clusters, available globally
        highlighted_colors = [cmap(cluster_id) for cluster_id in highlighted_plot_df["cluster"]]

        ax.scatter(highlighted_plot_df[x_feat], highlighted_plot_df[y_feat],
                   c=highlighted_colors, # Use their original cluster colors
                   s=65, # Slightly larger size for visibility
                   edgecolors='red', linewidth=1.5, zorder=4) # Red outline, higher zorder

    for _, row in players_to_annotate_df.iterrows():
        ax.annotate(row["player_name"], (row[x_feat], row[y_feat]), fontsize=12,
                    xytext=(4, 4), textcoords="offset points")

    ax.set_xlabel(FEATURE_LABELS.get(x_feat, x_feat))
    ax.set_ylabel(FEATURE_LABELS.get(y_feat, y_feat))
    #ax.set_xlim(0, 0.7)
    #ax.set_ylim(0, 0.9)
    ax.set_title(title or f"{FEATURE_LABELS.get(x_feat, x_feat)} vs. {FEATURE_LABELS.get(y_feat, y_feat)}")
    ax.legend(frameon=True, framealpha=0.6, bbox_to_anchor=(1.0, 1))
    fig.tight_layout()
    plt.show()
    return players_to_annotate_df[["player_name", x_feat, y_feat]]


feature_pair_scatter("npxG_per90", "xA_per90",
                     highlight_names=["Mohamed Salah", "Bradley Barcola", "Yan Diomande", "Michael Olise", "Ibrahim Mbaye", "Luca Koleosho"],
                     title="Goal threat vs. creativity")


feature_pair_scatter("shots_per90", "xG_per_shot",
                     highlight_names=["Mohamed Salah", "Bradley Barcola", "Yan Diomande", "Ibrahim Mbaye"],
                     title="Shot Volume vs. Quality")


import plotly.express as px
import plotly.graph_objects as go

# Ensure candidate_profiles contains the 'similarity_to_salah' column for hover data.
# It is generated in the 'ranked' DataFrame, so we merge it here.
if 'similarity_to_salah' not in candidate_profiles.columns:
    candidate_profiles = candidate_profiles.merge(ranked[['player_name', 'similarity_to_salah']], on='player_name', how='left')

# Get the list of players to highlight from the static plot, excluding Salah as he's already a target
highlight_names = ["Bradley Barcola", "Yan Diomande", "Michael Olise", "Ibrahim Mbaye"]
highlighted_players_df = candidate_profiles[candidate_profiles['player_name'].isin(highlight_names)].copy()

# Create an interactive scatter plot for npxG_per90 vs xA_per90 using Plotly Express
fig_interactive_npxG_xA = px.scatter(
    candidate_profiles,
    x="npxG_per90",
    y="xA_per90",
    color="cluster", # Color points by cluster
    hover_name="player_name", # Show player name on hover
    hover_data={
        "npxG_per90": ':.3f',
        "xA_per90": ':.3f',
        "cluster": True,
        "last_team": True,
        "last_league": True,
        "reliability": True,
        "total_minutes": True,
        "similarity_to_salah": ':.3f' # Now similarity_to_salah is ensured to be in candidate_profiles
    },
    title="Interactive: Non-pen xG /90 vs. xA /90 (Goal Threat vs. Creativity)",
    labels={
        "npxG_per90": "Non-pen xG /90",
        "xA_per90": "xA /90",
        "cluster": "Cluster"
    },
    color_continuous_scale=px.colors.sequential.Viridis # Use a sequential color scale matching viridis
)

# Add Salah's target profile to the interactive plot
fig_interactive_npxG_xA.add_trace(go.Scatter(
    x=[salah_target["npxG_per90"]],
    y=[salah_target["xA_per90"]],
    mode='markers',
    marker=dict(size=20, color='red', symbol='star', line=dict(width=2, color='Black')),
    name='Salah Target',
    hoverinfo='name'
))

# Add highlighted players with a ring around them
if not highlighted_players_df.empty:
    fig_interactive_npxG_xA.add_trace(go.Scatter(
        x=highlighted_players_df["npxG_per90"],
        y=highlighted_players_df["xA_per90"],
        mode='markers',
        marker=dict(size=12, color='rgba(0,0,0,0)', line=dict(width=2, color='Black')),
        name='Highlighted Players',
        showlegend=False, # Don't show this trace in the legend, as players are also colored by cluster
        text=highlighted_players_df["player_name"], # Use text for individual player names on hover
        customdata=highlighted_players_df[[
            "cluster", "last_team", "last_league", "reliability", "total_minutes", "similarity_to_salah"
        ]].values,
        hovertemplate=(
            "<b>%{text}</b><br>" +
            "Non-pen xG /90: %{x:.3f}<br>" +
            "xA /90: %{y:.3f}<br>" +
            "Cluster: %{customdata[0]}<br>" +
            "Last Team: %{customdata[1]}<br>" +
            "Last League: %{customdata[2]}<br>" +
            "Reliability: %{customdata[3]}<br>" +
            "Total Minutes: %{customdata[4]}<br>" +
            "Similarity to Salah: %{customdata[5]:.3f}"
            "<extra></extra>" # This hides the default trace name from the hover box
        )
    ))

# Add median lines for context
x_median = candidate_profiles["npxG_per90"].median()
y_median = candidate_profiles["xA_per90"].median()

fig_interactive_npxG_xA.add_shape(
    type="line",
    x0=x_median, y0=candidate_profiles["xA_per90"].min(),
    x1=x_median, y1=candidate_profiles["xA_per90"].max(),
    line=dict(color="grey", dash="dot", width=1)
)

fig_interactive_npxG_xA.add_shape(
    type="line",
    x0=candidate_profiles["npxG_per90"].min(), y0=y_median,
    x1=candidate_profiles["npxG_per90"].max(), y1=y_median,
    line=dict(color="grey", dash="dot", width=1)
)

fig_interactive_npxG_xA.update_layout(height=600)
fig_interactive_npxG_xA.show()
