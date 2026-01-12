import streamlit as st
import pandas as pd
import plotly.express as px

from utils.tokens_mock import generate_token_dataset, ma_30
from utils.formatting import colored_delta, pct_delta_str, badge
from utils.token_news_mock import get_mock_governance, get_mock_news

st.set_page_config(page_title="Tokens", layout="wide")

st.title("🪙 Tokens Dashboard")
st.caption("DefiLlama-style token pages (mock data for team discussion).")

# =======================
# Helpers
# =======================
def last_and_30d_change(df: pd.DataFrame):
    if len(df) < 31:
        v = float(df["value"].iloc[-1])
        return v, 0.0
    v = float(df["value"].iloc[-1])
    prev = float(df["value"].iloc[-31])
    chg = (v / prev - 1) * 100 if prev != 0 else 0.0
    return v, chg

def section_metric(label: str, value_str: str, pct: float):
    st.markdown(f"**{label}**  \n{value_str}  \n{colored_delta(pct)}")

# =======================
# Sidebar – clickable summary table (single-select)
# =======================
st.sidebar.header("Tokens Summary")
seed = st.sidebar.number_input("Mock seed", min_value=1, max_value=9999, value=42, step=1)

summary, details = generate_token_dataset(seed=seed)

if "selected_token" not in st.session_state:
    st.session_state.selected_token = summary["Token"].iloc[0]

summary_view = summary.copy()
for col in ["Price (30D %)", "FDV (30D %)", "Volume 24H (30D %)"]:
    summary_view[col] = summary_view[col].apply(pct_delta_str)

# Single-true checkbox column
summary_view.insert(0, "Pick", summary_view["Token"].eq(st.session_state.selected_token))

editor_cols = ["Pick", "Token", "Price (30D %)", "FDV (30D %)", "Volume 24H (30D %)", "Next Unlock (>2%)"]
summary_editor_df = summary_view[editor_cols].copy()

edited = st.sidebar.data_editor(
    summary_editor_df,
    use_container_width=True,
    hide_index=True,
    height=380,
    key="token_summary_editor",
    column_config={
        "Pick": st.column_config.CheckboxColumn("Pick", help="Select exactly one token"),
    },
    disabled=["Token", "Price (30D %)", "FDV (30D %)", "Volume 24H (30D %)", "Next Unlock (>2%)"],
)

picked = edited[edited["Pick"] == True]["Token"].tolist()

# Enforce SINGLE selection
if len(picked) == 0:
    picked_token = st.session_state.selected_token
elif len(picked) == 1:
    picked_token = picked[0]
else:
    candidates = [t for t in picked if t != st.session_state.selected_token]
    picked_token = candidates[0] if len(candidates) > 0 else picked[0]

if picked_token != st.session_state.selected_token:
    st.session_state.selected_token = picked_token
    st.rerun()

token = st.session_state.selected_token
d = details[token]

# =======================
# Alerts – unlock & market share
# =======================
unlock_df = d["unlock"].copy()
unlock_big = unlock_df[unlock_df["unlock_pct_of_circ"] > 2.0]
has_unlock_alert = len(unlock_big) > 0
if has_unlock_alert:
    first_unlock = unlock_big.iloc[0]
    unlock_tip = f"Next >2% unlock: {first_unlock['date'].date().isoformat()} ({first_unlock['unlock_pct_of_circ']:.1f}%)"
else:
    unlock_tip = "No >2% unlock in next 12 months (mock)."

share_last, share_chg = last_and_30d_change(d["fund_share"])
has_share_alert = share_chg <= -20.0
share_tip = f"30D change: {share_chg:+.2f}% (alert if ≤ -20%)"

# =======================
# Header row
# =======================
pos = d["position"]

h1, h2, h3, h4, h5 = st.columns([2.2, 1.4, 1.2, 1.6, 1.6])
with h1:
    st.subheader(token)
with h2:
    st.metric("PnL (abs)", f"${pos['pnl_abs']:,.0f}")
with h3:
    st.metric("PnL (%)", f"{pos['pnl_pct']:+.2f}%")
with h4:
    st.metric("Cost basis", f"${pos['cost_basis']:,.4f}")
with h5:
    st.markdown("**Alerts**")
    if has_unlock_alert:
        badge("Unlock >2%", color="red", tooltip=unlock_tip)
    else:
        badge("Unlock OK", color="green", tooltip=unlock_tip)
    st.write("")
    if has_share_alert:
        badge("Share Drop", color="red", tooltip=share_tip)
    else:
        badge("Share OK", color="green", tooltip=share_tip)

st.markdown("---")

# =======================
# Tabs (add Governance & News)
# =======================
tabs = st.tabs(["Overview", "Unlocks", "Fundamentals", "Governance & News"])

# =======================
# Overview
# =======================
with tabs[0]:
    c1, c2, c3 = st.columns(3)

    price_last, price_chg = last_and_30d_change(d["price"])
    fdv_last, fdv_chg = last_and_30d_change(d["fdv"])
    vol_last, vol_chg = last_and_30d_change(d["volume"])
    circ_last, circ_chg = last_and_30d_change(d["circ"])
    burn_last, burn_chg = last_and_30d_change(d["burn"])

    with c1:
        section_metric("Price", f"${price_last:,.4f}", price_chg)
        st.plotly_chart(px.line(d["price"], x="date", y="value"), use_container_width=True, key=f"{token}_price")

    with c2:
        section_metric("FDV", f"${fdv_last/1e9:,.2f}B", fdv_chg)
        st.plotly_chart(px.line(d["fdv"], x="date", y="value"), use_container_width=True, key=f"{token}_fdv")

    with c3:
        section_metric("Trading Volume (24H)", f"${vol_last/1e6:,.1f}M", vol_chg)
        st.plotly_chart(px.area(d["volume"], x="date", y="value"), use_container_width=True, key=f"{token}_volume")

    c4, c5, c6 = st.columns(3)

    with c4:
        section_metric("Circulating Supply", f"{circ_last/1e6:,.1f}M", circ_chg)
        st.plotly_chart(px.line(d["circ"], x="date", y="value"), use_container_width=True, key=f"{token}_circ")

    with c5:
        section_metric("Token Burning", f"{burn_last:,.0f}", burn_chg)
        st.plotly_chart(px.line(d["burn"], x="date", y="value"), use_container_width=True, key=f"{token}_burn")

    with c6:
        st.markdown("**Unlock Alert (12M)**")
        if not has_unlock_alert:
            st.success("No unlocks > 2% (mock).")
        else:
            badge("Unlock >2% detected", color="red", tooltip=unlock_tip)
            st.dataframe(unlock_big.head(6), use_container_width=True, hide_index=True)

# =======================
# Unlocks
# =======================
with tabs[1]:
    st.subheader("Token Unlocking Schedule (Next 12 Months)")
    unlock_df2 = d["unlock"].copy()
    unlock_df2["Alert (>2%)"] = unlock_df2["unlock_pct_of_circ"] > 2.0

    if has_unlock_alert:
        badge("Unlock alert: >2% months exist", color="red", tooltip=unlock_tip)
    else:
        badge("No unlock alert", color="green", tooltip=unlock_tip)

    st.dataframe(unlock_df2, use_container_width=True, hide_index=True)
    st.plotly_chart(px.bar(unlock_df2, x="date", y="unlock_pct_of_circ"), use_container_width=True, key=f"{token}_unlock_bar")

# =======================
# Fundamentals
# =======================
with tabs[2]:
    st.subheader("Fundamentals (mock)")

    fees_last, fees_chg = last_and_30d_change(d["fund_fees"])
    ann_fees = fees_last * 365

    tvl_df = ma_30(d["fund_tvl"])
    tvl_last = float(tvl_df["value"].iloc[-1])
    tvl_ma = float(tvl_df["ma30"].iloc[-1])
    tvl_vs_ma = (tvl_last / tvl_ma - 1) * 100 if tvl_ma else 0.0

    plat_df = ma_30(d["fund_platform_vol"])
    plat_last = float(plat_df["value"].iloc[-1])
    plat_ma = float(plat_df["ma30"].iloc[-1])
    plat_vs_ma = (plat_last / plat_ma - 1) * 100 if plat_ma else 0.0

    mau_last, mau_chg = last_and_30d_change(d["fund_mau"])
    dau_last, dau_chg = last_and_30d_change(d["fund_dau"])

    k1, k2, k3 = st.columns(3)
    with k1:
        section_metric("Revenues / Fees", f"${fees_last:,.0f}/day", fees_chg)
        st.plotly_chart(px.line(d["fund_fees"], x="date", y="value"), use_container_width=True, key=f"{token}_fees")

    with k2:
        section_metric("Annualized Fees", f"${ann_fees/1e6:,.2f}M", fees_chg)
        st.plotly_chart(px.line(d["fund_fees"], x="date", y="value"), use_container_width=True, key=f"{token}_ann_fees")

    with k3:
        section_metric("TVL (vs MA30)", f"${tvl_last/1e9:,.2f}B", tvl_vs_ma)
        st.plotly_chart(px.line(tvl_df, x="date", y="value"), use_container_width=True, key=f"{token}_tvl")

    k4, k5, k6 = st.columns(3)
    with k4:
        section_metric("Platform Trading Volume (vs MA30)", f"${plat_last/1e9:,.2f}B", plat_vs_ma)
        st.plotly_chart(px.line(plat_df, x="date", y="value"), use_container_width=True, key=f"{token}_platform_vol")

    with k5:
        section_metric("MAU", f"{mau_last:,.0f}", mau_chg)
        st.plotly_chart(px.line(d["fund_mau"], x="date", y="value"), use_container_width=True, key=f"{token}_mau")

    with k6:
        section_metric("DAU", f"{dau_last:,.0f}", dau_chg)
        st.plotly_chart(px.line(d["fund_dau"], x="date", y="value"), use_container_width=True, key=f"{token}_dau")

    st.markdown("### Market Share (mock)")
    if has_share_alert:
        badge("Market share dropped >20%", color="red", tooltip=share_tip)
    else:
        badge("Market share stable", color="green", tooltip=share_tip)

    st.markdown(f"Latest: **{share_last*100:.2f}%**  \n30D change: {colored_delta(share_chg)}")
    st.plotly_chart(px.line(d["fund_share"], x="date", y="value"), use_container_width=True, key=f"{token}_market_share")

# =======================
# Governance & News (new tab)
# =======================
with tabs[3]:
    st.subheader("Governance (mock)")
    gov_df = get_mock_governance(token).copy()

    # Ensure datetime formatting
    if "start" in gov_df.columns:
        gov_df["start"] = pd.to_datetime(gov_df["start"])
    if "end" in gov_df.columns:
        gov_df["end"] = pd.to_datetime(gov_df["end"])

    # Highlight logic via badges
    for _, row in gov_df.iterrows():
        cols = st.columns([5, 2, 2, 2, 2])
        with cols[0]:
            st.markdown(f"**{row.get('title','')}**")
        with cols[1]:
            st.write(row.get("type", "-"))
        with cols[2]:
            status = row.get("status", "-")
            impact = row.get("impact", "Low")
            if status == "Active" and impact == "High":
                badge("Active", color="red", tooltip="Active + High impact (mock)")
            elif status == "Active":
                badge("Active", color="blue", tooltip="Active (mock)")
            elif status == "Passed":
                badge("Passed", color="green", tooltip="Passed (mock)")
            else:
                badge(str(status), color="gray", tooltip="Mock")
        with cols[3]:
            st.write(impact)
        with cols[4]:
            s = row.get("start", None)
            e = row.get("end", None)
            if pd.notna(s) and pd.notna(e):
                st.write(f"{s.date()} → {e.date()}")
            else:
                st.write("-")

    st.markdown("---")
    st.subheader("News (mock)")
    news_df = get_mock_news(token).copy()
    if "date" in news_df.columns:
        news_df["date"] = pd.to_datetime(news_df["date"])

    # Simple feed with badges
    for _, row in news_df.sort_values("date", ascending=False).iterrows():
        c1, c2, c3, c4 = st.columns([1.2, 6, 2, 2])
        with c1:
            st.write(row["date"].date().isoformat())
        with c2:
            st.markdown(f"**{row.get('headline','')}**")
        with c3:
            st.write(row.get("source", "-"))
        with c4:
            cat = row.get("category", "Other")
            if cat in ["Security", "Regulation"]:
                badge(cat, color="red", tooltip="Potential downside risk (mock)")
            else:
                badge(cat, color="gray", tooltip="Mock")

st.caption("Mock data only. Next step: wire real governance/news sources (Snapshot, Tally, RSS, CryptoPanic).")
