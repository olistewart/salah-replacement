"""
Section 8a: Visuals - PCA scatter (static + interactive).

Static matplotlib PCA plot with a manually curated set of names labeled,
plus an interactive Plotly version (hover for name/team/league/
similarity, zoom/pan). `_maybe_download` replaces the notebook's
Colab-only `files.download(...)` calls -- it's a no-op outside Colab.
"""

'''Set plot features'''

import matplotlib.font_manager as fm

plt.style.use("default")

plt.rcParams.update({
    # Font
    "font.family": "serif",
    "mathtext.fontset": "cm",
    "font.size": 14,

    # Axes
    "axes.labelsize": 16,
    "axes.titlesize": 16,
    "axes.linewidth": 1.2,

    # Ticks
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.major.size": 6,
    "ytick.major.size": 6,

    # Lines
    "lines.linewidth": 2,

    # Legend
    "legend.frameon": False,
    "legend.fontsize": 12,

    # Figure
    "figure.figsize": (6,4),
    "figure.dpi": 120,

    # Save quality
    "savefig.dpi": 300,
    "savefig.bbox": "tight"
})

colors = {
    "stokes": "#4C72B0",   # blue
    "mle": "#55A868",      # green
    "nn": "#C44E52"        # red
}

def nice_axes(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


def _maybe_download(path):
    """Triggers a browser download when running in Google Colab; no-op elsewhere
    (e.g. running these scripts locally or in the repo's own environment)."""
    try:
        from google.colab import files as _colab_files
        _colab_files.download(path)
    except ImportError:
        pass



pca = PCA(n_components=2)
coords = pca.fit_transform(X_scaled)
plot_df = candidate_profiles.copy()
plot_df["PC1"], plot_df["PC2"] = coords[:, 0], coords[:, 1]

salah_scaled = scaler.transform(pd.DataFrame([salah_target[CLUSTER_FEATURES].values], columns=CLUSTER_FEATURES))
salah_pca = pca.transform(salah_scaled)

plt.figure(figsize=(11, 8))
scatter = plt.scatter(plot_df["PC1"], plot_df["PC2"], c=plot_df["cluster"], cmap="viridis", alpha=0.55, s=45)

# Manually select player names to display on the PCA plot
selected_pca_names = ['Ibrahim Mbaye', 'Brahim Diaz', 'Bradley Barcola', 'Yan Diomande', 'Karim Adeyemi', 'Luca Koleosho']

# Plot selected players with a red outline
selected_players_plot_df = plot_df[plot_df["player_name"].isin(selected_pca_names)]

# Get the viridis colormap
import matplotlib.cm as cm
cmap = plt.get_cmap('viridis', K) # Updated from cm.get_cmap

# Get the specific colors for the selected players based on their cluster
selected_player_colors = [cmap(cluster_id) for cluster_id in selected_players_plot_df["cluster"]]

plt.scatter(selected_players_plot_df["PC1"], selected_players_plot_df["PC2"],
            c=selected_player_colors, # Use the specific cluster colors
            s=60, # Slightly larger size for visibility
            edgecolors='red', linewidth=1.5, zorder=4) # Red outline, higher zorder

plt.scatter(salah_pca[:, 0], salah_pca[:, 1], color="red", s=220, edgecolors="black", zorder=5, label="Salah 2017-25")

for _, row in plot_df[plot_df["player_name"].isin(selected_pca_names)].iterrows():
    plt.text(row["PC1"] + 0.05, row["PC2"] + 0.05, row["player_name"], fontsize=10)

plt.xlabel("PC1"); plt.ylabel("PC2")
plt.ylim(-4, 6)
#plt.title("Candidate similarity space (PCA of clustering features)")
plt.legend(frameon=True, framealpha=0.6); plt.tight_layout()
plt.savefig("pca_plot.png")
_maybe_download("pca_plot.png")
plt.show()


import plotly.express as px
import plotly.graph_objects as go # Import go for Scatter trace
import matplotlib.cm as cm # Import cm to get viridis colormap

# Re-create plot_df for PCA context, as it might have been overwritten by other cells.
# This ensures 'PC1' and 'PC2' are present.
# pca, X_scaled, candidate_profiles, and ranked are expected to be available from previous cell executions.
pca = PCA(n_components=2)
coords = pca.fit_transform(X_scaled)
plot_df_pca = candidate_profiles.copy()
plot_df_pca["PC1"], plot_df_pca["PC2"] = coords[:, 0], coords[:, 1]

# Ensure plot_df_pca contains the 'similarity_to_salah' column for hover data
if 'similarity_to_salah' not in plot_df_pca.columns:
    plot_df_pca = plot_df_pca.merge(ranked[['player_name', 'similarity_to_salah']], on='player_name', how='left')

# Create a discrete color map for clusters to match the static plot and hide the colorbar
# K is the number of clusters, defined earlier in the notebook
cmap = plt.get_cmap('viridis', K)
cluster_colors = {str(i): f'rgba({int(c[0]*255)},{int(c[1]*255)},{int(c[2]*255)},{c[3]})' for i, c in enumerate(cmap(np.linspace(0, 1, K)))}

# Create an interactive PCA scatter plot using Plotly
fig_interactive_pca = px.scatter(
    plot_df_pca, # Use the PCA-specific dataframe
    x="PC1",
    y="PC2",
    color="cluster", # Color points by cluster
    color_discrete_map=cluster_colors, # Use discrete colors for clusters
    hover_name="player_name", # Show player name on hover
    hover_data={
        "PC1": ':.2f', # Format PC1 on hover
        "PC2": ':.2f', # Format PC2 on hover
        "cluster": True,
        "last_team": True,
        "last_league": True,
        "reliability": True,
        "total_minutes": True,
        "similarity_to_salah": ':.3f' # Show similarity on hover
    },
    #title="Interactive PCA Plot: Hover to Identify Players",
    labels={
        "PC1": "Principal Component 1",
        "PC2": "Principal Component 2",
        "cluster": "Cluster"
    }
)

# Add Salah's target profile to the interactive plot
# salah_pca is expected to be available from cell 69ae9db4.
fig_interactive_pca.add_trace(go.Scatter(
    x=[salah_pca[:, 0][0]],
    y=[salah_pca[:, 1][0]],
    mode='markers',
    marker=dict(size=20, color='red', symbol='star', line=dict(width=2, color='Black')),
    name='Salah 2017-25',
    hoverinfo='name'
))

# Highlight 'Bradley Barcola'
highlighted_player_name = "Bradley Barcola"
highlighted_player_data = plot_df_pca[plot_df_pca['player_name'] == highlighted_player_name] # Use plot_df_pca here

if not highlighted_player_data.empty:
    fig_interactive_pca.add_trace(go.Scatter(
        x=highlighted_player_data["PC1"],
        y=highlighted_player_data["PC2"],
        mode='markers',
        marker=dict(
            size=15, # Larger size
            color='rgba(0,0,0,0)', # Transparent fill
            line=dict(width=2, color='magenta') # Magenta border
        ),
        name=f'{highlighted_player_name}',
        showlegend=True, # Show in legend
        hovertemplate=(
            "<b>%{text}</b><br>" +
            "PC1: %{x:.2f}<br>" +
            "PC2: %{y:.2f}<br>" +
            "Cluster: %{customdata[0]}<br>" +
            "Last Team: %{customdata[1]}<br>" +
            "Last League: %{customdata[2]}<br>" +
            "Reliability: %{customdata[3]}<br>" +
            "Total Minutes: %{customdata[4]}<br>" +
            "Similarity to Salah: %{customdata[5]:.3f}"
            "<extra></extra>"
        ),
        text=[highlighted_player_name],
        customdata=highlighted_player_data[[
            "cluster", "last_team", "last_league", "reliability", "total_minutes", "similarity_to_salah"
        ]].values
    ))

fig_interactive_pca.update_layout(height=600,
                                  coloraxis_showscale=False, # Explicitly hide the colorbar
                                  title=f"Interactive PCA Plot") # Update title
fig_interactive_pca.show()

# Save the interactive Plotly figure to an HTML file
output_html_path = data_path("interactive_pca_plot.html")
fig_interactive_pca.write_html(output_html_path)
print(f"Interactive PCA plot saved to: {output_html_path}")
