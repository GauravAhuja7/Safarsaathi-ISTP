"""SMS gateway handler — Phase 5 implementation."""

ROUTE_CODES = {
    "P1": "parashar",
    "B1": "barot",
    "K1": "kullu-manali",
    "E": "emergency",
    "W": "weather",
}

HELP_SMS = "SafarSathi: P1=Parashar, B1=Barot, K1=Kullu-Manali, E=Emergency, W=Weather"

EMERGENCY_SMS = "EMERGENCY: Ambulance 108 | Police 100 | Disaster 1077 | Mandi Hospital 01905-222380"


async def handle_inbound_sms(from_number: str, body: str) -> str:
    """Parse inbound SMS and return a response string < 160 chars."""
    code = body.strip().upper()

    if code == "E":
        return EMERGENCY_SMS

    if code not in ROUTE_CODES:
        return HELP_SMS

    # Phase 5: call risk engine and format a < 160 char response
    # For now return a placeholder
    route = ROUTE_CODES[code]
    return f"{route.upper()}: Check WhatsApp bot for full safety details. Emergency: 108 | Mandi Hospital: 01905-222380"


async def send_sms(to_number: str, message: str) -> bool:
    """Send SMS via MSG91. Phase 5 implementation."""
    assert len(message) <= 160, f"SMS too long: {len(message)} chars"
    print(f"[SMS stub] To {to_number}: {message}")
    return False
