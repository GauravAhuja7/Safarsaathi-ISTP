from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class WeatherCache(Base):
    __tablename__ = "weather_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    district: Mapped[str] = mapped_column(String(50), nullable=False)
    forecast_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    summary: Mapped[str | None] = mapped_column(Text)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    source: Mapped[str | None] = mapped_column(String(50))

    def hours_old(self) -> float:
        now = datetime.now(timezone.utc)
        scraped = self.scraped_at
        if scraped.tzinfo is None:
            scraped = scraped.replace(tzinfo=timezone.utc)
        return (now - scraped).total_seconds() / 3600

    def is_fresh(self, max_hours: float = 12.0) -> bool:
        return self.hours_old() < max_hours


class OfficialAlert(Base):
    __tablename__ = "official_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int | None] = mapped_column(ForeignKey("routes.id", ondelete="SET NULL"))
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(50))
    scraped_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
