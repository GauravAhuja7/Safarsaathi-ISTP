from __future__ import annotations

import asyncio
import logging

from app.config import settings
from app.db.session import AsyncSessionLocal, create_tables
from telegram.client import TelegramClient
from telegram.handler import handle_update

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("safarsaathi.telegram")


async def run_polling() -> None:
    client = TelegramClient(settings.telegram_bot_token)
    me = await client.get_me()
    logger.info("Starting Telegram polling for @%s", me["result"].get("username"))

    await create_tables()
    await client.set_my_commands()
    await client.delete_webhook()

    offset: int | None = None
    while True:
        try:
            updates = await client.get_updates(offset=offset, timeout=25)
            for update in updates:
                offset = update["update_id"] + 1
                async with AsyncSessionLocal() as db:
                    await handle_update(update, db, client)
        except Exception:
            logger.exception("Telegram polling error")
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(run_polling())
