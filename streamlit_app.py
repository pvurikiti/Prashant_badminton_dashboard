import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(page_title="Prashant's Badminton Stats", layout="wide")
st.title("🏸 Prashant Vurikiti - Performance Dashboard")
st.markdown("---")

# Load Data
def load_data():
    with open("badminton_data.json", "r") as f:
        data = json.load(f)
    return pd.DataFrame(data)

df = load_data()

# Clean missing partners
df["partner"] = df["partner"].replace({"None": "Singles (No Partner)"})

# Sidebar filters
st.sidebar.header("🎯 Dashboard Controls")
tournaments = st.sidebar.multiselect("Tournaments:", options=sorted(df["tournament"].unique()), default=df["tournament"].unique())
events = st.sidebar.multiselect("Event Types:", options=df["event"].unique(), default=df["event"].unique())

# Filter data matrix
f_df = df[(df["tournament"].isin(tournaments)) & (df["event"].isin(events))]

# Calculate KPI stats
total = len(f_df)
wins = len(f_df[f_df["result"] == "Win"])
losses = len(f_df[f_df["result"] == "Loss"])
win_rate = (wins / total * 100) if total > 0 else 0

# UI scoreboards
c1, c2, c3, c4 = st.columns(4)
c1.metric("Matches Played", total)
c2.metric("Wins ✅", wins)
c3.metric("Losses ❌", losses)
c4.metric("Win Rate %", f"{win_rate:.1f}%")

st.markdown("---")

# Interactive Charts
ch1, ch2 = st.columns(2)
with ch1:
    st.subheader("Win / Loss Ratio")
    if total > 0:
        fig_pie = px.pie(f_df, names="result", color="result", color_discrete_map={"Win": "#2ecc71", "Loss": "#e74c3c"})
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.write("No data found matching your sidebar filter criteria.")

with ch2:
    st.subheader("Match Performance per Discipline")
    if total > 0:
        fig_bar = px.bar(f_df, x="event", color="result", color_discrete_map={"Win": "#2ecc71", "Loss": "#e74c3c"}, barmode="group")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.write("No data found matching your sidebar filter criteria.")

st.markdown("---")

# Main History Look-up Ledger
st.subheader("🔍 Master Match Records Search")
st.dataframe(f_df[["tournament", "event", "partner", "round", "opponents", "score", "result"]], use_container_width=True)
