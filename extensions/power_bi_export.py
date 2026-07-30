"""
Extension: export flat CSVs for Power BI.

Not part of the executed notebook -- built afterward, tested against
synthetic data (see extensions/README.md for what that means in practice).
Run this after the core pipeline -- specifically src/01, 03, 04, 05, 06, 07,
08_visuals_pca.py, 09_visuals_radar.py (defines FEATURE_LABELS), and
15_breakout_trajectory.py (defines ranked_full) -- so `ranked_full`,
`plot_df_pca`, `scaler`, `pca`, `candidate_profiles`, `salah_target`,
`salah_df`, `CLUSTER_FEATURES`, `FEATURE_LABELS`, and `data_path` are all in
scope.

Produces, in DATA_DIR:
  power_bi_players_wide.csv        one row per player (candidates + Salah),
                                    cluster features, PCA coords, similarity,
                                    trajectory score
  power_bi_players_long.csv        the same data unpivoted (one row per
                                    player x feature) for radar-style visuals
  power_bi_candidate_selector.csv  candidate names only (Salah excluded) --
                                    a disconnected slicer table so selecting
                                    a candidate doesn't filter Salah out too
  power_bi_league_translation.csv  the pooled league-translation ratio table
  power_bi_radar_script.py         a ready-to-paste Power BI Python-visual
                                    script for a dynamic candidate-vs-Salah
                                    radar chart

See the main README's Power BI section for how to wire these into a
dashboard, including guidance for the fact that Power BI Desktop is
Windows-only.
"""
import numpy as np
import pandas as pd

# --- Wide export: one row per player (candidates + Salah), Power BI-ready ---
export_df = ranked_full.copy()
export_df["player_type"] = "Candidate"

salah_export_row = {
    "player_name": "Mohamed Salah",
    "last_team": "Liverpool",
    "last_league": "Premier League",
    "total_minutes": salah_df["time"].sum(),
    "reliability": "N/A (target)",
    "cluster": np.nan,
    "similarity_to_salah": 1.0,
    "player_type": "Target",
}
for f in CLUSTER_FEATURES:
    salah_export_row[f] = salah_target[f]

salah_scaled_for_export = scaler.transform(
    pd.DataFrame([salah_target[CLUSTER_FEATURES].values], columns=CLUSTER_FEATURES)
)
salah_pca_coords = pca.transform(salah_scaled_for_export)[0]
salah_export_row["PC1"], salah_export_row["PC2"] = salah_pca_coords[0], salah_pca_coords[1]

pca_lookup = plot_df_pca.set_index("player_name")[["PC1", "PC2"]]
export_df = export_df.merge(pca_lookup, on="player_name", how="left")
export_df = pd.concat([export_df, pd.DataFrame([salah_export_row])], ignore_index=True)

power_bi_cols = (
    ["player_name", "player_type", "last_team", "last_league", "total_minutes", "reliability",
     "cluster", "PC1", "PC2", "similarity_to_salah", "breakout_trajectory_score", "trajectory_reliability"]
    + CLUSTER_FEATURES
)
power_bi_cols = [c for c in power_bi_cols if c in export_df.columns]
export_df = export_df[power_bi_cols]

export_df.to_csv(data_path("power_bi_players_wide.csv"), index=False)
print("Wide export:", export_df.shape)

# --- Long/unpivoted export: one row per player x feature, for radar-friendly visuals ---
long_df = export_df.melt(
    id_vars=["player_name", "player_type", "last_league", "cluster", "reliability"],
    value_vars=CLUSTER_FEATURES,
    var_name="feature",
    value_name="value",
)
long_df["feature_label"] = long_df["feature"].map(FEATURE_LABELS).fillna(long_df["feature"])

long_df.to_csv(data_path("power_bi_players_long.csv"), index=False)
print("Long export:", long_df.shape)

# --- Disconnected selector table: candidate names only (Salah excluded) ---
selector_df = export_df.loc[export_df["player_type"] == "Candidate", ["player_name"]].drop_duplicates()
selector_df = selector_df.sort_values("player_name").reset_index(drop=True)

selector_df.to_csv(data_path("power_bi_candidate_selector.csv"), index=False)
print("Selector table:", selector_df.shape)

# --- League translation table, cleaned up for import ---
if "translation_pooled" in dir() and not translation_pooled.empty:
    power_bi_translation = translation_pooled[
        ["from_league", "to_league", "n_transfers", "tier"]
        + [c for c in translation_pooled.columns if c.endswith("_ratio")]
    ].copy()
    power_bi_translation.to_csv(data_path("power_bi_league_translation.csv"), index=False)
    print("League translation export:", power_bi_translation.shape)
else:
    print("translation_pooled is empty or not in scope -- skipping league translation export "
          "(run src/14_league_translation_v2.py first).")

# --- Ready-to-paste Power BI Python visual: dynamic radar chart ---
# Power BI's Python visual re-runs this script on every filter-context change and exposes
# whatever's on the visual's fields as a dataframe called `dataset`. Expects `dataset` to
# contain `player_name` + CLUSTER_FEATURES (from power_bi_players_wide.csv) plus a
# `SelectedCandidate` measure: SELECTEDVALUE(power_bi_candidate_selector[player_name], "...").
power_bi_radar_script = f'''import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

CLUSTER_FEATURES = {CLUSTER_FEATURES!r}
FEATURE_LABELS = {FEATURE_LABELS!r}

selected = dataset["SelectedCandidate"].iloc[0]
plot_players = dataset[dataset["player_name"].isin([selected, "Mohamed Salah"])].drop_duplicates("player_name")

all_rows = plot_players[CLUSTER_FEATURES].reset_index(drop=True)
mins, maxs = all_rows.min(), all_rows.max()
normed = (all_rows - mins) / (maxs - mins).replace(0, 1)

labels = [FEATURE_LABELS.get(f, f) for f in CLUSTER_FEATURES]
angles = np.linspace(0, 2 * np.pi, len(CLUSTER_FEATURES), endpoint=False).tolist()
angles += angles[:1]

fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
for i, row in plot_players.reset_index(drop=True).iterrows():
    values = normed.iloc[i].tolist()
    values += values[:1]
    style = dict(linewidth=2.5, linestyle="--", color="black") if row["player_name"] == "Mohamed Salah" else dict(linewidth=2)
    ax.plot(angles, values, label=row["player_name"], **style)
    ax.fill(angles, values, alpha=0.08)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, fontsize=9)
ax.set_yticklabels([])
ax.set_title(f"{{selected}} vs. Salah target", fontsize=13, pad=20)
ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=9)
plt.show()
'''

with open(data_path("power_bi_radar_script.py"), "w") as f:
    f.write(power_bi_radar_script)

print("Power BI radar script written to:", data_path("power_bi_radar_script.py"))
