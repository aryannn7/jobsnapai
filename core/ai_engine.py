"""
core/ai_engine.py

AI reasoning layer for JobSnapAI.

Contract:
- Every public function MUST return a tuple: (data, error_message)
- Never return None directly.
"""

from __future__ import annotations

import os
from typing import List, Optional, Tuple


def _has_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _get_model() -> str:
    # Allow you to switch models without changing code
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _call_chat(prompt: str, temperature: float = 0.4) -> Tuple[Optional[str], Optional[str]]:
    """
    One place to call OpenAI safely.
    Returns (text, error).
    Works with newer OpenAI SDK style. If your SDK differs, it will return a readable error.
    """
    if not _has_key():
        return None, "Missing OPENAI_API_KEY"

    try:
        # Preferred: new style client
        from openai import OpenAI  # type: ignore

        client = OpenAI()
        resp = client.chat.completions.create(
            model=_get_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return None, "OpenAI returned empty content."
        return text, None

    except Exception as e:
        # IMPORTANT: never raise, always return error
        return None, f"AI call failed: {type(e).__name__}: {e}"


def ai_role_reality_check(role: str, job_skills: List[str]) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Returns (bullets, error)
    """
    prompt = f"""
You are a hiring manager.

In 3 bullets MAX, describe what is actually expected from a {role}.
Use ONLY these skills as context (some may be missing):
{job_skills[:25]}

Rules:
- short bullets
- practical expectations
- no fluff
"""
    text, err = _call_chat(prompt, temperature=0.3)
    if err:
        return None, err

    bullets = [b.strip().lstrip("-•").strip() for b in text.split("\n") if b.strip()]
    bullets = [b for b in bullets if len(b) > 3]
    return bullets[:3], None


def ai_blocker_explanation(role: str, focus_skill: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns (paragraph, error)
    """
    prompt = f"""
Explain in ONE short paragraph (<=60 words)
why missing "{focus_skill}" blocks progression for a {role}.

Rules:
- practical
- market-focused
- no buzzwords
"""
    text, err = _call_chat(prompt, temperature=0.4)
    if err:
        return None, err
    return text, None


def ai_7_day_plan(focus_skill: str) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Returns (steps, error)
    """
    prompt = f"""
Create a 7-day plan to build {focus_skill}.
One task per day.
Each task fits 60–90 minutes.
No fluff.
Return as 7 bullets.
"""
    text, err = _call_chat(prompt, temperature=0.4)
    if err:
        return None, err

    steps = [s.strip().lstrip("-•").strip() for s in text.split("\n") if s.strip()]
    steps = [s for s in steps if len(s) > 3]
    return steps[:7], None