"""Stateful reporter condition-reporting flow — shared between Telegram and WhatsApp."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Reporter, ReporterReport
from app.models.route import Route

# ── State machine ────────────────────────────────────────────────────────────

State = Literal["SELECT_ROUTE", "SELECT_CONDITION", "AWAIT_DETAIL"]

ROUTE_MENU = (
    "Which route are you reporting on?\n\n"
    "1️⃣  Parashar Lake\n"
    "2️⃣  Barot Valley\n"
    "3️⃣  Kullu-Manali (NH-3)\n\n"
    "Reply with 1, 2, or 3."
)

CONDITION_MENU = (
    "What is the current road condition?\n\n"
    "1️⃣  Road BLOCKED (landslide / flood / closure)\n"
    "2️⃣  Road ROUGH (open but dangerous)\n"
    "3️⃣  Road CLEAR (normal conditions)\n"
    "4️⃣  Other / not sure\n\n"
    "Reply with 1, 2, 3, or 4."
)

DETAIL_PROMPT = (
    "Optional: add a short note, photo, or video about the conditions.\n"
    "Type your note OR send a photo/video.\n"
    "Reply SKIP to finish without details."
)

ROUTE_CHOICE: dict[str, str] = {
    "1": "parashar",
    "2": "barot",
    "3": "kullu-manali",
}

CONDITION_CHOICE: dict[str, str] = {
    "1": "blocked",
    "2": "rough",
    "3": "clear",
    "4": "other",
}


@dataclass
class FlowSession:
    state: State = "SELECT_ROUTE"
    route_slug: str | None = None
    condition: str | None = None
    started_at: float = field(default_factory=time.time)

    def is_expired(self, timeout_seconds: int = 1800) -> bool:
        return (time.time() - self.started_at) > timeout_seconds


# ── In-memory session store ───────────────────────────────────────────────────
# Key: str(chat_id) for Telegram or phone number for WhatsApp
_sessions: dict[str, FlowSession] = {}


def has_active_session(key: str) -> bool:
    session = _sessions.get(key)
    if session is None:
        return False
    if session.is_expired():
        del _sessions[key]
        return False
    return True


def start_session(key: str) -> str:
    _sessions[key] = FlowSession()
    return ROUTE_MENU


def clear_session(key: str) -> None:
    _sessions.pop(key, None)


# ── Step handlers ─────────────────────────────────────────────────────────────

async def handle_step(
    key: str,
    text: str,
    photo_url: str | None,
    db: AsyncSession,
    reporter_id: int | None,
    submitted_by: str | None,
    source: str,
) -> str:
    """
    Advance the reporter flow one step. Returns the bot reply text.
    Saves the report to DB on completion.
    """
    session = _sessions.get(key)
    if session is None or session.is_expired():
        clear_session(key)
        return "Session expired. Send 'report' to start again."

    normalized = text.strip().lower()

    # ── SELECT_ROUTE ──────────────────────────────────────────────────────────
    if session.state == "SELECT_ROUTE":
        # Accept "1"/"2"/"3" or route name keywords
        slug = ROUTE_CHOICE.get(normalized)
        if slug is None:
            from whatsapp.keywords import match_route
            slug = match_route(text)
        if slug is None:
            return "Please reply with 1, 2, or 3 to select a route.\n\n" + ROUTE_MENU

        session.route_slug = slug
        session.state = "SELECT_CONDITION"
        return f"Route: {slug.replace('-', ' ').title()}\n\n{CONDITION_MENU}"

    # ── SELECT_CONDITION ──────────────────────────────────────────────────────
    if session.state == "SELECT_CONDITION":
        condition = CONDITION_CHOICE.get(normalized)
        if condition is None:
            return "Please reply with 1, 2, 3, or 4.\n\n" + CONDITION_MENU

        session.condition = condition
        session.state = "AWAIT_DETAIL"
        return DETAIL_PROMPT

    # ── AWAIT_DETAIL ──────────────────────────────────────────────────────────
    if session.state == "AWAIT_DETAIL":
        description = None if normalized == "skip" else (text.strip() or None)
        await _save_report(
            db=db,
            reporter_id=reporter_id,
            route_slug=session.route_slug,
            condition=session.condition,
            description=description,
            photo_url=photo_url,
            submitted_by=submitted_by,
            source=source,
        )
        clear_session(key)

        cond_label = {
            "blocked": "BLOCKED",
            "rough": "ROUGH",
            "clear": "CLEAR",
            "other": "OTHER",
        }.get(session.condition, session.condition.upper())

        return (
            f"Report saved! Thank you.\n\n"
            f"Route: {session.route_slug.replace('-', ' ').title()}\n"
            f"Condition: {cond_label}\n"
            + (f"Note: {description}\n" if description else "")
            + (f"Photo: received\n" if photo_url else "")
            + "\nYour report helps tourists travel safely. Send 'report' to submit another."
        )

    return "Something went wrong. Send 'report' to start again."


# ── DB save ───────────────────────────────────────────────────────────────────

async def _save_report(
    db: AsyncSession,
    reporter_id: int | None,
    route_slug: str | None,
    condition: str | None,
    description: str | None,
    photo_url: str | None,
    submitted_by: str | None,
    source: str,
) -> None:
    result = await db.execute(select(Route).where(Route.slug == route_slug))
    route = result.scalar_one_or_none()
    if route is None:
        return

    report = ReporterReport(
        reporter_id=reporter_id,
        route_id=route.id,
        condition=condition or "other",
        description=description,
        photo_url=photo_url,
        submitted_by=submitted_by,
        source=source,
    )
    db.add(report)
    await db.commit()


# ── Reporter lookup ────────────────────────────────────────────────────────────

async def find_reporter_by_telegram(chat_id: int, db: AsyncSession) -> Reporter | None:
    result = await db.execute(
        select(Reporter).where(
            Reporter.telegram_chat_id == chat_id,
            Reporter.active == True,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def find_reporter_by_phone(phone: str, db: AsyncSession) -> Reporter | None:
    normalized = phone.lstrip("+").lstrip("91") if phone.startswith("+91") else phone
    result = await db.execute(
        select(Reporter).where(
            Reporter.phone.in_([phone, f"+91{normalized}", normalized]),
            Reporter.active == True,  # noqa: E712
        )
    )
    return result.scalar_one_or_none()
