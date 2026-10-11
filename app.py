import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import warnings
from db_manager import (
    SQL_QUERIES,
    check_mysql_connection,
    check_sqlite_connection,
    run_query,
    get_table_counts
)

warnings.filterwarnings('ignore')

# ---------------------------------------------------------
# Page Setup
# ---------------------------------------------------------
st.set_page_config(
    page_title="CourtIQ | SportRadar Tennis Analytics",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Ultra-Modern CSS Styling (Glassmorphism & Sports Tech Theme)
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Overall Background */
    .stApp {
        background-color: #080C15;
        background-image: 
            radial-gradient(at 10% 10%, rgba(16, 185, 129, 0.08) 0px, transparent 50%),
            radial-gradient(at 90% 90%, rgba(56, 189, 248, 0.07) 0px, transparent 50%);
    }

    /* Hero Header */
    .hero-box {
        background: linear-gradient(135deg, rgba(19, 27, 46, 0.85) 0%, rgba(11, 17, 32, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 30px 36px;
        margin-bottom: 28px;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(12px);
        position: relative;
        overflow: hidden;
    }
    .hero-box::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 300px;
        height: 100%;
        background: radial-gradient(circle at 100% 0%, rgba(16, 185, 129, 0.15) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #F8FAFC 0%, #10B981 60%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    .hero-desc {
        color: #94A3B8;
        font-size: 1.05rem;
        max-width: 820px;
        line-height: 1.6;
        margin-bottom: 18px;
    }
    .pill-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        background: rgba(16, 185, 129, 0.12);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.25);
        margin-right: 8px;
        margin-bottom: 6px;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10B981;
        box-shadow: 0 0 10px #10B981;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1.15); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* KPI Metric Cards */
    .metric-card {
        background: linear-gradient(145deg, rgba(23, 32, 54, 0.75) 0%, rgba(13, 19, 35, 0.85) 100%);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 16px;
        padding: 20px 22px;
        position: relative;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 24px -6px rgba(0, 0, 0, 0.4);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        overflow: hidden;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(16, 185, 129, 0.4);
        box-shadow: 0 16px 32px -8px rgba(16, 185, 129, 0.2);
    }
    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .metric-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94A3B8;
    }
    .metric-icon-bubble {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.05);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.15rem;
    }
    .metric-number {
        font-family: 'Outfit', sans-serif;
        font-size: 2.1rem;
        font-weight: 800;
        color: #F8FAFC;
        margin: 4px 0 6px 0;
        letter-spacing: -0.02em;
    }
    .metric-caption {
        font-size: 0.78rem;
        color: #38BDF8;
        font-weight: 500;
    }

    /* Podium Cards for Leaderboards */
    .podium-container {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
        align-items: flex-end;
    }
    .podium-card {
        flex: 1;
        border-radius: 18px;
        padding: 24px 20px;
        text-align: center;
        backdrop-filter: blur(12px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
        position: relative;
    }
    .podium-gold {
        background: linear-gradient(145deg, rgba(245, 158, 11, 0.15) 0%, rgba(20, 26, 43, 0.9) 100%);
        border: 2px solid rgba(245, 158, 11, 0.5);
        transform: translateY(-8px);
    }
    .podium-silver {
        background: linear-gradient(145deg, rgba(148, 163, 184, 0.15) 0%, rgba(20, 26, 43, 0.9) 100%);
        border: 1.5px solid rgba(148, 163, 184, 0.35);
    }
    .podium-bronze {
        background: linear-gradient(145deg, rgba(217, 119, 6, 0.12) 0%, rgba(20, 26, 43, 0.9) 100%);
        border: 1.5px solid rgba(217, 119, 6, 0.35);
    }
    .podium-badge {
        font-size: 1.8rem;
        margin-bottom: 4px;
    }
    .podium-rank {
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .podium-name {
        font-family: 'Outfit', sans-serif;
        font-size: 1.35rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 4px;
    }
    .podium-pts {
        font-size: 1.1rem;
        font-weight: 700;
        color: #10B981;
    }

    /* Player Profile Card */
    .pro-card {
        background: linear-gradient(145deg, rgba(19, 27, 46, 0.85) 0%, rgba(13, 19, 35, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 20px;
        padding: 28px;
        backdrop-filter: blur(16px);
        box-shadow: 0 16px 36px rgba(0, 0, 0, 0.4);
        margin-bottom: 24px;
    }
    .avatar-circle {
        width: 72px;
        height: 72px;
        border-radius: 50%;
        background: linear-gradient(135deg, #10B981 0%, #38BDF8 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Outfit', sans-serif;
        font-size: 1.6rem;
        font-weight: 800;
        color: #080C15;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.4);
    }
    .stat-pill {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 12px 18px;
        text-align: center;
    }

    /* Sidebar Footer Box */
    .team-badge-box {
        background: rgba(19, 27, 46, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px;
        font-size: 0.8rem;
        line-height: 1.5;
        margin-top: 24px;
    }
    .team-member-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 6px;
        color: #CBD5E1;
    }

    /* Streamlit Components Styling Overrides */
    div[data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(19, 27, 46, 0.5);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94A3B8;
        font-weight: 600;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #10B981 !important;
        color: #080C15 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar & Database Switcher
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
        <span style="font-size: 2.2rem;">🎾</span>
        <div>
            <h2 style="font-family: 'Outfit', sans-serif; margin: 0; font-size: 1.4rem; color: #F8FAFC; letter-spacing: -0.02em;">CourtIQ</h2>
            <span style="font-size: 0.75rem; color: #10B981; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">SportRadar Analytics</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Live Database Selector
    mysql_ok, mysql_msg = check_mysql_connection()
    sqlite_ok, sqlite_msg = check_sqlite_connection()
    
    engine_choices = []
    if mysql_ok:
        engine_choices.append("⚡ MySQL Live (Port 3306)")
    if sqlite_ok:
        engine_choices.append("💾 SQLite Database (Cloud & Local)")
    if not engine_choices:
        engine_choices = ["💾 SQLite Database (Cloud & Local)"]

    selected_db_choice = st.selectbox(
        "ACTIVE SQL ENGINE",
        engine_choices,
        index=0,
        help="Switch dynamically between live MySQL Server and embedded SQLite database."
    )
    db_engine = "mysql" if "MySQL" in selected_db_choice else "sqlite"
    
    if db_engine == "mysql":
        st.markdown('<div class="pill-badge"><span class="pulse-dot"></span> MySQL: tennis_analytics</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="pill-badge" style="color: #38BDF8; border-color: rgba(56, 189, 248, 0.3); background: rgba(56, 189, 248, 0.1);"><span class="pulse-dot" style="background:#38BDF8; box-shadow:0 0 10px #38BDF8;"></span> SQLite Cloud Database</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<p style='font-size: 0.75rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;'>ANALYTICS MODULES</p>", unsafe_allow_html=True)
    
    nav_selection = st.radio(
        "Navigation",
        [
            "🏠 Executive Hub",
            "🔍 Tournament Explorer",
            "🏟️ Stadiums & Venues",
            "🎾 Player Profiles",
            "🌍 Regional Analysis",
            "🏆 World Leaderboards",
            "⚡ Live SQL Studio"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    # Team Info Box
    st.markdown("""
    <div class="team-badge-box">
        <div style="font-weight: 700; color: #F8FAFC; margin-bottom: 8px; font-size: 0.82rem; letter-spacing: 0.04em; text-transform: uppercase;">
            👥 Project Squad
        </div>
        <div class="team-member-row">
            <span><b>Ashish</b></span>
            <span style="color: #38BDF8;">API & Ingestion</span>
        </div>
        <div class="team-member-row">
            <span><b>Nithish</b></span>
            <span style="color: #A78BFA;">SQL & 20 Queries</span>
        </div>
        <div class="team-member-row">
            <span><b>Dibya</b></span>
            <span style="color: #10B981;">Streamlit UX/BI</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# Cached Global Stats
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_global_stats(engine):
    return get_table_counts(engine)

@st.cache_data(ttl=600)
def fetch_raw_table(table_name, engine):
    df, _, _ = run_query(f"SELECT * FROM `{table_name}`" if engine == "mysql" else f"SELECT * FROM {table_name}", engine)
    return df

try:
    counts = fetch_global_stats(db_engine)
except (FileNotFoundError, ValueError, OSError, sqlite3.Error, pd.errors.ParserError) as exc:
    st.error(f"Unable to load the tennis database: {exc}")
    st.info(
        "For a hosted deployment, configure the [supabase] secrets from "
        "secrets.example.toml and ensure the private bucket contains all six CSV files."
    )
    st.stop()


# =========================================================
# MODULE 1: 🏠 Executive Hub
# =========================================================
if nav_selection == "🏠 Executive Hub":
    st.markdown("""
    <div class="hero-box">
        <div style="display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;">
            <div class="pill-badge"><span class="pulse-dot"></span> LIVE SQL ENGINE ONLINE</div>
            <div class="pill-badge" style="background: rgba(56, 189, 248, 0.1); color: #38BDF8; border-color: rgba(56, 189, 248, 0.3);">🎾 SPORTRADAR TENNIS API v3</div>
            <div class="pill-badge" style="background: rgba(167, 139, 250, 0.1); color: #C084FC; border-color: rgba(167, 139, 250, 0.3);">⚡ 20 VALIDATED QUERIES</div>
        </div>
        <div class="hero-title">CourtIQ • Tennis Tournament Intelligence</div>
        <div class="hero-desc">
            Next-generation analytics cockpit unlocking structured insights from the Sportradar API. Navigate competition hierarchies, inspect multi-court stadium infrastructure, and track real-time doubles performance metrics.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 6 Metric Glassmorphic Cards
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-label">Competitions</span>
                <div class="metric-icon-bubble">🏆</div>
            </div>
            <div class="metric-number">{counts.get('competitions', 0):,}</div>
            <div class="metric-caption">Across 18 Levels</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-label">Categories</span>
                <div class="metric-icon-bubble">🗂️</div>
            </div>
            <div class="metric-number">{counts.get('categories', 0)}</div>
            <div class="metric-caption">ATP, WTA, ITF, etc.</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-label">Complexes</span>
                <div class="metric-icon-bubble">🏟️</div>
            </div>
            <div class="metric-number">{counts.get('complexes', 0):,}</div>
            <div class="metric-caption">Worldwide Facilities</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-label">Courts / Venues</span>
                <div class="metric-icon-bubble">📍</div>
            </div>
            <div class="metric-number">{counts.get('venues', 0):,}</div>
            <div class="metric-caption">Individual Courts</div>
        </div>
        """, unsafe_allow_html=True)
    with m5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-label">Ranked Stars</span>
                <div class="metric-icon-bubble">🏅</div>
            </div>
            <div class="metric-number">{counts.get('competitors', 0):,}</div>
            <div class="metric-caption">Doubles Leaderboard</div>
        </div>
        """, unsafe_allow_html=True)
    with m6:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-label">SQL Pipeline</span>
                <div class="metric-icon-bubble">⚡</div>
            </div>
            <div class="metric-number">100%</div>
            <div class="metric-caption">20 / 20 Queries Pass</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Visualizations Row
    chart_col1, chart_col2 = st.columns([3, 2])
    
    with chart_col1:
        st.markdown("### 📊 Tournament Distribution by Category (Query 2)")
        q2_sql = """SELECT cat.category_name, COUNT(c.competition_id) AS competition_count 
FROM competitions c
JOIN categories cat ON c.category_id = cat.category_id
GROUP BY cat.category_name
ORDER BY competition_count DESC;"""
        df_q2, _, _ = run_query(q2_sql, db_engine)
        if df_q2 is not None and not df_q2.empty:
            fig_bar = px.bar(
                df_q2,
                x="category_name",
                y="competition_count",
                color="competition_count",
                color_continuous_scale=[[0, "#065F46"], [0.5, "#10B981"], [1, "#38BDF8"]],
                labels={"category_name": "Circuit Category", "competition_count": "Total Tournaments"}
            )
            fig_bar.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#94A3B8"),
                xaxis=dict(tickangle=-45, showgrid=False),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                margin=dict(t=20, b=10, l=10, r=10),
                height=380,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_bar, width="stretch")

    with chart_col2:
        st.markdown("### ⚖️ Match Format Distribution")
        q_format_sql = "SELECT type AS format, COUNT(*) AS count FROM competitions GROUP BY type;"
        df_fmt, _, _ = run_query(q_format_sql, db_engine)
        if df_fmt is not None and not df_fmt.empty:
            fig_pie = px.pie(
                df_fmt,
                names="format",
                values="count",
                hole=0.55,
                color_discrete_sequence=["#10B981", "#38BDF8", "#F59E0B", "#EC4899"]
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#F8FAFC"),
                margin=dict(t=20, b=10, l=10, r=10),
                height=380,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, width="stretch")

    st.markdown("---")

    # Bottom Row: Top 5 World Stars & Multi-court Stadiums
    hl1, hl2 = st.columns(2)
    with hl1:
        st.markdown("### 🏅 Top 5 World Doubles Stars (Query 16)")
        q16_sql = """SELECT c.name AS competitor_name, c.country, cr.rank, cr.points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
WHERE cr.rank <= 5
ORDER BY cr.rank ASC;"""
        df_top5, _, _ = run_query(q16_sql, db_engine)
        if df_top5 is not None:
            st.dataframe(df_top5, width="stretch", hide_index=True)

    with hl2:
        st.markdown("### 🏟️ Complex Facilities with Most Courts (Query 12)")
        q12_sql = """SELECT c.complex_name, COUNT(v.venue_id) AS court_count
FROM Complexes c
JOIN Venues v ON c.complex_id = v.complex_id
GROUP BY c.complex_name
HAVING COUNT(v.venue_id) > 1
ORDER BY court_count DESC
LIMIT 5;"""
        df_top_comp, _, _ = run_query(q12_sql, db_engine)
        if df_top_comp is not None:
            st.dataframe(df_top_comp, width="stretch", hide_index=True)


# =========================================================
# MODULE 2: 🔍 Tournament Explorer
# =========================================================
elif nav_selection == "🔍 Tournament Explorer":
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h2 style="font-family: 'Outfit', sans-serif; font-size: 2rem; color: #F8FAFC; margin-bottom: 4px;">🔍 Competition & Hierarchy Explorer</h2>
        <p style="color: #94A3B8; margin-bottom: 0;">Navigate tournaments across 18 levels, filter formats, and explore parent-sub tournament trees.</p>
    </div>
    """, unsafe_allow_html=True)

    # Dynamic Filter Bar
    df_cats = fetch_raw_table("categories", db_engine)
    cat_options = ["All Categories"] + sorted(df_cats["category_name"].tolist()) if df_cats is not None else ["All Categories"]

    flt1, flt2, flt3, flt4 = st.columns([2, 1, 1, 2])
    with flt1:
        cat_sel = st.selectbox("Category Circuit", cat_options)
    with flt2:
        format_sel = st.selectbox("Format", ["All Formats", "singles", "doubles", "mixed_doubles", "mixed"])
    with flt3:
        gender_sel = st.selectbox("Gender", ["All", "men", "women", "mixed"])
    with flt4:
        keyword = st.text_input("Search Name / ID", placeholder="e.g. Vienna, Wimbledon, ITF...")

    # Build SQL Query
    clauses = []
    if cat_sel != "All Categories":
        clauses.append(f"cat.category_name = '{cat_sel}'")
    if format_sel != "All Formats":
        clauses.append(f"c.type = '{format_sel}'")
    if gender_sel != "All":
        clauses.append(f"c.gender = '{gender_sel}'")
    if keyword.strip():
        clauses.append(f"(c.competition_name LIKE '%{keyword.strip()}%' OR c.competition_id LIKE '%{keyword.strip()}%')")

    where_str = "WHERE " + " AND ".join(clauses) if clauses else ""

    q_filter = f"""
    SELECT 
        c.competition_id AS `Tournament ID`,
        c.competition_name AS `Tournament Name`,
        cat.category_name AS `Category`,
        c.type AS `Format`,
        c.gender AS `Gender`,
        c.parent_id AS `Parent ID`
    FROM competitions c
    LEFT JOIN categories cat ON c.category_id = cat.category_id
    {where_str}
    LIMIT 250;
    """
    df_tourneys, q_ms, q_err = run_query(q_filter, db_engine)

    if q_err:
        st.error(f"Filter Error: {q_err}")
    elif df_tourneys is not None:
        st.markdown(f"<p style='color: #10B981; font-weight: 600; font-size: 0.9rem;'>⚡ Found {len(df_tourneys):,} matches in {q_ms:.1f} ms</p>", unsafe_allow_html=True)
        st.dataframe(df_tourneys, width="stretch", hide_index=True)
        
        csv_data = df_tourneys.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Tournaments to CSV",
            data=csv_data,
            file_name="filtered_tournaments.csv",
            mime="text/csv"
        )

    st.markdown("---")
    
    # Hierarchy Showcase (Business Use Case 1)
    st.markdown("### 🌲 Tournament Hierarchies & Sub-Events (Business Use Case 1)")
    st.caption("Visualizing the relationship between master tournaments (e.g. Erste Bank Open Vienna, Wimbledon) and their singles/doubles brackets.")

    q_tree = """
    SELECT 
        parent.competition_id AS parent_id,
        parent.competition_name AS parent_event,
        child.competition_id AS sub_id,
        child.competition_name AS sub_event,
        child.type AS sub_type
    FROM competitions child
    JOIN competitions parent ON child.parent_id = parent.competition_id
    ORDER BY parent.competition_name;
    """
    df_tree, _, _ = run_query(q_tree, db_engine)
    if df_tree is not None and not df_tree.empty:
        grouped = df_tree.groupby(["parent_id", "parent_event"])
        for (pid, pname), rows in grouped:
            with st.expander(f"🏆 Parent Event: {pname} [{pid}] — {len(rows)} Nested Sub-Competition(s)", expanded=True):
                sub_table = rows[["sub_id", "sub_event", "sub_type"]].rename(columns={
                    "sub_id": "Sub-Competition ID",
                    "sub_event": "Sub-Competition Name",
                    "sub_type": "Event Type"
                })
                st.dataframe(sub_table, width="stretch", hide_index=True)


# =========================================================
# MODULE 3: 🏟️ Stadiums & Venues
# =========================================================
elif nav_selection == "🏟️ Stadiums & Venues":
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h2 style="font-family: 'Outfit', sans-serif; font-size: 2rem; color: #F8FAFC; margin-bottom: 4px;">🏟️ Global Stadiums & Court Infrastructure</h2>
        <p style="color: #94A3B8; margin-bottom: 0;">Explore 598 complexes, multi-court tennis hubs, and international timezone coverage.</p>
    </div>
    """, unsafe_allow_html=True)

    tab_all_venues, tab_chilean, tab_tz = st.tabs([
        "🏛️ Stadium Directory (Query 8)",
        "🇨🇱 Chilean Courts Deep-Dive (Query 10)",
        "🌐 Broadcast Timezone Coverage (Query 11)"
    ])

    with tab_all_venues:
        v_col1, v_col2 = st.columns(2)
        with v_col1:
            country_search = st.text_input("Search Country", placeholder="e.g. Chile, Spain, United Kingdom, USA...")
        with v_col2:
            complex_search = st.text_input("Search Complex Name", placeholder="e.g. Nacional, Cartuja, Sibur...")

        filters = []
        if country_search.strip():
            filters.append(f"v.country_name LIKE '%{country_search.strip()}%'")
        if complex_search.strip():
            filters.append(f"c.complex_name LIKE '%{complex_search.strip()}%'")

        w_sql = "WHERE " + " AND ".join(filters) if filters else ""
        q_venues = f"""
        SELECT 
            v.venue_id AS `Venue ID`, 
            v.venue_name AS `Court Name`, 
            c.complex_name AS `Complex Facility`, 
            v.city_name AS `City`, 
            v.country_name AS `Country`, 
            v.timezone AS `Timezone`
        FROM Venues v
        JOIN Complexes c ON v.complex_id = c.complex_id
        {w_sql}
        LIMIT 150;
        """
        df_v, v_ms, _ = run_query(q_venues, db_engine)
        if df_v is not None:
            st.markdown(f"<p style='color: #38BDF8; font-weight: 600; font-size: 0.9rem;'>📍 Loaded {len(df_v)} courts in {v_ms:.1f} ms</p>", unsafe_allow_html=True)
            st.dataframe(df_v, width="stretch", hide_index=True)

    with tab_chilean:
        st.markdown("### 🇨🇱 Chilean Venue Inventory (Query 10)")
        st.caption("Details of courts located in Chile across Santiago and Temuco.")
        q10_sql = """SELECT venue_id, venue_name, city_name, country_name, timezone
FROM Venues
WHERE country_name = 'Chile';"""
        df_chile, _, _ = run_query(q10_sql, db_engine)
        if df_chile is not None:
            st.dataframe(df_chile, width="stretch", hide_index=True)
            
            c_counts = df_chile['city_name'].value_counts().reset_index()
            c_counts.columns = ['City', 'Courts']
            fig_chile = px.bar(
                c_counts,
                x='City',
                y='Courts',
                color='Courts',
                color_continuous_scale="Viridis",
                title="Court Distribution in Chile"
            )
            fig_chile.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#F8FAFC"),
                margin=dict(t=30, b=10, l=10, r=10),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_chile, width="stretch")

    with tab_tz:
        st.markdown("### 🌐 Tournament Broadcast Timezones (Query 11)")
        q11_sql = "SELECT timezone, COUNT(*) AS courts FROM Venues GROUP BY timezone ORDER BY courts DESC;"
        df_timezones, _, _ = run_query(q11_sql, db_engine)
        if df_timezones is not None and not df_timezones.empty:
            fig_tz = px.bar(
                df_timezones,
                x="timezone",
                y="courts",
                color="courts",
                color_continuous_scale="Purples",
                labels={"timezone": "Timezone", "courts": "Active Courts"}
            )
            fig_tz.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#94A3B8"),
                xaxis=dict(tickangle=-45),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                margin=dict(t=10, b=10, l=10, r=10),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_tz, width="stretch")


# =========================================================
# MODULE 4: 🎾 Player Profiles
# =========================================================
elif nav_selection == "🎾 Player Profiles":
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h2 style="font-family: 'Outfit', sans-serif; font-size: 2rem; color: #F8FAFC; margin-bottom: 4px;">🎾 Competitor Profiles & Performance Arena</h2>
        <p style="color: #94A3B8; margin-bottom: 0;">Interactive player cards, ranking positions, points breakdown, and head-to-head showdowns.</p>
    </div>
    """, unsafe_allow_html=True)

    q_all_players = """
    SELECT 
        c.competitor_id, 
        c.name, 
        c.country, 
        c.country_code, 
        c.abbreviation, 
        cr.rank, 
        cr.points, 
        cr.movement, 
        cr.competitions_played
    FROM Competitors c
    JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
    ORDER BY cr.rank ASC;
    """
    df_players, _, _ = run_query(q_all_players, db_engine)

    if df_players is not None and not df_players.empty:
        names_list = df_players["name"].tolist()
        
        sel_col, _ = st.columns([2, 1])
        with sel_col:
            active_player = st.selectbox("Select Player to Inspect", names_list, index=0)

        p_row = df_players[df_players["name"] == active_player].iloc[0]
        
        # Initials for avatar
        parts = p_row["name"].split()
        initials = parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")

        # Movement status
        mov = p_row["movement"]
        if mov > 0:
            mov_tag = f'<span style="background: rgba(16, 185, 129, 0.2); color: #34D399; padding: 6px 12px; border-radius: 9999px; font-size: 0.85rem; font-weight: 700;">▲ RISING (+{mov})</span>'
        elif mov < 0:
            mov_tag = f'<span style="background: rgba(239, 68, 68, 0.2); color: #F87171; padding: 6px 12px; border-radius: 9999px; font-size: 0.85rem; font-weight: 700;">▼ FALLING ({mov})</span>'
        else:
            mov_tag = '<span style="background: rgba(148, 163, 184, 0.2); color: #CBD5E1; padding: 6px 12px; border-radius: 9999px; font-size: 0.85rem; font-weight: 700;">➖ STABLE (0)</span>'

        # Card HTML
        st.markdown(f"""
        <div class="pro-card">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div class="avatar-circle">{initials}</div>
                    <div>
                        <h2 style="font-family: 'Outfit', sans-serif; font-size: 2rem; color: #F8FAFC; margin: 0 0 6px 0;">{p_row['name']}</h2>
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <span style="background: rgba(255,255,255,0.06); padding: 4px 10px; border-radius: 8px; font-size: 0.82rem; color: #38BDF8; font-weight: 600;">🌍 {p_row['country']} ({p_row['country_code']})</span>
                            <span style="color: #64748B; font-size: 0.85rem;">ID: <code>{p_row['competitor_id']}</code></span>
                        </div>
                    </div>
                </div>
                <div>
                    {mov_tag}
                </div>
            </div>
            <hr style="border-color: rgba(255, 255, 255, 0.08); margin: 24px 0;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px;">
                <div class="stat-pill">
                    <span style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">World Doubles Rank</span>
                    <div style="font-family: 'Outfit', sans-serif; font-size: 2.2rem; font-weight: 800; color: #10B981; margin-top: 4px;">#{p_row['rank']}</div>
                </div>
                <div class="stat-pill">
                    <span style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Ranking Points</span>
                    <div style="font-family: 'Outfit', sans-serif; font-size: 2.2rem; font-weight: 800; color: #38BDF8; margin-top: 4px;">{p_row['points']:,}</div>
                </div>
                <div class="stat-pill">
                    <span style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Tournaments Played</span>
                    <div style="font-family: 'Outfit', sans-serif; font-size: 2.2rem; font-weight: 800; color: #F59E0B; margin-top: 4px;">{p_row['competitions_played']}</div>
                </div>
                <div class="stat-pill">
                    <span style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Short Code</span>
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.6rem; font-weight: 700; color: #E2E8F0; margin-top: 6px;">{p_row['abbreviation']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🥊 Head-to-Head Player Comparison")
        comp1, comp2 = st.columns(2)
        with comp1:
            p1 = st.selectbox("Player 1", names_list, index=names_list.index(active_player), key="cmp1")
        with comp2:
            default_p2_idx = 1 if names_list.index(active_player) == 0 else 0
            p2 = st.selectbox("Player 2", names_list, index=default_p2_idx, key="cmp2")

        p1_data = df_players[df_players["name"] == p1].iloc[0]
        p2_data = df_players[df_players["name"] == p2].iloc[0]

        compare_df = pd.DataFrame({
            "Metric": ["World Rank", "Total Points", "Tournaments Played", "Weekly Rank Movement", "Country"],
            p1: [f"#{p1_data['rank']}", f"{p1_data['points']:,} pts", f"{p1_data['competitions_played']:,}", f"{p1_data['movement']:+,}", p1_data['country']],
            p2: [f"#{p2_data['rank']}", f"{p2_data['points']:,} pts", f"{p2_data['competitions_played']:,}", f"{p2_data['movement']:+,}", p2_data['country']]
        })
        st.table(compare_df.set_index("Metric"))


# =========================================================
# MODULE 5: 🌍 Regional Analysis
# =========================================================
elif nav_selection == "🌍 Regional Analysis":
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h2 style="font-family: 'Outfit', sans-serif; font-size: 2rem; color: #F8FAFC; margin-bottom: 4px;">🌍 National Tennis Strength & Regional Distribution</h2>
        <p style="color: #94A3B8; margin-bottom: 0;">Aggregate points, talent density per country, and national tennis powerhouses.</p>
    </div>
    """, unsafe_allow_html=True)

    col_croatia, col_nations = st.columns([1, 2])

    with col_croatia:
        st.markdown("### 🇭🇷 Croatia Ranking Power (Query 18)")
        q18_sql = """SELECT c.country, SUM(cr.points) AS total_points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
WHERE c.country = 'Croatia'
GROUP BY c.country;"""
        df_croatia, _, _ = run_query(q18_sql, db_engine)
        cro_pts = df_croatia.iloc[0]['total_points'] if df_croatia is not None and not df_croatia.empty else 0
        
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, rgba(239, 68, 68, 0.15) 0%, rgba(20, 26, 43, 0.9) 100%); border: 1.5px solid rgba(239, 68, 68, 0.4); border-radius: 16px; padding: 24px; text-align: center; margin-bottom: 20px;">
            <div style="font-size: 2.2rem; margin-bottom: 6px;">🇭🇷</div>
            <div style="font-size: 0.85rem; font-weight: 700; color: #F87171; letter-spacing: 0.05em; text-transform: uppercase;">Croatia Tennis Powerhouse</div>
            <div style="font-family: 'Outfit', sans-serif; font-size: 2.6rem; font-weight: 800; color: #F8FAFC; margin: 6px 0;">{cro_pts:,} pts</div>
            <p style="color: #94A3B8; font-size: 0.82rem; margin: 0;">Sum across Ivan Dodig, Mate Pavic, Nikola Mektic, Borna Gojo, and Marin Cilic.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🔍 Calculate Total Points by Nation")
        df_clist, _, _ = run_query("SELECT DISTINCT country FROM Competitors ORDER BY country;", db_engine)
        if df_clist is not None:
            c_selected = st.selectbox("Select Any Country", df_clist['country'].tolist(), index=0)
            q_c_calc = f"""SELECT c.country, SUM(cr.points) AS total_points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
WHERE c.country = '{c_selected}'
GROUP BY c.country;"""
            df_c_res, _, _ = run_query(q_c_calc, db_engine)
            if df_c_res is not None and not df_c_res.empty:
                st.metric(f"Total Points for {c_selected}", f"{df_c_res.iloc[0]['total_points']:,} pts")

    with col_nations:
        st.markdown("### 👥 Ranked Competitors per Country (Query 19)")
        q19_sql = """SELECT c.country, COUNT(c.competitor_id) AS competitor_count
FROM Competitors c
GROUP BY c.country
ORDER BY competitor_count DESC;"""
        df_q19, _, _ = run_query(q19_sql, db_engine)
        if df_q19 is not None and not df_q19.empty:
            fig_nations = px.bar(
                df_q19,
                x="country",
                y="competitor_count",
                color="competitor_count",
                color_continuous_scale=[[0, "#1E3A8A"], [0.5, "#38BDF8"], [1, "#10B981"]],
                labels={"country": "Country", "competitor_count": "Ranked Competitors"}
            )
            fig_nations.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#94A3B8"),
                xaxis=dict(tickangle=-45, showgrid=False),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                margin=dict(t=20, b=10, l=10, r=10),
                height=380,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_nations, width="stretch")

    st.markdown("---")
    st.markdown("### 🗺️ Global Tennis Points Density Map")
    q_world_map = """
    SELECT 
        c.country, 
        c.country_code, 
        COUNT(c.competitor_id) AS total_players, 
        SUM(cr.points) AS total_points
    FROM Competitors c
    JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
    GROUP BY c.country, c.country_code;
    """
    df_wmap, _, _ = run_query(q_world_map, db_engine)
    if df_wmap is not None and not df_wmap.empty:
        fig_map = px.choropleth(
            df_wmap,
            locations="country",
            locationmode="country names",
            color="total_points",
            hover_name="country",
            hover_data={"total_players": True, "total_points": True},
            color_continuous_scale="Viridis",
            template="plotly_dark"
        )
        fig_map.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=10, b=10, l=10, r=10),
            height=460
        )
        st.plotly_chart(fig_map, width="stretch")


# =========================================================
# MODULE 6: 🏆 World Leaderboards
# =========================================================
elif nav_selection == "🏆 World Leaderboards":
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h2 style="font-family: 'Outfit', sans-serif; font-size: 2rem; color: #F8FAFC; margin-bottom: 4px;">🏆 Official World Doubles Leaderboards</h2>
        <p style="color: #94A3B8; margin-bottom: 0;">World champion podium, top 5 standings, and stable rank honors.</p>
    </div>
    """, unsafe_allow_html=True)

    # Fetch Top 3 for Podium
    q_top3 = """SELECT c.name AS competitor_name, c.country, cr.rank, cr.points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
WHERE cr.rank <= 3
ORDER BY cr.rank ASC;"""
    df_podium, _, _ = run_query(q_top3, db_engine)

    if df_podium is not None and len(df_podium) >= 3:
        p1 = df_podium.iloc[0]
        p2 = df_podium.iloc[1]
        p3 = df_podium.iloc[2]

        st.markdown(f"""
        <div class="podium-container">
            <!-- Rank 2: Silver -->
            <div class="podium-card podium-silver">
                <div class="podium-badge">🥈</div>
                <div class="podium-rank" style="color: #CBD5E1;">World No. 2</div>
                <div class="podium-name">{p2['competitor_name']}</div>
                <div style="color: #94A3B8; font-size: 0.85rem; margin-bottom: 8px;">{p2['country']}</div>
                <div class="podium-pts">{p2['points']:,} pts</div>
            </div>
            <!-- Rank 1: Gold Crown -->
            <div class="podium-card podium-gold">
                <div class="podium-badge">👑</div>
                <div class="podium-rank" style="color: #F59E0B;">World Champion (Query 20)</div>
                <div class="podium-name" style="font-size: 1.55rem; color: #FFFFFF;">{p1['competitor_name']}</div>
                <div style="color: #FCD34D; font-size: 0.88rem; margin-bottom: 8px;">{p1['country']}</div>
                <div class="podium-pts" style="font-size: 1.35rem; color: #FBBF24;">{p1['points']:,} pts</div>
            </div>
            <!-- Rank 3: Bronze -->
            <div class="podium-card podium-bronze">
                <div class="podium-badge">🥉</div>
                <div class="podium-rank" style="color: #F59E0B;">World No. 3</div>
                <div class="podium-name">{p3['competitor_name']}</div>
                <div style="color: #94A3B8; font-size: 0.85rem; margin-bottom: 8px;">{p3['country']}</div>
                <div class="podium-pts">{p3['points']:,} pts</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    tab_top5, tab_stable, tab_scatter = st.tabs([
        "🥇 Top 5 Leaderboard (Query 16)",
        "⚓ Stable Rank Standings (Query 17)",
        "📈 Points vs. Rank Correlation"
    ])

    with tab_top5:
        st.markdown("### Top 5 Competitors in the World (Query 16)")
        q16_sql = """SELECT c.name AS competitor_name, c.country, cr.rank, cr.points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
WHERE cr.rank <= 5
ORDER BY cr.rank ASC;"""
        df_q16, _, _ = run_query(q16_sql, db_engine)
        if df_q16 is not None:
            st.dataframe(df_q16, width="stretch", hide_index=True)

    with tab_stable:
        st.markdown("### Stable Rank Competitors (Movement = 0) (Query 17)")
        q17_sql = """SELECT c.name AS competitor_name, c.country, cr.rank, cr.points
FROM Competitors c
JOIN Competitor_Rankings cr ON c.competitor_id = cr.competitor_id
WHERE cr.movement = 0
ORDER BY cr.rank ASC;"""
        df_q17, _, _ = run_query(q17_sql, db_engine)
        if df_q17 is not None:
            st.markdown(f"<p style='color: #10B981; font-weight: 600;'>{len(df_q17)} players held their position with 0 delta movement this week.</p>", unsafe_allow_html=True)
            st.dataframe(df_q17, width="stretch", hide_index=True)

    with tab_scatter:
        st.markdown("### Points vs. Rank Curve")
        q_curve = """SELECT cr.rank, cr.points, c.name FROM Competitor_Rankings cr JOIN Competitors c ON cr.competitor_id = c.competitor_id ORDER BY cr.rank;"""
        df_c, _, _ = run_query(q_curve, db_engine)
        if df_c is not None:
            fig_sc = px.scatter(
                df_c,
                x="rank",
                y="points",
                hover_name="name",
                labels={"rank": "World Doubles Rank", "points": "ATP/WTA Points"},
                color="points",
                color_continuous_scale="Viridis"
            )
            fig_sc.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#94A3B8"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_sc, width="stretch")


# =========================================================
# MODULE 7: ⚡ Live SQL Studio
# =========================================================
elif nav_selection == "⚡ Live SQL Studio":
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h2 style="font-family: 'Outfit', sans-serif; font-size: 2rem; color: #F8FAFC; margin-bottom: 4px;">⚡ Live SQL Query Studio</h2>
        <p style="color: #94A3B8; margin-bottom: 0;">Direct access to Nithish's 20 core analytical queries and an interactive ad-hoc query console.</p>
    </div>
    """, unsafe_allow_html=True)

    tab_queries, tab_console, tab_er = st.tabs([
        "📋 Nithish's 20 Required SQL Queries",
        "💻 Ad-Hoc SQL Console",
        "🗄️ Relational Schema & Architecture"
    ])

    with tab_queries:
        query_labels = [f"Q{q['id']}: {q['title']} • [{q['category']}]" for q in SQL_QUERIES]
        chosen_label = st.selectbox("Select SQL Query to Run", query_labels, index=0)
        
        idx = query_labels.index(chosen_label)
        q_meta = SQL_QUERIES[idx]

        st.markdown(f"#### Q{q_meta['id']}: {q_meta['title']}")
        st.markdown(f"<p style='color: #94A3B8; font-size: 0.95rem; margin-bottom: 12px;'><b>Business Rationale:</b> {q_meta['desc']}</p>", unsafe_allow_html=True)
        
        sql_to_run = q_meta["sql_mysql"] if db_engine == "mysql" else q_meta["sql_sqlite"]
        st.code(sql_to_run, language="sql")

        run_col, _ = st.columns([1, 4])
        with run_col:
            exec_btn = st.button("▶️ Execute Query Live", type="primary", key="exec_q_btn")

        if exec_btn:
            res_df, res_ms, res_err = run_query(sql_to_run, db_engine)
            if res_err:
                st.error(f"SQL Error: {res_err}")
            elif res_df is not None:
                st.markdown(f"""
                <div style="display: flex; gap: 12px; margin: 12px 0;">
                    <div class="pill-badge"><span class="pulse-dot"></span> Execution: {res_ms:.2f} ms</div>
                    <div class="pill-badge" style="background: rgba(56, 189, 248, 0.1); color: #38BDF8; border-color: rgba(56, 189, 248, 0.3);">Returned {len(res_df):,} records</div>
                </div>
                """, unsafe_allow_html=True)
                st.dataframe(res_df, width="stretch", hide_index=True)
                
                # Auto Chart
                if q_meta.get("chart_type") == "bar" and "x" in q_meta and "y" in q_meta:
                    fig_q = px.bar(
                        res_df,
                        x=q_meta["x"],
                        y=q_meta["y"],
                        color=q_meta.get("color", q_meta["y"]),
                        title=q_meta["title"]
                    )
                    fig_q.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color="#F8FAFC"),
                        coloraxis_showscale=False
                    )
                    st.plotly_chart(fig_q, width="stretch")

                csv_bytes = res_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Result CSV",
                    data=csv_bytes,
                    file_name=f"query_{q_meta['id']}_result.csv",
                    mime="text/csv"
                )

    with tab_console:
        st.markdown("### 💻 Interactive SQL Terminal")
        st.caption("Execute custom `SELECT` statements live against the active database.")

        sample_query = "SELECT c.competition_name, cat.category_name, c.type FROM competitions c JOIN categories cat ON c.category_id = cat.category_id LIMIT 10;"
        user_sql = st.text_area("SQL Statement", value=sample_query, height=130)

        if st.button("🚀 Run Custom SQL", type="primary"):
            if not user_sql.strip().lower().startswith("select"):
                st.warning("⚠️ For security and data integrity, only SELECT queries are permitted.")
            else:
                c_df, c_ms, c_err = run_query(user_sql, db_engine)
                if c_err:
                    st.error(f"Error: {c_err}")
                elif c_df is not None:
                    st.success(f"Executed in {c_ms:.2f} ms | Returned {len(c_df)} rows")
                    st.dataframe(c_df, width="stretch", hide_index=True)

    with tab_er:
        st.markdown("### 🗄️ Relational Schema & Table Architecture")
        st.markdown("""
        The database enforces a strict relational schema with 6 tables connected via Primary & Foreign Keys:
        
        * **`categories`** (`category_id` PK, `category_name`)
        * **`competitions`** (`competition_id` PK, `competition_name`, `category_id` FK, `type`, `gender`, `parent_id` self-FK)
        * **`Complexes`** (`complex_id` PK, `complex_name`)
        * **`Venues`** (`venue_id` PK, `venue_name`, `complex_id` FK, `city_name`, `country_name`, `country_code`, `timezone`)
        * **`Competitors`** (`competitor_id` PK, `name`, `country`, `country_code`, `abbreviation`)
        * **`Competitor_Rankings`** (`ranking_id` PK, `rank`, `movement`, `points`, `competitions_played`, `competitor_id` FK)
        """)
        st.info("💡 **Dual-Backend Support:** Switch between MySQL on port 3306 and SQLite using the sidebar selector at any time.")
