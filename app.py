"""
app.py

JobSnapAI — Career Intelligence System
Minimal, decision-first, explainable.
"""
from dotenv import load_dotenv
load_dotenv()

import time
import os
import streamlit as st

from core.ui_theme import inject_global_css
from core.parsing import parse_resume
from core.cleaning import clean_text
from core.scoring import extract_skills_with_evidence, compute_match
from core.next_move import decide_next_move
from core.resume_health import resume_health_check
from core.role_paths import get_role_targets
from core.progress import load_progress, save_progress, mark_done

from core.ai_engine import (
    ai_role_reality_check,
    ai_blocker_explanation,
    ai_7_day_plan,
)


# ----------------------------
# Helpers
# ----------------------------
def safe_ai_tuple(x):
    if x is None:
        return None, "AI function returned None (check core/ai_engine.py)."
    if isinstance(x, tuple) and len(x) == 2:
        return x
    return x, None


def clear_results():
    if "analysis" in st.session_state:
        del st.session_state["analysis"]
    st.rerun()


# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="JobSnapAI", layout="wide")

# Default theme should be LIGHT
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

with st.sidebar:
    st.subheader("Settings")
    st.session_state["theme"] = st.radio(
        "Theme",
        ["light", "dark"],
        index=0 if st.session_state["theme"] == "light" else 1,
    )

    st.divider()
    st.subheader("AI status")
    if os.getenv("OPENAI_API_KEY"):
        st.success("OpenAI key detected")
    else:
        st.warning("No OpenAI key detected (AI Insights will be unavailable)")

inject_global_css(st.session_state["theme"])


# ----------------------------
# Header
# ----------------------------
st.title("JobSnapAI")
st.markdown("<div class='muted'>A decision engine that tells you exactly what to do next.</div>", unsafe_allow_html=True)
st.divider()


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

use_ai = st.toggle("Use AI for reasoning (optional)", value=False)
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

    # ----------------------------
    # Premium “thinking” buffer UI
    # ----------------------------
    status_box = st.empty()

    def thinking(message: str, cycles: int = 3, delay: float = 0.35):
        """
        Shows a looping '...' effect to simulate thoughtful processing.
        """
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

    # Step 1 — Parsing
    thinking("Parsing resume", cycles=1)
    _, raw_text = parse_resume(resume_file.name, resume_file.getvalue())
    resume_text = clean_text(raw_text)

    # Step 2 — Skill extraction
    thinking("Extracting skills and validating evidence", cycles=1)
    resume_evidence = extract_skills_with_evidence(
        resume_text, max_snippets_per_skill=2
    )
    resume_skills = set(resume_evidence.keys())

    # Step 3 — Role / JD evaluation
    thinking("Evaluating role readiness and skill gaps", cycles=2)
    role_targets = get_role_targets(target_role, seniority=seniority)
    covered_role = sorted(set(role_targets).intersection(resume_skills))
    missing_role = sorted(set(role_targets).difference(resume_skills))

    result = None
    job_skills = []

    if mode == "With Job Description":
        job_evidence = extract_skills_with_evidence(
            job_description, max_snippets_per_skill=1
        )
        job_skills = sorted(list(job_evidence.keys()))
        result = compute_match(resume_skills, set(job_skills))

    # Step 4 — Decision engine
    thinking("Identifying the most impactful next step", cycles=1)
    if mode == "With Job Description" and result is not None:
        next_move = decide_next_move(result["missing_skills"])
    else:
        next_move = decide_next_move(missing_role)

    health = resume_health_check(resume_text)
    progress = load_progress()

    # Clear buffer UI
    status_box.empty()

    # Persist analysis state
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

st.divider()
st.subheader("Your Result")

# KPI row depends on mode
if mode == "With Job Description" and result is not None:
    st.metric("Job Match", f"{result['match_percentage']}%")
    st.progress(min(int(result["match_percentage"]), 100))
    st.markdown("<div class='muted'>Match = matched skills / job skills (deterministic).</div>", unsafe_allow_html=True)
else:
    # Role readiness score
    total = max(len(covered_role) + len(missing_role), 1)
    readiness = round((len(covered_role) / total) * 100, 2)
    st.metric(f"{target_role} Readiness ({seniority})", f"{readiness}%")
    st.progress(min(int(readiness), 100))
    st.markdown("<div class='muted'>Readiness = covered role skills / role target skills (deterministic).</div>", unsafe_allow_html=True)

# One Next Move
st.markdown("<div class='card card-primary'>", unsafe_allow_html=True)
st.subheader("Your One Next Move")
st.markdown(f"**Focus skill:** {next_move['skill']}")
st.markdown(f"**What to do ({next_move['time']}):**")
st.write(next_move["action"])
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

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Evidence", "Role readiness", "AI Insights"])

with tab1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Resume health")
    st.metric("Score", f"{health['score']}/100")
    for tip in health["tips"]:
        st.write(f"- {tip}")
    st.markdown("</div>", unsafe_allow_html=True)

    # If JD mode show JD matched/missing
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
    # show evidence only for top 8 strongest matched skills
    # if JD mode, show evidence for JD matched skills; else show evidence for role-covered skills
    if mode == "With Job Description" and result is not None:
        top = result["present_skills"][:8]
    else:
        top = covered_role[:8]

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
    if not use_ai:
        st.info("Enable AI in the toggle above to see insights.")
        st.stop()

    if not os.getenv("OPENAI_API_KEY"):
        st.warning("No OpenAI key detected. Add it to your environment to enable AI Insights.")
        st.stop()

    # Inputs to AI: If JD exists, use JD skills; else use role targets.
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