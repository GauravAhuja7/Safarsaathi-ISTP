from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
import httpx
from app.db.session import get_db
from app.models.report import Reporter, ReporterReport
from app.models.route import Route
from app.config import settings

router = APIRouter()

ADMIN_KEY = "safarsaathi-admin-2026"  # Replace with env var in production


def _require_admin(x_admin_key: str = Header(...)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")


class ReporterCreate(BaseModel):
    name: str
    phone: str
    role: str | None = None
    location_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    route_slug: str
    telegram_chat_id: int | None = None
    consent_given: bool = False


class ReporterOut(BaseModel):
    id: int
    name: str
    phone: str
    role: str | None
    location_name: str | None
    route_id: int | None
    consent_given: bool
    active: bool
    strike_count: int
    created_at: datetime


@router.get("/reporters", response_model=list[ReporterOut])
async def list_reporters(db: AsyncSession = Depends(get_db), _: str = Depends(_require_admin)):
    result = await db.execute(select(Reporter).order_by(Reporter.id))
    return list(result.scalars().all())


@router.post("/reporters", response_model=ReporterOut, status_code=201)
async def create_reporter(
    payload: ReporterCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(_require_admin),
):
    # Resolve route slug → id
    result = await db.execute(select(Route).where(Route.slug == payload.route_slug))
    route = result.scalar_one_or_none()
    if route is None:
        raise HTTPException(status_code=404, detail=f"Route '{payload.route_slug}' not found")

    reporter = Reporter(
        name=payload.name,
        phone=payload.phone,
        role=payload.role,
        location_name=payload.location_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        route_id=route.id,
        telegram_chat_id=payload.telegram_chat_id,
        consent_given=payload.consent_given,
        consent_date=date.today() if payload.consent_given else None,
    )
    db.add(reporter)
    await db.commit()
    await db.refresh(reporter)
    return reporter


@router.patch("/reporters/{reporter_id}/deactivate", response_model=ReporterOut)
async def deactivate_reporter(
    reporter_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(_require_admin),
):
    result = await db.execute(select(Reporter).where(Reporter.id == reporter_id))
    reporter = result.scalar_one_or_none()
    if reporter is None:
        raise HTTPException(status_code=404, detail="Reporter not found")
    reporter.active = False
    await db.commit()
    await db.refresh(reporter)
    return reporter


@router.patch("/reporters/{reporter_id}/strike", response_model=ReporterOut)
async def add_strike(
    reporter_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(_require_admin),
):
    result = await db.execute(select(Reporter).where(Reporter.id == reporter_id))
    reporter = result.scalar_one_or_none()
    if reporter is None:
        raise HTTPException(status_code=404, detail="Reporter not found")
    reporter.strike_count += 1
    if reporter.strike_count >= 3:
        reporter.active = False
    await db.commit()
    await db.refresh(reporter)
    return reporter


# ── Public report submission (website + bots) ─────────────────────────────────

class ReportSubmit(BaseModel):
    route_slug: str
    condition: str  # blocked | rough | clear | other
    description: str | None = None
    photo_url: str | None = None
    submitted_by: str | None = None  # optional name for anonymous submitters
    source: str = "website"


class ReportOut(BaseModel):
    id: int
    route_slug: str
    condition: str
    description: str | None
    photo_url: str | None
    submitted_by: str | None
    source: str
    reported_at: datetime


VALID_CONDITIONS = {"blocked", "rough", "clear", "other"}
VALID_SOURCES = {"telegram", "whatsapp", "website", "admin"}


@router.post("/reports", response_model=ReportOut, status_code=201)
async def submit_report(payload: ReportSubmit, db: AsyncSession = Depends(get_db)):
    if payload.condition not in VALID_CONDITIONS:
        raise HTTPException(status_code=422, detail=f"condition must be one of {VALID_CONDITIONS}")

    source = payload.source if payload.source in VALID_SOURCES else "website"

    result = await db.execute(select(Route).where(Route.slug == payload.route_slug))
    route = result.scalar_one_or_none()
    if route is None:
        raise HTTPException(status_code=404, detail=f"Route '{payload.route_slug}' not found")

    report = ReporterReport(
        reporter_id=None,
        route_id=route.id,
        condition=payload.condition,
        description=payload.description,
        photo_url=payload.photo_url,
        submitted_by=payload.submitted_by,
        source=source,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return ReportOut(
        id=report.id,
        route_slug=payload.route_slug,
        condition=report.condition,
        description=report.description,
        photo_url=report.photo_url,
        submitted_by=report.submitted_by,
        source=report.source,
        reported_at=report.reported_at,
    )


@router.get("/reports/{report_id}/photo")
async def get_report_photo(report_id: int, db: AsyncSession = Depends(get_db)):
    """Proxy the reporter photo so the bot token never reaches the browser."""
    result = await db.execute(select(ReporterReport).where(ReporterReport.id == report_id))
    report = result.scalar_one_or_none()
    if report is None or not report.photo_url:
        raise HTTPException(status_code=404, detail="Photo not found")

    async def stream():
        async with httpx.AsyncClient(timeout=15) as client:
            async with client.stream("GET", report.photo_url) as r:
                async for chunk in r.aiter_bytes(8192):
                    yield chunk

    return StreamingResponse(stream(), media_type="image/jpeg")


@router.get("/reports")
async def list_recent_reports(route_slug: str | None = None, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """List recent reports — used by admin dashboard and PWA."""
    query = select(ReporterReport).order_by(desc(ReporterReport.reported_at)).limit(limit)
    if route_slug:
        route_result = await db.execute(select(Route).where(Route.slug == route_slug))
        route = route_result.scalar_one_or_none()
        if route:
            query = query.where(ReporterReport.route_id == route.id)

    result = await db.execute(query)
    reports = result.scalars().all()
    return [
        {
            "id": r.id,
            "condition": r.condition,
            "condition_display": r.condition_display,
            "description": r.description,
            "photo_url": r.photo_url,
            "submitted_by": r.submitted_by,
            "source": r.source,
            "hours_old": round(r.hours_old(), 1),
            "reported_at": r.reported_at,
        }
        for r in reports
    ]
