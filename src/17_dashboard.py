"""
Section 13: Dashboard - single-file HTML for the recruitment team.

Packages the leaderboard, top-3 radar, and league translation table into
one self-contained HTML file (Plotly loaded from CDN, no server needed).
The notebook also had a fuller v2 of this function that accepted extra
PCA/goal-threat/shot-volume figures, but it depended on figures from the
broken `feature_pair_scatter_plotly` experiment (see 10_visuals_scatters.py)
and never successfully ran -- this is the v1 function, which is complete,
self-contained, and did run.
"""

import plotly.graph_objects as go
from plotly.io import to_html

RELIABILITY_COLORS = {"High": "#2a6f97", "Medium": "#89c2d9", "Low": "#e07a5f"}


def _leaderboard_fig(ranked_df, top_n=15):
    top = ranked_df.head(top_n).iloc[::-1]
    colors = [RELIABILITY_COLORS.get(r, "#999") for r in top["reliability"]]
    fig = go.Figure(go.Bar(
        x=top["similarity_to_salah"], y=top["player_name"], orientation="h", marker_color=colors,
        text=[f"{v:.3f}" for v in top["similarity_to_salah"]], textposition="outside",
        customdata=top[["last_league", "last_team", "total_minutes", "reliability"]],
        hovertemplate="<b>%{y}</b><br>League: %{customdata[0]}<br>Club: %{customdata[1]}"
                      "<br>Minutes: %{customdata[2]}<br>Reliability: %{customdata[3]}<extra></extra>",
    ))
    fig.update_layout(title=f"Top {top_n} candidates by similarity to Salah", xaxis_title="Cosine similarity",
                       xaxis_range=[0, 1], height=max(400, 28 * top_n), margin=dict(l=160))
    return fig


def _radar_fig_plotly(players_df, target, name_col="player_name"):
    features = [f for f in CLUSTER_FEATURES if f in players_df.columns and f in target.index]
    all_rows = pd.concat([players_df[features].reset_index(drop=True),
                          pd.DataFrame([target[features].values], columns=features)], ignore_index=True)
    normed = (all_rows - all_rows.min()) / (all_rows.max() - all_rows.min()).replace(0, 1)
    labels = [FEATURE_LABELS.get(f, f) for f in features]

    fig = go.Figure()
    for i, (_, row) in enumerate(players_df.iterrows()):
        values = normed.iloc[i].tolist()
        fig.add_trace(go.Scatterpolar(r=values + values[:1], theta=labels + labels[:1], fill="toself",
                                       name=row[name_col], opacity=0.6))
    salah_vals = normed.iloc[-1].tolist()
    fig.add_trace(go.Scatterpolar(r=salah_vals + salah_vals[:1], theta=labels + labels[:1], name="Salah target",
                                   line=dict(color="black", dash="dash", width=3)))
    fig.update_layout(title="Top targets vs. Salah (min-max scaled)",
                       polar=dict(radialaxis=dict(visible=True, range=[0, 1])), height=520)
    return fig


def build_html_dashboard(ranked_df, target, top_n=15, top_k_radar=3, translation_table=None,
                          output_path="salah_replacement_dashboard.html"):
    leaderboard_fig = _leaderboard_fig(ranked_df, top_n=top_n)
    radar_fig = _radar_fig_plotly(ranked_df.head(top_k_radar), target)

    sections = [("Top targets", leaderboard_fig), (f"Top {top_k_radar} vs. Salah", radar_fig)]
    plot_html_blocks = [f'<section class="card"><h2>{t}</h2>{to_html(f, full_html=False, include_plotlyjs=False)}</section>'
                        for t, f in sections]

    if translation_table is not None and not translation_table.empty:
        cols = [c for c in ["from_league", "to_league", "n_transfers", "confidence"] + CLUSTER_FEATURES if c in translation_table.columns]
        translation_html = translation_table[cols].round(3).to_html(index=False, classes="tbl")
    else:
        translation_html = "<p><em>No league translation table available.</em></p>"

    leaderboard_rows = "".join(
        f"<tr><td>{i+1}</td><td>{r.player_name}</td><td>{r.last_team}</td><td>{r.last_league}</td>"
        f"<td>{r.total_minutes:,}</td><td>{r.reliability}</td><td>{r.similarity_to_salah:.3f}</td></tr>"
        for i, r in ranked_df.head(top_n).reset_index(drop=True).iterrows()
    )

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Mohamed Salah Replacement -- Recruitment Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin:0; background:#f4f6f8; color:#1a1a1a; }}
  header {{ background:#c8102e; color:white; padding:28px 40px; }}
  header h1 {{ margin:0 0 6px 0; font-size:26px; }}
  main {{ max-width:1100px; margin:0 auto; padding:24px 20px 60px; }}
  .card {{ background:white; border-radius:10px; padding:20px 24px; margin-bottom:24px; box-shadow:0 1px 3px rgba(0,0,0,0.08); }}
  table.tbl {{ border-collapse:collapse; width:100%; font-size:13px; }}
  table.tbl th, table.tbl td {{ border:1px solid #e2e2e2; padding:6px 10px; text-align:left; }}
  table.tbl th {{ background:#f0f0f0; }}
  .note {{ font-size:13px; color:#666; margin-top:8px; }}
</style></head><body>
<header><h1>Mohamed Salah Replacement -- Recruitment Dashboard</h1>
<p>Unsupervised clustering + cosine similarity to a career-weighted Salah target profile, Big-5 league attackers.</p></header>
<main>
  <div class="card"><h2>Shortlist</h2>
    <table class="tbl"><tr><th>#</th><th>Player</th><th>Club</th><th>League</th><th>Minutes</th><th>Reliability</th><th>Similarity</th></tr>
    {leaderboard_rows}</table>
    <p class="note">Reliability reflects sample size, not a filter -- every attacking player stays in the pool.</p>
  </div>
  {''.join(plot_html_blocks)}
  <div class="card"><h2>League translation model</h2>{translation_html}</div>
  <div class="card"><h2>Methodology</h2>
    <p>Target profile: Salah's per-90 output, career-weighted (2018-2025 Liverpool seasons, recent seasons weighted higher).</p>
    <p>Candidate pool: all attacking players across the Big-5 leagues in the last two completed seasons, no minutes cutoff.</p>
    <p>Ranking: cosine similarity between each candidate's scaled profile and the Salah target vector.</p>
  </div>
</main></body></html>"""

    with open(output_path, "w") as f:
        f.write(html)
    return output_path


dashboard_path = build_html_dashboard(ranked, salah_target, top_n=20, top_k_radar=3,
                                       translation_table=translation_table,
                                       output_path=data_path("salah_replacement_dashboard.html"))
print("Dashboard written to:", dashboard_path)
