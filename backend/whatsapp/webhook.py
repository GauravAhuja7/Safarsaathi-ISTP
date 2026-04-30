"""WhatsApp Cloud API webhook — full message processing."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import AsyncSessionLocal
from bot.reporter_flow import (
    find_reporter_by_phone,
    handle_step,
    has_active_session,
    start_session,
)
from bot.responder import location_reply, text_reply
from whatsapp.client import download_whatsapp_media, send_whatsapp
from whatsapp.keywords import match_intent

logger = logging.getLogger("safarsaathi.whatsapp.webhook")

router = APIRouter()


# ── Webhook verification (Meta handshake) ─────────────────────────────────────

@router.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == settings.whatsapp_verify_token
    ):
        return Response(content=params["hub.challenge"], media_type="text/plain")
    return Response(content="Forbidden", status_code=403)


# ── Incoming message handler ──────────────────────────────────────────────────

@router.post("/webhook/whatsapp")
async def receive_message(request: Request):
    body = await request.json()
    try:
        async with AsyncSessionLocal() as db:
            await _process_body(body, db)
    except Exception:
        logger.exception("WhatsApp webhook processing error")
    # Always return 200 so Meta doesn't retry
    return {"status": "ok"}


async def _process_body(body: dict, db: AsyncSession) -> None:
    for e in body.get("entry", []):
        for change in e.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                await _handle_message(msg, db)


async def _handle_message(msg: dict, db: AsyncSession) -> None:
    from_phone = msg.get("from")
    if not from_phone:
        return

    msg_type = msg.get("type", "text")
    text_raw = ""
    photo_url: str | None = None

    if msg_type == "text":
        text_raw = (msg.get("text") or {}).get("body", "")

    elif msg_type in {"image", "video", "document"}:
        media_obj = msg.get(msg_type, {})
        media_id = media_obj.get("id")
        caption = media_obj.get("caption") or ""
        text_raw = caption
        if media_id:
            photo_url = await download_whatsapp_media(media_id)

    elif msg_type == "location":
        loc = msg.get("location", {})
        lat, lon = loc.get("latitude"), loc.get("longitude")
        if lat is not None and lon is not None:
            reply = await location_reply(lat, lon, db)
            await send_whatsapp(from_phone, reply.text)
        return

    else:
        await send_whatsapp(
            from_phone,
            "Send text like Parashar, Weather, Checklist, Emergency, or Report.",
        )
        return

    # ── Reporter flow ─────────────────────────────────────────────────────────
    session_key = from_phone

    if has_active_session(session_key):
        reporter = await find_reporter_by_phone(from_phone, db)
        reporter_id = reporter.id if reporter else None
        reply_text = await handle_step(
            key=session_key,
            text=text_raw or "skip",
            photo_url=photo_url,
            db=db,
            reporter_id=reporter_id,
            submitted_by=from_phone if reporter_id is None else None,
            source="whatsapp",
        )
        await send_whatsapp(from_phone, reply_text)
        return

    if not text_raw:
        if photo_url:
            await send_whatsapp(
                from_phone,
                "Got your photo! Send 'report' first to submit a road condition report.",
            )
        return

    # ── "report" intent ───────────────────────────────────────────────────────
    intent = match_intent(text_raw)
    if intent == "report" or text_raw.strip().lower() == "report":
        reply_text = start_session(session_key)
        await send_whatsapp(from_phone, reply_text)
        return

    # ── Tourist text query ────────────────────────────────────────────────────
    reply = await text_reply(text_raw, db)
    await send_whatsapp(from_phone, reply.text)
