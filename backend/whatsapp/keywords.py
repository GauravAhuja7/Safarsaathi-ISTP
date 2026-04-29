"""Keyword → route/intent mapping for WhatsApp message parsing — Phase 3."""

ROUTE_KEYWORDS: dict[str, list[str]] = {
    "parashar": ["parashar", "prashar", "parshar", "parashar lake", "parashar jheel", "parasher"],
    "barot": ["barot", "brot", "barod", "barot valley", "barot ghati", "barat"],
    "kullu-manali": ["kullu", "manali", "kullu manali", "nh3", "nh 3", "nh21", "national highway", "manali road"],
}

INTENT_KEYWORDS: dict[str, list[str]] = {
    "weather": ["weather", "mausam", "barish", "rain", "baarish", "mosam", "baarish hai"],
    "emergency": ["emergency", "help", "hospital", "ambulance", "doctor", "accident", "madad", "aspatal"],
    "checklist": ["checklist", "prepare", "taiyari", "kya lana", "what to bring", "kya kya chahiye"],
    "report": ["report", "condition", "rasta", "block", "band", "khula", "road", "sarak"],
}


def match_route(text: str) -> str | None:
    normalized = text.lower().strip().rstrip("?!.")
    for slug, keywords in ROUTE_KEYWORDS.items():
        if any(kw in normalized for kw in keywords):
            return slug
    return None


def match_intent(text: str) -> str | None:
    normalized = text.lower().strip()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in normalized for kw in keywords):
            return intent
    return None
