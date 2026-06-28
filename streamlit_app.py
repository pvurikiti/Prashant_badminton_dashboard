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
            event_upper = str(row.get('event', '')).upper().strip()
            round_upper = str(row.get('round', '')).upper().strip()
            
            # 1. Category Mapping
            cat = "Other"
            if "MIXED" in event_upper or "XD" in event_upper:
                cat = "Mixed Doubles"
            elif ("MEN" in event_upper and "DOUBLE" in event_upper) or "MD" in event_upper:
                cat = "Men's Doubles"
            elif ("MEN" in event_upper and "SINGLE" in event_upper) or "MS" in event_upper:
                cat = "Men's Singles"
                
            # 2. Division Mapping (Fixed to prioritize standalone codes over text container matches)
            div = "Other"
            # Explicitly capture shorthand flight codes first
            if "CXD" in event_upper or "CMD" in event_upper or "CMS" in event_upper or "XD C" in event_upper or "C MIXED" in event_upper or "C MEN" in event_upper:
                div = "C"
            elif "DXD" in event_upper or "DMD" in event_upper or "DMS" in event_upper or "XD D" in event_upper or "D MIXED" in event_upper or "D MEN" in event_upper:
                div = "D"
            elif "EXD" in event_upper or "EMD" in event_upper or "EMS" in event_upper or "XD E" in event_upper or "E MIXED" in event_upper or "E MEN" in event_upper or "E SINGLE" in event_upper:
                div = "E"
            else:
                # Fallback if no clean block is found, checking for standalone letters
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
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🎯 Dashboard Filters")
    
    selected_year = st.sidebar.selectbox("📅 Choose Year", ["All"] + sorted(df["year"].unique().tolist(), reverse=True))
    selected_tournament = st.sidebar.selectbox("🏆 Choose Tournament", ["All"] + sorted(df["tournament"].unique().tolist()))
    selected_category = st.sidebar.selectbox("🏸 Choose Category", ["All"] + sorted(df["standard_category"].unique().tolist()))
    selected_division = st.sidebar.selectbox("🎖️ Choose Division", ["All"] + sorted(df["standard_division"].unique().tolist()))
    
    # Partner Selection Filter (Clean and Deduplicated via Title Case normalization above)
    partner_roster = sorted([p for p in df["partner"].unique() if p != "None"])
    partner_options = ["All", "None (Singles)"] + partner_roster
    selected_partner = st.sidebar.selectbox("🤝 Choose Partner", partner_options)
    
    # New Filter: Bracket Track Type
    selected_bracket = st.sidebar.selectbox("🌿 Choose Bracket Track", ["All", "MAINS", "CONS"])
    
    # New Filter: Standardized Round Stage
    round_order = ["R64", "R32", "R16", "QF", "SF", "F", "Other"]
    available_rounds = ["All"] + [r for r in round_order if r in df["standard_round"].unique()]
    selected_round = st.sidebar.selectbox("⌛ Choose Round Stage", available_rounds)

    # Filter Logic Cascades
    filtered_df = df.copy()
    if selected_year != "All":
        filtered_df = filtered_df[filtered_df["year"] == selected_year]
    if selected_tournament != "All":
        filtered_df = filtered_df[filtered_df["tournament"] == selected_tournament]
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df["standard_category"] == selected_category]
    if selected_division != "All":
        filtered_df = filtered_df[filtered_df["standard_division"] == selected_division]
    if selected_partner == "None (Singles)":
        filtered_df = filtered_df[filtered_df["partner"] == "None"]
    elif selected_partner != "All":
        filtered_df = filtered_df[filtered_df["partner"] == selected_partner]
    if selected_bracket != "All":
        filtered_df = filtered_df[filtered_df["bracket_type"] == selected_bracket]
    if selected_round != "All":
        filtered_df = filtered_df[filtered_df["standard_round"] == selected_round]

    # --- HEADER ---
    st.title("🏸 Prashant's Badminton Performance Insights")
    st.markdown("Advanced standardized telemetry analytics and multi-angle performance matrix tracking.")
    st.markdown("---")

    # --- TOP ROW: KPI METRICS ---
    total_matches = len(filtered_df)
    wins = len(filtered_df[filtered_df["result"] == "Win"])
    losses = len(filtered_df[filtered_df["result"] == "Loss"])
    win_rate = (wins / total_matches * 100) if total_matches > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="TOTAL MATCHES", value=total_matches)
    with col2:
        st.metric(label="TOTAL WINS", value=wins)
    with col3:
        st.metric(label="TOTAL LOSSES", value=losses)
    with col4:
        st.metric(label="WIN RATE", value=f"{win_rate:.1f}%")

    st.write("")

    # --- CORE VIEW TABS ---
    st.subheader("🔍 Performance Perspectives")
    tab_overview, tab_wins, tab_losses, tab_h2h = st.tabs([
        "📊 Main Analytics Overview", 
        "🟢 View All Wins", 
        "🔴 View All Losses", 
        "⚔️ Head-to-Head Radar"
    ])

    # ================= TAB 1: OVERVIEW =================
    with tab_overview:
        chart_col1, chart_col2 = st.columns([1, 1])

        with chart_col1:
            st.markdown("#### Win / Loss Ratio Split")
            if total_matches > 0:
                res_counts = filtered_df["result"].value_counts().reset_index()
                res_counts.columns = ["result", "count"]
                
                fig_pie = px.pie(
                    res_counts, 
                    values="count", 
                    names="result", 
                    hole=0.55,
                    color="result",
                    color_discrete_map={"Win": "#00f2fe", "Loss": "#ff4b4b"},
                    template="plotly_dark"
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=280)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No records match your selected filter cascade.")

        with chart_col2:
            st.markdown("#### Win Percentage per Event Division")
            if total_matches > 0:
                # Calculate Win % mathematically per Event Division grouping
                div_stats = filtered_df.groupby("standard_division", as_index=False)["result"].value_counts()
                div_stats = div_stats.pivot(index="standard_division", columns="result", values="count").fillna(0).reset_index()
                
                if "Win" not in div_stats.columns: div_stats["Win"] = 0
                if "Loss" not in div_stats.columns: div_stats["Loss"] = 0
                
                div_stats["Total"] = div_stats["Win"] + div_stats["Loss"]
                div_stats["WIN_PCT"] = (div_stats["Win"] / div_stats["Total"] * 100).round(1)
                
                # Sort explicitly by flight priority ranking
                div_stats["sort_idx"] = div_stats["standard_division"].map({"C": 0, "D": 1, "E": 2}).fillna(3)
                div_stats = div_stats.sort_values("sort_idx")

                fig_pct = px.bar(
                    div_stats,
                    x="standard_division",
                    y="WIN_PCT",
                    text=div_stats["WIN_PCT"].apply(lambda x: f"{x}%"),
                    color="standard_division",
                    color_discrete_sequence=["#00f2fe", "#a3e5fc", "#3a86c8"],
                    template="plotly_dark"
                )
                fig_pct.update_layout(
                    xaxis_title="Division Tier",
                    yaxis_title="Win Percentage (%)",
                    yaxis=dict(range=[0, 105]),
                    showlegend=False,
                    height=280
                )
                fig_pct.update_traces(textposition="outside", cliponaxis=False)
                st.plotly_chart(fig_pct, use_container_width=True)

        # Timeline performance volume tracking
        st.markdown("#### Performance Volume Over Time")
        if total_matches > 0:
            timeline_data = filtered_df.groupby(["tournament", "result"], sort=False).size().unstack(fill_value=0).reset_index()
            if "Win" not in timeline_data.columns: timeline_data["Win"] = 0
            if "Loss" not in timeline_data.columns: timeline_data["Loss"] = 0
            
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=timeline_data["tournament"], y=timeline_data["Win"], mode='lines+markers', name='Wins', line=dict(color='#00f2fe', width=3)))
            fig_line.add_trace(go.Bar(x=timeline_data["tournament"], y=timeline_data["Loss"], name='Losses', marker_color='rgba(255, 75, 75, 0.4)'))
            fig_line.update_layout(template="plotly_dark", height=280, barmode='group', margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_line, use_container_width=True)

    # ================= TAB 2: ALL WINS =================
    with tab_wins:
        st.markdown("#### 🟢 Complete Victory Ledger")
        wins_df = filtered_df[filtered_df["result"] == "Win"]
        st.metric(label="Total Wins in View", value=len(wins_df))
        
        # Standardize and map titles in all caps safely
        wins_display = wins_df.rename(columns={
            "year": "YEAR", "tournament": "TOURNAMENT", "standard_category": "CATEGORY",
            "standard_division": "DIVISION", "bracket_type": "TRACK", "standard_round": "ROUND",
            "partner": "PARTNER", "opponents": "OPPONENTS", "score": "SCORE RESULT"
        })
        st.dataframe(
            wins_display[["YEAR", "TOURNAMENT", "CATEGORY", "DIVISION", "TRACK", "ROUND", "PARTNER", "OPPONENTS", "SCORE RESULT"]],
            use_container_width=True, hide_index=True
        )

    # ================= TAB 3: ALL LOSSES =================
    with tab_losses:
        st.markdown("#### 🔴 Complete Defeat Ledger")
        losses_df = filtered_df[filtered_df["result"] == "Loss"]
        st.metric(label="Total Losses in View", value=len(losses_df))
        
        losses_display = losses_df.rename(columns={
            "year": "YEAR", "tournament": "TOURNAMENT", "standard_category": "CATEGORY",
            "standard_division": "DIVISION", "bracket_type": "TRACK", "standard_round": "ROUND",
            "partner": "PARTNER", "opponents": "OPPONENTS", "score": "SCORE RESULT"
        })
        st.dataframe(
            losses_display[["YEAR", "TOURNAMENT", "CATEGORY", "DIVISION", "TRACK", "ROUND", "PARTNER", "OPPONENTS", "SCORE RESULT"]],
            use_container_width=True, hide_index=True
        )

    # ================= TAB 4: HEAD TO HEAD =================
    with tab_h2h:
        st.markdown("#### ⚔️ Opponent Matchup Telemetry")
        
        opp_list = set()
        for opps in df["opponents"].unique():
            for names in str(opps).split("&"):
                # Clean and Title Case every single parsed opponent name to avoid duplicate list variants
                opp_list.add(names.strip().title())
                
        sorted_opponents = sorted(list(opp_list))
        selected_opp = st.selectbox("🎯 Select/Type Opponent Name to Query:", sorted_opponents)
        
        if selected_opp:
            h2h_df = df[df["opponents"].str.contains(selected_opp, case=False, na=False)]
            
            h2h_total = len(h2h_df)
            h2h_wins = len(h2h_df[h2h_df["result"] == "Win"])
            h2h_losses = len(h2h_df[h2h_df["result"] == "Loss"])
            
            h2h_col1, h2h_col2, h2h_col3 = st.columns(3)
            h2h_col1.metric("Matches Played", h2h_total)
            h2h_col2.metric("Your Wins", h2h_wins)
            h2h_col3.metric("Your Losses", h2h_losses)
            
            st.markdown(f"##### Encounter History Matrix vs. {selected_opp}")
            h2h_display = h2h_df.rename(columns={
                "year": "YEAR", "tournament": "TOURNAMENT", "standard_category": "CATEGORY",
                "standard_division": "DIVISION", "bracket_type": "TRACK", "standard_round": "ROUND",
                "partner": "PARTNER", "opponents": "OPPONENTS", "score": "SCORE RESULT", "result": "RESULT"
            })
            st.dataframe(
                h2h_display[["YEAR", "TOURNAMENT", "CATEGORY", "DIVISION", "TRACK", "ROUND", "PARTNER", "OPPONENTS", "SCORE RESULT", "RESULT"]],
                use_container_width=True, hide_index=True
            )

    # --- GLOBAL DATA LEDGER SEARCH FOOTER ---
    st.markdown("---")
    st.subheader("📋 FILTERED MATCH REGISTRY")
    
    # Map exact column names uppercase to match your design parameters flawlessly
    registry_df = filtered_df.rename(columns={
        "year": "YEAR",
        "tournament": "TOURNAMENT",
        "standard_category": "CATEGORY",
        "standard_division": "DIVISION",
        "standard_round": "ROUND",
        "bracket_type": "TRACK",
        "partner": "PARTNER",
        "opponents": "OPPONENTS",
        "score": "SCORE RESULT",
        "result": "RESULT"
    })
    
    st.dataframe(
        registry_df[["YEAR", "TOURNAMENT", "CATEGORY", "DIVISION", "TRACK", "ROUND", "PARTNER", "OPPONENTS", "SCORE RESULT", "RESULT"]],
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning("Empty dataset or file path configuration problem.")
