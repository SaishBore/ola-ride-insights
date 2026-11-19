"""
Ola Ride Insights - Streamlit app
---------------------------------
Pages
    1. Overview         KPIs and charts with sidebar filters
    2. SQL Insights     the 10 business questions, with search and download
    3. Power BI         the embedded dashboard (or screenshots as a fallback)
    4. Custom SQL       run your own read-only SELECT query

Data source
    * MySQL      if a [mysql] section exists in .streamlit/secrets.toml
    * CSV/SQLite otherwise (data/ola_cleaned.csv), which is what a deployed
      app uses because a local MySQL server is not reachable from the cloud.

Run:  streamlit run app.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import queries as q

# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------
# Paste the "Publish to web" / embed link of your Power BI report here
# (or put it in secrets.toml as powerbi_url = "..."). Leave empty to show
# screenshots from the dashboard_images folder instead.
POWERBI_EMBED_URL = ""

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "data" / "ola_cleaned.csv"
IMAGE_DIR = BASE_DIR / "dashboard_images"
MAX_ROWS_SHOWN = 1000

st.set_page_config(page_title="Ola Ride Insights", page_icon="🚖", layout="wide")


# --------------------------------------------------------------------------
# Database access
# --------------------------------------------------------------------------
@st.cache_resource(show_spinner="Connecting to the database...")
def get_connection():
    """Return (connection, label). MySQL if configured, else SQLite built from the CSV."""
    try:
        cfg = st.secrets["mysql"]
    except Exception:  # no secrets file or no [mysql] section
        cfg = None

    if cfg:
        from sqlalchemy import create_engine

        url = (
            f"mysql+pymysql://{cfg['user']}:{quote_plus(str(cfg['password']))}"
            f"@{cfg['host']}:{cfg.get('port', 3306)}/{cfg['database']}"
        )
        return create_engine(url, pool_pre_ping=True), "MySQL"

    df = pd.read_csv(CSV_PATH)
    con = sqlite3.connect(":memory:", check_same_thread=False)
    df.to_sql("ola_rides", con, index=False)
    return con, "SQLite (loaded from CSV)"


@st.cache_data(show_spinner=False)
def run_query(sql: str) -> pd.DataFrame:
    con, _ = get_connection()
    return pd.read_sql(sql, con)


def powerbi_url() -> str:
    try:
        return st.secrets.get("powerbi_url", POWERBI_EMBED_URL)
    except Exception:
        return POWERBI_EMBED_URL


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def search_filter(df: pd.DataFrame, term: str) -> pd.DataFrame:
    """Keep rows where any column contains the search text (case-insensitive)."""
    if not term:
        return df
    mask = df.astype(str).apply(lambda col: col.str.contains(term, case=False, na=False)).any(axis=1)
    return df[mask]


def show_table(df: pd.DataFrame, key: str, file_name: str) -> None:
    """Search box + table (capped for speed) + CSV download of the full result."""
    term = st.text_input("Search in results", key=f"search_{key}", placeholder="Type to filter rows...")
    shown = search_filter(df, term)
    st.caption(f"{len(shown):,} of {len(df):,} rows"
               + (f" (showing the first {MAX_ROWS_SHOWN:,})" if len(shown) > MAX_ROWS_SHOWN else ""))
    st.dataframe(shown.head(MAX_ROWS_SHOWN), use_container_width=True, hide_index=True)
    st.download_button(
        "Download full result as CSV",
        shown.to_csv(index=False).encode("utf-8"),
        file_name=file_name,
        mime="text/csv",
        key=f"download_{key}",
    )


# --------------------------------------------------------------------------
# Page 1: Overview
# --------------------------------------------------------------------------
def page_overview() -> None:
    st.title("Ola Ride Insights")
    st.caption("Ride-sharing analytics for July 2024")

    vehicles_all = run_query(q.vehicles_sql())["vehicle_type"].tolist()
    span = run_query(q.date_range_sql()).iloc[0]
    first_day = pd.to_datetime(span["first_day"]).date()
    last_day = pd.to_datetime(span["last_day"]).date()

    with st.sidebar:
        st.subheader("Filters")
        chosen = st.multiselect("Vehicle type", vehicles_all, placeholder="All vehicle types")
        dates = st.date_input("Date range", (first_day, last_day), min_value=first_day, max_value=last_day)

    if not isinstance(dates, tuple) or len(dates) != 2:
        st.info("Pick both a start and an end date in the sidebar.")
        return

    where = q.build_where(chosen, dates[0], dates[1])
    kpi = run_query(q.kpi_sql(where)).iloc[0]
    total = int(kpi["total_rides"])
    if total == 0:
        st.warning("No rides match these filters.")
        return

    success_rate = kpi["successful_rides"] / total
    cancel_rate = kpi["cancelled_rides"] / total

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total rides", f"{total:,}")
    c2.metric("Success rate", f"{success_rate:.2%}")
    c3.metric("Cancellation rate", f"{cancel_rate:.2%}")
    c4.metric("Revenue (successful rides)", f"{int(kpi['revenue']):,}")
    st.caption("Cancellation rate counts customer and driver cancellations; "
               "'Driver Not Found' bookings are counted separately.")

    left, right = st.columns(2)
    with left:
        st.subheader("Booking status")
        status = run_query(q.status_sql(where))
        st.bar_chart(status.set_index("booking_status")["rides"])
    with right:
        st.subheader("Rides per day")
        daily = run_query(q.daily_sql(where))
        daily["booking_date"] = pd.to_datetime(daily["booking_date"])
        st.line_chart(daily.set_index("booking_date")["rides"])


# --------------------------------------------------------------------------
# Page 2: SQL Insights (the 10 questions)
# --------------------------------------------------------------------------
def page_sql_insights() -> None:
    st.title("SQL Insights")
    st.caption("The ten business questions from the project brief, answered with SQL.")

    labels = [f"Q{item['id']}. {item['title']}" for item in q.QUERIES]
    choice = st.selectbox("Choose a question", labels)
    item = q.QUERIES[labels.index(choice)]

    st.subheader(choice)
    with st.expander("Show SQL", expanded=True):
        st.code(item["sql"], language="sql")

    df = run_query(item["sql"])

    if df.shape == (1, 1):  # a single number
        st.metric(df.columns[0].replace("_", " ").title(), f"{df.iloc[0, 0]:,}")
    elif df.shape[0] == 1:  # one row, several values (Q6)
        cols = st.columns(df.shape[1])
        for col, name in zip(cols, df.columns):
            col.metric(name.replace("_", " ").title(), f"{df.iloc[0][name]}")
    else:
        if item["chart"]:
            st.bar_chart(df.set_index(item["chart"]["x"])[item["chart"]["y"]])
        show_table(df, key=f"q{item['id']}", file_name=f"ola_q{item['id']}.csv")

    st.success(f"Insight: {item['insight']}")


# --------------------------------------------------------------------------
# Page 3: Power BI dashboard
# --------------------------------------------------------------------------
def page_powerbi() -> None:
    st.title("Power BI Dashboard")
    url = powerbi_url()

    if url:
        components.iframe(url, height=720, scrolling=True)
        st.caption("If the dashboard does not load, open it directly: " + url)
        return

    images = sorted(IMAGE_DIR.glob("*.png")) if IMAGE_DIR.exists() else []
    if images:
        st.info("Showing dashboard screenshots. Add your Power BI link to display the live report.")
        for image in images:
            st.image(str(image), caption=image.stem.replace("_", " ").title(), use_container_width=True)
    else:
        st.info(
            "No Power BI link has been added yet.\n\n"
            "1. Publish your report, then copy its embed link.\n"
            "2. Paste it into `POWERBI_EMBED_URL` in app.py, or into `powerbi_url` in secrets.toml.\n"
            "3. Alternatively, put PNG screenshots of the five dashboard pages in a folder named "
            "`dashboard_images` next to app.py."
        )


# --------------------------------------------------------------------------
# Page 4: Custom SQL
# --------------------------------------------------------------------------
def page_custom_sql() -> None:
    st.title("Custom SQL")
    st.caption("Run your own read-only query on the table `ola_rides`.")

    with st.expander("Columns available"):
        st.write(", ".join(run_query("SELECT * FROM ola_rides LIMIT 1").columns))

    default = ("SELECT vehicle_type, COUNT(*) AS rides\n"
               "FROM ola_rides\nGROUP BY vehicle_type\nORDER BY rides DESC")
    sql = st.text_area("SQL query", default, height=160)

    if st.button("Run query", type="primary"):
        error = q.validate_select(sql)
        if error:
            st.error(error)
            return
        try:
            result = run_query(sql.strip().rstrip(";"))
        except Exception as exc:  # show database errors to the user
            st.error(f"Query failed: {exc}")
            return
        show_table(result, key="custom", file_name="ola_custom_query.csv")


# --------------------------------------------------------------------------
# Navigation
# --------------------------------------------------------------------------
PAGES = {
    "Overview": page_overview,
    "SQL Insights": page_sql_insights,
    "Power BI Dashboard": page_powerbi,
    "Custom SQL": page_custom_sql,
}

with st.sidebar:
    st.header("Ola Ride Insights")
    page = st.radio("Go to", list(PAGES), label_visibility="collapsed")
    _, source = get_connection()
    st.caption(f"Data source: {source}")

PAGES[page]()