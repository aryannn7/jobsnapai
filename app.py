# app.py
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import hashlib
import urllib.parse
from typing import Dict, List, Optional, Tuple

import streamlit as st

import core.monetization as monetization
from core.session import init_session, is_authed, sign_in, sign_out, clear_analysis
from core.ui_theme import inject_global_css

from core.config import (
    ENABLE_PAYWALL,
    FREE_RUN_LIMIT_PER_PERIOD,
    AI_RUN_LIMIT_PRO_PER_PERIOD,
    PRO_ACCESS_CODE,
    STRIPE_PAYMENT_LINK,
)

from core.user_store import (
    validate_email,
    get_or_create_user,
    reset_period_if_needed,
    increment_free_run,
    increment_ai_run,
    set_user_pro,
    is_vip_email,
    reset_usage,
)

from core.parsing import parse_resume
from core.cleaning import clean_text
from core.scoring import extract_skills_with_evidence, compute_match
from core.role_paths import get_role_targets
from core.resume_health import resume_health_check
from core.next_move import decide_next_move

from core.auth_google import google_oauth_available, get_google_authorize_url, try_complete_google_oauth
from core.ai_engine import ai_insights_bundle

from core.maps import (
    make_demo_market_points,
    points_to_df,
    resolve_city_center,
    make_view_state,
    tooltip_html,
    CITY_COORDS,
)

# -----------------------------
# Streamlit setup
# -----------------------------
st.set_page_config(page_title="JobSnapAI", layout="wide", page_icon="🧭")
init_session()


# -----------------------------
# Query param helpers
# -----------------------------
def _get_qp(key: str, default: str = "") -> str:
    try:
        v = st.query_params.get(key)  # type: ignore[attr-defined]
        return (v or default)
    except Exception:
        qp = st.experimental_get_query_params()
        return (qp.get(key) or [default])[0]


def _set_qp(**kwargs: str) -> None:
    payload = {k: v for k, v in kwargs.items() if v}
    try:
        st.query_params.clear()  # type: ignore[attr-defined]
        for k, v in payload.items():
            st.query_params[k] = v  # type: ignore[attr-defined]
    except Exception:
        st.experimental_set_query_params(**payload)


def _sync_state_from_url() -> None:
    url_theme = _get_qp("theme", "")
    url_view = _get_qp("view", "")

    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark"
    if "view" not in st.session_state:
        st.session_state["view"] = "Analyze"

    if url_theme in {"dark", "light"}:
        st.session_state["theme"] = url_theme
    if url_view in {"Analyze", "Map", "Pricing", "Changelog"}:
        st.session_state["view"] = url_view


# -----------------------------
# Caching: resume pipeline
# -----------------------------
def _hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


@st.cache_data(show_spinner=False)
def _cached_resume_pipeline(
    filename: str, file_hash: str, file_bytes: bytes
) -> Tuple[Optional[str], str, Dict[str, List[str]], Optional[str]]:
    file_type, raw, perr = parse_resume(filename, file_bytes)
    if perr or not raw:
        return file_type, "", {}, (perr or "Could not extract text from resume.")
    cleaned = clean_text(raw)
    evidence = extract_skills_with_evidence(cleaned)
    return file_type, cleaned, evidence, None


# -----------------------------
# Skill normalization + robust match
# -----------------------------
def _norm(s: str) -> str:
    """
    Meaning:
    - Normalizes skills for matching: lowercase, strip spaces, collapse internal spaces.
    - Prevents 'SQL' vs 'sql' vs 'Sql ' mismatch.
    """
    return " ".join((s or "").strip().lower().split())


def _robust_match_from_sets(resume_skills: List[str], context_skills: List[str]) -> Dict:
    """
    Always returns a stable schema:
    - score: 0..100
    - coverage: 0..1
    - overlap_count
    - matched_skills
    - missing_skills
    """
    resume_norm = {_norm(x): x for x in resume_skills if _norm(x)}
    context_norm = {_norm(x): x for x in context_skills if _norm(x)}

    resume_keys = set(resume_norm.keys())
    context_keys = set(context_norm.keys())

    overlap_keys = sorted(resume_keys & context_keys)
    missing_keys = sorted(context_keys - resume_keys)

    matched = [context_norm[k] for k in overlap_keys]  # show in "context style"
    missing = [context_norm[k] for k in missing_keys]

    denom = max(1, len(context_keys))
    coverage = len(overlap_keys) / denom
    score = int(round(coverage * 100))

    return {
        "score": score,
        "coverage": coverage,
        "overlap_count": len(overlap_keys),
        "matched_skills": matched,
        "missing_skills": missing,
    }


# -----------------------------
# Job Links generator (no APIs)
# -----------------------------
def _role_query(role: str, seniority: str, extra_terms: Optional[List[str]] = None) -> str:
    extra_terms = extra_terms or []
    senior = seniority.strip()
    r = role.strip()
    terms = [senior, r] if senior else [r]
    terms.extend([t for t in extra_terms if t])
    return " ".join(terms).strip()


def _make_job_links(query: str, location: str = "United Kingdom") -> List[Dict[str, str]]:
    q = urllib.parse.quote_plus(query)
    loc = urllib.parse.quote_plus(location)
    return [
        {"label": "LinkedIn Jobs", "url": f"https://www.linkedin.com/jobs/search/?keywords={q}&location={loc}"},
        {"label": "Indeed", "url": f"https://uk.indeed.com/jobs?q={q}&l={loc}"},
        {"label": "Reed", "url": f"https://www.reed.co.uk/jobs?keywords={q}&location={loc}"},
        {"label": "Totaljobs", "url": f"https://www.totaljobs.com/jobs?Keywords={q}&Location={loc}"},
        {"label": "Glassdoor", "url": f"https://www.glassdoor.co.uk/Job/jobs.htm?sc.keyword={q}"},
        {"label": "Google Jobs", "url": f"https://www.google.com/search?q={q}+jobs+in+{loc}"},
    ]


# -----------------------------
# UI helpers
# -----------------------------
def page_header(kicker: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="hero">
            <div class="kicker">{kicker}</div>
            <h1 style="margin: 0.35rem 0 0.45rem 0;">{title}</h1>
            <div class="muted">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Auth page
# -----------------------------
def render_auth_page() -> None:
    # Apply CSS early so auth page is themed
    inject_global_css(st.session_state.get("theme", "dark"))

    # Complete Google OAuth if callback is present
    email_from_google, gerr = try_complete_google_oauth()
    if gerr:
        st.error(gerr)
    if email_from_google:
        user = reset_period_if_needed(get_or_create_user(email_from_google))
        sign_in(email_from_google, "google")
        st.session_state["is_pro"] = bool(user.is_pro) if user else False
        st.session_state["view"] = "Analyze"
        _set_qp(view="Analyze", theme=st.session_state.get("theme", "dark"))
        st.rerun()

    c1, c2, c3 = st.columns([2, 2, 1])
    with c3:
        theme = st.radio(
            "Theme",
            ["dark", "light"],
            index=0 if st.session_state.get("theme") == "dark" else 1,
            horizontal=True,
            label_visibility="collapsed",
            key="theme_auth_radio",
        )
        if theme != st.session_state.get("theme"):
            st.session_state["theme"] = theme
            _set_qp(view=_get_qp("view", "Analyze") or "Analyze", theme=theme)
            st.rerun()

    left, right = st.columns([1.25, 1.0], gap="large")

    with left:
        page_header(
            "JobSnapAI",
            "Career clarity that feels obvious.",
            "Evidence-first diagnostics. Pro adds recruiter-style screening feedback + one-click AI plan.",
        )

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Free")
        st.write("- Evidence-backed skill detection (no black box).")
        st.write("- Match score vs a role or job description.")
        st.write("- Missing skills + one best next action.")
        st.write("- Job application links tailored to your gaps.")
        st.write(f"- {FREE_RUN_LIMIT_PER_PERIOD} analyses / month.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card card-primary'>", unsafe_allow_html=True)
        st.subheader("Pro")
        st.write("- Pro AI Insights: blockers + recruiter-style reasons + fixes.")
        st.write("- 7-day plan based on missing skills + resume health issues.")
        st.write("- AI Location Strategy (where to apply + why).")
        if STRIPE_PAYMENT_LINK:
            st.link_button("View Pro pricing", STRIPE_PAYMENT_LINK, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card card-primary'>", unsafe_allow_html=True)
        st.subheader("Sign in to start")

        if google_oauth_available():
            url, err = get_google_authorize_url()
            if err:
                st.warning(err)
            else:
                st.link_button("Continue with Google", url, use_container_width=True)
                st.caption("Stores email for usage tracking + Pro status only.")
                st.markdown("<hr/>", unsafe_allow_html=True)

        st.markdown("**Or continue with email**")

        # Persist the email value across reruns (theme toggle, rerun, etc.)
        default_email = st.session_state.get("auth_email_entry", "")

        email = st.text_input(
            "Email",
            placeholder="name@email.com",
            key="auth_email_entry",
            value=default_email,
            label_visibility="collapsed",
        ).strip().lower()

        if st.button(
            "Continue",
            key="auth_continue_btn",
            type="primary",
            use_container_width=True,
            disabled=not validate_email(email),
        ):
            user = reset_period_if_needed(get_or_create_user(email))
            sign_in(email, "email")
            st.session_state["is_pro"] = bool(user.is_pro) if user else False
            st.session_state["view"] = "Analyze"
            _set_qp(view="Analyze", theme=st.session_state.get("theme", "dark"))
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Sidebar
# -----------------------------
def render_sidebar(email: str) -> None:
    with st.sidebar:
        st.markdown("<div class='kicker'>JobSnapAI</div>", unsafe_allow_html=True)
        st.markdown("<div class='muted small'>Decision-first career intelligence.</div>", unsafe_allow_html=True)
        st.divider()

        st.subheader("Theme")
        theme = st.radio(
            "Theme",
            ["dark", "light"],
            index=0 if st.session_state.get("theme") == "dark" else 1,
            horizontal=True,
            label_visibility="collapsed",
            key="theme_sidebar_radio",
        )
        if theme != st.session_state.get("theme"):
            st.session_state["theme"] = theme
            inject_global_css(theme)
            _set_qp(view=st.session_state.get("view", "Analyze"), theme=theme)
            st.rerun()

        st.divider()

        st.subheader("Account")
        provider = st.session_state.get("auth_provider") or "email"
        st.markdown(
            f"<div class='callout'><b>Signed in:</b><br/>{email}<br/><span class='muted small'>via {provider}</span></div>",
            unsafe_allow_html=True,
        )
        if st.button("Sign out", key="sidebar_signout_btn", use_container_width=True):
            sign_out()

        user = reset_period_if_needed(get_or_create_user(email))
        st.session_state["is_pro"] = bool(user.is_pro) if user else False

        st.markdown(
            f"<div><b>Status:</b> {monetization.pro_badge(st.session_state['is_pro'])}</div>",
            unsafe_allow_html=True,
        )

        if user:
            st.caption(
                f"Usage: Free {user.free_runs_used}/{FREE_RUN_LIMIT_PER_PERIOD} • "
                f"AI {user.ai_runs_used}/{AI_RUN_LIMIT_PRO_PER_PERIOD}"
            )

        if is_vip_email(email):
            st.divider()
            st.subheader("Admin tools")
            if st.button("Reset my usage counters", key="admin_reset_usage_btn", use_container_width=True):
                reset_usage(email)
                st.success("Usage counters reset.")
                st.rerun()

        if ENABLE_PAYWALL and (not st.session_state.get("is_pro", False)) and PRO_ACCESS_CODE:
            with st.expander("Have an access code?"):
                code = st.text_input("Access code", type="password", key="pro_access_code_input")
                if st.button("Unlock Pro", key="unlock_pro_btn", use_container_width=True):
                    if code.strip() == PRO_ACCESS_CODE:
                        set_user_pro(email, True)
                        st.session_state["is_pro"] = True
                        st.success("Pro unlocked.")
                        st.rerun()
                    else:
                        st.error("Invalid code.")

        st.divider()

        prev_view = st.session_state.get("view", "Analyze")
        monetization.top_nav()  # expected to update st.session_state["view"]
        new_view = st.session_state.get("view", "Analyze")
        if new_view != prev_view:
            _set_qp(view=new_view, theme=st.session_state.get("theme", "dark"))
            st.rerun()


# -----------------------------
# Analyze helpers
# -----------------------------
def _parse_role_context(mode: str, target_role: str, seniority: str, job_text: str) -> List[str]:
    if mode == "With Job Description" and job_text.strip():
        job_evidence = extract_skills_with_evidence(job_text.strip())
        return sorted(list(job_evidence.keys()))
    return sorted(list(set(get_role_targets(target_role, seniority=seniority))))


def _render_analysis_details(analysis: dict) -> None:
    match = analysis.get("match", {}) or {}
    evidence: Dict[str, List[str]] = analysis.get("evidence", {}) or {}
    health = analysis.get("health", {}) or {}

    score = match.get("score")
    overlap = match.get("overlap_count")
    coverage = match.get("coverage")
    missing = match.get("missing_skills", []) or []
    matched = match.get("matched_skills", []) or []
    next_move = analysis.get("next_move")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Match score")
        st.metric("Score", f"{score} / 100" if isinstance(score, int) else str(score))
        if isinstance(coverage, (int, float)):
            st.caption(f"Deterministic %: {round(coverage * 100, 2)}%")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Coverage")
        if isinstance(coverage, (int, float)):
            st.metric("Coverage", f"{int(round(coverage * 100))}%")
        else:
            st.metric("Coverage", "—")
        if isinstance(overlap, int):
            st.caption(f"Overlapping skills: {overlap}")
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Next move")
        if isinstance(next_move, dict):
            st.write(next_move.get("title", "") or next_move.get("action", "") or "—")
            st.caption(next_move.get("reason", "") or next_move.get("why", ""))
        else:
            st.write(str(next_move) if next_move else "—")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Missing skills (priority)")
    if not missing:
        st.success("No missing skills detected for this target context.")
    else:
        for sk in missing[:30]:
            st.write(f"- {sk}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Matched skills (with evidence)")
    if not matched:
        st.info("Matched skills are empty — usually caused by skill name mismatch.")
    else:
        evidence_norm = {_norm(k): v for k, v in evidence.items()}
        for sk in matched[:20]:
            snippets = evidence_norm.get(_norm(sk), [])
            with st.expander(f"{sk}  ({len(snippets)} evidence windows)", expanded=False):
                if not snippets:
                    st.write("No evidence windows found.")
                else:
                    for s in snippets[:6]:
                        st.write(f"- {s}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Resume health checks")
    if not health:
        st.write("No health checks returned.")
    else:
        for k, v in health.items():
            st.write(f"**{k}:** {v}")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_job_links(analysis: dict) -> None:
    target_role = analysis.get("target_role", "Data Analyst")
    seniority = analysis.get("seniority", "Junior")
    missing = (analysis.get("match", {}) or {}).get("missing_skills", []) or []

    st.markdown("<div class='card card-primary'>", unsafe_allow_html=True)
    st.subheader("Apply now (job links)")
    st.caption("Real job boards. Use missing skills to sharpen your search query.")

    location = st.selectbox(
        "Location for searches",
        ["United Kingdom", "London", "Manchester", "Birmingham", "Leeds", "Edinburgh", "Glasgow", "Bristol"],
        index=0,
        key="joblinks_location_select",
    )

    top_missing = missing[:8]
    use_missing = st.multiselect(
        "Add missing skills to your search query (optional)",
        options=top_missing,
        default=top_missing[:3] if top_missing else [],
        key="joblinks_missing_multiselect",
    )

    query = _role_query(target_role, seniority, extra_terms=use_missing)
    st.write(f"**Search query:** {query}")

    links = _make_job_links(query=query, location=location)
    cols = st.columns(3)
    for i, item in enumerate(links):
        with cols[i % 3]:
            st.link_button(item["label"], item["url"], use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _render_pro_ai(email: str, analysis: dict) -> None:
    st.markdown("<div class='card card-primary'>", unsafe_allow_html=True)
    st.subheader("Pro AI Insights")
    st.write("- Recruiter-style blockers and fixes")
    st.write("- A 7-day plan tailored to your missing skills and resume signals")
    st.write("- Optional: location strategy is on the Map page")

    allowed = monetization.require_pro_or_preview(
        "Pro AI Insights",
        "Preview: You'll get (1) biggest blocker, (2) recruiter screening reasons, (3) a step-by-step 7-day plan.",
    )
    if not allowed:
        st.markdown("</div>", unsafe_allow_html=True)
        return

    user = reset_period_if_needed(get_or_create_user(email))
    st.session_state["is_pro"] = bool(user.is_pro) if user else False

    if user and user.ai_runs_used >= AI_RUN_LIMIT_PRO_PER_PERIOD:
        st.warning("You have reached your Pro AI limit for this month.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    target_role = analysis.get("target_role", "")
    seniority = analysis.get("seniority", "")
    missing = (analysis.get("match", {}) or {}).get("missing_skills", []) or []
    health = analysis.get("health", {}) or {}

    context = [
        f"Target: {target_role} ({seniority})",
        f"Missing skills (top): {missing[:12]}",
        f"Resume health signals: {health}",
        "Goal: increase interview conversion in 14 days, with actions realistic for student/early-career candidate.",
    ]

    if st.button("Run Pro AI Insights", key="run_pro_ai_btn", type="primary", use_container_width=True):
        data, err = ai_insights_bundle(
            role=f"{target_role} ({seniority})",
            focus_skill="Interview conversion + gap closure",
            context_skills=context,
            mode="quick",
        )
        if err:
            st.error(err)
        else:
            if user:
                increment_ai_run(user)
            st.session_state["pro_ai_bundle"] = data
            st.success("Pro AI insights generated.")

    data = st.session_state.get("pro_ai_bundle")
    if data:
        st.markdown("### Output")
        st.write("**Role reality:**")
        for b in (data.get("role_reality", []) or [])[:7]:
            st.write(f"- {b}")
        st.write("**Main blocker:**")
        st.write(data.get("blocker", "") or "—")
        st.write("**Plan (7 days):**")
        for d in (data.get("plan", []) or [])[:7]:
            st.write(f"- {d}")

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Analyze page
# -----------------------------
def render_analyze(email: str) -> None:
    page_header(
        "Analyze",
        "Know exactly what to do next in your career",
        "Upload your resume → pick a target → get evidence-backed results + application links.",
    )

    user = reset_period_if_needed(get_or_create_user(email))
    st.session_state["is_pro"] = bool(user.is_pro) if user else False

    left, right = st.columns([1.15, 0.85], gap="large")

    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Upload and target")

        uploaded = st.file_uploader("PDF or DOCX", type=["pdf", "docx"], key="resume_uploader")

        target_role = st.selectbox(
            "Target role",
            ["Data Analyst", "Business Analyst", "Data Engineer", "Analytics Engineer", "ML Engineer"],
            index=0,
            key="target_role_select",
        )
        seniority = st.selectbox("Seniority", ["Junior", "Mid", "Senior"], index=0, key="seniority_select")

        mode = st.radio(
            "Context",
            ["Role Targets", "With Job Description"],
            horizontal=True,
            key="context_radio",
        )
        job_text = (
            st.text_area("Paste job description (optional)", height=140, key="job_desc_textarea")
            if mode == "With Job Description"
            else ""
        )

        run = st.button(
            "Run analysis",
            key="run_analysis_btn",
            type="primary",
            use_container_width=True,
            disabled=(uploaded is None),
        )

        if run and uploaded is not None:
            if (not is_vip_email(email)) and user and (user.free_runs_used >= FREE_RUN_LIMIT_PER_PERIOD):
                st.warning("You have used your free analyses for this month.")
                monetization.upgrade_cta(compact=False)
                st.info("Tip: Upgrade to Pro for more usage, or come back next month.")
                st.markdown("</div>", unsafe_allow_html=True)
                return

            file_bytes = uploaded.getvalue()
            file_hash = _hash_bytes(file_bytes)

            _, cleaned, evidence, err = _cached_resume_pipeline(uploaded.name, file_hash, file_bytes)
            if err or not cleaned:
                st.error(err or "Could not extract text from resume.")
                st.stop()

            resume_skills = sorted(list(evidence.keys()))
            context_skills = _parse_role_context(mode, target_role, seniority, job_text)

            raw_match = compute_match(set(resume_skills), set(context_skills)) or {}
            robust = _robust_match_from_sets(resume_skills, context_skills)
            match = {**raw_match, **robust}

            health = resume_health_check(cleaned)
            missing = match.get("missing_skills", []) or []
            next_move = decide_next_move(missing)

            st.session_state["analysis"] = {
                "target_role": target_role,
                "seniority": seniority,
                "resume_filename": uploaded.name,
                "evidence": evidence,
                "resume_skills": resume_skills,
                "context_skills": context_skills,
                "match": match,
                "health": health,
                "next_move": next_move,
            }

            if user:
                increment_free_run(user)

            st.success("Analysis complete.")
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Why this is trustworthy")
        st.write("- Parsing and skill extraction are deterministic.")
        st.write("- Skills are backed by evidence windows from your resume.")
        st.write("- Pro AI is optional and generates action plans (one click = one run).")
        st.markdown("</div>", unsafe_allow_html=True)

    analysis = st.session_state.get("analysis")
    if not analysis:
        return

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Results")
    st.write(f"Resume: **{analysis['resume_filename']}**")
    st.write(f"Target: **{analysis['target_role']} ({analysis['seniority']})**")

    if st.button("Clear and run again", key="clear_and_rerun_btn"):
        clear_analysis()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    _render_analysis_details(analysis)
    _render_job_links(analysis)
    _render_pro_ai(email, analysis)


# -----------------------------
# Map page
# -----------------------------
def render_map(email: str) -> None:
    import pydeck as pdk

    page_header(
        "Map",
        "Plan where to apply",
        "Use a market map to prioritize cities. Pro adds AI Location Strategy.",
    )

    if "saved_targets" not in st.session_state:
        st.session_state["saved_targets"] = []

    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Market map")

        role = st.selectbox(
            "Target role (map)",
            ["Data Analyst", "Business Analyst", "Data Engineer", "Analytics Engineer", "ML Engineer"],
            index=0,
            key="map_role_select",
        )

        city_options = sorted({c.title() for c in CITY_COORDS.keys() if len(c) > 2})
        base_city = st.selectbox(
            "Base city",
            city_options,
            index=city_options.index("London") if "London" in city_options else 0,
            key="map_base_city_select",
        )

        points = make_demo_market_points(role=role, base_city=base_city)
        df = points_to_df(points)

        center_lat, center_lon = resolve_city_center(base_city)
        view_state = make_view_state(center_lat, center_lon, zoom=5.2)

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position="[lon, lat]",
            get_radius="(score * 1400) + 9000",
            get_fill_color="[29, 78, 216, 120]",
            pickable=True,
        )

        deck = pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(**view_state),
            layers=[layer],
            tooltip=tooltip_html(),
        )

        st.pydeck_chart(deck, use_container_width=True)
        st.caption("MVP note: market scores are heuristic. Next: plug real job-volume data.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Save target cities")
        st.caption("Build a short list. This will later feed your application plan + recruiter simulator.")

        pick = st.selectbox("Add city", sorted({p.name for p in points}), key="save_city_select")
        note = st.text_input("Note (optional)", placeholder="e.g., prioritize fintech roles", key="save_note_input")

        if st.button("Save city", key="save_city_btn", use_container_width=True):
            st.session_state["saved_targets"].append({"city": pick, "note": note.strip()})
            st.success("Saved.")

        if st.session_state["saved_targets"]:
            st.write("Saved targets:")
            for i, t in enumerate(st.session_state["saved_targets"], start=1):
                st.write(f"{i}. **{t['city']}** — {t.get('note','')}")
        else:
            st.info("No saved cities yet.")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card card-primary'>", unsafe_allow_html=True)
        st.subheader("AI Location Strategy (Pro)")

        allowed = monetization.require_pro_or_preview(
            "AI Location Strategy",
            "Get a ranked list of cities to focus on, with a short rationale and a 2-week action plan.",
        )
        if allowed:
            user = reset_period_if_needed(get_or_create_user(email))
            st.session_state["is_pro"] = bool(user.is_pro) if user else False

            if user and user.ai_runs_used >= AI_RUN_LIMIT_PRO_PER_PERIOD:
                st.warning("You have reached your Pro AI limit for this month.")
            else:
                if st.button("Generate strategy", key="gen_location_strategy_btn", type="primary", use_container_width=True):
                    saved = st.session_state.get("saved_targets", [])
                    saved_text = [f"{x['city']} ({x.get('note','')})" for x in saved][:12]

                    context = [
                        f"Base city: {base_city}",
                        f"Target role: {role}",
                        f"Saved targets: {saved_text}",
                        "Goal: maximize interviews in 30 days with a realistic plan.",
                    ]

                    data, err = ai_insights_bundle(
                        role=f"{role} — Location Strategy",
                        focus_skill="Application targeting by geography",
                        context_skills=context,
                        mode="quick",
                    )
                    if err:
                        st.error(err)
                    else:
                        if user:
                            increment_ai_run(user)
                        st.session_state["ai_location_strategy"] = data
                        st.success("Done.")

        data = st.session_state.get("ai_location_strategy")
        if data:
            st.markdown("### Strategy output")
            st.write("**Top reasons:**")
            for b in data.get("role_reality", [])[:5]:
                st.write(f"- {b}")
            st.write("**Main blocker:**")
            st.write(data.get("blocker", ""))
            st.write("**7-day plan:**")
            for d in data.get("plan", [])[:7]:
                st.write(f"- {d}")

        st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Pricing / Changelog
# -----------------------------
def render_pricing() -> None:
    page_header("Pricing", "Upgrade when you want deeper clarity", "Free gives deterministic diagnostics. Pro adds one-click AI.")
    c1, c2 = st.columns([1, 1], gap="large")

    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Free — basics that work")
        st.write("- Skill detection + evidence snippets")
        st.write("- Match score + missing skills")
        st.write("- Job application links")
        st.write(f"- {FREE_RUN_LIMIT_PER_PERIOD} full analyses / month")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='card card-primary'>", unsafe_allow_html=True)
        st.subheader("Pro — increase interview conversion")
        st.write("- Pro AI Insights (blockers + fixes + 7-day plan)")
        st.write("- AI Location Strategy")
        st.write(f"- Up to {AI_RUN_LIMIT_PRO_PER_PERIOD} AI runs / month (capped)")
        monetization.upgrade_cta(compact=True)
        st.markdown("</div>", unsafe_allow_html=True)


def render_changelog() -> None:
    page_header("Changelog", "What’s new", "A quick log of features and fixes.")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.write("- Added robust matching (prevents null scores).")
    st.write("- Added Apply Now job links.")
    st.write("- Added Pro AI Insights on Analyze page.")
    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Main router
# -----------------------------
def render_main() -> None:
    email = (st.session_state.get("authed_email") or "").strip().lower()

    # If session lost, go back to auth page
    if not validate_email(email):
        sign_out()
        return

    inject_global_css(st.session_state.get("theme", "dark"))
    render_sidebar(email)

    view = st.session_state.get("view", "Analyze")
    if view == "Pricing":
        render_pricing()
    elif view == "Changelog":
        render_changelog()
    elif view == "Map":
        render_map(email)
    else:
        render_analyze(email)


# -----------------------------
# Bootstrap
# -----------------------------
_sync_state_from_url()
inject_global_css(st.session_state.get("theme", "dark"))

if not is_authed():
    render_auth_page()
else:
    render_main()
