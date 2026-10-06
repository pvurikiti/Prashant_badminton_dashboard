import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

# Set page config for a widescreen, modern layout
st.set_page_config(
    page_title="Prashant's Badminton Performance Insights",
    page_icon="🏸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Load and Standardize Data
@st.cache_data
def load_data():
    try:
        with open("badminton_data.json", "r") as f:
            data = json.load(f)
        df = pd.DataFrame(data)

        # Standardize basic results
        df['result'] = df['result'].fillna("").str.capitalize().str.strip()

        # FIX CASE SENSITIVITY: Standardize partner names to Title Case to group duplicates
        df['partner'] = df['partner'].fillna("None").astype(str).replace(r'^\s*$', 'None', regex=True).str.strip()
        df['partner'] = df['partner'].apply(lambda x: "None" if x == "None" else x.title())

        # FIX CASE SENSITIVITY: Standardize opponent combinations to Title Case
        df['opponents'] = df['opponents'].fillna("Unknown").astype(str).str.title().str.strip()

        # Extract Year from the date string
        df['year'] = df['date'].str.extract(r'(\d{4})').fillna("Unknown")

        # --- ROBUST TELEMETRY NORMALIZATION MATRIX ---
        def parse_advanced_features(row):
            event_upper = str(row.get('event', '') or '').upper().strip()
            round_upper = str(row.get('round', '') or '').upper().strip()

            # 1. Category Mapping
            cat = "Other"
            if "MIXED" in event_upper or "XD" in event_upper:
                cat = "Mixed Doubles"
            elif ("MEN" in event_upper and "DOUBLE" in event_upper) or "MD" in event_upper:
                cat = "Men's Doubles"
            elif ("MEN" in event_upper and "SINGLE" in event_upper) or "MS" in event_upper:
                cat = "Men's Singles"

            # 2. Division Mapping
            div = "Other"
            if "CXD" in event_upper or "CMD" in event_upper or "CMS" in event_upper or "XD C" in event_upper or "C MIXED" in event_upper or "C MEN" in event_upper:
                div = "C"
            elif "DXD" in event_upper or "DMD" in event_upper or "DMS" in event_upper or "XD D" in event_upper or "D MIXED" in event_upper or "D MEN" in event_upper:
                div = "D"
            elif "EXD" in event_upper or "EMD" in event_upper or "EMS" in event_upper or "XD E" in event_upper or "E MIXED" in event_upper or "E MEN" in event_upper or "E SINGLE" in event_upper:
                div = "E"
            else:
                if " C " in f" {event_upper} " or "C" == event_upper:
                    div = "C"
                elif " D " in f" {event_upper} " or "D" == event_upper:
                    div = "D"
                elif " E " in f" {event_upper} " or "E" == event_upper:
                    div = "E"

            # 3. Bracket Type Mapping (MAINS vs CONS)
            bracket = "MAINS"
            if "CONSOLATION" in round_upper or "CONS" in round_upper:
                bracket = "CONS"

            # 4. Round Stage Standardization
            stage = "Other"
            if "64" in round_upper:
                stage = "R64"
            elif "32" in round_upper:
                stage = "R32"
            elif "16" in round_upper:
                stage = "R16"
            elif "QUARTER" in round_upper or "QF" in round_upper:
                stage = "QF"
            elif "SEMI" in round_upper or "SF" in round_upper:
                stage = "SF"
            elif "FINAL" in round_upper or round_upper == "F":
                stage = "F"

            return pd.Series([cat, div, bracket, stage])

        df[['standard_category', 'standard_division', 'bracket_type', 'standard_round']] = df.apply(parse_advanced_features, axis=1)
        return df
    except Exception as e:
        st.error(f"Error loading JSON data structure: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- SIDEBAR CASCADING FILTERS ---
    st.sidebar.header("🎯 Dashboard Filters")

    # Start with a full copy that cascades as choices are made
    f_df = df.copy()

    # 1. Year Filter
    available_years = ["All"] + sorted(f_df["year"].unique().tolist(), reverse=True)
    selected_year = st.sidebar.selectbox("📅 Choose Year", available_years)
    if selected_year != "All":
        f_df = f_df[f_df["year"] == selected_year]

    # 2. Tournament Filter (Cascaded by Year)
    available_tournaments = ["All"] + sorted(f_df["tournament"].unique().tolist())
    selected_tournament = st.sidebar.selectbox("🏆 Choose Tournament", available_tournaments)
    if selected_tournament != "All":
        f_df = f_df[f_df["tournament"] == selected_tournament]

    # 3. Category Filter (Cascaded by Year & Tournament)
    available_categories = ["All"] + sorted(f_df["standard_category"].unique().tolist())
    selected_category = st.sidebar.selectbox("🏸 Choose Category", available_categories)
    if selected_category != "All":
        f_df = f_df[f_df["standard_category"] == selected_category]

    # 4. Division Filter (Cascaded by Year, Tournament & Category)
    available_divisions = ["All"] + sorted(f_df["standard_division"].unique().tolist())
    selected_division = st.sidebar.selectbox("🎖️ Choose Division", available_divisions)
    if selected_division != "All":
        f_df = f_df[f_df["standard_division"] == selected_division]

    # 5. Partner Filter (Cascaded by prior filters)
    partner_roster = sorted([p for p in f_df["partner"].unique() if p != "None"])
    has_singles = "None" in f_df["partner"].values
    partner_options = ["All"] + (["None (Singles)"] if has_singles else []) + partner_roster
    selected_partner = st.sidebar.selectbox("🤝 Choose Partner", partner_options)
    if selected_partner == "None (Singles)":
        f_df = f_df[f_df["partner"] == "None"]
    elif selected_partner != "All":
        f_df = f_df[f_df["partner"] == selected_partner]

    # 6. Bracket Track Filter (Cascaded)
    available_brackets = ["All"] + sorted(f_df["bracket_type"].unique().tolist())
    selected_bracket = st.sidebar.selectbox("🌿 Choose Bracket Track", available_brackets)
    if selected_bracket != "All":
        f_df = f_df[f_df["bracket_type"] == selected_bracket]

    # 7.
