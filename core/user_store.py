# core/user_store.py
from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

# -----------------------------
# Model
# -----------------------------
@dataclass
class User:
    email: str
    created_at: str
    period_start: str
    free_runs_used: int
    ai_runs_used: int
    is_pro: int  # 0/1 stored in DB


# -----------------------------
# Config / paths
# -----------------------------
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email: str) -> bool:
    return bool(email and _EMAIL_RE.match(email.strip().lower()))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _month_start_iso() -> str:
    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    return start.replace(microsecond=0).isoformat()


def _default_db_path() -> str:
    """
    Streamlit Cloud often has a read-only repo filesystem.
    Use /tmp on Streamlit Cloud, otherwise use project data/ folder.
    You can override via JOBSNAPAI_DB_PATH env var.
    """
    override = os.getenv("JOBSNAPAI_DB_PATH", "").strip()
    if override:
        return override

    # Streamlit Cloud usually exposes this env var
    if os.getenv("STREAMLIT_RUNTIME_ENV", "").lower() == "cloud":
        return "/tmp/jobsnapai_users.db"

    # Local default
    return os.path.join("data", "jobsnapai_users.db")


DB_PATH = _default_db_path()


def _conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True) if os.path.dirname(DB_PATH) else None
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA synchronous=NORMAL;")
    return c


def _init_db() -> None:
    with _conn() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                period_start TEXT NOT NULL,
                free_runs_used INTEGER NOT NULL DEFAULT 0,
                ai_runs_used INTEGER NOT NULL DEFAULT 0,
                is_pro INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        con.commit()


_init_db()


# -----------------------------
# Helpers
# -----------------------------
def _row_to_user(row) -> User:
    return User(
        email=row[0],
        created_at=row[1],
        period_start=row[2],
        free_runs_used=int(row[3]),
        ai_runs_used=int(row[4]),
        is_pro=int(row[5]),
    )


def _save_user(u: User) -> None:
    with _conn() as con:
        con.execute(
            """
            INSERT INTO users (email, created_at, period_start, free_runs_used, ai_runs_used, is_pro)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                created_at=excluded.created_at,
                period_start=excluded.period_start,
                free_runs_used=excluded.free_runs_used,
                ai_runs_used=excluded.ai_runs_used,
                is_pro=excluded.is_pro;
            """,
            (u.email, u.created_at, u.period_start, u.free_runs_used, u.ai_runs_used, u.is_pro),
        )
        con.commit()


def _reset_if_new_period(u: User) -> User:
    """
    Resets monthly counters if the stored period_start is not the current month.
    IMPORTANT: must return u (not None), otherwise callers break.
    """
    now_period = _month_start_iso()
    if u.period_start != now_period:
        u.period_start = now_period
        u.free_runs_used = 0
        u.ai_runs_used = 0
        _save_user(u)
    return u


# -----------------------------
# Public API
# -----------------------------
def get_or_create_user(email: str) -> Optional[User]:
    email = (email or "").strip().lower()
    if not validate_email(email):
        return None

    with _conn() as con:
        row = con.execute(
            "SELECT email, created_at, period_start, free_runs_used, ai_runs_used, is_pro FROM users WHERE email=?",
            (email,),
        ).fetchone()

    if row:
        return _reset_if_new_period(_row_to_user(row))

    u = User(
        email=email,
        created_at=_utc_now_iso(),
        period_start=_month_start_iso(),
        free_runs_used=0,
        ai_runs_used=0,
        is_pro=0,
    )
    _save_user(u)
    return u


def reset_period_if_needed(u: Optional[User]) -> Optional[User]:
    if not u:
        return None
    return _reset_if_new_period(u)


def increment_free_run(u: Optional[User]) -> Optional[User]:
    if not u:
        return None
    u = _reset_if_new_period(u)
    u.free_runs_used = int(u.free_runs_used) + 1
    _save_user(u)
    return u


def increment_ai_run(u: Optional[User]) -> Optional[User]:
    if not u:
        return None
    u = _reset_if_new_period(u)
    u.ai_runs_used = int(u.ai_runs_used) + 1
    _save_user(u)
    return u


def set_user_pro(email: str, is_pro: bool) -> Optional[User]:
    u = get_or_create_user(email)
    if not u:
        return None
    u.is_pro = 1 if is_pro else 0
    _save_user(u)
    return u


def reset_usage(email: str) -> Optional[User]:
    u = get_or_create_user(email)
    if not u:
        return None
    u.free_runs_used = 0
    u.ai_runs_used = 0
    _save_user(u)
    return u


def is_vip_email(email: str) -> bool:
    """
    Optional admin list. Add comma-separated VIP emails in env:
    JOBSNAPAI_VIP_EMAILS="a@x.com,b@y.com"
    """
    vip = os.getenv("JOBSNAPAI_VIP_EMAILS", "").strip()
    if not vip:
        return False
    vip_set = {x.strip().lower() for x in vip.split(",") if x.strip()}
    return (email or "").strip().lower() in vip_set
