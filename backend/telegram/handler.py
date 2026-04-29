from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.responder import location_reply, text_reply
from telegram.client import TelegramClient


async def handle_update(update: dict, db: AsyncSession, client: TelegramClient) -> bool:
    message = update.get("message")
    if not message:
        return False

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return False

    if location := message.get("location"):
        reply = await location_reply(location["latitude"], location["longitude"], db)
        await client.send_message(chat_id, reply.text)
        return True

    text = message.get("text")
    if not text:
        await client.send_message(chat_id, "Send text like Parashar, Weather, Checklist, or Emergency.")
        return True

    reply = await text_reply(text, db)
    await client.send_message(chat_id, reply.text)
    return True

