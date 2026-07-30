# Extensions

These two scripts were built in a later, separate working session -- after
the notebook in `notebooks/` was already run and the shortlist finalised --
as answers to two follow-up questions: "can I build a Power BI dashboard
from this?" and "can I get a compact dashboard for just my final 3
candidates, including Transfermarkt data?"

They are **not part of the executed notebook**. They were tested by running
them against synthetic (fabricated) player data with the same schema as the
real pipeline, to confirm the code is correct and produces the right shapes
of output -- not against the real candidate pool. Before trusting the actual
numbers they produce, run them against real data: execute `src/01` through
`src/09_visuals_radar.py`, plus `src/13`-`src/15`, in one session (or import
the equivalent cells from `notebooks/salah_replacement_analysis.ipynb`),
then run one of these scripts in the same session/notebook.

- **`power_bi_export.py`** -- exports flat CSVs (`power_bi_players_wide.csv`,
  `power_bi_players_long.csv`, `power_bi_candidate_selector.csv`,
  `power_bi_league_translation.csv`) plus a ready-to-paste Power BI Python
  radar-chart script, for building a dashboard in Power BI Desktop or
  Power BI Service.
- **`shortlist_dashboard.py`** -- a single self-contained HTML file (Plotly
  via CDN, no server needed) scoped to a final, narrowed shortlist rather
  than the whole candidate pool: an interactive PCA scatter, a goal-threat-
  vs-creativity scatter, a compact table, one radar chart per candidate vs.
  Salah, and a Transfermarkt panel read from a small manually-filled CSV
  (age, contract, market value, injury history -- created blank on first
  run since Transfermarkt scraping isn't reliable, see `src/12_transfermarkt.py`).

## What's not here

An earlier version of this project also added take-ons, dribbles, and
crosses (including crosses into the penalty box specifically) as extra
cluster features, sourced from FBref since Understat doesn't track them --
motivated by wanting a replacement who can service a target-man striker,
not just replicate Salah's shooting/creating numbers. That code isn't
included here: it was built in a working session whose exact final source
isn't available at the time this repo was put together, and retyping it
from memory risked introducing subtle differences from what was actually
tested. If you want to re-add it, `data/manual/final_shortlist_manual_data_template.csv`
already has placeholder columns (`take_ons_per90`, `take_on_success_rate`,
`crosses_per90`, `box_crosses_per90`) for exactly this purpose.
