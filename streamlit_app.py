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

# 1. Load Data safely
@st.cache_data
def load_data():
    try:
        with open("badminton_data.json", "r") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        
        # Standardize strings for seamless data grouping
        df['result'] = df['result'].fillna("").str.capitalize().str.strip()
        df['event'] = df['event'].fillna("").str.replace(r'[\(\)]', '', regex=True).str.strip()
        df['partner'] = df['partner'].fillna("None")
        df['opponents'] = df['opponents'].fillna("Unknown")
        return df
    except Exception as e:
        st.error(f"Error loading JSON data structure: {e}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # --- SIDEBAR FILTERS ---
    st.sidebar.header("🎯 Dashboard Filters")
    
    all_tournaments = ["All"] + sorted(df["tournament"].unique().tolist())
    selected_tournament = st.sidebar.selectbox("Choose Tournament", all_tournaments)
    
    all_events = ["All"] + sorted(df["event"].unique().tolist())
    selected_event = st.sidebar.selectbox("Choose Flight Division/Event", all_events)
    
    # Filter Logic
    filtered_df = df.copy()
    if selected_tournament != "All":
        filtered_df = filtered_df[filtered_df["tournament"] == selected_tournament]
    if selected_event != "All":
        filtered_df = filtered_df[filtered_df["event"] == selected_event]

    # --- HEADER ---
    st.title("🏸 Prashant's Badminton Performance Insights")
    st.markdown("Advanced telemetry analytics and win/loss breakdown across tournament tracks.")
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

    st.markdown("<br>", unsafe_allowed_html=True)

    # --- MIDDLE ROW: THE GRAPHICS ---
    chart_col1, chart_col2 = st.columns([1, 1])

    with chart_col1:
        st.subheader("📊 Win / Loss Ratio Split")
        if not filtered_df.empty and total_matches > 0:
            res_counts = filtered_df["result"].value_counts().reset_index()
            res_counts.columns = ["result", "count"] # Robust column safety mapping
            
            fig_pie = px.pie(
                res_counts, 
                values="count", 
                names="result", 
                hole=0.55,
                color="result",
                color_discrete_map={"Win": "#00f2fe", "Loss": "#ff4b4b"},
                template="plotly_dark"
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#111', width=2)))
            fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=320)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No records match current filter metrics.")

    with chart_col2:
        st.subheader("🔥 Match Outings by Division")
        if not filtered_df.empty:
            fig_bar = px.bar(
                filtered_df, 
                y="event", 
                color="result",
                color_discrete_map={"Win": "#00f2fe", "Loss": "#ff4b4b"},
                orientation="h",
                template="plotly_dark",
                category_orders={"result": ["Win", "Loss"]}
            )
            fig_bar.update_layout(
                xaxis_title="Match Count",
                yaxis_title=None,
                legend_title=None,
                margin=dict(t=10, b=10, l=10, r=10),
                height=320,
                barmode="stack"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    # --- ROW 3: TOURNEY TIMELINE PERFORMANCES ---
    st.subheader("📈 Tournament Performance Timeline")
    
    if not filtered_df.empty:
        # Sort by index grouping safely without crashing on missing key lookups
        timeline_data = filtered_df.groupby(["tournament", "result"], sort=False).size().unstack(fill_value=0).reset_index()
        
        fig_line = go.Figure()
        if "Win" in timeline_data.columns:
            fig_line.add_trace(go.Scatter(
                x=timeline_data["tournament"], 
                y=timeline_data["Win"],
                mode='lines+markers',
                name='Wins',
                line=dict(color='#00f2fe', width=3),
                marker=dict(size=8, color='#fff', line=dict(color='#00f2fe', width=2))
            ))
        if "Loss" in timeline_data.columns:
            fig_line.add_trace(go.Bar(
                x=timeline_data["tournament"],
                y=timeline_data["Loss"],
                name='Losses',
                marker_color='rgba(255, 75, 75, 0.4)',
            ))
        
        fig_line.update_layout(
            template="plotly_dark",
            margin=dict(t=20, b=40, l=20, r=20),
            height=350,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            barmode='group'
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # --- BOTTOM ROW: SEARCHABLE LEDGER MATRIX ---
    st.subheader("📋 Searchable Interactive Match Ledger")
    
    search_query = st.text_input("🔍 Filter by Opponent or Partner Name:", "")
    if search_query:
        filtered_df = filtered_df[
            filtered_df["opponents"].str.contains(search_query, case=False, na=False) |
            filtered_df["partner"].str.contains(search_query, case=False, na=False)
        ]
        
    st.dataframe(
        filtered_df[["tournament", "event", "round", "partner", "opponents", "score", "result"]],
        use_container_width=True,
        hide_index=True
    )

else:
    st.warning("Empty dataset or file path configuration problem.")
