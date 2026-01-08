"""
core/progress.py

Lightweight progress tracking stored in a local JSON file.

Why:
- Creates retention (streaks)
- Gives the product a "daily habit" loop
- Works locally without a database

Later:
- Replace JSON storage with a database (PostgreSQL) without changing app logic much.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_PROGRESS_PATH = Path("data/progress.json")


@dataclass
class ProgressState:
    """
    Tracks user progress in a minimal way.
    """
    streak: int = 0
    last_done: Optional[str] = None  # ISO date string "YYYY-MM-DD"
    history: List[Dict[str, str]] = None  # list of {"date": "...", "skill": "...", "action": "..."}

    def __post_init__(self):
        if self.history is None:
            self.history = []


def load_progress(path: Path = DEFAULT_PROGRESS_PATH) -> ProgressState:
    """
    Load progress from JSON. If not found, return default state.
    """
    if not path.exists():
        return ProgressState()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ProgressState(
            streak=int(data.get("streak", 0)),
            last_done=data.get("last_done"),
            history=data.get("history", []) or [],
        )
    except Exception:
        # If file gets corrupted, fail safe
        return ProgressState()


def save_progress(state: ProgressState, path: Path = DEFAULT_PROGRESS_PATH) -> None:
    """
    Save progress to JSON.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")


def mark_done(state: ProgressState, skill: str, action: str) -> ProgressState:
    """
    Mark today's task as done and update streak.

    Streak rules:
    - If last_done is yesterday -> streak += 1
    - If last_done is today -> no change
    - Else -> streak = 1 (reset)
    """
    today = date.today()
    today_str = today.isoformat()

    if state.last_done == today_str:
        # Already marked done today; no updates needed
        return state

    if state.last_done:
        try:
            last = date.fromisoformat(state.last_done)
        except ValueError:
            last = None
    else:
        last = None

    if last and last == (today - timedelta(days=1)):
        state.streak += 1
    else:
        state.streak = 1

    state.last_done = today_str
    state.history.insert(0, {"date": today_str, "skill": skill, "action": action})
    state.history = state.history[:30]  # keep last 30 entries

    return state
