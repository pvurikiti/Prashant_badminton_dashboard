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
        df['partner'] = df['partner'].fillna("None")
        df['opponents'] = df['opponents'].fillna("Unknown")
        
        # Extract Year from the date string (e.g., "Apr 13 2024 to..." -> 2024)
        df['year'] = df['date'].str.extract(r'(\d{4})').fillna("Unknown")
        
        # --- ROBUST EVENT NORMALIZATION MATRIX ---
        def parse_category_and_division(event_str):
            event_upper = str(event_str).upper()
            
            # Default fallbacks
            cat = "Other"
            div = "Open"
            
            # 1. Determine Category
            if "MIXED" in event_upper or "XD" in event_upper:
                cat = "Mixed Doubles"
            elif "MEN" in event_upper and "DOUBLE" in event_upper or "MD" in event_upper:
                cat = "Men's Doubles"
            elif "MEN" in event_upper and "SINGLE" in event_upper or "MS" in event_upper:
                cat = "Men's Singles"
                
            # 2. Determine Division
            if "C" in event_upper:
                div = "C"
            elif "D" in event_upper:
                div = "D"
            elif "E" in event_upper:
                div = "E"
                
            return pd.Series([cat, div])

        df[['standard_category', 'standard_division']] = df['event'].apply(parse_category_and_division)
        return df
    except Exception as e:
        st.error(f"Error loading JSON data structure: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🎯 Dashboard Filters")
    
    # 1. Filter by Year
    all_years = ["All"] + sorted(df["year"].unique().tolist(), reverse=True)
    selected_year = st.sidebar.selectbox("📅 Choose Year", all_years)
    
    # 2. Filter by Tournament
    all_tournaments = ["All"] + sorted(df["tournament"].unique().tolist())
    selected_tournament = st.sidebar.selectbox("🏆 Choose Tournament", all_tournaments)
    
    # 3. Standardized Category Filter
    all_categories = ["All"] + sorted(df["standard_category"].unique().tolist())
    selected_category = st.sidebar.selectbox("🏸 Choose Category", all_categories)
    
    # 4. Standardized Division Filter
    all_divisions = ["All"] + sorted(df["standard_division"].unique().tolist())
    selected_division = st.sidebar.selectbox("🎖️ Choose Division", all_divisions)

    # Apply Sidebar Filter Logic Cascades
    filtered_df = df.copy()
    if selected_year != "All":
        filtered_df = filtered_df[filtered_df["year"] == selected_year]
    if selected_tournament != "All":
        filtered_df = filtered_df[filtered_df["tournament"] == selected_tournament]
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df["standard_category"] == selected_category]
    if selected_division != "All":
        filtered_df = filtered_df[filtered_df["standard_division"] == selected_division]

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
            st.markdown("#### Distribution by Standardized Division")
            if total_matches > 0:
                fig_bar = px.bar(
                    filtered_df, 
                    x="standard_division", 
                    color="result",
                    color_discrete_map={"Win": "#00f2fe", "Loss": "#ff4b4b"},
                    template="plotly_dark",
                    category_orders={"standard_division": ["C", "D", "E"], "result": ["Win", "Loss"]}
                )
                fig_bar.update_layout(xaxis_title="Division", yaxis_title="Matches", legend_title=None, height=280)
                st.plotly_chart(fig_bar, use_container_width=True)

        # Timeline performance breakdown
        st.markdown("#### Performance Volume Over Time")
        timeline_data = filtered_df.groupby(["tournament", "result"], sort=False).size().unstack(fill_value=0).reset_index()
        fig_line = go.Figure()
        if "Win" in timeline_data.columns:
            fig_line.add_trace(go.Scatter(x=timeline_data["tournament"], y=timeline_data["Win"], mode='lines+markers', name='Wins', line=dict(color='#00f2fe', width=3)))
        if "Loss" in timeline_data.columns:
            fig_line.add_trace(go.Bar(x=timeline_data["tournament"], y=timeline_data["Loss"], name='Losses', marker_color='rgba(255, 75, 75, 0.4)'))
        fig_line.update_layout(template="plotly_dark", height=280, barmode='group', margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_line, use_container_width=True)

    # ================= TAB 2: ALL WINS =================
    with tab_wins:
        st.markdown("#### 🟢 Complete Victory Ledger")
        wins_df = filtered_df[filtered_df["result"] == "Win"]
        st.metric(label="Total Wins in View", value=len(wins_df))
        st.dataframe(
            wins_df[["year", "tournament", "standard_category", "standard_division", "round", "partner", "opponents", "score"]],
            use_container_width=True, hide_index=True
        )

    # ================= TAB 3: ALL LOSSES =================
    with tab_losses:
        st.markdown("#### 🔴 Complete Defeat Ledger")
        losses_df = filtered_df[filtered_df["result"] == "Loss"]
        st.metric(label="Total Losses in View", value=len(losses_df))
        st.dataframe(
            losses_df[["year", "tournament", "standard_category", "standard_division", "round", "partner", "opponents", "score"]],
            use_container_width=True, hide_index=True
        )

    # ================= TAB 4: HEAD TO HEAD =================
    with tab_h2h:
        st.markdown("#### ⚔️ Opponent Matchup Telemetry")
        
        # Build an interactive list of unique individual opponent names
        opp_list = set()
        for opps in df["opponents"].unique():
            # Split clean pairings separated by '&' or 'vs'
            for names in str(opps).split("&"):
                opp_list.add(names.strip())
                
        sorted_opponents = sorted(list(opp_list))
        selected_opp = st.selectbox("🎯 Select/Type Opponent Name to Query:", sorted_opponents)
        
        if selected_opp:
            # Query if selected opponent string is found anywhere inside opponent column layer
            h2h_df = df[df["opponents"].str.contains(selected_opp, case=False, na=False)]
            
            h2h_total = len(h2h_df)
            h2h_wins = len(h2h_df[h2h_df["result"] == "Win"])
            h2h_losses = len(h2h_df[h2h_df["result"] == "Loss"])
            
            h2h_col1, h2h_col2, h2h_col3 = st.columns(3)
            h2h_col1.metric("Matches Played", h2h_total)
            h2h_col2.metric("Your Wins", h2h_wins)
            h2h_col3.metric("Your Losses", h2h_losses)
            
            st.markdown(f"##### Encounter History Matrix vs. {selected_opp}")
            st.dataframe(
                h2h_df[["year", "tournament", "standard_category", "standard_division", "round", "partner", "opponents", "score", "result"]],
                use_container_width=True, hide_index=True
            )

    # --- GLOBAL DATA LEDGER SEARCH FOOTER ---
    st.markdown("---")
    st.subheader("📋 Filtered Match Registry")
    st.dataframe(
        filtered_df[["year", "tournament", "standard_category", "standard_division", "round", "partner", "opponents", "score", "result"]],
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning("Empty dataset or file path configuration problem.")
