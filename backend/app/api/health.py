from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from sqlalchemy import text, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.weather import WeatherCache

router = APIRouter()


def _hours_since(dt: datetime | None) -> str:
    if dt is None:
        return "never"
    delta = datetime.now(timezone.utc) - dt
    h = delta.total_seconds() / 3600
    return f"{h:.1f}h ago"


@router.get("/health")
async def health_check(request: Request, db: AsyncSession = Depends(get_db)):
    issues: list[str] = []

    # DB connectivity
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        return {
            "status": "unhealthy",
            "issues": [f"Database unreachable: {e}"],
            "timestamp": datetime.now(timezone.utc),
        }

    # IMD weather freshness
    weather_status = "no_data"
    try:
        result = await db.execute(
            select(WeatherCache)
            .where(WeatherCache.district == "mandi")
            .order_by(desc(WeatherCache.scraped_at))
            .limit(1)
        )
        weather = result.scalar_one_or_none()
        if weather is None:
            issues.append("No IMD weather data in database yet")
        elif not weather.is_fresh(8):
            issues.append(f"IMD weather data stale ({weather.hours_old():.0f}h old)")
            weather_status = f"stale ({weather.hours_old():.0f}h)"
        else:
            weather_status = f"fresh ({weather.hours_old():.1f}h old) — {weather.summary or 'no summary'}"
    except Exception as e:
        issues.append(f"Weather check failed: {e}")

    # Scraper last-run timestamps (set by scheduler in app.state)
    scraper_status = getattr(request.app.state, "scraper_status", {})
    scraper_report = {
        name: _hours_since(ts) for name, ts in scraper_status.items()
    }

    # Flag scrapers that have never run (only an issue if they've had time to run)
    for name, ts in scraper_status.items():
        if ts is None:
            issues.append(f"Scraper '{name}' has not run yet")

    return {
        "status": "ok" if not issues else "degraded",
        "issues": issues,
        "weather": weather_status,
        "scrapers": scraper_report,
        "timestamp": datetime.now(timezone.utc),
    }
