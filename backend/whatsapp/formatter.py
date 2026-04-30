"""Format bot responses — clean, honest, scannable."""

RISK_EMOJI = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢", "UNKNOWN": "⚫"}
RISK_LABEL = {
    "HIGH":    "HIGH RISK — avoid or verify before going",
    "MEDIUM":  "MEDIUM RISK — proceed with caution",
    "LOW":     "LOW RISK — generally safe to travel",
    "UNKNOWN": "UNKNOWN — current data unavailable",
}
ROLE_LABEL = {
    "taxi_driver":    "Taxi driver",
    "dhaba_owner":    "Dhaba owner",
    "homestay_owner": "Homestay owner",
    "other":          "Local contact",
}

PRE_TRIP_CHECKLIST = """SafarSathi — Pre-Trip Checklist

Before any mountain trip:
1. Drink 4-6 litres water daily (start the day before)
2. No alcohol for first 24h at altitude
3. Carry Diamox 125mg if going above 2,500m (ask your doctor)
4. Warm layer + rain cover — always, even in summer
5. Fill fuel before entering mountain roads
6. Tell someone your route and expected return time
7. Save these numbers now: Ambulance 108 | Police 100 | Disaster 1077

Altitude warning signs: headache, nausea, dizziness at rest
EMERGENCY signs: confusion, blue lips, can't walk straight
→ DESCEND IMMEDIATELY and call 108

Reply 'emergency' for all Mandi district numbers."""

EMERGENCY_TEXT = """SafarSathi — Emergency Numbers

UNIVERSAL
Ambulance: 108
Police: 100
Disaster Helpline: 1077
Women Helpline: 1091

MANDI DISTRICT
Mandi Zonal Hospital: 01905-222380
District Control Room: 01905-226201
SP Mandi Office: 01905-222402
HP Tourism Helpline: 0177-2625924

Reply a route name (Parashar / Barot / Manali) for route-specific contacts."""

HELP_TEXT = """SafarSathi — Mountain Safety for Mandi Region

Send any of these:
  Parashar  — Parashar Lake route safety
  Barot     — Barot Valley route safety
  Manali    — Kullu-Manali highway safety
  Weather   — Current IMD weather for Mandi
  Checklist — Pre-trip preparation guide
  Emergency — All emergency numbers
  /report   — Submit a road condition report

Or share your location to find the nearest hospital."""


def _age_label(hours: float) -> str:
    if hours < 1:
        return "just now"
    if hours < 2:
        return f"{hours:.0f}h ago (very recent)"
    if hours < 6:
        return f"{hours:.0f}h ago — verify before travel"
    return f"{hours:.0f}h ago — conditions may have changed"


def _weather_line(summary: str | None, hours_old: float | None) -> str:
    if not summary:
        return "Weather: No data from IMD — check mausam.imd.gov.in or call 0177-2629747"
    age = f" (updated {hours_old:.0f}h ago)" if hours_old is not None else ""
    return f"Weather (IMD Mandi){age}: {summary}"


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
    label = RISK_LABEL.get(risk_level, risk_level)
    lines = []

    # ── Header ────────────────────────────────────────────────────────────────
    lines += [
        f"SafarSathi — {route_name}",
        f"{emoji} {label}",
        f"(Seasonal baseline this month: {baseline})",
        "",
    ]

    # ── High risk advisory ────────────────────────────────────────────────────
    if risk_level == "HIGH":
        lines += [
            "ADVISORY: Conditions are risky. Call a local contact",
            "below to confirm road status before you travel.",
            "",
        ]
    elif risk_level == "UNKNOWN":
        lines += [
            "We don't have fresh data right now. Treat as HIGH RISK",
            "until you can confirm with a local contact.",
            "",
        ]

    # ── Weather ───────────────────────────────────────────────────────────────
    lines.append(_weather_line(weather_summary, weather_hours_old))

    # ── Official alerts ───────────────────────────────────────────────────────
    # (Passed through the reason field from the risk engine for now)

    # ── Local reporter update ─────────────────────────────────────────────────
    if latest_report and report_hours_old is not None:
        lines.append(f"Ground report ({_age_label(report_hours_old)}): {latest_report}")
    else:
        lines.append("Ground report: No recent reports from local contacts")

    lines.append("")

    # ── Hospital ──────────────────────────────────────────────────────────────
    if hospital_name and hospital_phone:
        lines += [
            f"Nearest hospital: {hospital_name}",
            f"  {hospital_phone}",
        ]

    # ── Reporter contacts ─────────────────────────────────────────────────────
    if reporter_contacts:
        lines += ["", "Verify road status — call a local:"]
        for r in reporter_contacts[:2]:
            role = ROLE_LABEL.get(r.get("role") or "", "Local contact")
            loc = f", {r['location']}" if r.get("location") else ""
            lines.append(f"  {r['name']} ({role}{loc})")
            lines.append(f"    {r['phone']}")
    else:
        lines += ["", "No verified local contacts on this route yet."]

    # ── Footer ────────────────────────────────────────────────────────────────
    lines += [
        "",
        "─────────────────────────",
        "Reply 'checklist' — pre-trip preparation",
        "Reply 'emergency' — all emergency numbers",
        "Reply '/report' — submit a road condition",
    ]

    return "\n".join(lines)
