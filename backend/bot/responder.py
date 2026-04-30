from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.engine.risk import calculate_risk
from app.models.poi import POI
from app.models.report import Reporter, ReporterReport
from app.models.route import Route, RouteBaseline
from app.models.weather import OfficialAlert, WeatherCache
from whatsapp.formatter import EMERGENCY_TEXT, HELP_TEXT, PRE_TRIP_CHECKLIST, format_route_response
from whatsapp.keywords import match_intent, match_route


@dataclass
class BotReply:
    text: str
    photo_url: str | None = None


def _plain(text: str) -> str:
    """Convert WhatsApp-style lightweight markdown to safe Telegram plain text."""
    return text.replace("*", "").replace("_", "")


async def _get_route(slug: str, db: AsyncSession) -> Route | None:
    result = await db.execute(
        select(Route).options(selectinload(Route.baselines)).where(Route.slug == slug)
    )
    return result.scalar_one_or_none()


def _get_baseline(route: Route, month: int) -> RouteBaseline | None:
    for baseline in route.baselines:
        if baseline.matches_month(month):
            return baseline
    return route.baselines[0] if route.baselines else None


async def _get_latest_weather(db: AsyncSession) -> WeatherCache | None:
    result = await db.execute(
        select(WeatherCache)
        .where(WeatherCache.district == "mandi")
        .order_by(desc(WeatherCache.scraped_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _get_active_alerts(route_id: int, db: AsyncSession) -> list[OfficialAlert]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(OfficialAlert).where(
            OfficialAlert.route_id == route_id,
            (OfficialAlert.expires_at == None) | (OfficialAlert.expires_at > now),  # noqa: E711
        )
    )
    return list(result.scalars().all())


async def _get_recent_reports(route_id: int, db: AsyncSession) -> list[ReporterReport]:
    result = await db.execute(
        select(ReporterReport)
        .where(ReporterReport.route_id == route_id)
        .order_by(desc(ReporterReport.reported_at))
        .limit(10)
    )
    return [report for report in result.scalars().all() if report.hours_old() < 24]


async def _get_active_reporters(route_id: int, db: AsyncSession) -> list[Reporter]:
    result = await db.execute(
        select(Reporter).where(
            Reporter.route_id == route_id,
            Reporter.active == True,  # noqa: E712
            Reporter.consent_given == True,  # noqa: E712
        )
    )
    return list(result.scalars().all())


async def route_reply(slug: str, db: AsyncSession) -> BotReply:
    route = await _get_route(slug, db)
    if route is None:
        return BotReply(f"Route '{slug}' not found yet.\n\n{_plain(HELP_TEXT)}")

    now = datetime.now(timezone.utc)
    baseline = _get_baseline(route, now.month)
    if baseline is None:
        return BotReply(f"No seasonal baseline is configured for {route.name}.")

    weather = await _get_latest_weather(db)
    alerts = await _get_active_alerts(route.id, db)
    reports = await _get_recent_reports(route.id, db)
    reporters = await _get_active_reporters(route.id, db)
    latest_report = reports[0] if reports else None
    risk = calculate_risk(route.slug, now.month, now.hour, baseline, weather, alerts, reports)

    text = format_route_response(
        route_name=route.name,
        route_slug=route.slug,
        risk_level=risk.level,
        score=risk.score,
        baseline=risk.baseline,
        weather_summary=weather.summary if weather else None,
        weather_hours_old=round(weather.hours_old(), 1) if weather else None,
        latest_report=latest_report.condition_display if latest_report else None,
        report_hours_old=round(latest_report.hours_old(), 1) if latest_report else None,
        hospital_name=route.nearest_hospital_name,
        hospital_phone=route.nearest_hospital_phone,
        reporter_contacts=[
            {"name": r.name, "role": r.role, "phone": r.phone, "location": r.location_name}
            for r in reporters
        ],
    )
    photo_url = latest_report.photo_url if latest_report else None
    return BotReply(_plain(text), photo_url=photo_url)


async def weather_reply(db: AsyncSession) -> BotReply:
    weather = await _get_latest_weather(db)
    if weather is None:
        return BotReply(
            "Mandi weather data is not available yet.\n"
            "The app can still use seasonal route baselines. Send Parashar, Barot, or Manali."
        )

    freshness = "fresh" if weather.is_fresh(12) else "stale"
    text = (
        "SafarSathi — Mandi Weather\n\n"
        f"Summary: {weather.summary or 'No summary available'}\n"
        f"Source: {weather.source or 'unknown'}\n"
        f"Updated: {weather.hours_old():.0f}h ago ({freshness})\n\n"
        "Send a route name for route-specific risk."
    )
    return BotReply(text)


async def location_reply(lat: float, lon: float, db: AsyncSession) -> BotReply:
    result = await db.execute(
        select(POI).where(
            POI.latitude != None,  # noqa: E711
            POI.longitude != None,  # noqa: E711
            POI.category.in_(["hospital", "police", "emergency", "checkpoint"]),
        )
    )
    pois = list(result.scalars().all())
    pois.sort(key=lambda poi: poi.distance_km_to(lat, lon))

    if not pois:
        return BotReply(_plain(EMERGENCY_TEXT))

    lines = ["Nearest SafarSathi locations:"]
    for poi in pois[:5]:
        distance = poi.distance_km_to(lat, lon)
        phone = f" | {poi.phone}" if poi.phone else ""
        lines.append(f"- {poi.name} ({poi.category}) — {distance:.1f} km{phone}")

    lines.extend(["", "Emergency: Ambulance 108 | Police 100 | Disaster 1077"])
    return BotReply("\n".join(lines))


async def text_reply(text: str, db: AsyncSession) -> BotReply:
    normalized = text.strip()
    lowered = normalized.lower()

    if lowered in {"/start", "start", "/help", "help", "hi", "hello", "namaste"}:
        return BotReply(_plain(HELP_TEXT))

    route = match_route(normalized)
    if route:
        return await route_reply(route, db)

    intent = match_intent(normalized)
    if intent == "weather":
        return await weather_reply(db)
    if intent == "emergency":
        return BotReply(_plain(EMERGENCY_TEXT))
    if intent == "checklist":
        return BotReply(_plain(PRE_TRIP_CHECKLIST))

    return BotReply(
        "I did not understand that yet.\n\n"
        "Try: Parashar, Barot, Manali, Weather, Checklist, Emergency.\n"
        "You can also share your location to find nearby help."
    )

