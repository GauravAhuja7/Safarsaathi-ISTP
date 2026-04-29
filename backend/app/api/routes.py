from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from app.db.session import get_db
from app.models.route import Route, RouteBaseline
from app.models.weather import WeatherCache, OfficialAlert
from app.models.report import Reporter, ReporterReport
from app.engine.risk import calculate_risk

router = APIRouter()


class ReporterContact(BaseModel):
    name: str
    role: str | None
    phone: str
    location: str | None


class RiskResponse(BaseModel):
    route: str
    name: str
    risk_level: str
    score: int
    seasonal_baseline: str
    reason: str
    weather_summary: str | None
    weather_hours_old: float | None
    weather_is_fresh: bool
    latest_report: str | None
    report_hours_old: float | None
    nearest_hospital_name: str | None
    nearest_hospital_phone: str | None
    reporters: list[ReporterContact]
    assessed_at: datetime


class RouteListItem(BaseModel):
    slug: str
    name: str
    distance_km: int | None
    max_altitude_m: int | None
    seasonal_baseline: str
    current_risk: str


async def _get_route_or_404(slug: str, db: AsyncSession) -> Route:
    result = await db.execute(
        select(Route).options(selectinload(Route.baselines)).where(Route.slug == slug)
    )
    route = result.scalar_one_or_none()
    if route is None:
        raise HTTPException(status_code=404, detail=f"Route '{slug}' not found")
    return route


async def _get_baseline(route: Route, month: int) -> RouteBaseline:
    for b in route.baselines:
        if b.matches_month(month):
            return b
    # Fallback: return the first baseline (shouldn't happen with complete seed data)
    return route.baselines[0]


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
    reports = list(result.scalars().all())
    return [r for r in reports if r.hours_old() < 24]


async def _get_active_reporters(route_id: int, db: AsyncSession) -> list[Reporter]:
    result = await db.execute(
        select(Reporter).where(
            Reporter.route_id == route_id,
            Reporter.active == True,        # noqa: E712
            Reporter.consent_given == True, # noqa: E712
        )
    )
    return list(result.scalars().all())


@router.get("/routes", response_model=list[RouteListItem])
async def list_routes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Route).options(selectinload(Route.baselines)))
    routes = result.scalars().all()

    now = datetime.now(timezone.utc)
    month = now.month
    hour = now.hour

    items = []
    for route in routes:
        baseline = await _get_baseline(route, month)
        weather = await _get_latest_weather(db)
        alerts = await _get_active_alerts(route.id, db)
        reports = await _get_recent_reports(route.id, db)
        risk = calculate_risk(route.slug, month, hour, baseline, weather, alerts, reports)

        items.append(RouteListItem(
            slug=route.slug,
            name=route.name,
            distance_km=route.distance_km,
            max_altitude_m=route.max_altitude_m,
            seasonal_baseline=baseline.risk_level,
            current_risk=risk.level,
        ))

    return items


@router.get("/routes/{slug}/risk", response_model=RiskResponse)
async def get_route_risk(slug: str, db: AsyncSession = Depends(get_db)):
    route = await _get_route_or_404(slug, db)

    now = datetime.now(timezone.utc)
    month, hour = now.month, now.hour

    baseline = await _get_baseline(route, month)
    weather = await _get_latest_weather(db)
    alerts = await _get_active_alerts(route.id, db)
    recent_reports = await _get_recent_reports(route.id, db)
    reporters = await _get_active_reporters(route.id, db)

    risk = calculate_risk(route.slug, month, hour, baseline, weather, alerts, recent_reports)

    latest_report = recent_reports[0] if recent_reports else None

    return RiskResponse(
        route=route.slug,
        name=route.name,
        risk_level=risk.level,
        score=risk.score,
        seasonal_baseline=risk.baseline,
        reason=risk.reason,
        weather_summary=weather.summary if weather else None,
        weather_hours_old=round(weather.hours_old(), 1) if weather else None,
        weather_is_fresh=weather.is_fresh(12) if weather else False,
        latest_report=latest_report.condition_display if latest_report else None,
        report_hours_old=round(latest_report.hours_old(), 1) if latest_report else None,
        nearest_hospital_name=route.nearest_hospital_name,
        nearest_hospital_phone=route.nearest_hospital_phone,
        reporters=[
            ReporterContact(name=r.name, role=r.role, phone=r.phone, location=r.location_name)
            for r in reporters
        ],
        assessed_at=now,
    )
