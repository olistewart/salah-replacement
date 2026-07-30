"""
Section 6: Clustering.

K-means over the standardized 9-feature candidate profiles. K=5 chosen
from the elbow plot. Real run: cluster 2 (94 players) is where Salah's
own target profile lands -- see 07_similarity_ranking.py.
"""

'''Elbow Plot - K-means clustering'''

X = candidate_profiles[CLUSTER_FEATURES].copy()
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

inertias = []
k_values = range(2, 11)
for k in k_values:
    km = KMeans(n_clusters=k, random_state=42, n_init=20).fit(X_scaled)
    inertias.append(km.inertia_)

plt.figure(figsize=(8, 5))
plt.plot(list(k_values), inertias, marker="o")
plt.xlabel("Number of clusters (k)")
plt.ylabel("Inertia")
plt.title("Elbow plot -- pick k where the curve flattens")
plt.show()


K = 5  # set from the elbow plot above

kmeans = KMeans(n_clusters=K, random_state=42, n_init=20)
candidate_profiles["cluster"] = kmeans.fit_predict(X_scaled)

print(candidate_profiles["cluster"].value_counts().sort_index())
cluster_summary = candidate_profiles.groupby("cluster")[CLUSTER_FEATURES].mean().round(3)
print(cluster_summary)
