from __future__ import annotations

import os
import time
from typing import List

import streamlit as st

from core.cleaning import clean_text
from core.parsing import parse_resume
from core.progress import load_progress, save_progress, mark_done
from core.resume_health import resume_health_check
from core.role_paths import get_role_targets
from core.scoring import extract_skills_with_evidence, compute_match
from core.next_move import decide_next_move
from core.ai_engine import ai_role_reality_check, ai_blocker_explanation, ai_7_day_plan

from core.monetization import require_pro_or_preview
from core.session import clear_results
from core.config import STRIPE_PAYMENT_LINK, ENABLE_PAYWALL


def safe_ai_tuple(x):
    if x is None:
        return None, "AI function returned None (check core/ai_engine.py)."
    if isinstance(x, tuple) and len(x) == 2:
        return x
    return x, None


def pricing_view():
    st.title("Pricing")
    st.markdown(
        "<div class='muted'>One clear next step by default — deeper explainability when you want it.</div>",
        unsafe_allow_html=True,
    )
    st.divider()

    c1, c2 = st.columns([1, 1], gap="large")

    with c1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Free")
        st.write("For quick direction.")
        st.markdown("- Deterministic skill extraction + evidence")
        st.markdown("- Role readiness or JD match")
        st.markdown("- One recommended next move")
        st.markdown("- Basic resume health checks")
        st.button("Current plan", disabled=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='card card-primary'>", unsafe_allow_html=True)
        st.subheader("Pro — £9.99/mo")
        st.write("For faster iteration and higher confidence.")
        st.markdown("- Detailed explainability mode")
        st.markdown("- AI Insights (optional reasoning layer)")
        st.markdown("- PDF export (coming next)")
        st.markdown("- History (coming next)")
        st.markdown("—")
        if STRIPE_PAYMENT_LINK:
            st.link_button("Upgrade with Stripe", STRIPE_PAYMENT_LINK, use_container_width=True)
        else:
            st.info("Set STRIPE_PAYMENT_LINK in your .env for checkout.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    with st.expander("FAQ"):
        st.write("**Is my resume stored?**")
        st.write("Right now: no. It is processed in-session. History will be opt-in for Pro.")
        st.write("**What happens after payment?**")
        st.write("Currently: Pro is unlocked using an access code. Next: automatic unlock via Stripe webhook + login.")


def changelog_view():
    st.title("Changelog")
    st.markdown("<div class='muted'>Keep this short and real. Hiring managers love it.</div>", unsafe_allow_html=True)
    st.divider()

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("v0.3")
    st.write("- Reduced clutter: upgrade prompts now appear only inside Pro features")
    st.write("- Added one-time Pro Preview gating")
    st.write("- Refactored app.py into modular views + monetization + session management")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("v0.2")
    st.write("- Added Analyze/Pricing/Changelog navigation")
    st.write("- Added Pro gating + Stripe payment link surface")
    st.write("- Added presentation modes (Quick/Supportive/Detailed)")
    st.write("- Gated AI Insights + Detailed mode behind Pro")
    st.markdown("</div>", unsafe_allow_html=True)


def render_next_move_card(next_move: dict, progress):
    mode = st.session_state.presentation_mode

    st.markdown("<div class='card card-primary'>", unsafe_allow_html=True)
    st.subheader("Your One Next Move")
    st.markdown(f"**Focus skill:** {next_move['skill']}")
    st.markdown(f"**What to do ({next_move['time']}):**")
    st.write(next_move["action"])

    if mode == "Quick & Direct":
        st.caption("Want the reasoning? Switch to Supportive or Detailed.")
    elif mode == "Supportive":
        with st.expander("Why this matters (optional)"):
            st.write(next_move["why"])
    else:
        # Detailed is Pro preview gated at selection time
        st.markdown("**Why this matters:**")
        st.write(next_move["why"])

    c1, c2 = st.columns([1, 1])
    with c1:
        st.metric("Current streak", f"{progress.streak} day(s)")
    with c2:
        if st.button("Mark as done"):
            progress = mark_done(progress, next_move["skill"], next_move["action"])
            save_progress(progress)
            st.success("Saved. Come back tomorrow.")
            clear_results()
    st.markdown("</div>", unsafe_allow_html=True)


def analyze_view():
    # ----------------------------
    # Inputs
    # ----------------------------
    col1, col2 = st.columns([2, 1])

    with col1:
        target_role = st.selectbox(
            "Target role",
            ["Data Analyst", "Data Engineer", "Analytics Engineer", "Business Analyst", "Machine Learning Engineer"],
            index=0,
        )

    with col2:
        seniority = st.selectbox("Seniority", ["Entry", "Mid", "Senior"], index=1)

    mode = st.radio(
        "Mode",
        ["With Job Description", "Without Job Description (role readiness)"],
        index=0,
    )

    resume_file = st.file_uploader("Upload resume (PDF or DOCX)", type=["pdf", "docx"])

    job_description = ""
    if mode == "With Job Description":
        job_description = st.text_area("Paste job description", height=200)

    # Output style (keep minimal; Pro gating happens cleanly)
    with st.expander("Output style", expanded=False):
        selected_mode = st.radio(
            "How would you like results presented?",
            ["Quick & Direct", "Supportive", "Detailed"],
            horizontal=True,
            key="presentation_mode_ui",
        )
        st.session_state.presentation_mode = selected_mode

        # Pro Preview gate only triggers when they explicitly choose Detailed
        if selected_mode == "Detailed":
            require_pro_or_preview("Detailed mode")

    # AI toggle: keep quiet unless user chooses it
    use_ai = st.toggle("Use AI for reasoning (Pro)", value=False)
    if use_ai:
        require_pro_or_preview("AI Insights")  # uses the same preview token
    st.caption("AI is optional. Deterministic extraction stays the source of truth.")

    btnA, btnB = st.columns([1, 1])
    with btnA:
        analyze_clicked = st.button("Analyze", type="primary")
    with btnB:
        if st.button("Clear results"):
            clear_results()

    # ----------------------------
    # Analyze
    # ----------------------------
    if analyze_clicked:
        if not resume_file:
            st.error("Please upload a resume.")
            st.stop()

        if mode == "With Job Description" and not job_description.strip():
            st.error("Please paste a job description or switch mode.")
            st.stop()

        status_box = st.empty()

        def thinking(message: str, cycles: int = 2, delay: float = 0.25):
            for _ in range(cycles):
                for dots in [".", "..", "..."]:
                    status_box.markdown(
                        f"""
                        <div class="card">
                            <strong>{message}{dots}</strong>
                            <div class="muted">Please wait while we analyze your profile.</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    time.sleep(delay)

        thinking("Parsing resume", cycles=1)
        _, raw_text = parse_resume(resume_file.name, resume_file.getvalue())
        resume_text = clean_text(raw_text)

        thinking("Extracting skills and validating evidence", cycles=1)
        resume_evidence = extract_skills_with_evidence(resume_text, max_snippets_per_skill=2)
        resume_skills = set(resume_evidence.keys())

        thinking("Evaluating role readiness and skill gaps", cycles=1)
        role_targets = get_role_targets(target_role, seniority=seniority)
        covered_role = sorted(set(role_targets).intersection(resume_skills))
        missing_role = sorted(set(role_targets).difference(resume_skills))

        result = None
        job_skills: List[str] = []
        if mode == "With Job Description":
            job_evidence = extract_skills_with_evidence(job_description, max_snippets_per_skill=1)
            job_skills = sorted(list(job_evidence.keys()))
            result = compute_match(resume_skills, set(job_skills))

        thinking("Identifying the most impactful next step", cycles=1)
        if mode == "With Job Description" and result is not None:
            next_move = decide_next_move(result["missing_skills"])
        else:
            next_move = decide_next_move(missing_role)

        health = resume_health_check(resume_text)
        progress = load_progress()

        status_box.empty()

        st.session_state["analysis"] = {
            "mode": mode,
            "target_role": target_role,
            "seniority": seniority,
            "resume_text": resume_text,
            "resume_evidence": resume_evidence,
            "resume_skills": sorted(list(resume_skills)),
            "job_skills": job_skills,
            "result": result,
            "role_targets": role_targets,
            "covered_role": covered_role,
            "missing_role": missing_role,
            "next_move": next_move,
            "health": health,
            "progress": progress,
            "use_ai": use_ai,
            "presentation_mode": st.session_state.presentation_mode,
        }
        st.rerun()

    # ----------------------------
    # Render
    # ----------------------------
    analysis = st.session_state.get("analysis")
    if not analysis:
        st.stop()

    mode = analysis["mode"]
    target_role = analysis["target_role"]
    seniority = analysis["seniority"]
    resume_evidence = analysis["resume_evidence"]
    result = analysis["result"]
    job_skills = analysis["job_skills"]
    covered_role = analysis["covered_role"]
    missing_role = analysis["missing_role"]
    next_move = analysis["next_move"]
    health = analysis["health"]
    progress = analysis["progress"]
    use_ai = analysis["use_ai"]

    st.session_state.presentation_mode = analysis.get("presentation_mode", st.session_state.presentation_mode)

    st.divider()
    st.subheader("Your Result")

    if mode == "With Job Description" and result is not None:
        st.metric("Job Match", f"{result['match_percentage']}%")
        st.progress(min(int(result["match_percentage"]), 100))
        st.markdown("<div class='muted'>Match = matched skills / job skills (deterministic).</div>", unsafe_allow_html=True)
    else:
        total = max(len(covered_role) + len(missing_role), 1)
        readiness = round((len(covered_role) / total) * 100, 2)
        st.metric(f"{target_role} Readiness ({seniority})", f"{readiness}%")
        st.progress(min(int(readiness), 100))
        st.markdown("<div class='muted'>Readiness = covered role skills / role target skills (deterministic).</div>", unsafe_allow_html=True)

    render_next_move_card(next_move, progress)

    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Evidence", "Role readiness", "AI Insights"])

    with tab1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Resume health")
        st.metric("Score", f"{health['score']}/100")
        for tip in health["tips"]:
            st.write(f"- {tip}")
        st.markdown("</div>", unsafe_allow_html=True)

        if mode == "With Job Description" and result is not None:
            colA, colB = st.columns(2, gap="large")
            with colA:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader("Matched skills (this job)")
                chips = "".join([f"<span class='chip chip-ok'>{s}</span>" for s in result["present_skills"]])
                st.markdown(chips if chips else "—", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with colB:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.subheader("Missing skills (this job)")
                chips = "".join([f"<span class='chip chip-miss'>{s}</span>" for s in result["missing_skills"][:12]])
                st.markdown(chips if chips else "—", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Evidence (short snippets)")
        top = result["present_skills"][:8] if (mode == "With Job Description" and result is not None) else covered_role[:8]
        if not top:
            st.write("No items to show evidence for.")
        else:
            for skill in top:
                with st.expander(skill, expanded=False):
                    snippets = resume_evidence.get(skill, [])[:2]
                    if not snippets:
                        st.write("No snippet found.")
                    for snip in snippets:
                        st.markdown(f"<div class='snippet'>{snip}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader(f"{target_role} readiness ({seniority})")
        st.write("Covered")
        chips = "".join([f"<span class='chip chip-ok'>{s}</span>" for s in covered_role])
        st.markdown(chips if chips else "—", unsafe_allow_html=True)

        st.write("Missing (priority)")
        chips = "".join([f"<span class='chip chip-miss'>{s}</span>" for s in missing_role[:12]])
        st.markdown(chips if chips else "—", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with tab4:
        # Only show Pro Preview / Upgrade here (no clutter elsewhere)
        require_pro_or_preview("AI Insights")

        if not use_ai:
            st.info("Enable AI in the toggle above to see insights.")
            st.stop()

        if not os.getenv("OPENAI_API_KEY"):
            st.warning("No OpenAI key detected. Add it to your environment to enable AI Insights.")
            st.stop()

        ai_context_skills = job_skills if (mode == "With Job Description" and job_skills) else analysis["role_targets"]

        @st.cache_data(show_spinner=True, ttl=3600)
        def cached_role_reality(role: str, skills: list[str]):
            return ai_role_reality_check(role, skills)

        @st.cache_data(show_spinner=True, ttl=3600)
        def cached_blocker(role: str, focus_skill: str):
            return ai_blocker_explanation(role, focus_skill)

        @st.cache_data(show_spinner=True, ttl=3600)
        def cached_plan(skill: str):
            return ai_7_day_plan(skill)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Role reality check")
        bullets, err = safe_ai_tuple(cached_role_reality(target_role, ai_context_skills))
        if err:
            st.error(err)
        elif bullets:
            for b in bullets[:3]:
                st.write(f"- {b}")
        else:
            st.info("No AI output returned.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Why this is blocking you")
        reason, err = safe_ai_tuple(cached_blocker(target_role, next_move["skill"]))
        if err:
            st.error(err)
        elif reason:
            st.write(reason)
        else:
            st.info("No AI output returned.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("If you had 7 days")
        plan, err = safe_ai_tuple(cached_plan(next_move["skill"]))
        if err:
            st.error(err)
        elif plan:
            for i, step in enumerate(plan[:7], 1):
                st.write(f"Day {i}: {step}")
        else:
            st.info("No AI output returned.")
        st.markdown("</div>", unsafe_allow_html=True)
