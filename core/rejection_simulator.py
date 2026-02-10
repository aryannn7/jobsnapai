# core/rejection_simulator.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

try:
    from core.skills import SKILL_PRIORITY, SKILL_CATEGORY  # optional if you added it
except Exception:
    SKILL_PRIORITY = {}
    SKILL_CATEGORY = {}


@dataclass
class RejectionReason:
    severity: str          # "Critical" | "Moderate" | "Cosmetic"
    title: str
    reason: str
    evidence: str
    fix: str


def _priority(skill: str) -> int:
    try:
        return int(SKILL_PRIORITY.get(skill, 1))
    except Exception:
        return 1


def _category(skill: str) -> str:
    return str(SKILL_CATEGORY.get(skill, "General"))


def _severity_from_priority(p: int) -> str:
    if p >= 5:
        return "Critical"
    if p >= 3:
        return "Moderate"
    return "Cosmetic"


def run_recruiter_rejection_simulator(
    *,
    target_role: str,
    seniority: str,
    resume_skills: Set[str],
    target_skills: Set[str],
    evidence: Dict[str, List[str]],
    resume_health: Dict[str, object],
    max_reasons: int = 6,
) -> List[Dict[str, str]]:
    """
    Deterministic "recruiter rejection simulator".
    Returns list of dicts: [{severity,title,reason,evidence,fix}, ...]
    No AI. No external calls.
    """
    reasons: List[RejectionReason] = []

    missing = sorted(list(target_skills - resume_skills), key=lambda s: _priority(s), reverse=True)

    # 1) Missing high-priority skills
    if missing:
        top_missing = missing[:3]
        for sk in top_missing:
            p = _priority(sk)
            sev = _severity_from_priority(p)
            cat = _category(sk)
            reasons.append(
                RejectionReason(
                    severity=sev,
                    title=f"Missing {sk} ({cat}) evidence",
                    reason=(
                        f"For {target_role} ({seniority}), recruiters screen for clear proof of {sk}. "
                        "If it’s not visible in experience bullets, you’re often filtered out early."
                    ),
                    evidence="Not found in resume evidence snippets.",
                    fix=f"Add 1–2 bullets showing where you used {sk}, what you built, and measurable impact.",
                )
            )

    # 2) “Mentioned but weak evidence” (skill exists but only 1 weak snippet or only in skills section)
    weak_skills: List[Tuple[str, int]] = []
    for sk in sorted(list(resume_skills)):
        snippets = evidence.get(sk) or []
        if 0 < len(snippets) < 2:
            weak_skills.append((sk, _priority(sk)))
    weak_skills.sort(key=lambda x: x[1], reverse=True)

    if weak_skills:
        sk = weak_skills[0][0]
        snippets = (evidence.get(sk) or [])
        sample = snippets[0] if snippets else "Found but limited evidence."
        reasons.append(
            RejectionReason(
                severity="Moderate",
                title=f"Weak proof for {sk}",
                reason=(
                    "Recruiters don’t just want keyword mentions. They want proof inside projects/experience "
                    "that shows scope, tools, and outcomes."
                ),
                evidence=f"Example snippet: {sample}",
                fix=f"Rewrite one bullet to show: problem → action using {sk} → measurable result.",
            )
        )

    # 3) Resume health blockers (deterministic)
    tips = resume_health.get("tips", []) if isinstance(resume_health, dict) else []
    if isinstance(tips, list) and tips:
        # pick up to 2 tips as “cosmetic/moderate” blockers
        for tip in tips[:2]:
            reasons.append(
                RejectionReason(
                    severity="Cosmetic",
                    title="Resume presentation issue",
                    reason="Small presentation issues reduce interview conversion even with strong skills.",
                    evidence=str(tip),
                    fix="Apply the tip above and re-run analysis.",
                )
            )

    # 4) Overly broad positioning (generic profile)
    if len(resume_skills.intersection(target_skills)) < max(1, int(0.25 * len(target_skills))):
        reasons.append(
            RejectionReason(
                severity="Critical",
                title="Profile looks generic for the target role",
                reason=(
                    "If your resume doesn’t show enough overlap with role skills, recruiters assume you’re not aligned "
                    "and move to candidates with obvious fit."
                ),
                evidence="Low overlap between detected skills and target role skills.",
                fix="Tailor the top section: headline + 3 bullets aligned to the role’s core tools and outcomes.",
            )
        )

    # Deduplicate by title, keep ordering
    seen = set()
    deduped: List[RejectionReason] = []
    for r in reasons:
        if r.title not in seen:
            deduped.append(r)
            seen.add(r.title)

    deduped = deduped[:max_reasons]

    # Convert to JSON-friendly dicts
    out: List[Dict[str, str]] = []
    for r in deduped:
        out.append(
            {
                "severity": r.severity,
                "title": r.title,
                "reason": r.reason,
                "evidence": r.evidence,
                "fix": r.fix,
            }
        )
    return out
