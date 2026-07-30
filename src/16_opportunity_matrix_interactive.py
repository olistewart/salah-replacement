"""
Section 12b: Interactive opportunity matrix + growth-curve overlay.

Plotly version of the opportunity matrix (similarity today vs. breakout
trajectory score), with Bradley Barcola highlighted as the headline pick,
plus a growth-curve overlay comparing the top trajectory matches against
Salah's own breakout arc. (The notebook had a second, near-identical cell
re-adding the same highlight to an already-built figure -- a leftover
from interactive editing that errored on a fresh top-to-bottom run since
it depended on Colab cell-execution order; dropped here as redundant.)
"""

import plotly.express as px
import plotly.graph_objects as go
import os
import pandas as pd

RELIABILITY_COLORS = {"High": "#2a6f97", "Medium": "#89c2d9", "Low": "#e07a5f"}

def data_path(filename):
    # Re-define data_path here if it might not be in scope (e.g., if running this cell independently)
    # For simplicity, assuming DATA_DIR is globally defined from an earlier setup cell.
    # If DATA_DIR is also not defined, it would cause another NameError, which would need to be addressed.
    # For this specific fix, I'm assuming DATA_DIR is present.
    global DATA_DIR # Access the global DATA_DIR
    return os.path.join(DATA_DIR, filename)

# Ensure ranked_full is defined. If it's not in scope, load it from CSV.
if 'ranked_full' not in locals() and 'ranked_full' not in globals():
    try:
        ranked_full = pd.read_csv(data_path("salah_replacement_ranked_with_trajectory.csv"))
        print("Loaded ranked_full from CSV.")
    except FileNotFoundError:
        print("Error: 'salah_replacement_ranked_with_trajectory.csv' not found. Please run cell '0c41adfc' first.")
        ranked_full = pd.DataFrame() # Create an empty DataFrame to avoid further errors

# Ensure plot_df is defined with the correct columns for the opportunity matrix
plot_df = ranked_full.dropna(subset=["breakout_trajectory_score"]).copy()

fig_interactive_opportunity_matrix = px.scatter(
    plot_df,
    x="similarity_to_salah",
    y="breakout_trajectory_score",
    color="trajectory_reliability",
    color_discrete_map=RELIABILITY_COLORS, # Use the predefined reliability colors
    hover_name="player_name",
    hover_data={
        "similarity_to_salah": ':.3f',
        "breakout_trajectory_score": ':.3f',
        "last_team": True,
        "last_league": True,
        "total_minutes": True,
        "n_transitions": True,
        "trajectory_reliability": True
    },
    title="Interactive Opportunity Matrix: Similarity vs. Trajectory",
    labels={
        "similarity_to_salah": "Similarity to Salah TODAY (static snapshot, Section 7)",
        "breakout_trajectory_score": "Breakout trajectory score (growth SHAPE vs. Salah's Roma->Liverpool arc)",
        "trajectory_reliability": "Trajectory Reliability"
    },
    height=600
)

# Add median lines
x_mid, y_mid = plot_df["similarity_to_salah"].median(), plot_df["breakout_trajectory_score"].median()

fig_interactive_opportunity_matrix.add_trace(go.Scatter(
    x=[x_mid, x_mid],
    y=[plot_df["breakout_trajectory_score"].min(), plot_df["breakout_trajectory_score"].max()],
    mode="lines",
    line=dict(color="grey", dash="dot", width=1),
    showlegend=False
))

fig_interactive_opportunity_matrix.add_trace(go.Scatter(
    x=[plot_df["similarity_to_salah"].min(), plot_df["similarity_to_salah"].max()],
    y=[y_mid, y_mid],
    mode="lines",
    line=dict(color="grey", dash="dot", width=1),
    showlegend=False
))

fig_interactive_opportunity_matrix.update_layout(
    annotations=[
        dict(xref='paper', yref='paper', x=0.9, y=1.05, showarrow=False, text='Top-right: High conviction targets'),
        dict(xref='paper', yref='paper', x=0.9, y=0.05, showarrow=False, text='Bottom-right: Plateaued/declined'),
        dict(xref='paper', yref='paper', x=0.1, y=1.05, showarrow=False, text='Top-left: Value/upside picks'),
        dict(xref='paper', yref='paper', x=0.1, y=0.05, showarrow=False, text='Bottom-left: Not suitable')
    ]
)

# Highlighting 'Bradley Barcola'
highlighted_player_name = "Bradley Barcola"
highlighted_player_data = plot_df[plot_df['player_name'] == highlighted_player_name]

if not highlighted_player_data.empty:
    fig_interactive_opportunity_matrix.add_trace(go.Scatter(
        x=highlighted_player_data["similarity_to_salah"],
        y=highlighted_player_data["breakout_trajectory_score"],
        mode='markers',
        marker=dict(
            size=15, # Larger size
            color='rgba(0,0,0,0)', # Transparent fill
            line=dict(width=2, color='magenta') # Magenta border
        ),
        name=f'{highlighted_player_name} (Highlighted)',
        showlegend=True, # Show in legend
        hovertemplate=(
            "<b>%{text}</b><br>" +
            "Similarity to Salah: %{x:.3f}<br>" +
            "Breakout Score: %{y:.3f}"
            "<extra></extra>"
        ),
        text=[highlighted_player_name]
    ))

fig_interactive_opportunity_matrix.update_layout(title=f"Interactive Opportunity Matrix: Similarity vs. Trajectory ({highlighted_player_name} Highlighted)")
fig_interactive_opportunity_matrix.show()


# --- Growth-curve overlay: Salah's own arc vs. the top trajectory matches ---
def relative_season_series(player_df: pd.DataFrame, feature: str, n_seasons: int = 3):
    d = player_df.sort_values("season").tail(n_seasons)
    x = list(range(-(len(d) - 1), 1))  # e.g. [-2, -1, 0] = 3 seasons ending "now"
    return x, d[feature].tolist()

fig, ax = plt.subplots(figsize=(9, 6))
feature_to_plot = "npxG_per90"

x, y = relative_season_series(salah_breakout_df, feature_to_plot, n_seasons=3)
ax.plot(x, y, linewidth=3, color="black", linestyle="--", marker="o", label="Salah (Roma -> Liverpool breakout)")

top_trajectory = plot_df.sort_values("breakout_trajectory_score", ascending=False).head(3)["player_name"].tolist()
for name in top_trajectory:
    player_hist = df[(df["player_name"] == name) & df["season"].isin(TRAJECTORY_WINDOW_SEASONS)]
    if player_hist["season"].nunique() < 2:
        continue
    x, y = relative_season_series(player_hist, feature_to_plot, n_seasons=3)
    ax.plot(x, y, linewidth=2, marker="o", label=name)

ax.set_xlabel("Seasons relative to most recent (0 = latest season)")
ax.set_ylabel(FEATURE_LABELS.get(feature_to_plot, feature_to_plot))
ax.set_title("Growth curves: top trajectory matches vs. Salah's own breakout arc")
ax.legend()
fig.tight_layout()
plt.show()
