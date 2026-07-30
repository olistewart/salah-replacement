"""
Section 7: Similarity ranking vs. the Salah target.

Cosine similarity, on the same standardized feature space as the
clustering, between each candidate and Salah's target vector.
"""

def rank_by_similarity(candidates: pd.DataFrame, target: pd.Series, scaler) -> pd.DataFrame:
    Xc = scaler.transform(candidates[CLUSTER_FEATURES])
    target_scaled = scaler.transform(pd.DataFrame([target[CLUSTER_FEATURES].values], columns=CLUSTER_FEATURES))
    sims = cosine_similarity(target_scaled, Xc)[0]
    out = candidates.copy()
    out["similarity_to_salah"] = sims
    return out.sort_values("similarity_to_salah", ascending=False).reset_index(drop=True)


ranked = rank_by_similarity(candidate_profiles, salah_target, scaler)
#ranked.to_csv(data_path("salah_replacement_ranked.csv"), index=False)

print(ranked[["player_name", "last_team", "last_league", "total_minutes", "reliability", "cluster", "similarity_to_salah"]].head(25))


salah_target_scaled = scaler.transform(pd.DataFrame([salah_target[CLUSTER_FEATURES].values], columns=CLUSTER_FEATURES))
salah_target_cluster = kmeans.predict(salah_target_scaled)[0]

print(f"Mohamed Salah's target profile belongs to Cluster: {salah_target_cluster}")
print("Salah target profile:\n", salah_target)
print("Corresponding cluster summary:\n", cluster_summary.loc[salah_target_cluster])


ranked_cluster_2 = ranked[ranked['cluster'] == 2].reset_index(drop=True)
print("Top players in Cluster 2:")
print(ranked_cluster_2[["player_name", "last_team", "total_minutes", "seasons_count", "reliability", "cluster", "similarity_to_salah"]].head(50))
