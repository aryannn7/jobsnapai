"""
core/next_move.py

Purpose:
Decide ONE high-impact next action for the user.

Rules:
- One action only
- Time-boxed
- Explainable
"""

from typing import Dict, List


# Action templates keyed by canonical skill name (must match skills in skills.py)
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
        "action": "Create a GitHub repository for this project, push your code, and write a clean README.",
        "time": "35 minutes",
        "why": "Hiring teams value evidence of real projects, version control, and clear documentation.",
    },
}


def decide_next_move(missing_skills: List[str]) -> Dict[str, str]:
    """
    Decide one best next move based on missing skills.

    Parameters
    ----------
    missing_skills : List[str]
        Skills required by the job but not found in the resume.

    Returns
    -------
    Dict[str, str]
        A dictionary containing:
        - skill: which skill to focus on
        - action: what to do
        - time: time-box
        - why: one-sentence rationale
    """
    # Try to pick the first missing skill that we have a prepared action for.
    for skill in missing_skills:
        if skill in SKILL_ACTIONS:
            data = SKILL_ACTIONS[skill]
            return {"skill": skill, "action": data["action"], "time": data["time"], "why": data["why"]}

    # Fallback if we don't have a template for the missing skills.
    return {
        "skill": "Evidence Strengthening",
        "action": "Rewrite one resume bullet to include the tool used and a measurable impact (numbers) truthfully.",
        "time": "30 minutes",
        "why": "Strong evidence improves shortlisting even when you already have the skills.",
    }
