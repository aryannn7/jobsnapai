# core/monetization.py
from __future__ import annotations

import streamlit as st
from core.config import ENABLE_PAYWALL, STRIPE_PAYMENT_LINK


def top_nav() -> None:
    """
    Uses st.session_state["view"] as single source of truth.

    WHY:
    - Streamlit reruns the script on every interaction.
    - session_state is the stable place to store "where the user is" (Analyze/Map/etc).
    """

    current = st.session_state.get("view", "Analyze")
    options = ["Analyze", "Map", "Pricing", "Changelog"]
    if current not in options:
        current = "Analyze"

    # IMPORTANT FIX:
    # label must not be empty ("") even if label_visibility is collapsed.
    chosen = st.radio(
        "Top navigation",              # non-empty label for accessibility
        options,
        index=options.index(current),
        horizontal=True,
        label_visibility="collapsed",  # hides it visually
        key="topnav",                  # stable widget identity across reruns
    )
    st.session_state["view"] = chosen


def pro_badge(is_pro: bool) -> str:
    if is_pro:
        return "<span style='padding:4px 10px;border-radius:999px;border:1px solid rgba(255,255,255,0.18);'>PRO</span>"
    return "<span style='padding:4px 10px;border-radius:999px;border:1px solid rgba(15,23,42,0.18);'>FREE</span>"


def upgrade_cta(compact: bool = True) -> None:
    """
    Standard CTA used across pages.
    """
    if not ENABLE_PAYWALL:
        st.info("Paywall disabled (dev).")
        return

    if STRIPE_PAYMENT_LINK:
        label = "Upgrade to Pro" if compact else "Upgrade to Pro (unlock recruiter simulator + AI plan)"
        st.link_button(label, STRIPE_PAYMENT_LINK, use_container_width=True)
        if "/test_" in STRIPE_PAYMENT_LINK:
            st.caption("Stripe is in TEST mode (no real money).")
    else:
        st.warning("STRIPE_PAYMENT_LINK not set.")


def require_pro_or_preview(feature_name: str, preview_text: str) -> bool:
    """
    If Pro: return True (feature allowed).
    If Free: show preview + upgrade CTA, return False.
    """
    if (not ENABLE_PAYWALL) or st.session_state.get("is_pro"):
        return True

    st.markdown("<div class='callout'>", unsafe_allow_html=True)
    st.markdown(f"**{feature_name} is Pro**")
    st.write(preview_text)
    upgrade_cta(compact=True)
    st.markdown("</div>", unsafe_allow_html=True)
    return False
