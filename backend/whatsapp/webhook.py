"""WhatsApp Cloud API webhook — Phase 3 implementation."""
from fastapi import APIRouter, Request, Response
from app.config import settings

router = APIRouter()


@router.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    """Meta webhook verification handshake."""
    params = dict(request.query_params)
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == settings.whatsapp_verify_token
    ):
        return Response(content=params["hub.challenge"], media_type="text/plain")
    return Response(content="Forbidden", status_code=403)


@router.post("/webhook/whatsapp")
async def receive_message(request: Request):
    """Receive and route incoming WhatsApp messages — Phase 3 implementation."""
    # Phase 3: parse message, detect tourist vs reporter, call appropriate handler
    body = await request.json()
    print(f"[WhatsApp webhook] Received: {body}")
    return {"status": "ok"}
