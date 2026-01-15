import streamlit as st
import pandas as pd

from utils.tokens_mock import generate_token_dataset
from utils.formatting import pct_delta_str

st.set_page_config(page_title="Dashboard Home", layout="wide")

st.title("📊 Crypto Dashboard – Summary")
st.caption("Token overview for quick screening (mock data)")

# =======================
# Generate data
# =======================
seed = st.number_input("Mock seed", min_value=1, max_value=9999, value=42, step=1)
summary, _ = generate_token_dataset(seed=seed)

summary_view = summary.copy()

for col in ["Price (30D %)", "FDV (30D %)", "Volume 24H (30D %)"]:
    summary_view[col] = summary_view[col].apply(pct_delta_str)

# =======================
# Summary Table
# =======================
st.subheader("🪙 Tokens Summary")

st.dataframe(
    summary_view,
    use_container_width=True,
    hide_index=True,
)

st.markdown(
    """
👉 **How to use**
- Go to **Tokens** page to drill down into individual token details  
- This page is for **quick comparison & screening**
"""
)
