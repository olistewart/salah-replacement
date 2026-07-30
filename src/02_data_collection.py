"""
Section 2: Data collection (Understat, Big-5 leagues).

Pulls per-90 player-season data via the `understatapi` client for the
main 5-season window plus extra historical seasons for Salah specifically
(Premier League 2017-2020, Serie A 2015-2016 -- his Roma-to-Liverpool
breakout window, needed later for the trajectory-matching section).
Caches to CSV so re-runs don't re-hit the API.
"""

from understatapi import UnderstatClient

LEAGUES = {
    "EPL": "Premier League",
    "La_Liga": "La Liga",
    "Bundesliga": "Bundesliga",
    "Serie_A": "Serie A",
    "Ligue_1": "Ligue 1",
}

MAIN_SEASONS = ["2021", "2022", "2023", "2024", "2025"]
#SALAH_EXTRA_SEASONS = ["2017", "2018", "2019", "2020"]  # Premier League only
SALAH_EXTRA_PULLS = {
    "Premier League": ["2017", "2018", "2019", "2020"],
    "Serie A": ["2015", "2016"],  # Roma, pre-Liverpool -- the breakout window
}

CANDIDATE_SEASONS = [int(s) for s in MAIN_SEASONS[-2:]]  # last two completed seasons


def fetch_understat(leagues: dict, seasons: list) -> pd.DataFrame:
    client = UnderstatClient()
    frames = []
    for league_key, league_name in leagues.items():
        for season in seasons:
            print(f"Loading {league_name}, {season}...")
            league = client.league(league=league_key)
            players = league.get_player_data(season=season)
            df = pd.DataFrame(players)
            df["league"] = league_name
            df["season"] = season
            frames.append(df)
    return pd.concat(frames, ignore_index=True)


raw_path = data_path("understat_big5_player_seasons_raw_breakout.csv")

if os.path.exists(raw_path):
    print(f"Found cached raw pull at {raw_path}, loading from disk.")
    player_seasons = pd.read_csv(raw_path)
else:
    main_pull = fetch_understat(LEAGUES, MAIN_SEASONS)

    salah_extra_frames = []
    # Invert the LEAGUES dictionary to easily get the Understat league_key from its full name
    league_name_to_key = {v: k for k, v in LEAGUES.items()}

    # Iterate through SALAH_EXTRA_PULLS to fetch data for each league and its specific seasons
    for league_name_to_pull, seasons_list_to_pull in SALAH_EXTRA_PULLS.items():
        if league_name_to_pull in league_name_to_key:
            understat_league_key = league_name_to_key[league_name_to_pull]
            print(f"Fetching extra seasons for {league_name_to_pull}...")
            # Call fetch_understat with the single league and its specific seasons list
            salah_extra_frames.append(fetch_understat({understat_league_key: league_name_to_pull}, seasons_list_to_pull))
        else:
            print(f"Warning: League '{league_name_to_pull}' from SALAH_EXTRA_PULLS not found in LEAGUES mapping. Skipping.")

    # Concatenate all collected Salah extra season data
    salah_extra = pd.concat(salah_extra_frames, ignore_index=True) if salah_extra_frames else pd.DataFrame()

    player_seasons = pd.concat([main_pull, salah_extra], ignore_index=True).drop_duplicates(
        subset=["player_name", "league", "season"]
    )
    player_seasons.to_csv(raw_path, index=False)
    print(f"Saved raw pull to {raw_path}")

print(player_seasons.shape)
print(player_seasons.groupby(["league", "season"]).size())
