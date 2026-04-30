"""WhatsApp Cloud API client — full implementation."""
import httpx
from app.config import settings

WA_API_BASE = "https://graph.facebook.com/v18.0"


async def download_whatsapp_media(media_id: str) -> str | None:
    """Resolve a WhatsApp media_id to a download URL. Returns URL string or None."""
    if not settings.whatsapp_access_token:
        return None
    headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{WA_API_BASE}/{media_id}", headers=headers, timeout=10)
            r.raise_for_status()
            return r.json().get("url")
        except Exception as e:
            print(f"[WhatsApp] Media fetch error for {media_id}: {e}")
            return None


async def send_whatsapp(to_phone: str, message: str) -> bool:
    """Send a text message via WhatsApp Cloud API. Returns True on success."""
    if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
        print(f"[WhatsApp stub] To {to_phone}: {message[:80]}...")
        return False

    url = f"{WA_API_BASE}/{settings.whatsapp_phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message},
    }
    headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url, json=payload, headers=headers, timeout=10)
            r.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            print(f"[WhatsApp] Error sending to {to_phone}: {e.response.text}")
            return False
        except Exception as e:
            print(f"[WhatsApp] Network error: {e}")
            return False
