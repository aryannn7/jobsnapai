"""
core/role_paths.py

Role + seniority targets (deterministic).
Scales via optional JSON file: data/role_skills.json

JSON format example:
{
  "Data Analyst": {
    "Entry": ["SQL", "Excel", "..."],
    "Mid": ["A/B Testing", "..."],
    "Senior": ["Stakeholder Management", "..."]
  }
}
"""

from __future__ import annotations

import json
import os
from typing import Dict, List


# Fallback defaults (works even without JSON)
ROLE_SKILLS: Dict[str, Dict[str, List[str]]] = {
    "Data Analyst": {
        "Entry": ["Structured Query Language", "Excel", "Statistics", "Data Visualization"],
        "Mid": ["Power BI", "Tableau", "A/B Testing", "Stakeholder Management"],
        "Senior": ["Analytics Strategy", "Experimentation Design", "Leadership", "Roadmapping"],
    },
    "Data Engineer": {
        "Entry": ["Python", "Structured Query Language", "PostgreSQL", "Data Modeling"],
        "Mid": ["Apache Spark", "Databricks", "Azure Data Factory", "Orchestration"],
        "Senior": ["Architecture", "Cost Optimization", "Reliability", "Governance"],
    },
    "Analytics Engineer": {
        "Entry": ["Structured Query Language", "Version Control", "Warehouse"],
        "Mid": ["dbt", "Data Modeling", "Testing", "Documentation"],
        "Senior": ["Semantic Layer", "Governance", "Data Contracts", "Team Enablement"],
    },
    "Business Analyst": {
        "Entry": ["Requirements Gathering", "Stakeholder Communication", "Excel"],
        "Mid": ["Process Mapping", "Data Analysis", "Reporting"],
        "Senior": ["Change Management", "Business Strategy", "Leadership"],
    },
    "Machine Learning Engineer": {
        "Entry": ["Python", "Machine Learning", "Model Evaluation"],
        "Mid": ["MLOps", "Deployment", "Monitoring"],
        "Senior": ["System Design", "Scaling", "Cost & Latency Optimization"],
    },
}


def _load_json_role_skills() -> Dict[str, Dict[str, List[str]]]:
    """
    If data/role_skills.json exists, use it.
    Otherwise fallback to ROLE_SKILLS above.
    """
    path = os.path.join("data", "role_skills.json")
    if not os.path.exists(path):
        return ROLE_SKILLS

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # basic validation
        if isinstance(data, dict):
            return data  # type: ignore
        return ROLE_SKILLS
    except Exception:
        return ROLE_SKILLS


def get_role_targets(role: str, seniority: str = "Entry") -> List[str]:
    skills_map = _load_json_role_skills()

    role_map = skills_map.get(role, {})
    entry = role_map.get("Entry", [])
    mid = role_map.get("Mid", [])
    senior = role_map.get("Senior", [])

    # Build cumulative expectations
    if seniority == "Entry":
        return entry
    if seniority == "Mid":
        return list(dict.fromkeys(entry + mid))
    if seniority == "Senior":
        return list(dict.fromkeys(entry + mid + senior))
    return entry
