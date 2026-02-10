# core/auth_google.py
from __future__ import annotations

import os
import secrets
from typing import Optional, Tuple

import streamlit as st

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


def _get_env(name: str) -> str:
    return (os.getenv(name) or "").strip()


def google_oauth_available() -> bool:
    return bool(_get_env("GOOGLE_CLIENT_ID") and _get_env("GOOGLE_CLIENT_SECRET") and _get_env("GOOGLE_REDIRECT_URI"))


def get_google_authorize_url() -> Tuple[Optional[str], Optional[str]]:
    if not google_oauth_available():
        return None, "Google OAuth is not configured. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI."

    client_id = _get_env("GOOGLE_CLIENT_ID")
    redirect_uri = _get_env("GOOGLE_REDIRECT_URI")

    state = secrets.token_urlsafe(24)
    st.session_state["_google_oauth_state"] = state

    scope = "openid email profile"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
        "include_granted_scopes": "true",
    }

    from urllib.parse import urlencode
    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return url, None


def _get_query_params() -> dict:
    # Support new + old Streamlit APIs
    try:
        qp = dict(st.query_params)  # type: ignore[attr-defined]
        return qp
    except Exception:
        qp = st.experimental_get_query_params()
        # experimental returns list values; normalize to single str
        return {k: (v[0] if isinstance(v, list) and v else v) for k, v in qp.items()}


def _set_query_params_preserve(preserve: dict) -> None:
    # Only keep keys we want (like view/theme)
    try:
        st.query_params.clear()  # type: ignore[attr-defined]
        for k, v in preserve.items():
            if v is None:
                continue
            st.query_params[k] = str(v)  # type: ignore[attr-defined]
    except Exception:
        # experimental expects lists
        cleaned = {k: v for k, v in preserve.items() if v is not None}
        st.experimental_set_query_params(**cleaned)


def try_complete_google_oauth() -> Tuple[Optional[str], Optional[str]]:
    if not google_oauth_available():
        return None, None

    qp = _get_query_params()
    code = qp.get("code")
    state = qp.get("state")

    if not code:
        return None, None

    expected_state = st.session_state.get("_google_oauth_state")
    if not expected_state or not state or state != expected_state:
        return None, "Google login failed (state mismatch). Please try again."

    client_id = _get_env("GOOGLE_CLIENT_ID")
    client_secret = _get_env("GOOGLE_CLIENT_SECRET")
    redirect_uri = _get_env("GOOGLE_REDIRECT_URI")

    try:
        import requests

        token_resp = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
            timeout=12,
        )
        if token_resp.status_code != 200:
            return None, f"Google token exchange failed ({token_resp.status_code})."

        token = token_resp.json().get("access_token")
        if not token:
            return None, "Google token exchange returned no access token."

        user_resp = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=12,
        )
        if user_resp.status_code != 200:
            return None, f"Google userinfo failed ({user_resp.status_code})."

        email = (user_resp.json().get("email") or "").strip().lower()
        if not email:
            return None, "Google userinfo returned no email."

        # Preserve your app routing params; remove oauth params only
        preserve = {}
        for k, v in qp.items():
            if k not in {"code", "state", "scope", "authuser", "prompt"}:
                preserve[k] = v
        _set_query_params_preserve(preserve)

        return email, None

    except Exception as e:
        return None, f"Google login failed: {type(e).__name__}: {e}"
