import streamlit as st

def cached(ttl: int = 600):
    def _wrap(fn):
        return st.cache_data(ttl=ttl, show_spinner=False)(fn)
    return _wrap
