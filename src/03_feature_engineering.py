"""
Section 3: Cleaning & feature engineering.

Builds the 9 per-90 CLUSTER_FEATURES used throughout the analysis, flags
attacking-role players, and attaches a reliability flag (High/Medium/Low
by minutes) instead of hard-filtering low-minute players out -- see the
top-level README for why that threshold was removed.
"""

CLUSTER_FEATURES = [
    "npg_per90",
    "npxG_per90",
    "shots_per90",
    "assists_per90",
    "xA_per90",
    "key_passes_per90",
    "xGChain_per90",
    "xGBuildup_per90",
    "xG_per_shot",
]

RAW_NUMERIC_COLS = [
    "games", "time", "goals", "xG", "assists", "xA", "shots",
    "key_passes", "yellow_cards", "red_cards", "npg", "npxG",
    "xGChain", "xGBuildup",
]

PER90_SOURCE_COLS = ["goals", "xG", "assists", "xA", "shots", "key_passes", "npg", "npxG", "xGChain", "xGBuildup"]

MIN_SANITY_MINUTES = 270  # ~3 full matches -- a floor against noise, not a confidence cutoff


def is_attacking(position: str) -> bool:
    """Forwards, plus midfielders who aren't also tagged as defenders.
    Broad on purpose: catches wingers/10s mistagged as pure 'M'."""
    if not isinstance(position, str):
        return False
    tags = set(position.split())
    if "GK" in tags:
        return False
    if "F" in tags:
        return True
    if "M" in tags and "D" not in tags:
        return True
    return False


def reliability_flag(minutes: float) -> str:
    if minutes >= 1800:
        return "High"
    if minutes >= 900:
        return "Medium"
    return "Low"


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in RAW_NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["season"] = pd.to_numeric(df["season"], errors="coerce")
    df = df[df["time"] >= MIN_SANITY_MINUTES].copy()

    for col in PER90_SOURCE_COLS:
        df[f"{col}_per90"] = df[col] / df["time"] * 90

    df["shot_conversion"] = df["goals"] / df["shots"].replace(0, np.nan)
    df["xG_per_shot"] = (df["xG"] / df["shots"].replace(0, np.nan)).fillna(0.0)
    df["is_attacking"] = df["position"].apply(is_attacking)
    df["reliability"] = df["time"].apply(reliability_flag)
    return df

# --- Debugging Salah's missing Roma data ---
print("\n--- Mohamed Salah's data in player_seasons BEFORE feature engineering ---")
salah_player_seasons_check = player_seasons[
    (player_seasons['player_name'] == 'Mohamed Salah') &
    (player_seasons['season'].isin(['2015', '2016', '2017', '2018', '2019']))
].sort_values('season')
print(salah_player_seasons_check[['season', 'team_title', 'league', 'time']])
print("----------------------------------------------------------------------\n")

df = engineer_features(player_seasons)
clean_path = data_path("understat_big5_player_seasons_clean.csv")
df.to_csv(clean_path, index=False)

print(f"Saved cleaned dataset to: {clean_path}")
print(df.shape)
print(df["reliability"].value_counts())
print(f"Attacking-role rows: {df['is_attacking'].sum()} / {len(df)}")
