"""Format API data into WhatsApp-readable messages — Phase 3."""

RISK_EMOJI = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢", "UNKNOWN": "⚫"}

PRE_TRIP_CHECKLIST = """*SafarSathi — Pre-Trip Checklist* ✅

Before any mountain trip:
1. 💧 Drink 4–6 liters water daily (start day before)
2. 🚫 No alcohol for first 24h at altitude
3. 💊 Carry Diamox 125mg if going above 2,500m (consult doctor)
4. 🧥 Warm layer + rain cover — always
5. ⛽ Check fuel before entering mountain roads
6. 📍 Tell someone your route + expected return time
7. 📞 Save emergency numbers: Ambulance 108 | Police 100 | Disaster 1077

Altitude warning signs: headache, nausea, dizziness → rest, drink water
EMERGENCY signs: confusion, blue lips, can't walk straight → *DESCEND IMMEDIATELY, call 108*

Reply *emergency* for all Mandi district numbers."""

EMERGENCY_TEXT = """*SafarSathi — Emergency Contacts* 🆘

Universal:
🚑 Ambulance: *108*
🚔 Police: *100*
🆘 Disaster Helpline: *1077*
👩 Women Helpline: *1091*

Mandi District:
🏥 Mandi Zonal Hospital: *01905-222380*
🏛️ District Control Room: *01905-226201*
👮 SP Mandi: *01905-222402*
ℹ️ HP Tourism: *0177-2625924*

Reply route name (e.g. *Parashar*) for route-specific contacts."""

HELP_TEXT = """*SafarSathi* — Mountain Safety Assistant 🏔️

Send any of these:
• *Parashar* — Parashar Lake route safety
• *Barot* — Barot Valley route safety
• *Manali* — Kullu-Manali highway safety
• *Weather* — Current Mandi district weather
• *Checklist* — Pre-trip preparation guide
• *Emergency* — All emergency numbers

Or share your 📍 *location* to find the nearest hospital."""


def format_route_response(
    route_name: str,
    route_slug: str,
    risk_level: str,
    score: int,
    baseline: str,
    weather_summary: str | None,
    weather_hours_old: float | None,
    latest_report: str | None,
    report_hours_old: float | None,
    hospital_name: str | None,
    hospital_phone: str | None,
    reporter_contacts: list[dict],
) -> str:
    emoji = RISK_EMOJI.get(risk_level, "⚫")
    lines = [
        f"*SafarSathi — {route_name}*",
        f"Risk Level: {emoji} *{risk_level}*",
        "",
    ]

    if risk_level == "HIGH":
        lines.append("⚠️ HIGH RISK — Use extreme caution. Consider postponing or calling ahead.")
    elif risk_level == "UNKNOWN":
        lines.append("⚫ Current conditions not verified. Call a local before traveling.")
    elif risk_level == "LOW":
        lines.append("✅ Generally safe. Still follow the checklist and call if unsure.")

    lines.append(f"_(Seasonal baseline: {baseline})_")
    lines.append("")

    if weather_summary and weather_hours_old is not None:
        lines.append(f"🌦 Weather: {weather_summary} _{weather_hours_old:.0f}h ago_")
    else:
        lines.append("🌦 Weather: Checking with IMD — call before travel")

    if latest_report and report_hours_old is not None:
        lines.append(f"📍 Local report: {latest_report} _{report_hours_old:.0f}h ago_")

    lines.append("")

    if hospital_name and hospital_phone:
        lines.append(f"🏥 Nearest hospital: {hospital_name}")
        lines.append(f"📞 {hospital_phone}")

    if reporter_contacts:
        lines.append("")
        lines.append("For current road status, call:")
        for r in reporter_contacts[:2]:
            role = r.get("role", "local contact") or "local contact"
            lines.append(f"  • {r['name']} ({role}): {r['phone']}")

    lines.extend([
        "",
        "Reply *checklist* for pre-trip prep",
        "Reply *emergency* for all emergency numbers",
    ])

    return "\n".join(lines)
