"""Telegram update handler — tourist queries + reporter flow + photo support."""
from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from bot.reporter_flow import (
    find_reporter_by_telegram,
    handle_step,
    has_active_session,
    start_session,
)
from bot.responder import location_reply, text_reply
from telegram.client import TelegramClient
from whatsapp.keywords import match_intent

logger = logging.getLogger("safarsaathi.telegram.handler")


async def handle_update(update: dict, db: AsyncSession, client: TelegramClient) -> bool:
    message = update.get("message")
    if not message:
        return False

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return False

    sender = message.get("from") or {}
    sender_name = sender.get("first_name") or sender.get("username") or "Unknown"

    # ── Location pin ──────────────────────────────────────────────────────────
    if location := message.get("location"):
        reply = await location_reply(location["latitude"], location["longitude"], db)
        await client.send_message(chat_id, reply.text)
        return True

    # ── Photo / video message ─────────────────────────────────────────────────
    photo_url: str | None = None
    is_media_message = False

    if photos := message.get("photo"):
        # Telegram sends multiple sizes; take the largest (last)
        largest = photos[-1]
        file_id = largest.get("file_id")
        if file_id:
            photo_url = await client.get_file_url(file_id)
        is_media_message = True

    elif video := message.get("video"):
        # For video we just note it was received; URL retrieval same pattern
        file_id = video.get("file_id")
        if file_id:
            photo_url = await client.get_file_url(file_id)
        is_media_message = True

    elif doc := message.get("document"):
        # Documents (e.g. photos sent as files)
        mime = doc.get("mime_type", "")
        if mime.startswith("image/") or mime.startswith("video/"):
            file_id = doc.get("file_id")
            if file_id:
                photo_url = await client.get_file_url(file_id)
            is_media_message = True

    # Caption on a photo counts as the text
    text_raw: str = (
        message.get("caption")
        or message.get("text")
        or ""
    )

    # ── Reporter flow ─────────────────────────────────────────────────────────
    session_key = str(chat_id)

    # If there's an active reporter session, feed any message into it
    if has_active_session(session_key):
        reporter = await find_reporter_by_telegram(chat_id, db)
        reporter_id = reporter.id if reporter else None
        reply_text = await handle_step(
            key=session_key,
            text=text_raw or "skip",
            photo_url=photo_url,
            db=db,
            reporter_id=reporter_id,
            submitted_by=sender_name if reporter_id is None else None,
            source="telegram",
        )
        await client.send_message(chat_id, reply_text)
        return True

    # Media with no active session — prompt them to start a report
    if is_media_message and not text_raw:
        await client.send_message(
            chat_id,
            "Got your photo/video! To submit a road condition report, send 'report' first, then attach your media.",
        )
        return True

    # No text at all
    if not text_raw:
        await client.send_message(
            chat_id,
            "Send text like Parashar, Weather, Checklist, Emergency, or Report.",
        )
        return True

    # ── Check for "report" intent ─────────────────────────────────────────────
    intent = match_intent(text_raw)
    if intent == "report" or text_raw.strip().lower() in {"report", "/report"}:
        reply_text = start_session(session_key)
        await client.send_message(chat_id, reply_text)
        return True

    # ── Tourist text query ────────────────────────────────────────────────────
    reply = await text_reply(text_raw, db)
    await client.send_message(chat_id, reply.text)
    if reply.photo_url:
        await client.send_photo(chat_id, reply.photo_url, caption="📸 Road condition photo from local reporter")
    return True
