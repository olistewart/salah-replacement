"""
Extension: single-file HTML dashboard for a final, narrowed shortlist.

Not part of the executed notebook -- built afterward, tested against
synthetic data (see extensions/README.md). Run this after the core pipeline
-- specifically src/01, 03, 04, 05, 06, 07, 08_visuals_pca.py,
09_visuals_radar.py (defines FEATURE_LABELS), and 15_breakout_trajectory.py
(defines ranked_full) -- so `ranked_full`, `plot_df_pca`, `scaler`, `pca`,
`candidate_profiles`, `salah_target`, `CLUSTER_FEATURES`, `FEATURE_LABELS`,
and `data_path` are all in scope.

Unlike the full dashboard in src/17_dashboard.py (built for the whole
candidate pool), this is scoped to a small, final shortlist: an interactive
PCA scatter, a goal-threat-vs-creativity scatter, a compact shortlist table,
one radar chart per candidate vs. Salah, and a Transfermarkt panel
(age/contract/value/injury history) read from a small manually-filled CSV --
Transfermarkt scraping isn't reliable enough to trust unattended (see
src/12_transfermarkt.py), and injury history isn't a structured Transfermarkt
field at all.

Edit SHORTLIST_NAMES below to your actual final picks -- e.g. the 8 real
candidates in data/results/final_shortlist_vs_salah_profiles.csv, narrowed
to your final 3.
"""
import os

import pandas as pd
import plotly.graph_objects as go
from plotly.io import to_html

# --- Config: edit this to your final shortlist ---
SHORTLIST_NAMES = ranked_full.sort_values("similarity_to_salah", ascending=False).head(3)["player_name"].tolist()
print("Shortlist (placeholder -- replace with your final picks):", SHORTLIST_NAMES)

shortlist_df = ranked_full[ranked_full["player_name"].isin(SHORTLIST_NAMES)].copy()
shortlist_df["player_name"] = pd.Categorical(shortlist_df["player_name"], categories=SHORTLIST_NAMES, ordered=True)
shortlist_df = shortlist_df.sort_values("player_name").reset_index(drop=True)

# --- Transfermarkt panel: age, contract, market value, injury history (manual entry) ---
TM_SHORTLIST_PATH = data_path("shortlist_transfermarkt_data.csv")
TM_COLS = ["player_name", "age", "contract_expires", "market_value_eur_m", "injury_history_notes"]

if os.path.exists(TM_SHORTLIST_PATH):
    shortlist_tm = pd.read_csv(TM_SHORTLIST_PATH)
    missing_names = set(SHORTLIST_NAMES) - set(shortlist_tm["player_name"])
    if missing_names:
        print(f"NOTE: {missing_names} in SHORTLIST_NAMES but not yet in {TM_SHORTLIST_PATH} -- add rows for them.")
else:
    shortlist_tm = pd.DataFrame({"player_name": SHORTLIST_NAMES})
    for c in TM_COLS[1:]:
        shortlist_tm[c] = "TBD"
    shortlist_tm.to_csv(TM_SHORTLIST_PATH, index=False)
    print(f"Created a blank Transfermarkt template at {TM_SHORTLIST_PATH}.")
    print("Fill in age / contract_expires / market_value_eur_m / injury_history_notes by hand, "
          "then re-run this script.")


# --- PCA scatter (interactive: hover, zoom, pan), shortlist highlighted ---
def pca_scatter_fig(plot_df, salah_target, scaler, pca, highlight_names):
    fig = go.Figure()
    background = plot_df[~plot_df["player_name"].isin(highlight_names)]
    fig.add_trace(go.Scatter(
        x=background["PC1"], y=background["PC2"], mode="markers", name="Candidate pool",
        marker=dict(color=background["cluster"], colorscale="Viridis", size=8, opacity=0.4),
        text=background["player_name"],
        hovertemplate="<b>%{text}</b><br>PC1: %{x:.2f}<br>PC2: %{y:.2f}<extra></extra>",
    ))
    highlight = plot_df[plot_df["player_name"].isin(highlight_names)]
    fig.add_trace(go.Scatter(
        x=highlight["PC1"], y=highlight["PC2"], mode="markers+text", name="Shortlist",
        marker=dict(color="#c8102e", size=16, line=dict(color="black", width=1)),
        text=highlight["player_name"], textposition="top center",
        hovertemplate="<b>%{text}</b><br>PC1: %{x:.2f}<br>PC2: %{y:.2f}<extra></extra>",
    ))
    salah_scaled = scaler.transform(pd.DataFrame([salah_target[CLUSTER_FEATURES].values], columns=CLUSTER_FEATURES))
    salah_pca = pca.transform(salah_scaled)[0]
    fig.add_trace(go.Scatter(
        x=[salah_pca[0]], y=[salah_pca[1]], mode="markers+text", name="Salah target",
        marker=dict(color="black", size=18, symbol="star"), text=["Salah"], textposition="top center",
    ))
    fig.update_layout(title="Candidate similarity space (PCA), shortlist highlighted",
                       xaxis_title="PC1", yaxis_title="PC2", height=560, hovermode="closest")
    return fig


pca_fig = pca_scatter_fig(plot_df_pca, salah_target, scaler, pca, SHORTLIST_NAMES)


# --- Goal threat vs. creativity scatter, same highlight treatment ---
def feature_pair_fig(candidate_profiles, salah_target, x_feat, y_feat, highlight_names, title=None):
    fig = go.Figure()
    background = candidate_profiles[~candidate_profiles["player_name"].isin(highlight_names)]
    fig.add_trace(go.Scatter(
        x=background[x_feat], y=background[y_feat], mode="markers", name="Candidate pool",
        marker=dict(color=background["cluster"], colorscale="Viridis", size=8, opacity=0.4),
        text=background["player_name"],
        hovertemplate=f"<b>%{{text}}</b><br>{x_feat}: %{{x:.2f}}<br>{y_feat}: %{{y:.2f}}<extra></extra>",
    ))
    highlight = candidate_profiles[candidate_profiles["player_name"].isin(highlight_names)]
    fig.add_trace(go.Scatter(
        x=highlight[x_feat], y=highlight[y_feat], mode="markers+text", name="Shortlist",
        marker=dict(color="#c8102e", size=16, line=dict(color="black", width=1)),
        text=highlight["player_name"], textposition="top center",
    ))
    fig.add_trace(go.Scatter(
        x=[salah_target[x_feat]], y=[salah_target[y_feat]], mode="markers+text", name="Salah target",
        marker=dict(color="black", size=18, symbol="star"), text=["Salah"], textposition="top center",
    ))
    fig.update_layout(title=title or f"{FEATURE_LABELS.get(x_feat, x_feat)} vs. {FEATURE_LABELS.get(y_feat, y_feat)}",
                       xaxis_title=FEATURE_LABELS.get(x_feat, x_feat), yaxis_title=FEATURE_LABELS.get(y_feat, y_feat),
                       height=520)
    return fig


creativity_fig = feature_pair_fig(candidate_profiles, salah_target, "npxG_per90", "xA_per90",
                                   SHORTLIST_NAMES, title="Goal threat vs. creativity")


# --- One radar chart per shortlisted candidate vs. Salah ---
def single_radar_fig(player_row, target, name):
    features = CLUSTER_FEATURES
    all_rows = pd.concat([
        pd.DataFrame([player_row[features].values], columns=features),
        pd.DataFrame([target[features].values], columns=features),
    ], ignore_index=True)
    normed = (all_rows - all_rows.min()) / (all_rows.max() - all_rows.min()).replace(0, 1)
    labels = [FEATURE_LABELS.get(f, f) for f in features]

    player_vals = normed.iloc[0].tolist(); player_vals += player_vals[:1]
    salah_vals = normed.iloc[1].tolist(); salah_vals += salah_vals[:1]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=player_vals, theta=labels + labels[:1], fill="toself", name=name, opacity=0.65))
    fig.add_trace(go.Scatterpolar(r=salah_vals, theta=labels + labels[:1], name="Salah target",
                                   line=dict(color="black", dash="dash", width=3)))
    fig.update_layout(title=f"{name} vs. Salah", polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                       height=420, showlegend=True)
    return fig


radar_figs = {row["player_name"]: single_radar_fig(row, salah_target, row["player_name"])
              for _, row in shortlist_df.iterrows()}


# --- Assemble everything into one self-contained HTML file ---
def build_shortlist_dashboard(shortlist_df, shortlist_tm, pca_fig, creativity_fig, radar_figs,
                               output_path="salah_shortlist_dashboard.html"):
    shortlist_rows = "".join(
        f"<tr><td>{r.player_name}</td><td>{r.last_team}</td><td>{r.last_league}</td>"
        f"<td>{r.cluster}</td><td>{r.similarity_to_salah:.3f}</td>"
        f"<td>{r.npxG_per90:.2f}</td><td>{r.xA_per90:.2f}</td></tr>"
        for r in shortlist_df.itertuples()
    )

    tm_rows = "".join(
        f"<tr><td>{r.player_name}</td><td>{r.age}</td><td>{r.contract_expires}</td>"
        f"<td>{r.market_value_eur_m}</td><td>{r.injury_history_notes}</td></tr>"
        for r in shortlist_tm.itertuples()
    )

    radar_blocks = "".join(
        f'<div class="radar-card">{to_html(fig, full_html=False, include_plotlyjs=False)}</div>'
        for fig in radar_figs.values()
    )

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Salah Replacement -- Final Shortlist</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin:0; background:#f4f6f8; color:#1a1a1a; }}
  header {{ background:#c8102e; color:white; padding:28px 40px; }}
  header h1 {{ margin:0 0 6px 0; font-size:26px; }}
  main {{ max-width:1200px; margin:0 auto; padding:24px 20px 60px; }}
  .card {{ background:white; border-radius:10px; padding:20px 24px; margin-bottom:24px; box-shadow:0 1px 3px rgba(0,0,0,0.08); }}
  table.tbl {{ border-collapse:collapse; width:100%; font-size:13px; }}
  table.tbl th, table.tbl td {{ border:1px solid #e2e2e2; padding:6px 10px; text-align:left; }}
  table.tbl th {{ background:#f0f0f0; }}
  .radar-row {{ display:flex; flex-wrap:wrap; gap:16px; }}
  .radar-card {{ flex:1; min-width:340px; background:white; border-radius:10px; padding:8px;
                 box-shadow:0 1px 3px rgba(0,0,0,0.08); }}
  .note {{ font-size:13px; color:#666; margin-top:8px; }}
</style></head><body>
<header><h1>Mohamed Salah Replacement -- Final Shortlist</h1>
<p>Three candidates, benchmarked against a career-weighted Salah target profile.</p></header>
<main>
  <div class="card"><h2>Shortlist</h2>
    <table class="tbl"><tr><th>Player</th><th>Club</th><th>League</th><th>Cluster</th><th>Similarity</th>
    <th>npxG/90</th><th>xA/90</th></tr>
    {shortlist_rows}</table>
  </div>
  <div class="card"><h2>Similarity space (PCA)</h2>{to_html(pca_fig, full_html=False, include_plotlyjs=False)}</div>
  <div class="card"><h2>Goal threat vs. creativity</h2>{to_html(creativity_fig, full_html=False, include_plotlyjs=False)}</div>
  <div class="card"><h2>Radar profiles vs. Salah</h2><div class="radar-row">{radar_blocks}</div></div>
  <div class="card"><h2>Transfermarkt: age, contract, value, injury history</h2>
    <table class="tbl"><tr><th>Player</th><th>Age</th><th>Contract expires</th>
    <th>Market value (EUR m)</th><th>Injury history</th></tr>{tm_rows}</table>
    <p class="note">Manually entered -- Transfermarkt scraping isn't reliable enough to trust
    unattended (see src/12_transfermarkt.py), and injury history isn't a structured
    Transfermarkt field at all.</p>
  </div>
</main></body></html>"""

    with open(output_path, "w") as f:
        f.write(html)
    return output_path


shortlist_dashboard_path = build_shortlist_dashboard(
    shortlist_df, shortlist_tm, pca_fig, creativity_fig, radar_figs,
    output_path=data_path("salah_shortlist_dashboard.html"),
)
print("Shortlist dashboard written to:", shortlist_dashboard_path)
