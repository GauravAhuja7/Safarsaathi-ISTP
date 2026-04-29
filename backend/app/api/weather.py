from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.models.weather import WeatherCache

router = APIRouter()


@router.get("/weather/mandi")
async def get_mandi_weather(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WeatherCache)
        .where(WeatherCache.district == "mandi")
        .order_by(desc(WeatherCache.scraped_at))
        .limit(1)
    )
    weather = result.scalar_one_or_none()

    if weather is None:
        raise HTTPException(status_code=404, detail="No weather data available yet. Scrapers have not run.")

    return {
        "district": weather.district,
        "summary": weather.summary,
        "forecast": weather.forecast_json,
        "source": weather.source,
        "scraped_at": weather.scraped_at,
        "hours_old": round(weather.hours_old(), 1),
        "is_fresh": weather.is_fresh(12),
    }
