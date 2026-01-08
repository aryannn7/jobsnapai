"""
core/ui_theme.py

Readable, minimal theme.
"""

from __future__ import annotations


def inject_global_css(theme: str = "light") -> None:
    import streamlit as st

    theme = theme if theme in {"dark", "light"} else "light"

    if theme == "dark":
        bg = "#0B0F19"
        sidebar_bg = "#0B0F19"
        surface = "#111827"
        widget = "#0F172A"
        text = "#E5E7EB"
        muted = "rgba(229,231,235,0.70)"
        border = "rgba(255,255,255,0.12)"
        primary = "#4F8EF7"
    else:
        bg = "#F6F7FB"
        sidebar_bg = "#FFFFFF"
        surface = "#FFFFFF"
        widget = "rgba(17,24,39,0.05)"
        text = "#111827"
        muted = "rgba(17,24,39,0.60)"
        border = "rgba(17,24,39,0.12)"
        primary = "#4F8EF7"

    st.markdown(
        f"""
<style>
.stApp {{ background: {bg}; color: {text}; }}
.block-container {{ max-width: 1100px; padding-top: 2rem; }}

h1,h2,h3,h4,h5,h6,p,li,label,span,div {{ color: {text} !important; }}
.muted {{ color: {muted} !important; font-size: 0.95rem; }}

section[data-testid="stSidebar"] > div {{
  background: {sidebar_bg};
  border-right: 1px solid {border};
}}
section[data-testid="stSidebar"] * {{ color: {text} !important; }}

.card {{
  background: {surface};
  border: 1px solid {border};
  border-radius: 16px;
  padding: 18px 20px;
  margin-bottom: 16px;
}}
.card-primary {{ border-color: rgba(79,142,247,0.35); }}

.chip {{
  display:inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid {border};
  margin: 4px 6px 0 0;
  font-size: 0.95rem;
}}
.chip-ok {{ border-color: rgba(34,197,94,0.55); }}
.chip-miss {{ border-color: rgba(239,68,68,0.45); }}

.snippet {{
  background: {widget};
  border: 1px solid {border};
  border-radius: 12px;
  padding: 10px 12px;
  margin: 8px 0;
  color: {text} !important;
  line-height: 1.35;
}}

button[role="tab"] {{ color: {text} !important; }}
button[role="tab"][aria-selected="true"] {{
  color: {primary} !important;
  border-bottom: 2px solid {primary} !important;
}}

div[data-baseweb="textarea"] textarea {{
  background: {widget} !important;
  color: {text} !important;
  border: 1px solid {border} !important;
  border-radius: 12px !important;
}}
div[data-baseweb="select"] > div {{
  background: {widget} !important;
  border: 1px solid {border} !important;
  border-radius: 12px !important;
}}
div[data-baseweb="select"] * {{ color: {text} !important; }}

section[data-testid="stFileUploader"] > div {{
  background: {widget} !important;
  border: 1px solid {border} !important;
  border-radius: 12px !important;
}}
section[data-testid="stFileUploader"] * {{ color: {text} !important; }}

[data-testid="stMetricValue"] {{ color: {text} !important; }}
[data-testid="stMetricLabel"] {{ color: {muted} !important; }}
</style>
""",
        unsafe_allow_html=True,
    )
