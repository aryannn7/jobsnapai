# core/session.py
from __future__ import annotations

import streamlit as st


def init_session() -> None:
    defaults = {
        # App state
        "theme": "dark",          # "dark" | "light"
        "view": "Analyze",        # Analyze | Map | Pricing | Changelog

        # Auth
        "authed_email": "",
        "auth_provider": "",      # "email" | "google"

        # Plan state
        "is_pro": False,

        # Analysis cache
        "analysis": None,

        # AI cache (optional)
        "ai_location_strategy": None,

        # Misc UI
        "presentation_mode": "Quick & Direct",
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def is_authed() -> bool:
    email = (st.session_state.get("authed_email") or "").strip().lower()
    return bool(email)


def sign_in(email: str, provider: str = "email") -> None:
    st.session_state["authed_email"] = (email or "").strip().lower()
    st.session_state["auth_provider"] = (provider or "email").strip().lower()


def sign_out() -> None:
    # Keep theme/view (better UX), clear identity + cached outputs
    st.session_state["authed_email"] = ""
    st.session_state["auth_provider"] = ""
    st.session_state["is_pro"] = False
    st.session_state["analysis"] = None
    st.session_state["ai_location_strategy"] = None
    st.rerun()


def clear_analysis() -> None:
    st.session_state["analysis"] = None
    st.session_state["ai_location_strategy"] = None
