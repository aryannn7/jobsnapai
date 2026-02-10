# core/demo_data.py
from __future__ import annotations

from typing import Dict, List


def demo_analysis_payload() -> Dict[str, object]:
    # A safe, generic demo payload (no real personal data)
    evidence = {
        "Python": [
            "Built data cleaning scripts in Python to standardize incoming reports | Reduced manual effort by 30%",
            "Automated KPI reporting using pandas | Delivered weekly dashboards for stakeholders",
        ],
        "Structured Query Language": [
            "Wrote SQL queries to extract product and customer metrics | Improved reporting turnaround",
        ],
        "Power BI": [
            "Created Power BI dashboards tracking sales funnel performance | Shared insights with leadership",
        ],
        "Git": [
            "Used Git for version control across analytics projects | Maintained clean commit history",
        ],
    }

    missing_skills = ["Tableau", "Statistics", "Data Modeling", "Azure", "Docker"]

    payload = {
        "target_role": "Data Analyst",
        "seniority": "Mid",
        "mode": "Role Targets",
        "file_type": "demo",
        "resume_filename": "Demo Resume",
        "cleaned_text": "Demo resume text used for sample report.",
        "evidence": evidence,
        "resume_skills": sorted(list(evidence.keys())),
        "context_skills": [
            "Python",
            "Structured Query Language",
            "Power BI",
            "Tableau",
            "Statistics",
            "Data Modeling",
            "Azure",
            "Git",
            "Docker",
        ],
        "match": {
            "match_percentage": 44.4,
            "present_skills": ["Python", "Structured Query Language", "Power BI", "Git"],
            "missing_skills": missing_skills,
            "job_skill_count": 9,
            "matched_count": 4,
        },
        "health": {
            "score": 72,
            "tips": [
                "Add metrics to 2–3 bullets (%, £, time saved) to increase credibility.",
                "Ensure tools appear inside experience bullets, not only in a skills list.",
            ],
        },
        "next_move": {
            "skill": "Evidence Strengthening",
            "action": "Rewrite one resume bullet to include the tool used and a measurable impact (numbers) truthfully.",
            "time": "30 minutes",
            "why": "Strong evidence improves shortlisting even when you already have the skills.",
        },
        "role_readiness": 56.0,
    }
    return payload


def demo_share_text() -> str:
    return (
        "JobSnapAI Sample Report\n"
        "Target: Data Analyst (Mid)\n"
        "Role readiness: 56/100 | Match: 44.4% | Resume health: 72/100\n\n"
        "Top next move:\n"
        "- Rewrite one bullet to include tool + measurable impact.\n\n"
        "Common screening gaps (example):\n"
        "- Tableau, Statistics, Data Modeling, Azure, Docker\n"
    )
