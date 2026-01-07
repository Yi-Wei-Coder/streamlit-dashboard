import streamlit as st

def kpi_row(items):
    cols = st.columns(len(items))
    for col, (label, value, delta) in zip(cols, items):
        with col:
            if delta is None:
                st.metric(label, value)
            else:
                st.metric(label, value, delta)

def section_header(title: str, subtitle: str = ""):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)

def divider():
    st.markdown("---")
