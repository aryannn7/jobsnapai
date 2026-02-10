# core/ui_theme.py
from __future__ import annotations


def inject_global_css(theme: str = "light") -> None:
    import streamlit as st

    theme = theme if theme in {"dark", "light"} else "light"

    if theme == "dark":
        bg = "#070A12"
        sidebar_bg = "#0B1220"
        surface = "#0F172A"
        surface2 = "#111C33"
        text = "#EAF0FF"
        muted = "rgba(234,240,255,0.72)"
        border = "rgba(234,240,255,0.14)"
        primary = "#6EA8FF"
        shadow = "0 10px 30px rgba(0,0,0,0.40)"
        shadow_soft = "0 12px 40px rgba(0,0,0,0.35)"
        placeholder = "rgba(234,240,255,0.50)"
        input_bg = "#0B1220"
        input_text = "#EAF0FF"
        button_text = "#FFFFFF"
        sidebar_text = "#EAF0FF"
        sidebar_muted = "rgba(234,240,255,0.70)"

        app_bg = """
          radial-gradient(1200px 650px at 22% 0%, rgba(110,168,255,0.22) 0%, rgba(7,10,18,0) 60%),
          radial-gradient(900px 520px at 85% 12%, rgba(110,168,255,0.12) 0%, rgba(7,10,18,0) 55%),
          radial-gradient(1100px 720px at 55% 115%, rgba(110,168,255,0.08) 0%, rgba(7,10,18,0) 55%),
          linear-gradient(180deg, #070A12 0%, #070A12 100%)
        """
        sidebar_grad = """
          linear-gradient(180deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.00) 35%),
          var(--sidebar-bg)
        """
        hero_grad = """
          linear-gradient(135deg,
            rgba(110,168,255,0.18) 0%,
            rgba(15,23,42,0.92) 62%,
            rgba(15,23,42,0.92) 100%
          )
        """

        disabled_text = "rgba(234,240,255,0.55)"
        disabled_bg = "rgba(255,255,255,0.05)"
        disabled_border = "rgba(234,240,255,0.12)"

    else:
        bg = "#F7F9FF"
        sidebar_bg = "#FFFFFF"
        surface = "rgba(255,255,255,0.86)"
        surface2 = "rgba(255,255,255,0.72)"
        text = "#0B1220"
        muted = "rgba(11,18,32,0.70)"
        border = "rgba(15,23,42,0.12)"
        primary = "#1D4ED8"
        shadow = "0 14px 34px rgba(15,23,42,0.12)"
        shadow_soft = "0 22px 60px rgba(15,23,42,0.12)"
        placeholder = "rgba(11,18,32,0.42)"
        input_bg = "rgba(255,255,255,0.92)"
        input_text = "#0B1220"
        button_text = "#FFFFFF"
        sidebar_text = "#0B1220"
        sidebar_muted = "rgba(11,18,32,0.65)"

        app_bg = """
          radial-gradient(1200px 700px at 18% 0%,
            rgba(29,78,216,0.22) 0%,
            rgba(247,249,255,0) 58%),
          radial-gradient(900px 520px at 85% 12%,
            rgba(99,102,241,0.16) 0%,
            rgba(247,249,255,0) 55%),
          radial-gradient(900px 620px at 55% 115%,
            rgba(29,78,216,0.10) 0%,
            rgba(247,249,255,0) 55%),
          linear-gradient(180deg, #F7F9FF 0%, #F3F6FF 100%)
        """
        sidebar_grad = """
          linear-gradient(180deg,
            rgba(29,78,216,0.08) 0%,
            rgba(99,102,241,0.05) 22%,
            rgba(255,255,255,0.00) 42%),
          var(--sidebar-bg)
        """
        hero_grad = """
          linear-gradient(135deg,
            rgba(29,78,216,0.12) 0%,
            rgba(255,255,255,0.88) 55%,
            rgba(255,255,255,0.88) 100%
          )
        """

        disabled_text = "rgba(11,18,32,0.55)"
        disabled_bg = "rgba(15,23,42,0.06)"
        disabled_border = "rgba(15,23,42,0.14)"

    st.markdown(
        f"""
<style>
:root {{
  --bg: {bg};
  --sidebar-bg: {sidebar_bg};
  --surface: {surface};
  --surface2: {surface2};
  --text: {text};
  --muted: {muted};
  --border: {border};
  --primary: {primary};
  --shadow: {shadow};
  --shadow-soft: {shadow_soft};
  --placeholder: {placeholder};
  --input-bg: {input_bg};
  --input-text: {input_text};
  --button-text: {button_text};
  --sidebar-text: {sidebar_text};
  --sidebar-muted: {sidebar_muted};
  --disabled-text: {disabled_text};
  --disabled-bg: {disabled_bg};
  --disabled-border: {disabled_border};
}}

#MainMenu, footer, header {{ visibility: hidden; }}

.stApp {{
  background: {app_bg};
  color: var(--text);
}}

.stApp:before {{
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(1100px 700px at 50% 60%,
      rgba(0,0,0,0.00) 0%,
      rgba(0,0,0,0.00) 58%,
      rgba(0,0,0,0.05) 100%);
  z-index: 0;
}}

.stApp > div {{
  position: relative;
  z-index: 1;
}}

section[data-testid="stSidebar"] {{
  background: {sidebar_grad} !important;
  border-right: 1px solid var(--border);
}}

section[data-testid="stSidebar"] * {{
  color: var(--sidebar-text) !important;
}}
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] small {{
  color: var(--sidebar-muted) !important;
}}

.block-container {{
  max-width: 1200px;
  padding-top: 1.15rem;
  padding-bottom: 3rem;
}}

.kicker {{
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-size: 0.78rem;
  color: var(--muted);
}}
.muted {{ color: var(--muted); }}
.small {{ font-size: 0.92rem; }}

.hero {{
  padding: 22px 24px;
  border-radius: 18px;
  background: {hero_grad};
  border: 1px solid var(--border);
  box-shadow: var(--shadow-soft);
  margin-bottom: 18px;
  backdrop-filter: blur(10px);
}}

.card {{
  background: var(--surface);
  border-radius: 16px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  padding: 18px 20px;
  margin-bottom: 16px;
  backdrop-filter: blur(10px);
}}

/* Ensure all text inside cards uses theme text color */
.card, .card * {{
  color: var(--text) !important;
}}
.card .muted, .card .muted * {{
  color: var(--muted) !important;
}}

.card-primary {{
  border-color: color-mix(in srgb, var(--primary) 40%, var(--border));
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--primary) 7%, var(--surface)) 0%,
    var(--surface) 72%
  );
}}

.callout {{
  border-left: 4px solid var(--primary);
  padding: 10px 12px;
  background: var(--surface2);
  border-radius: 12px;
  border: 1px solid var(--border);
}}

/* ---------- Inputs ---------- */
div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div {{
  background: var(--input-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  min-height: 44px !important;
  box-shadow: none !important;
}}
div[data-baseweb="textarea"] textarea {{
  background: var(--input-bg) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}}

div[data-baseweb="input"] input {{
  color: var(--input-text) !important;
  -webkit-text-fill-color: var(--input-text) !important;
  caret-color: var(--primary) !important;
}}
div[data-baseweb="textarea"] textarea {{
  color: var(--input-text) !important;
  -webkit-text-fill-color: var(--input-text) !important;
  caret-color: var(--primary) !important;
}}
div[data-baseweb="select"] span {{
  color: var(--input-text) !important;
  -webkit-text-fill-color: var(--input-text) !important;
}}

input::placeholder, textarea::placeholder {{
  color: var(--placeholder) !important;
  opacity: 1 !important;
}}

/* ---------- Radios ---------- */
div[role="radiogroup"] label *,
div[role="radiogroup"] span {{
  color: var(--text) !important;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label *,
section[data-testid="stSidebar"] div[role="radiogroup"] span {{
  color: var(--sidebar-text) !important;
}}

/* ---------- Buttons ---------- */
.stButton > button {{
  border-radius: 12px !important;
  padding: 0.70rem 1rem !important;
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  color: var(--text) !important;
}}

.stButton > button[data-testid="baseButton-primary"] {{
  background: var(--primary) !important;
  color: var(--button-text) !important;
  border-color: color-mix(in srgb, var(--primary) 55%, var(--border)) !important;
  box-shadow: var(--shadow);
}}

.stButton > button:disabled,
.stButton > button[disabled],
.stButton > button[aria-disabled="true"] {{
  background: var(--disabled-bg) !important;
  color: var(--disabled-text) !important;
  -webkit-text-fill-color: var(--disabled-text) !important;
  border-color: var(--disabled-border) !important;
  opacity: 1 !important;
  box-shadow: none !important;
}}

a[data-testid="stLinkButton"] {{
  display: inline-flex !important;
  justify-content: center !important;
  width: 100% !important;
  border-radius: 12px !important;
  padding: 0.70rem 1rem !important;
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  color: var(--text) !important;
  text-decoration: none !important;
}}
a[data-testid="stLinkButton"]:hover {{
  border-color: color-mix(in srgb, var(--primary) 30%, var(--border)) !important;
}}

/* ---------- Metrics ---------- */
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] * {{
  color: var(--muted) !important;
}}
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] * {{
  color: var(--text) !important;
}}
[data-testid="stMetricDelta"],
[data-testid="stMetricDelta"] * {{
  color: var(--muted) !important;
}}

h1, h2, h3 {{ letter-spacing: -0.02em; }}

/* ============================
   File uploader readability
   ============================ */
[data-testid="stFileUploaderDropzone"] {{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
}}
[data-testid="stFileUploaderDropzone"] * {{
  color: var(--text) !important;
}}
[data-testid="stFileUploaderDropzone"] button {{
  background: var(--surface2) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  opacity: 1 !important;
}}
[data-testid="stFileUploaderFileName"],
[data-testid="stFileUploaderFileName"] * {{
  color: var(--text) !important;
}}

/* ============================
   Selectbox/value text
   ============================ */
div[data-baseweb="select"] * {{
  color: var(--input-text) !important;
  -webkit-text-fill-color: var(--input-text) !important;
}}
ul[role="listbox"] * {{
  color: var(--text) !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )
