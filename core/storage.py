# core/storage.py
from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from core.config import VIP_EMAILS


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class User:
    email: str
    is_pro: bool
    period_start: str  # YYYY-MM-01
    free_runs_used: int
    ai_runs_used: int


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def validate_email(email: str) -> bool:
    """Basic email sanity check. (We only need 'good enough' for gating + account keying.)"""
    email = normalize_email(email)
    return bool(_EMAIL_RE.match(email))


def is_vip_email(email: str) -> bool:
    """VIP emails always treated as Pro and never increment usage."""
    return normalize_email(email) in set(VIP_EMAILS)


def _month_start_iso(d: Optional[date] = None) -> str:
    d = d or date.today()
    return f"{d.year:04d}-{d.month:02d}-01"


def _resolve_db_path() -> Path:
    """
    Streamlit Community Cloud file system rules:
    - Your repo folder may be read-only at runtime.
    - /tmp is writable.
    So we:
      1) respect JOBSNAPAI_DB_PATH if set
      2) otherwise try repo/data/users.db
      3) if not writable, fallback to /tmp/users.db
    """
    env_path = (os.getenv("JOBSNAPAI_DB_PATH") or "").strip()
    if env_path:
        return Path(env_path).expanduser()

    # Try repo-local data directory first (great for local dev)
    base_dir = Path(__file__).resolve().parents[1]  # project root
    candidate = base_dir / "data" / "users.db"
    try:
        candidate.parent.mkdir(parents=True, exist_ok=True)
        # Write permission check
        test_file = candidate.parent / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return candidate
    except Exception:
        # Streamlit Cloud: fallback to /tmp
        return Path("/tmp/users.db")


DB_PATH = _resolve_db_path()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH.as_posix(), check_same_thread=False, timeout=15)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db() -> None:
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            is_pro INTEGER NOT NULL DEFAULT 0,
            period_start TEXT NOT NULL,
            free_runs_used INTEGER NOT NULL DEFAULT 0,
            ai_runs_used INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()


def _row_to_user(row) -> User:
    return User(
        email=row[0],
        is_pro=bool(row[1]),
        period_start=row[2],
        free_runs_used=int(row[3]),
        ai_runs_used=int(row[4]),
    )


def _save_user(u: User) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO users(email, is_pro, period_start, free_runs_used, ai_runs_used)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(email) DO UPDATE SET
            is_pro=excluded.is_pro,
            period_start=excluded.period_start,
            free_runs_used=excluded.free_runs_used,
            ai_runs_used=excluded.ai_runs_used
        """,
        (u.email, int(u.is_pro), u.period_start, u.free_runs_used, u.ai_runs_used),
    )
    conn.commit()
    conn.close()


def _reset_if_new_period(u: User) -> User:
    now_period = _month_start_iso()
    if u.period_start != now_period:
        u.period_start = now_period
        u.free_runs_used = 0
        u.ai_runs_used = 0
        _save_user(u)
    return u


def reset_period_if_needed(u: User) -> User:
    """Call this on every app load to enforce monthly reset."""
    return _reset_if_new_period(u)


def get_or_create_user(email: str) -> User:
    init_db()
    email = normalize_email(email)

    conn = _connect()
    cur = conn.execute(
        "SELECT email, is_pro, period_start, free_runs_used, ai_runs_used FROM users WHERE email=?",
        (email,),
    )
    row = cur.fetchone()
    conn.close()

    if row:
        u = _row_to_user(row)
        u = _reset_if_new_period(u)
    else:
        u = User(
            email=email,
            is_pro=False,
            period_start=_month_start_iso(),
            free_runs_used=0,
            ai_runs_used=0,
        )
        _save_user(u)

    # VIP rule: always Pro
    if is_vip_email(email) and not u.is_pro:
        u.is_pro = True
        _save_user(u)

    return u


def increment_free_run(u: User) -> User:
    if is_vip_email(u.email):
        return u
    u.free_runs_used += 1
    _save_user(u)
    return u


def increment_ai_run(u: User) -> User:
    if is_vip_email(u.email):
        return u
    u.ai_runs_used += 1
    _save_user(u)
    return u


def set_user_pro(email: str, is_pro: bool = True) -> User:
    u = get_or_create_user(email)
    u.is_pro = bool(is_pro)
    _save_user(u)
    return u


def reset_usage(email: str) -> User:
    """Force-reset counters immediately (useful if someone is 'blocked')."""
    u = get_or_create_user(email)
    u.period_start = _month_start_iso()
    u.free_runs_used = 0
    u.ai_runs_used = 0
    _save_user(u)
    return u
