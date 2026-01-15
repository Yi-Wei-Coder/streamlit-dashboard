import streamlit as st
import pandas as pd
import plotly.express as px

from utils.fake_data import make_series
from utils.ui import kpi_row, section_header, divider

st.set_page_config(page_title="Macro", layout="wide")

st.title("🌍 Macro Dashboard")
st.caption("DefiLlama-style layout (mock data for team discussion).")

st.sidebar.header("Controls")
show_raw = st.sidebar.checkbox("Show data table", value=False)
seed = st.sidebar.number_input("Mock seed", min_value=1, max_value=9999, value=42, step=1)

m2 = make_series("M2", years=3, freq="W", kind="level", seed=seed)
stable = make_series("Stablecoin Supplies", years=3, freq="W", kind="level", seed=seed)
spot = make_series("Spot Trading Volume", years=3, freq="W", kind="volume", seed=seed)
perp = make_series("Perp Trading Volume", years=3, freq="W", kind="volume", seed=seed)
mvrv = make_series("BTC MVRV", years=3, freq="W", kind="ratio", seed=seed)
fg = make_series("Fear & Greed", years=1, freq="D", kind="index", seed=seed)

def last_and_change(df: pd.DataFrame):
    v = df["value"].iloc[-1]
    prev = df["value"].iloc[-2] if len(df) > 1 else v
    chg = (v / prev - 1) * 100 if prev != 0 else 0
    return v, chg

m2_last, m2_chg = last_and_change(m2)
st_last, st_chg = last_and_change(stable)
spot_last, spot_chg = last_and_change(spot)
perp_last, perp_chg = last_and_change(perp)
mvrv_last, mvrv_chg = last_and_change(mvrv)
fg_last, fg_chg = last_and_change(fg)

kpi_row([
    ("M2 (mock)", f"{m2_last:,.0f}", f"{m2_chg:+.2f}% WoW"),
    ("Stablecoin Supply (mock)", f"{st_last:,.0f}", f"{st_chg:+.2f}% WoW"),
    ("Spot Vol (mock)", f"{spot_last:,.0f}", f"{spot_chg:+.2f}% WoW"),
    ("Perp Vol (mock)", f"{perp_last:,.0f}", f"{perp_chg:+.2f}% WoW"),
    ("BTC MVRV (mock)", f"{mvrv_last:.2f}", f"{mvrv_chg:+.2f}% WoW"),
    ("Fear & Greed (mock)", f"{fg_last:.0f}", f"{fg_chg:+.2f}% DoD"),
])

divider()

tabs = st.tabs(["Liquidity", "Market Activity", "Valuation", "Sentiment"])

with tabs[0]:
    section_header("Liquidity", "3Y • Weekly • Mock")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("M2")
        st.plotly_chart(px.line(m2, x="date", y="value"), use_container_width=True)
        if show_raw:
            st.dataframe(m2, use_container_width=True)
    with c2:
        st.subheader("Stablecoin Supplies")
        st.plotly_chart(px.line(stable, x="date", y="value"), use_container_width=True)
        if show_raw:
            st.dataframe(stable, use_container_width=True)

with tabs[1]:
    section_header("Market Activity", "3Y • Weekly • Mock")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Spot Trading Volume")
        st.plotly_chart(px.area(spot, x="date", y="value"), use_container_width=True)
        if show_raw:
            st.dataframe(spot, use_container_width=True)
    with c2:
        st.subheader("Perp Trading Volume")
        st.plotly_chart(px.area(perp, x="date", y="value"), use_container_width=True)
        if show_raw:
            st.dataframe(perp, use_container_width=True)

with tabs[2]:
    section_header("Valuation", "3Y • Weekly • Mock")
    st.subheader("BTC MVRV")
    st.plotly_chart(px.line(mvrv, x="date", y="value"), use_container_width=True)
    if show_raw:
        st.dataframe(mvrv, use_container_width=True)

with tabs[3]:
    section_header("Sentiment", "1Y • Daily • Mock")
    st.subheader("Fear & Greed Index")
    st.plotly_chart(px.line(fg, x="date", y="value"), use_container_width=True)
    st.caption("Scale: 0 (Extreme Fear) → 100 (Extreme Greed).")
    if show_raw:
        st.dataframe(fg, use_container_width=True)

divider()
st.caption("Replace mock data sources later; this is for layout discussion.")
