"""
core/ai_engine.py

AI reasoning layer for JobSnapAI.

Contract:
- Every public function returns (data, error_message)
- No exceptions leak to app.py
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Iterable, Optional, Tuple

from core.config import OPENAI_MODEL


def _has_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to recover the first JSON object found in text.
    Handles common cases:
    - code fences ```json ... ```
    - extra leading/trailing commentary
    """
    if not text:
        return None

    t = text.strip()

    # Remove fenced code blocks if present
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```$", "", t)

    # Direct parse
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    # Recover first {...} block
    m = re.search(r"\{.*\}", t, flags=re.DOTALL)
    if not m:
        return None

    candidate = m.group(0)
    try:
        obj = json.loads(candidate)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _call_chat(prompt: str, temperature: float = 0.2) -> Tuple[Optional[str], Optional[str]]:
    if not _has_key():
        return None, "Missing OPENAI_API_KEY. Add it to your environment."

    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI()
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You output only valid JSON objects and nothing else."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return None, "OpenAI returned empty content."
        return text, None

    except Exception as e:
        # Handles insufficient_quota / 429, etc.
        return None, f"AI call failed: {type(e).__name__}: {e}"


def ai_insights_bundle(
    role: str,
    focus_skill: str,
    context_skills: Iterable[str],
    mode: str = "quick",
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    One-call bundle.

    Returns:
      {
        "role_reality": [...],
        "blocker": "...",
        "plan": ["Day 1: ...", ... "Day 7: ..."]
      }
    """
    try:
        skills_list = [s for s in list(context_skills) if isinstance(s, str)]
        skills_list = skills_list[:25]
    except Exception:
        skills_list = []

    depth = "short and practical" if mode == "quick" else "specific and action-oriented"

    prompt = f"""
Create a JSON object ONLY (no markdown, no extra text). Use this schema exactly:
{{
  "role_reality": ["bullet 1", "bullet 2", "bullet 3"],
  "blocker": "one paragraph <= 70 words",
  "plan": ["Day 1: ...", "Day 2: ...", "Day 3: ...", "Day 4: ...", "Day 5: ...", "Day 6: ...", "Day 7: ..."]
}}

Context:
Role: {role}
Focus skill: {focus_skill}
Context skills (some may be missing): {skills_list}

Rules:
- Tone: {depth}
- No fluff, no buzzwords.
- Keep bullets tight.
- Each plan task must be 45–75 minutes.
"""

    text, err = _call_chat(prompt, temperature=0.2)
    if err:
        return None, err

    data = _extract_json_object(text or "")
    if not data:
        return None, "AI output was not valid JSON. Try again."

    # Validate minimally
    if "role_reality" not in data or "blocker" not in data or "plan" not in data:
        return None, "AI output JSON missing required keys. Try again."

    return data, None
