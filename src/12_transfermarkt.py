"""
Section 9: Transfermarkt analysis - value over time & age curves.

Transfermarkt has no official API, so this scrapes public pages. In the
real run this returned empty responses for every player (search URL
response length: 0) -- Transfermarkt blocks scripted/datacenter access,
so `tm_profiles` came back with `found=False` for the whole shortlist,
and the age-curve cell below errored as a knock-on effect.

The functions are real and would work against a normal browser session
or a residential IP, but don't rely on this running unattended. For the
actual final shortlist, age/contract/market value/injury history were
filled in by hand -- see data/manual/final_shortlist_manual_data_template.csv.
"""

import requests
from bs4 import BeautifulSoup

TM_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "en-GB,en;q=0.9",
}
SEARCH_URL = "https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche"
VALUE_HISTORY_URL = "https://www.transfermarkt.com/ceapi/marketValueDevelopment/graph/{player_id}"
PROFILE_URL = "https://www.transfermarkt.com/{slug}/profil/spieler/{player_id}"


def _polite_get(session, url, **kwargs):
    resp = session.get(url, headers=TM_HEADERS, timeout=20, **kwargs)
    resp.raise_for_status()
    time.sleep(random.uniform(2, 4))
    return resp


def tm_search_player(session, player_name):
    print(f"Searching for player: {player_name}")
    search_params = {"query": player_name}
    search_url_full = f"{SEARCH_URL}?query={player_name}"
    print(f"  Search URL: {search_url_full}")

    resp = _polite_get(session, SEARCH_URL, params=search_params)
    print(f"  Response text length: {len(resp.text)}")
    soup = BeautifulSoup(resp.text, "html.parser")
    print(f"  Soup object length (str): {len(str(soup))}")

    link = soup.select_one("table.items td.hauptlink a[href*='/profil/spieler/']")

    if link is None:
        print(f"  No direct search result link found for {player_name}")
        print("  ------ HTML content of search results page (truncated) ------")
        # Print first 2000 characters of the soup for debugging, to avoid overwhelming output
        print(str(soup)[:2000])
        print("  ------------------------------------------------------------")
        return None

    print(f"  Found link for {player_name}: {link.get('href')}")

    match = re.search(r"/([^/]+)/profil/spieler/(\d+)", link.get("href", ""))
    if not match:
        print(f"  No player_id/slug match in link for {player_name}")
        return None
    row = link.find_parent("tr")
    club_cell = row.select_one("td.zentriert a") if row else None
    return {"player_id": match.group(2), "slug": match.group(1),
            "name": link.get_text(strip=True), "club": club_cell.get_text(strip=True) if club_cell else None}


def tm_market_value_history(session, player_id):
    resp = _polite_get(session, VALUE_HISTORY_URL.format(player_id=player_id))
    points = resp.json().get("list", [])
    return pd.DataFrame([{"date": p.get("datum_mw") or p.get("date"), "value_eur": p.get("y"),
                           "age": p.get("age"), "club": p.get("verein")} for p in points])


def tm_player_profile(session, slug, player_id):
    resp = _polite_get(session, PROFILE_URL.format(slug=slug, player_id=player_id))
    soup = BeautifulSoup(resp.text, "html.parser")
    facts = {}
    for item in soup.select("li.data-header__label"):
        # Only the li's own direct text node -- NOT get_text() on the whole
        # <li>, which would concatenate the label with the child span's value.
        label_node = item.find(string=True, recursive=False)
        label = label_node.strip().rstrip(":") if label_node else ""
        value_el = item.select_one(".data-header__content")
        facts[label] = value_el.get_text(" ", strip=True) if value_el else None

    dob_match = re.search(r"(\d{4}-\d{2}-\d{2}|\w+ \d{1,2}, \d{4})", facts.get("Date of birth/Age", "") or "")
    age_match = re.search(r"\((\d+)\)", facts.get("Date of birth/Age", "") or "")
    value_el = soup.select_one(".data-header__market-value-wrapper")

    return {"player_id": player_id, "date_of_birth": dob_match.group(1) if dob_match else None,
            "age": int(age_match.group(1)) if age_match else None, "foot": facts.get("Foot"),
            "height": facts.get("Height"), "contract_expires": facts.get("Contract expires"),
            "current_club": facts.get("Current club"),
            "current_value_text": value_el.get_text(" ", strip=True) if value_el else None}


def enrich_with_transfermarkt(player_names, cache_path):
    if os.path.exists(cache_path):
        # Delete the cache file to force fresh scraping
        os.remove(cache_path)
        print(f"Deleted existing cache file: {cache_path}")
        cache, done = pd.DataFrame(), set()
    else:
        cache, done = pd.DataFrame(), set()

    session = requests.Session()
    new_rows = []

    # Define all expected columns for a complete record, with default None values
    # This ensures that even for unfound players, the DataFrame has all columns.
    all_expected_columns = {
        "query_name": None, "found": None,
        "player_id": None, "slug": None, "name": None, "club": None,
        "date_of_birth": None, "age": None, "foot": None, "height": None,
        "contract_expires": None, "current_club": None, "current_value_text": None,
        "latest_value_eur": None, "value_history_points": None
    }

    for name in player_names:
        if name in done:
            continue

        current_row_data = all_expected_columns.copy() # Start with all columns set to None
        current_row_data["query_name"] = name

        hit = tm_search_player(session, name)

        if hit is None:
            current_row_data["found"] = False
            new_rows.append(current_row_data) # Add row with 'found'=False and other fields as None
            continue

        current_row_data["found"] = True
        current_row_data.update(hit) # Update with details from tm_search_player

        profile = tm_player_profile(session, hit["slug"], hit["player_id"])
        current_row_data.update(profile) # Update with details from tm_player_profile

        history = tm_market_value_history(session, hit["player_id"])
        if not history.empty:
            current_row_data["latest_value_eur"] = history.iloc[-1]["value_eur"]
        current_row_data["value_history_points"] = len(history)

        new_rows.append(current_row_data)

    # Ensure the cache DataFrame also has all expected columns before concatenation
    # This handles cases where the cache might have been created with older logic
    for col in all_expected_columns.keys():
        if col not in cache.columns:
            cache[col] = None

    # Concatenate, ensuring columns are consistent.
    if not new_rows and cache.empty: # Edge case: no new rows and empty cache
        result = pd.DataFrame(columns=list(all_expected_columns.keys()))
    else:
        result = pd.concat([cache, pd.DataFrame(new_rows)], ignore_index=True) if new_rows else cache

    result.to_csv(cache_path, index=False)
    return result


# Run on the shortlist only (~15-20 names) -- TM will throttle bulk scraping.
#shortlist_names = ranked.head(15)["player_name"].tolist() + [


# Value-over-time chart for the shortlist
import plotly.graph_objects as go

# Ensure tm_profiles is created if not already present
# Run on the shortlist only (~15-20 names) -- TM will throttle bulk scraping.
shortlist_names = ranked.head(15)["player_name"].tolist() # Using top 15 from ranked
tm_profiles_cache_path = data_path("transfermarkt_profiles.csv")
tm_profiles = enrich_with_transfermarkt(shortlist_names, tm_profiles_cache_path)

session = requests.Session()
value_histories = {}
for _, row in tm_profiles[tm_profiles["found"] == True].iterrows():
    hist = tm_market_value_history(session, str(int(row["player_id"])))
    value_histories[row["query_name"]] = hist

fig = go.Figure()
for name, hist in value_histories.items():
    if hist.empty:
        continue
    fig.add_trace(go.Scatter(x=hist["date"], y=hist["value_eur"], mode="lines+markers", name=name))
fig.update_layout(title="Market value over time -- shortlist", xaxis_title="Date", yaxis_title="Value (EUR)", height=500)
fig.show()


# Age curve: candidate output vs. age, once Transfermarkt ages are merged in
age_lookup = tm_profiles.set_index("query_name")["age"].to_dict()
age_df = candidate_profiles.copy()
age_df["age"] = age_df["player_name"].map(age_lookup)
age_df = age_df.dropna(subset=["age"])

fig = go.Figure(go.Scatter(x=age_df["age"], y=age_df["npxG_per90"], mode="markers",
                            marker=dict(color="#89c2d9", size=7, opacity=0.7), text=age_df["player_name"],
                            hovertemplate="<b>%{text}</b><br>Age: %{x}<br>npxG/90: %{y:.2f}<extra></extra>"))
if len(age_df) >= 5:
    coeffs = np.polyfit(age_df["age"], age_df["npxG_per90"], 2)
    xs = np.linspace(age_df["age"].min(), age_df["age"].max(), 50)
    fig.add_trace(go.Scatter(x=xs, y=np.polyval(coeffs, xs), mode="lines", name="Age trend", line=dict(color="black")))
fig.update_layout(title="Age curve: non-penalty xG/90 by age", xaxis_title="Age", yaxis_title="npxG /90", height=500)
fig.show()
