"""
SportRadar Tennis API extraction.

Pulls Competitions, Complexes and Doubles Rankings, and flattens the nested
JSON into lists of dicts that match the project's table schema:
    categories, competitions, complexes, venues, competitors, competitor_rankings

Setup:
    pip install requests pandas
    set SPORTRADAR_API_KEY=your_key_here      (Windows CMD)
"""

import logging
import os
import time

import pandas as pd
import requests

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
API_KEY = os.getenv("SPORTRADAR_API_KEY")
BASE_URL = "https://api.sportradar.com/tennis/trial/v3/en"

# Check the exact path of each endpoint on the docs pages linked in the
# project PDF, and edit here if yours differs.
ENDPOINTS = {
    "competitions": "competitions.json",
    "complexes": "complexes.json",
    "doubles_rankings": "double_competitors_rankings.json",
}

REQUEST_GAP_SECONDS = 1.2   # trial keys allow ~1 request per second
MAX_RETRIES = 5
TIMEOUT_SECONDS = 30

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Fetching (errors + rate limits)
# --------------------------------------------------------------------------
def fetch_json(endpoint_key):
    """Call one endpoint and return its JSON, retrying on rate limits/server errors."""
    if not API_KEY:
        raise RuntimeError("Set the SPORTRADAR_API_KEY environment variable first.")

    url = f"{BASE_URL}/{ENDPOINTS[endpoint_key]}"
    params = {"api_key": API_KEY}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)

            if response.status_code == 200:
                time.sleep(REQUEST_GAP_SECONDS)  # be polite before the next call
                return response.json()

            if response.status_code == 429:  # rate limit hit
                wait = int(response.headers.get("Retry-After", 2 ** attempt))
                log.warning("429 rate limit on %s, waiting %ss", endpoint_key, wait)
                time.sleep(wait)
                continue

            if response.status_code >= 500:  # server trouble, try again
                log.warning("Server error %s on %s", response.status_code, endpoint_key)
                time.sleep(2 ** attempt)
                continue

            # 401/403 (bad key) or 404 (wrong path): retrying will not help
            response.raise_for_status()

        except (requests.ConnectionError, requests.Timeout) as exc:
            log.warning("Network issue on %s (attempt %s): %s", endpoint_key, attempt, exc)
            time.sleep(2 ** attempt)

    raise RuntimeError(f"Gave up on '{endpoint_key}' after {MAX_RETRIES} attempts")


# --------------------------------------------------------------------------
# Parsing (nested JSON -> flat rows)
# --------------------------------------------------------------------------
def parse_competitions(payload):
    """Return (categories, competitions) as lists of dicts."""
    categories, competitions = {}, []
    for item in payload.get("competitions", []):
        category = item.get("category") or {}
        if category.get("id"):
            categories[category["id"]] = {
                "category_id": category["id"],
                "category_name": category.get("name"),
            }
        competitions.append({
            "competition_id": item.get("id"),
            "competition_name": item.get("name"),
            "parent_id": item.get("parent_id"),   # nullable on purpose
            "type": item.get("type"),
            "gender": item.get("gender"),
            "category_id": category.get("id"),
        })
    return list(categories.values()), competitions


def parse_complexes(payload):
    """Return (complexes, venues) as lists of dicts."""
    complexes, venues = [], []
    for item in payload.get("complexes", []):
        complexes.append({
            "complex_id": item.get("id"),
            "complex_name": item.get("name"),
        })
        for venue in item.get("venues", []):
            venues.append({
                "venue_id": venue.get("id"),
                "venue_name": venue.get("name"),
                "city_name": venue.get("city_name"),
                "country_name": venue.get("country_name"),
                "country_code": venue.get("country_code"),
                "timezone": venue.get("timezone"),
                "complex_id": item.get("id"),
            })
    return complexes, venues


def parse_doubles_rankings(payload):
    """Return (competitors, rankings) as lists of dicts."""
    competitors, rankings = {}, []
    for ranking_list in payload.get("rankings", []):
        for entry in ranking_list.get("competitor_rankings", []):
            comp = entry.get("competitor") or {}
            if not comp.get("id"):
                continue  # cannot link a ranking without a competitor
            competitors[comp["id"]] = {
                "competitor_id": comp["id"],
                "name": comp.get("name"),
                "country": comp.get("country"),
                "country_code": comp.get("country_code"),
                "abbreviation": comp.get("abbreviation"),
            }
            rankings.append({
                "rank": entry.get("rank"),
                "movement": entry.get("movement", 0),
                "points": entry.get("points"),
                "competitions_played": entry.get("competitions_played"),
                "competitor_id": comp["id"],
            })
    return list(competitors.values()), rankings


# --------------------------------------------------------------------------
# Cleaning + saving
# --------------------------------------------------------------------------
def to_clean_frame(rows, key_column=None):
    """Make a DataFrame, drop duplicate keys and rows with a missing key."""
    df = pd.DataFrame(rows)
    if key_column and not df.empty:
        df = df.dropna(subset=[key_column]).drop_duplicates(subset=[key_column])
    return df


def main():
    output_dir = "extracted_data"
    os.makedirs(output_dir, exist_ok=True)

    categories, competitions = parse_competitions(fetch_json("competitions"))
    complexes, venues = parse_complexes(fetch_json("complexes"))
    competitors, rankings = parse_doubles_rankings(fetch_json("doubles_rankings"))

    tables = {
        "categories": to_clean_frame(categories, "category_id"),
        "competitions": to_clean_frame(competitions, "competition_id"),
        "complexes": to_clean_frame(complexes, "complex_id"),
        "venues": to_clean_frame(venues, "venue_id"),
        "competitors": to_clean_frame(competitors, "competitor_id"),
        "competitor_rankings": to_clean_frame(rankings),
    }

    for name, df in tables.items():
        df.to_csv(os.path.join(output_dir, f"{name}.csv"), index=False)
        log.info("%-20s %6d rows saved", name, len(df))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # top-level safety net so the failure is readable
        log.error("Extraction failed: %s", exc)
        raise
