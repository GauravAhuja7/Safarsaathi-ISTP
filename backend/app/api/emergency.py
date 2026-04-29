from fastapi import APIRouter

router = APIRouter()

EMERGENCY_CONTACTS = {
    "universal": [
        {"name": "Ambulance", "number": "108", "icon": "🚑"},
        {"name": "Police", "number": "100", "icon": "🚔"},
        {"name": "Fire", "number": "101", "icon": "🚒"},
        {"name": "Disaster Helpline", "number": "1077", "icon": "🆘"},
        {"name": "Women Helpline", "number": "1091", "icon": "📞"},
    ],
    "mandi_district": [
        {"name": "District Control Room", "number": "01905-226201", "icon": "🏛️"},
        {"name": "District Control Room (alt)", "number": "01905-226202", "icon": "🏛️"},
        {"name": "Mandi Zonal Hospital", "number": "01905-222380", "icon": "🏥"},
        {"name": "Grievance (WhatsApp)", "number": "7650025201", "icon": "📱"},
        {"name": "SP Mandi Office", "number": "01905-222402", "icon": "👮"},
        {"name": "HP Tourism Helpline", "number": "0177-2625924", "icon": "ℹ️"},
    ],
    "route_specific": {
        "parashar": [
            {"name": "Baggi Village Dhaba (verify road status)", "number": "TBD after fieldwork", "icon": "🍽️"},
            {"name": "Mandi Zonal Hospital (nearest)", "number": "01905-222380", "icon": "🏥"},
        ],
        "barot": [
            {"name": "Ghatasani Taxi Stand (verify road status)", "number": "TBD after fieldwork", "icon": "🚕"},
            {"name": "Jogindernagar Hospital", "number": "TBD after fieldwork", "icon": "🏥"},
        ],
        "kullu-manali": [
            {"name": "NHAI Helpline", "number": "1033", "icon": "🛣️"},
            {"name": "Pandoh Police Post", "number": "TBD after fieldwork", "icon": "👮"},
        ],
    },
}


@router.get("/emergency")
async def get_all_emergency():
    return EMERGENCY_CONTACTS


@router.get("/emergency/{route_slug}")
async def get_route_emergency(route_slug: str):
    base = {
        "universal": EMERGENCY_CONTACTS["universal"],
        "mandi_district": EMERGENCY_CONTACTS["mandi_district"],
    }
    route_specific = EMERGENCY_CONTACTS["route_specific"].get(route_slug, [])
    return {**base, "route_specific": route_specific}
