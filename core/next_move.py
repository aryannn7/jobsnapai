"""
core/next_move.py

Purpose:
Decide ONE high-impact next action for the user.

Rules:
- One action only
- Time-boxed
- Explainable
"""

from __future__ import annotations

from typing import Dict, List


SKILL_ACTIONS: Dict[str, Dict[str, str]] = {
    "Power BI": {
        "action": "Build one Power BI dashboard (1 page) using a public dataset and add it to your portfolio.",
        "time": "45 minutes",
        "why": "Power BI is common in analytics roles; adding a real dashboard closes a high-impact gap quickly.",
    },
    "Tableau": {
        "action": "Create one Tableau dashboard showing a trend over time and add a screenshot to your portfolio.",
        "time": "40 minutes",
        "why": "Dashboard proof is a frequent screening signal for analyst roles.",
    },
    "Git": {
        "action": "Create a GitHub repository for a project, push your code, and write a clean README.",
        "time": "35 minutes",
        "why": "Hiring teams value evidence of real projects, version control, and clear documentation.",
    },
}


def decide_next_move(missing_skills: List[str]) -> Dict[str, str]:
    for skill in missing_skills:
        if skill in SKILL_ACTIONS:
            data = SKILL_ACTIONS[skill]
            return {"skill": skill, "action": data["action"], "time": data["time"], "why": data["why"]}

    return {
        "skill": "Evidence Strengthening",
        "action": "Rewrite one resume bullet to include the tool used and a measurable impact (numbers) truthfully.",
        "time": "30 minutes",
        "why": "Stronger evidence improves shortlisting even when you already have the skills.",
    }
