import streamlit as st

def pct_delta_str(pct: float) -> str:
    return f"{pct:+.2f}%"

def colored_delta(pct: float) -> str:
    color = "green" if pct >= 0 else "red"
    return f":{color}[{pct_delta_str(pct)}]"

def warn_if(condition: bool, msg: str):
    if condition:
        st.warning(msg)

def badge(text: str, color: str = "gray", tooltip: str | None = None):
    """
    color: red | green | gray | blue
    tooltip: hover text
    """
    bg = {
        "red": "#EF4444",
        "green": "#22C55E",
        "blue": "#3B82F6",
        "gray": "#111827",
    }.get(color, "#111827")

    title_attr = f'title="{tooltip}"' if tooltip else ""
    st.markdown(
        f"""
        <span {title_attr}
              style="display:inline-block;padding:2px 8px;border-radius:999px;
                     background:{bg};color:#fff;font-size:12px;line-height:18px;">
          {text}
        </span>
        """,
        unsafe_allow_html=True
    )
