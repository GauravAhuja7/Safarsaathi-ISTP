from __future__ import annotations

import httpx


class TelegramClient:
    def __init__(self, token: str):
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not configured")
        self.base_url = f"https://api.telegram.org/bot{token}"

    async def _post(self, method: str, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f"{self.base_url}/{method}", json=payload)
            response.raise_for_status()
            data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error from {method}: {data}")
        return data

    async def _get(self, method: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=35) as client:
            response = await client.get(f"{self.base_url}/{method}", params=params)
            response.raise_for_status()
            data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API error from {method}: {data}")
        return data

    async def get_me(self) -> dict:
        return await self._get("getMe")

    async def send_message(self, chat_id: int | str, text: str) -> dict:
        return await self._post(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text[:4096],
                "disable_web_page_preview": True,
            },
        )

    async def set_my_commands(self) -> dict:
        return await self._post(
            "setMyCommands",
            {
                "commands": [
                    {"command": "start", "description": "Open SafarSathi help"},
                    {"command": "parashar", "description": "Parashar Lake route safety"},
                    {"command": "barot", "description": "Barot Valley route safety"},
                    {"command": "manali", "description": "Kullu-Manali highway safety"},
                    {"command": "weather", "description": "Mandi weather summary"},
                    {"command": "checklist", "description": "Pre-trip preparation checklist"},
                    {"command": "emergency", "description": "Emergency numbers"},
                ],
            },
        )

    async def get_updates(self, offset: int | None = None, timeout: int = 25) -> list[dict]:
        params = {"timeout": timeout, "allowed_updates": '["message"]'}
        if offset is not None:
            params["offset"] = offset
        data = await self._get("getUpdates", params=params)
        return data["result"]

    async def set_webhook(self, url: str, secret_token: str | None = None) -> dict:
        payload = {"url": url, "allowed_updates": ["message"]}
        if secret_token:
            payload["secret_token"] = secret_token
        return await self._post("setWebhook", payload)

    async def delete_webhook(self) -> dict:
        return await self._post("deleteWebhook", {"drop_pending_updates": False})
