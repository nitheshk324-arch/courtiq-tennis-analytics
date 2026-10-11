from io import BytesIO
import sqlite3
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "tennis_analytics.sqlite"
TABLE_NAMES = [
    "categories",
    "competitions",
    "competitors",
    "competitor_rankings",
    "complexes",
    "venues",
]


def _get_supabase_settings():
    try:
        settings = st.secrets.get("supabase")
    except StreamlitSecretNotFoundError:
        return None

    if not settings:
        return None

    required = ("url", "bucket", "service_role_key")
    missing = [key for key in required if not settings.get(key)]
    if missing:
        raise ValueError(
            "Supabase configuration is incomplete. Add "
            f"{', '.join(missing)} to the [supabase] Streamlit secrets section."
        )
    return settings


def _read_supabase_csv(table_name: str, settings) -> pd.DataFrame:
    files = settings.get("files", {})
    object_path = files.get(table_name, f"{table_name}.csv").strip("/")
    encoded_path = "/".join(quote(part, safe="") for part in object_path.split("/"))
    bucket = quote(settings["bucket"], safe="")
    url = f"{settings['url'].rstrip('/')}/storage/v1/object/{bucket}/{encoded_path}"
    service_role_key = settings["service_role_key"]
    request = Request(
        url,
        headers={
            "apikey": service_role_key,
            "Authorization": f"Bearer {service_role_key}",
        },
    )
    with urlopen(request, timeout=30) as response:
        return pd.read_csv(BytesIO(response.read()))


def _ensure_sqlite_database() -> None:
    if DB_PATH.exists():
        try:
            with sqlite3.connect(DB_PATH) as conn:
                existing = pd.read_sql_query(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
                    conn,
                )
            if set(existing["name"]) >= set(TABLE_NAMES):
                return
        except Exception:
            pass

    csv_files = {table_name: BASE_DIR / f"{table_name}.csv" for table_name in TABLE_NAMES}
    if all(csv_path.is_file() for csv_path in csv_files.values()):
        settings = None
    else:
        settings = _get_supabase_settings()
        if settings is None:
            missing = [
                csv_path.name
                for csv_path in csv_files.values()
                if not csv_path.is_file()
            ]
            raise FileNotFoundError(
                "Missing required tennis data files: "
                f"{', '.join(missing)}. Place all six CSVs beside db_manager.py, "
                "or configure a private Supabase bucket in Streamlit secrets."
            )

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        for table_name, csv_path in csv_files.items():
            df = (
                pd.read_csv(csv_path)
                if settings is None
                else _read_supabase_csv(table_name, settings)
            )
            df = df.where(pd.notnull(df), None)
            df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()


def check_mysql_connection():
    return False, "MySQL is not configured for this project. SQLite is the default local database engine."


def check_sqlite_connection():
    try:
        _ensure_sqlite_database()
        return True, f"SQLite database ready at {DB_PATH.name}"
    except Exception as exc:  # pragma: no cover - defensive guard
        return False, f"SQLite unavailable: {exc}"


def _get_sqlite_connection():
    _ensure_sqlite_database()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run_query(sql, engine="sqlite"):
    start = time.perf_counter()
    conn = None
    try:
        if engine != "sqlite":
            raise ValueError("MySQL is not configured for this project. Please switch to SQLite.")

        conn = _get_sqlite_connection()
        df = pd.read_sql_query(sql, conn)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return df, elapsed_ms, None
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return None, elapsed_ms, str(exc)
    finally:
        if conn is not None:
            conn.close()


def get_table_counts(engine="sqlite"):
    if engine != "sqlite":
        return {}

    conn = None
    try:
        conn = _get_sqlite_connection()
        counts = {}
        for table_name in TABLE_NAMES:
            try:
                count_df = pd.read_sql_query(f"SELECT COUNT(*) AS row_count FROM \"{table_name}\"", conn)
                counts[table_name] = int(count_df.iloc[0]["row_count"])
            except Exception:
                continue
        return counts
    finally:
        if conn is not None:
            conn.close()


SQL_QUERIES = [
    {
        "id": 1,
        "title": "List competitions with category names",
        "category": "Core Data",
        "desc": "Returns every competition together with its parent category for operational reference.",
        "sql_mysql": "SELECT c.competition_id, c.competition_name, cat.category_name FROM competitions AS c JOIN categories AS cat ON c.category_id = cat.category_id;",
        "sql_sqlite": "SELECT c.competition_id, c.competition_name, cat.category_name FROM competitions AS c JOIN categories AS cat ON c.category_id = cat.category_id;",
    },
    {
        "id": 2,
        "title": "Count competitions by category",
        "category": "Competition Overview",
        "desc": "Measures the volume of tournaments by circuit category to highlight distribution.",
        "sql_mysql": "SELECT cat.category_name, COUNT(c.competition_id) AS competition_count FROM competitions c JOIN categories cat ON c.category_id = cat.category_id GROUP BY cat.category_name ORDER BY competition_count DESC;",
        "sql_sqlite": "SELECT cat.category_name, COUNT(c.competition_id) AS competition_count FROM competitions c JOIN categories cat ON c.category_id = cat.category_id GROUP BY cat.category_name ORDER BY competition_count DESC;",
    },
    {
        "id": 3,
        "title": "Filter doubles competitions",
        "category": "Format Analysis",
        "desc": "Retrieves all doubles-format tournaments for format comparison and pipeline validation.",
        "sql_mysql": "SELECT c.competition_id, c.competition_name, cat.category_name FROM competitions c JOIN categories cat ON c.category_id = cat.category_id WHERE c.type = 'doubles';",
        "sql_sqlite": "SELECT c.competition_id, c.competition_name, cat.category_name FROM competitions c JOIN categories cat ON c.category_id = cat.category_id WHERE c.type = 'doubles';",
    },
    {
        "id": 4,
        "title": "Competitions in a selected category",
        "category": "Category Drilldown",
        "desc": "Returns all competitions within a given category such as ITF Men or ATP.",
        "sql_mysql": "SELECT c.competition_id, c.competition_name FROM competitions c JOIN categories cat ON c.category_id = cat.category_id WHERE cat.category_name = 'ITF Men';",
        "sql_sqlite": "SELECT c.competition_id, c.competition_name FROM competitions c JOIN categories cat ON c.category_id = cat.category_id WHERE cat.category_name = 'ITF Men';",
    },
    {
        "id": 5,
        "title": "Parent and sub-competitions",
        "category": "Hierarchy Mapping",
        "desc": "Maps each sub-competition to its parent competition to understand event hierarchies.",
        "sql_mysql": "SELECT parent.competition_id AS parent_competition, child.competition_name AS sub_competition FROM competitions child LEFT JOIN competitions parent ON child.parent_id = parent.competition_id WHERE child.parent_id IS NOT NULL;",
        "sql_sqlite": "SELECT parent.competition_id AS parent_competition, child.competition_name AS sub_competition FROM competitions child LEFT JOIN competitions parent ON child.parent_id = parent.competition_id WHERE child.parent_id IS NOT NULL;",
    },
    {
        "id": 6,
        "title": "Competition types by category",
        "category": "Composition Analysis",
        "desc": "Breaks down format mix within each category to understand tournament type distribution.",
        "sql_mysql": "SELECT cat.category_name, c.type, COUNT(c.competition_id) AS type_count FROM competitions c JOIN categories cat ON c.category_id = cat.category_id GROUP BY cat.category_name, c.type ORDER BY cat.category_name, type_count DESC;",
        "sql_sqlite": "SELECT cat.category_name, c.type, COUNT(c.competition_id) AS type_count FROM competitions c JOIN categories cat ON c.category_id = cat.category_id GROUP BY cat.category_name, c.type ORDER BY cat.category_name, type_count DESC;",
    },
    {
        "id": 7,
        "title": "Top-level competitions",
        "category": "Hierarchy Filters",
        "desc": "Lists only top-level competitions with no parent relationship, representing primary event nodes.",
        "sql_mysql": "SELECT c.competition_id, c.competition_name, cat.category_name FROM competitions c JOIN categories cat ON c.category_id = cat.category_id WHERE c.parent_id IS NULL;",
        "sql_sqlite": "SELECT c.competition_id, c.competition_name, cat.category_name FROM competitions c JOIN categories cat ON c.category_id = cat.category_id WHERE c.parent_id IS NULL;",
    },
    {
        "id": 8,
        "title": "Venues with associated complexes",
        "category": "Facility Inventory",
        "desc": "Shows each venue paired with its owning complex for facility analysis.",
        "sql_mysql": "SELECT v.venue_id, v.venue_name, c.complex_name FROM Venues v JOIN Complexes c ON v.complex_id = c.complex_id;",
        "sql_sqlite": "SELECT v.venue_id, v.venue_name, c.complex_name FROM Venues v JOIN Complexes c ON v.complex_id = c.complex_id;",
    },
    {
        "id": 9,
        "title": "Venue count per complex",
        "category": "Infrastructure",
        "desc": "Counts the number of courts or venues per complex to identify infrastructure scale.",
        "sql_mysql": "SELECT c.complex_name, COUNT(v.venue_id) AS venue_count FROM Complexes c LEFT JOIN Venues v ON c.complex_id = v.complex_id GROUP BY c.complex_name;",
        "sql_sqlite": "SELECT c.complex_name, COUNT(v.venue_id) AS venue_count FROM Complexes c LEFT JOIN Venues v ON c.complex_id = v.complex_id GROUP BY c.complex_name;",
    },
    {
        "id": 10,
        "title": "Venues in Chile",
        "category": "Regional Intelligence",
        "desc": "Retrieves all Chilean venues by country to support regional venue investigations.",
        "sql_mysql": "SELECT venue_id, venue_name, city_name, country_name, timezone FROM Venues WHERE country_name = 'Chile';",
        "sql_sqlite": "SELECT venue_id, venue_name, city_name, country_name, timezone FROM Venues WHERE country_name = 'Chile';",
    },
    {
        "id": 11,
        "title": "Venue-to-timezone mapping",
        "category": "Operations",
        "desc": "Lists all venues and their timezone offsets to support scheduling and logistics analysis.",
        "sql_mysql": "SELECT venue_id, venue_name, timezone FROM Venues;",
        "sql_sqlite": "SELECT venue_id, venue_name, timezone FROM Venues;",
    },
    {
        "id": 12,
        "title": "Complexes with multiple venues",
        "category": "Facility Quality",
        "desc": "Finds stadium complexes with more than one venue to highlight multi-court infrastructure.",
        "sql_mysql": "SELECT c.complex_name, COUNT(v.venue_id) AS venue_count FROM Complexes c JOIN Venues v ON c.complex_id = v.complex_id GROUP BY c.complex_name HAVING COUNT(v.venue_id) > 1;",
        "sql_sqlite": "SELECT c.complex_name, COUNT(v.venue_id) AS venue_count FROM Complexes c JOIN Venues v ON c.complex_id = v.complex_id GROUP BY c.complex_name HAVING COUNT(v.venue_id) > 1;",
    },
    {
        "id": 13,
        "title": "List venues grouped by country",
        "category": "Country Coverage",
        "desc": "Aggregates venues by country to show geographic coverage and venue concentration.",
        "sql_mysql": "SELECT country_name, STRING_AGG(venue_name, ', ') AS venues FROM Venues GROUP BY country_name;",
        "sql_sqlite": "SELECT country_name, GROUP_CONCAT(venue_name, ', ') AS venues FROM Venues GROUP BY country_name;",
    },
    {
        "id": 14,
        "title": "Venues for a specific complex",
        "category": "Venue Lookup",
        "desc": "Finds all venues under a named complex, such as Nacional, for focused stadium diagnostics.",
        "sql_mysql": "SELECT v.venue_id, v.venue_name, c.complex_name FROM Venues v JOIN Complexes c ON v.complex_id = c.complex_id WHERE c.complex_name = 'Nacional';",
        "sql_sqlite": "SELECT v.venue_id, v.venue_name, c.complex_name FROM Venues v JOIN Complexes c ON v.complex_id = c.complex_id WHERE c.complex_name = 'Nacional';",
    },
    {
        "id": 15,
        "title": "Competitor rankings and points",
        "category": "Player Metrics",
        "desc": "Combines competitor and ranking information to build a ranked player reference table.",
        "sql_mysql": "SELECT c.name AS competitor_name, c.country, cr.rank, cr.points FROM Competitors c JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id;",
        "sql_sqlite": "SELECT c.name AS competitor_name, c.country, cr.rank, cr.points FROM Competitors c JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id;",
    },
    {
        "id": 16,
        "title": "Top 5 ranked competitors",
        "category": "Leaderboards",
        "desc": "Shows the current top five competitors by rank for headline leaderboard analysis.",
        "sql_mysql": "SELECT c.name AS competitor_name, c.country, cr.rank, cr.points FROM Competitors c JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id WHERE cr.rank <= 5 ORDER BY cr.rank ASC;",
        "sql_sqlite": "SELECT c.name AS competitor_name, c.country, cr.rank, cr.points FROM Competitors c JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id WHERE cr.rank <= 5 ORDER BY cr.rank ASC;",
    },
    {
        "id": 17,
        "title": "Competitors with no rank movement",
        "category": "Stability",
        "desc": "Identifies players whose rank movement is zero, indicating stable ranking performance.",
        "sql_mysql": "SELECT c.name AS competitor_name, c.country, cr.rank, cr.points FROM Competitors c JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id WHERE cr.movement = 0;",
        "sql_sqlite": "SELECT c.name AS competitor_name, c.country, cr.rank, cr.points FROM Competitors c JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id WHERE cr.movement = 0;",
    },
    {
        "id": 18,
        "title": "Total points by country",
        "category": "Country Analytics",
        "desc": "Aggregates total points by country to summarize national player strength.",
        "sql_mysql": "SELECT c.country, SUM(cr.points) AS total_points FROM Competitors c JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id WHERE c.country = 'Croatia' GROUP BY c.country;",
        "sql_sqlite": "SELECT c.country, SUM(cr.points) AS total_points FROM Competitors c JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id WHERE c.country = 'Croatia' GROUP BY c.country;",
    },
    {
        "id": 19,
        "title": "Competitor counts by country",
        "category": "Country Distribution",
        "desc": "Counts how many competitors originate from each country to detect concentration patterns.",
        "sql_mysql": "SELECT c.country, COUNT(c.competitor_id) AS competitor_count FROM Competitors c GROUP BY c.country;",
        "sql_sqlite": "SELECT c.country, COUNT(c.competitor_id) AS competitor_count FROM Competitors c GROUP BY c.country;",
    },
    {
        "id": 20,
        "title": "Highest-scoring competitors",
        "category": "Performance Peaks",
        "desc": "Returns the current highest-scoring competitors to identify the peak performers in the system.",
        "sql_mysql": "SELECT c.name AS competitor_name, c.country, cr.rank, cr.points FROM Competitors c JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id WHERE cr.points = (SELECT MAX(points) FROM Competitor_Rankings);",
        "sql_sqlite": "SELECT c.name AS competitor_name, c.country, cr.rank, cr.points FROM Competitors c JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id WHERE cr.points = (SELECT MAX(points) FROM Competitor_Rankings);",
    },
]
