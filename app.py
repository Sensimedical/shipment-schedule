import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "orders.db"
LOGO_PATH = BASE_DIR / "assets" / "sensimedical-logo.png"
FILE_PATTERNS = ("Pending Orders *.csv", "Pending Orders *.xlsx")

# SensiMedical theme – aligned with sensimedical.com (clean, professional medical)
SENSIMEDICAL_CSS = """
<style>
    /* Main – clean white/grey like SensiMedical site */
    .stApp { background-color: #ffffff; }
    header[data-testid="stHeader"] { background: #fff; }
    /* Sidebar – SensiMedical blue */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #2d5a87 100%);
    }
    [data-testid="stSidebar"] .stMarkdown { color: #e8eef4; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 { color: #fff !important; }
    /* Main content headers – dark blue */
    h1, h2, h3 { color: #1e3a5f !important; font-weight: 600; }
    /* Primary button – SensiMedical teal accent */
    .stButton > button {
        background: linear-gradient(90deg, #0d9488 0%, #0f766e 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
    }
    .stButton > button:hover {
        background: #0f766e !important;
        color: white !important;
    }
    /* Inputs – light border */
    .stTextInput input, .stDataFrame { border-radius: 6px; }
    /* Expander – light blue tint */
    .streamlit-expanderHeader { background-color: #f0f9ff; color: #1e3a5f; border-radius: 6px; }
    /* Alerts */
    [data-testid="stSuccess"] { border-left: 4px solid #0d9488; background: #f0fdfa; }
    [data-testid="stWarning"] { border-left: 4px solid #2d5a87; background: #f0f9ff; }
    [data-testid="stError"] { border-left: 4px solid #b91c1c; }
</style>
"""


def get_latest_file() -> Path | None:
    if not DATA_DIR.exists():
        return None
    files = []
    for pattern in FILE_PATTERNS:
        files.extend(DATA_DIR.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS followup_overrides (
            order_key TEXT PRIMARY KEY,
            follow_up TEXT
        )
        """
    )
    conn.commit()
    return conn


def load_base_data() -> pd.DataFrame:
    path = get_latest_file()
    if not path:
        return pd.DataFrame()

    if path.suffix.lower() == ".xlsx":
        df = pd.read_excel(path, engine="openpyxl")
    else:
        df = pd.read_csv(path)

    # Parse dates (Excel may already give datetime)
    if "Created Date" in df.columns:
        df["Created Date"] = pd.to_datetime(df["Created Date"], errors="coerce")
    if "Follow up" in df.columns:
        df["Follow up"] = pd.to_datetime(df["Follow up"], errors="coerce").dt.date

    # Build a stable order key (replace with real Order ID if available)
    df["order_key"] = (
        df["Customer"].astype(str)
        + "|" + df["Created Date"].dt.strftime("%Y-%m-%d")
        + "|" + df["Cases #"].astype(str)
        + "|" + df["Sales"].astype(str)
    )

    return df


def apply_overrides(df: pd.DataFrame, conn: sqlite3.Connection) -> pd.DataFrame:
    overrides = pd.read_sql_query(
        "SELECT order_key, follow_up FROM followup_overrides", conn
    )
    if overrides.empty:
        return df

    overrides["follow_up"] = pd.to_datetime(overrides["follow_up"]).dt.date
    df = df.merge(overrides, on="order_key", how="left", suffixes=("", "_override"))
    df["Follow up"] = df["follow_up"].combine_first(df["Follow up"])
    df = df.drop(columns=["follow_up"])
    return df


def save_overrides(
    original: pd.DataFrame, edited: pd.DataFrame, conn: sqlite3.Connection
) -> int:
    cols = ["order_key", "Follow up"]
    orig = original[cols].rename(columns={"Follow up": "Follow_up_orig"})
    merged = edited[cols].merge(orig, on="order_key")

    # Detect changed rows (including filling in missing values)
    changed = merged[
        merged["Follow up"].astype(str) != merged["Follow_up_orig"].astype(str)
    ].dropna(subset=["Follow up"])

    if changed.empty:
        return 0

    cur = conn.cursor()
    for _, row in changed.iterrows():
        cur.execute(
            """
            INSERT INTO followup_overrides (order_key, follow_up)
            VALUES (?, ?)
            ON CONFLICT(order_key) DO UPDATE SET follow_up=excluded.follow_up
            """,
            (row["order_key"], str(row["Follow up"]))
        )
    conn.commit()
    return len(changed)


def main() -> None:
    st.set_page_config(
        page_title="SensiMedical™ – Pending Orders",
        layout="wide",
        page_icon="📦",
    )
    st.markdown(SENSIMEDICAL_CSS, unsafe_allow_html=True)

    # SensiMedical logo in sidebar
    if LOGO_PATH.exists():
        st.sidebar.image(str(LOGO_PATH), use_container_width=True)
    st.sidebar.markdown("---")
    st.sidebar.header("Daily workflow")
    st.sidebar.markdown(
        f"""
        1. Export/download today's **Pending Orders** file (CSV or Excel).
        2. Save or move it into the `data` folder:
           `{DATA_DIR}`
        3. Reload this page (or use Streamlit's rerun button).
        4. Edit **Follow up** dates and click **Save changes**.
        """
    )

    st.title("Pending Orders – Schedule Manager")
    st.caption("SensiMedical™ Shipment Schedule")

    if not DATA_DIR.exists():
        st.error(
            f"`data` folder not found.\n\n"
            f"Please create: `{DATA_DIR}` and put your daily CSV there."
        )
        return

    conn = init_db()
    base_df = load_base_data()
    if base_df.empty:
        st.warning(
            "No 'Pending Orders' file found in the `data` folder.\n\n"
            "Expected: `Pending Orders *.csv` or `Pending Orders *.xlsx`"
        )
        return

    df = apply_overrides(base_df.copy(), conn)

    with st.expander("Filters", expanded=True):
        customer_filter = st.text_input("Filter by customer (contains):", "")
        if customer_filter:
            df = df[
                df["Customer"]
                .astype(str)
                .str.contains(customer_filter, case=False, na=False)
            ]

    st.write("Edit the **Follow up** date using the calendar.")

    # Show table without order_key (internal use only)
    display_df = df.drop(columns=["order_key"])
    edited_display = st.data_editor(
        display_df,
        column_config={
            "Follow up": st.column_config.DateColumn("Follow up"),
        },
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
    )
    # Reattach order_key for save logic
    edited_df = edited_display.copy()
    edited_df["order_key"] = df["order_key"].values

    if st.button("Save changes"):
        n = save_overrides(base_df, edited_df, conn)
        if n > 0:
            st.success(f"Saved {n} updated follow-up date(s).")
        else:
            st.info("No changes to save.")


if __name__ == "__main__":
    main()
