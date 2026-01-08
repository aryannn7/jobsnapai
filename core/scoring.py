"""
core/scoring.py

Deterministic skill extraction + evidence snippets + match scoring.

Key improvement:
- Evidence is extracted from LINES + a small context window,
  so we never display the entire resume as one blob.
"""

from __future__ import annotations

import re
from typing import Dict, List, Set

from core.skills import SKILL_ALIASES  # canonical -> list of aliases


def _normalize_for_search(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _lines(text: str) -> List[str]:
    """
    Split into meaningful lines. This relies on clean_text preserving newlines.
    """
    t = text or ""
    raw = [ln.strip() for ln in t.split("\n")]
    # keep non-empty lines, and ignore very short noise
    return [ln for ln in raw if len(ln) >= 4]


def _make_alias_pattern(aliases: List[str]) -> re.Pattern:
    """
    Build a regex that matches aliases with word boundaries where possible.
    """
    escaped = [re.escape(a) for a in aliases if a.strip()]
    if not escaped:
        # match nothing
        return re.compile(r"a^")

    # Use word boundaries. Works well for most skills (SQL, Python, GitHub, etc.)
    return re.compile(r"(?i)\b(" + "|".join(escaped) + r")\b")


def _evidence_window(lines: List[str], hit_index: int, window: int = 1) -> str:
    """
    Return a small snippet around the hit line:
    - previous line (optional)
    - hit line
    - next line (optional)
    """
    start = max(0, hit_index - window)
    end = min(len(lines), hit_index + window + 1)
    snippet = " | ".join(lines[start:end])
    snippet = _normalize_for_search(snippet)
    # cap length so UI stays clean
    return snippet[:260] + ("…" if len(snippet) > 260 else "")


def extract_skills_with_evidence(text: str, max_snippets_per_skill: int = 2) -> Dict[str, List[str]]:
    """
    Extract canonical skills present in text and attach short evidence snippets.

    Returns:
        {canonical_skill: [snippet1, snippet2]}
    """
    if not text:
        return {}

    lines = _lines(text)
    found: Dict[str, List[str]] = {}

    for canonical, aliases in SKILL_ALIASES.items():
        pattern = _make_alias_pattern(aliases)

        hits: List[str] = []
        for idx, ln in enumerate(lines):
            if pattern.search(ln):
                hits.append(_evidence_window(lines, idx, window=1))
            if len(hits) >= max_snippets_per_skill:
                break

        if hits:
            found[canonical] = hits

    return found


def compute_match(resume_skills: Set[str], job_skills: Set[str]) -> Dict[str, object]:
    """
    Compute match percentage based on overlap of deterministic skills.
    """
    matched = sorted(list(resume_skills.intersection(job_skills)))
    missing = sorted(list(job_skills.difference(resume_skills)))

    job_count = len(job_skills)
    pct = round((len(matched) / job_count) * 100, 2) if job_count else 0.0

    return {
        "match_percentage": pct,
        "present_skills": matched,
        "missing_skills": missing,
        "job_skill_count": job_count,
        "matched_count": len(matched),
    }