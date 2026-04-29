from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.models.report import Reporter
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
