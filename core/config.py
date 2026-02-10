# core/config.py
from __future__ import annotations

import os
from typing import List

# -------------------------
# App flags
# -------------------------
ENABLE_PAYWALL: bool = (os.getenv("ENABLE_PAYWALL", "1").strip() == "1")

# -------------------------
# Limits
# -------------------------
FREE_RUN_LIMIT_PER_PERIOD: int = int(os.getenv("FREE_RUN_LIMIT_PER_PERIOD", "3"))
AI_RUN_LIMIT_PRO_PER_PERIOD: int = int(os.getenv("AI_RUN_LIMIT_PRO_PER_PERIOD", "25"))

# -------------------------
# Pro unlock
# -------------------------
PRO_ACCESS_CODE: str = (os.getenv("PRO_ACCESS_CODE", "").strip() or "")
STRIPE_PAYMENT_LINK: str = (os.getenv("STRIPE_PAYMENT_LINK", "").strip() or "")

# -------------------------
# OpenAI
# -------------------------
OPENAI_MODEL: str = (os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini")

# -------------------------
# VIP / Admin allowlist
# -------------------------
def _parse_csv_emails(v: str) -> List[str]:
    out: List[str] = []
    for part in (v or "").split(","):
        e = part.strip().lower()
        if e:
            out.append(e)
    return out

# You can set this in your .env:
# VIP_EMAILS="email1@gmail.com,email2@gmail.com"
VIP_EMAILS: List[str] = sorted(
    set(
        _parse_csv_emails(os.getenv("VIP_EMAILS", ""))
        + ["aryandhawan210@gmail.com"]  # your explicit exception
    )
)
