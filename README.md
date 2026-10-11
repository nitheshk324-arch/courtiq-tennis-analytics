# CourtIQ — SportRadar Tennis Analytics

CourtIQ is a Streamlit dashboard for exploring tennis competitions, player rankings, venues, and complexes using a local SQLite database.

## Included

- `app.py` — Streamlit dashboard
- `db_manager.py` — SQLite initialization and query helpers
- `Game Analytics.sql` — example analytical queries

This public repository intentionally excludes Sportradar CSV exports, generated SQLite databases, and the project PDF. Obtain the data through an account and license that permits your use of the Sportradar API; do not upload or redistribute it without permission.

## Run locally

1. Install Python 3.10 or newer.
2. Clone this repository and install its dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Place these licensed CSV exports in the project root:

   - `categories.csv`
   - `competitions.csv`
   - `competitors.csv`
   - `competitor_rankings.csv`
   - `complexes.csv`
   - `venues.csv`

   The dashboard builds `tennis_analytics.sqlite` from these files on first run.
4. Start the dashboard:

   ```bash
   streamlit run app.py
   ```

## Deploy a public dashboard

1. Create a **private** Supabase Storage bucket and upload the six licensed CSVs listed above. Keep the bucket private; the app reads it from the server.
2. Deploy this repository as a Streamlit Community Cloud app, selecting `app.py` as the entry point.
3. In the app's Streamlit Cloud settings, add the values from [`secrets.example.toml`](./secrets.example.toml) as app secrets. Set `url`, `bucket`, and `service_role_key` to your Supabase project values.
4. Keep the Supabase service-role key in Streamlit's server-side secrets only. It bypasses Supabase row-level security; never commit it, put it in the app source, or expose it to visitors. Restrict access to the bucket and rotate the key if it is exposed.

For local development, either provide the six CSVs beside `db_manager.py` or create `.streamlit/secrets.toml` using the example configuration. Local CSV files take precedence over Supabase. The database is built on first run and reused on subsequent runs.

The app server—not each visitor—fetches the private data. Confirm your Sportradar license permits the intended public display before sharing the deployed dashboard URL.
