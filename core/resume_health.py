"""
core/resume_health.py

Deterministic resume health checks.
"""

from typing import Dict
import re


def resume_health_check(text: str) -> Dict[str, object]:
    """
    Returns a small health report suitable for UI display.
    """
    t = text or ""
    t_lower = t.lower()

    has_metrics = bool(re.search(r"\b\d+%|\b\d+\b", t))
    has_experience = ("experience" in t_lower) or ("work experience" in t_lower)
    has_skills = "skills" in t_lower
    has_projects = "projects" in t_lower

    score = 0
    score += 25 if has_experience else 0
    score += 25 if has_skills else 0
    score += 25 if has_projects else 0
    score += 25 if has_metrics else 0

    tips = []
    if not has_metrics:
        tips.append("Add measurable impact (numbers, percentages, scale) in 2–4 bullets.")
    if not has_projects:
        tips.append("Add a Projects section with 1–2 strong, relevant projects.")
    if not has_skills:
        tips.append("Add a clear Skills section grouped by category (Data, Cloud, Tools).")
    if not has_experience:
        tips.append("Add a Work Experience section with role, dates, and outcomes.")

    tips = tips[:3] if tips else ["Your resume structure looks solid. Strengthen evidence for key skills."]

    return {"score": score, "tips": tips}
