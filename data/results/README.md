# Results

`final_shortlist_vs_salah_profiles.csv` - the 8-player final comparison set
(plus Salah's own target row) from the real, executed notebook run: per-90
profile, cluster assignment (all 8 fall in cluster 2, same as Salah's target),
and cosine similarity to Salah.

This file is reconstructed from the notebook's own saved print/display output
(`notebooks/salah_replacement.ipynb`, cells building `ranked`,
`ranked_cluster_2`, and `comparison_profiles_df`) rather than copied from a
live CSV export, because the original run saved its CSV outputs to a mounted
Google Drive folder that wasn't included in the upload. The numbers
themselves are exactly what that run produced -- open the notebook and
search for "Player profiles saved to" to see the original output cell.

Team/league values for Koleosho, Olise, and Diomande are filled in from the
club names in the notebook's own cluster-2 printout (Paris FC -> Ligue 1,
Bayern Munich / RB Leipzig -> Bundesliga) since the specific print statement
used didn't include a `last_league` column for that view.
