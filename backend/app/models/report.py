from datetime import datetime, timezone
from sqlalchemy import BigInteger, Integer, String, Text, Boolean, Date, DateTime, ForeignKey, Double
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Reporter(Base):
    __tablename__ = "reporters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    role: Mapped[str | None] = mapped_column(String(50))
    location_name: Mapped[str | None] = mapped_column(String(150))
    latitude: Mapped[float | None] = mapped_column(Double)
    longitude: Mapped[float | None] = mapped_column(Double)
    route_id: Mapped[int | None] = mapped_column(ForeignKey("routes.id", ondelete="SET NULL"))
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_date: Mapped[datetime | None] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    strike_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    route: Mapped["Route"] = relationship(back_populates="reporters")  # type: ignore[name-defined]
    reports: Mapped[list["ReporterReport"]] = relationship(back_populates="reporter", cascade="all, delete-orphan")


class ReporterReport(Base):
    __tablename__ = "reporter_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reporter_id: Mapped[int | None] = mapped_column(ForeignKey("reporters.id", ondelete="CASCADE"), nullable=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    condition: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    photo_url: Mapped[str | None] = mapped_column(String(500))
    submitted_by: Mapped[str | None] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    reported_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    reporter: Mapped["Reporter"] = relationship(back_populates="reports")

    def hours_old(self) -> float:
        now = datetime.now(timezone.utc)
        delta = now - self.reported_at.replace(tzinfo=timezone.utc) if self.reported_at.tzinfo is None else now - self.reported_at
        return delta.total_seconds() / 3600

    @property
    def condition_display(self) -> str:
        return {
            "blocked": "Road blocked",
            "rough": "Road open but rough/dangerous",
            "clear": "Road clear",
            "other": "Conditions reported",
        }.get(self.condition, self.condition)
