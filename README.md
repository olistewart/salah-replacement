# Mohamed Salah Replacement - Recruitment Analysis

A data-driven shortlist of stylistically similar, realistic replacements for
Mohamed Salah, built from Understat per-90 data across the Big-5 European
leagues, unsupervised k-means clustering, and cosine similarity to a
career-weighted Salah target profile.

## Project Overview

Liverpool are facing one of their biggest recruitment decisions ever: they need to replace Salah. 
Rather than starting from reputation or a scout's shortlist, this project starts from data: every
attacking player in the Big-5 leagues (Premier League, La Liga, Bundesliga,
Serie A, Ligue 1) over the last two completed seasons, profiled on nine
per-90 attacking metrics, clustered, and ranked by similarity to Salah's own
statistical profile based on his Liverpool career. A handful of supplementary analyses - league
translation (how do stats change when a player switches leagues?) and
breakout trajectory matching (who's on the same growth curve Salah was on
before his own move to Liverpool?) - add context beyond a single snapshot
similarity score.

**The final shortlist that came out of this analysis:** Bradley Barcola,
Ibrahim Mbaye, and Yan Diomande. Luca Koleosho emerged as one to watch, but
has played insufficient minutes for his profile to be robust. see [Results](#results) below.

## Repo structure

```
notebooks/
  salah_replacement_analysis.ipynb   the actual executed notebook, with real
                                      outputs and charts -- open this on
                                      GitHub or in Jupyter/Colab to see the
                                      full analysis end to end

src/
  01_setup.py ... 17_dashboard.py    the same analysis as the notebook,
                                      split into narratively-ordered scripts
                                      (one per notebook section) so the
                                      pipeline can be read or run outside a
                                      notebook
  run_all.py                         runs every numbered script in order

data/
  manual/                            hand-filled data (Transfermarkt fields
                                      that couldn't be scraped -- see Caveats)
  results/                           the real final shortlist vs. Salah
                                      comparison table, reconstructed from
                                      the notebook's own saved output

extensions/                          two follow-up scripts (Power BI export,
                                      a compact final-shortlist dashboard)
                                      built after the core analysis -- see
                                      extensions/README.md for what that
                                      means for how much to trust them

requirements.txt
LICENSE
```

## Methodology

1. **Setup & data collection** (`src/01`, `src/02`). Pulls per-90 player-season
   data via the `understatapi` Python client: five main seasons (2021-2025)
   across all five leagues, plus extra historical seasons for Salah
   specifically (Premier League 2017-2020, Serie A 2015-2016 -- his Roma
   seasons, needed later for breakout trajectory matching).
2. **Feature engineering** (`src/03`). Nine per-90 features: non-penalty
   goals, non-penalty xG, shots, assists, xA, key passes, xGChain, xGBuildup,
   and xG per shot. A `reliability` flag (High/Medium/Low by minutes played)
   is attached to every player instead of hard-filtering low-minute players
   out -- an earlier version of this project used a minutes cutoff and it
   was silently excluding plausible candidates (e.g. Brahim Diaz).
3. **Salah target profile** (`src/04`). Salah's own per-90 output at
   Liverpool, 2017-2025, each season weighted equally (the in-progress
   2025-26 season is excluded).
4. **Candidate pool** (`src/05`). Every attacking player across the Big-5
   leagues in the last two completed seasons.
5. **Clustering** (`src/06`). K-means (K=5, chosen from the elbow plot) over
   the standardized candidate profiles.
6. **Similarity ranking** (`src/07`). Cosine similarity between each
   candidate and Salah's target vector, in the same standardized feature
   space as the clustering.
7. **Visuals** (`src/08`-`src/11`). PCA scatter, radar
   plots (combined and per-candidate vs. Salah), stat-vs-stat scatters
   (goal threat vs. creativity, shot volume vs. quality), a minutes-vs-
   similarity check, and per-feature distribution histograms.
8. **Transfermarkt analysis** (`src/12`). Scrapes public Transfermarkt pages
   for market value history and age. **This did not return usable data in
   the actual run** but can be obtained manually - see Caveats.
9. **League translation model**, v1 and v2 (`src/13`, `src/14`). Projects a
   candidate's stats into a different league using empirically observed
   cross-league transfers (v2 adds minutes-weighting, cluster-aware ratios,
   and a proper z-scored fallback for league pairs with too little data).
10. **Breakout trajectory matching** (`src/15`, `src/16`). A complementary
    signal to the static similarity score: does a candidate's own
    season-over-season growth shape resemble Salah's Roma-to-Liverpool
    breakout arc?
11. **Dashboard** (`src/17`). Packages the leaderboard, top-3 radar, and
    league translation table into one self-contained HTML file.

## Results

Real output from the executed notebook. The candidate pool: **1,504
attacking players** across the Big-5 leagues, last two completed seasons, no
minutes cutoff. K-means (K=5) split them into clusters of 452 / 183 / 94 /
337 / 438 players. Salah's own target profile lands in **cluster 2** (94
players) -- the highest-output cluster on creativity (xA, key passes) and
overall attacking involvement (xGChain, xGBuildup) combined with strong
non-penalty output, rather than the pure-poacher cluster.

The final 8-name comparison set (all cluster 2, all ranked by cosine
similarity to the Salah target vector) - full per-90 breakdown in
[`data/results/final_shortlist_vs_salah_profiles.csv`](data/results/final_shortlist_vs_salah_profiles.csv):

| Player | Club | League | Similarity to Salah |
|---|---|---|---|
| Ousmane Dembélé | Paris Saint-Germain | Ligue 1 | 0.973 |
| Vinícius Júnior | Real Madrid | La Liga | 0.948 |
| Raphinha | Barcelona | La Liga | 0.944 |
| Bradley Barcola | Paris Saint-Germain | Ligue 1 | 0.935 |
| Ibrahim Mbaye | Paris Saint-Germain | Ligue 1 | 0.926 |
| Luca Koleosho | Paris FC | Ligue 1 | 0.915 |
| Michael Olise | Bayern Munich | Bundesliga | 0.838 |
| Yan Diomande | RB Leipzig | Bundesliga | 0.785 |

Similarity alone doesn't account for realism of a move (Dembélé, Vinícius,
Raphinha, and Olise are established starters at elite clubs, not realistic
transfer targets) - the lower-similarity names further down the list
(Mbaye, Koleosho, Diomande, and Barcola) are the more actionable targets,
which is why the project's own follow-on discussion focused on that group,
Barcola in particular.

## Caveats

- **Transfermarkt scraping did not work in the actual run.** Every search
  request came back empty (0-length response) - Transfermarkt blocks
  scripted/datacenter access. `src/12_transfermarkt.py` contains real,
  workable scraping code, but don't rely on it running unattended; for the
  final shortlist, age/contract/market value/injury history need to be
  filled in by hand (see `data/manual/final_shortlist_manual_data_template.csv`).
- **Minutes threshold.** Every attacking player stays in the candidate
  pool regardless of sample size; a `reliability` flag (High/Medium/Low)
  makes the sample size visible instead of silently filtering on it. Treat
  "Low" reliability results as noisier, not wrong.
- **Two cells in the original notebook never successfully ran**: the
  Colab-interactive-editing artifacts are called out in the relevant
  `src/` file docstrings (`src/12_transfermarkt.py` and `src/17_dashboard.py`)
  rather than silently fixed and hidden.
- **League translation and breakout trajectory are both thin-data models**
  by nature - cross-Big-5-league transfers within a 5-season window aren't
  a large sample, and both models are explicit about confidence/reliability
  tiers rather than presenting every estimate as equally trustworthy.

## Running it

```bash
pip install -r requirements.txt
```

**Option 1: the notebook.** Open `notebooks/salah_replacement.ipynb`
in Jupyter, Colab, or VS Code and run cells top to bottom. This is the
version with real charts and output already saved in it -- you can also just
read it on GitHub without running anything.

**Option 2: the scripts.**

```bash
cd src
python run_all.py
```

Runs every numbered script in order, in one shared session. Set `SALAH_DATA_DIR` as an
environment variable to control where CSVs get cached (defaults to
`./salah_replacement_data`). Note `02_data_collection.py` hits the live
Understat API and `12_transfermarkt.py` hits Transfermarkt (which, per the
caveat above, doesn't return usable data) - both are slow/network-dependent;
everything from `03` onward is pure computation over the cached CSVs.

## Extensions

Two follow-up scripts - a Power BI CSV/dashboard export, and a compact
dashboard for a final, narrowed 3-name shortlist - live in `extensions/`.
They were built after the core analysis and tested against synthetic data
rather than the real candidate pool; see `extensions/README.md` before
trusting their output.

## License

MIT -- see [LICENSE](LICENSE).
