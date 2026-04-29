from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import settings
from app.db.session import AsyncSessionLocal
from telegram.client import TelegramClient
from telegram.handler import handle_update

router = APIRouter()


@router.get("/telegram/me")
async def telegram_me():
    client = TelegramClient(settings.telegram_bot_token)
    return await client.get_me()


@router.post("/telegram/commands")
async def set_telegram_commands():
    client = TelegramClient(settings.telegram_bot_token)
    return await client.set_my_commands()


@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if settings.telegram_webhook_secret:
        if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
            raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")

    update = await request.json()
    client = TelegramClient(settings.telegram_bot_token)
    async with AsyncSessionLocal() as db:
        handled = await handle_update(update, db, client)
    return {"ok": True, "handled": handled}


@router.post("/telegram/webhook/set")
async def set_telegram_webhook(url: str):
    client = TelegramClient(settings.telegram_bot_token)
    return await client.set_webhook(url, settings.telegram_webhook_secret or None)


@router.post("/telegram/webhook/delete")
async def delete_telegram_webhook():
    client = TelegramClient(settings.telegram_bot_token)
    return await client.delete_webhook()
