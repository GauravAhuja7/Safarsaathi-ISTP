from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    distance_km: Mapped[int | None] = mapped_column(Integer)
    max_altitude_m: Mapped[int | None] = mapped_column(Integer)
    last_connectivity_point: Mapped[str | None] = mapped_column(String(150))
    nearest_hospital_name: Mapped[str | None] = mapped_column(String(100))
    nearest_hospital_phone: Mapped[str | None] = mapped_column(String(20))
    nearest_hospital_distance_km: Mapped[int | None] = mapped_column(Integer)

    baselines: Mapped[list["RouteBaseline"]] = relationship(back_populates="route", cascade="all, delete-orphan")
    reporters: Mapped[list["Reporter"]] = relationship(back_populates="route")  # type: ignore[name-defined]
    pois: Mapped[list["POI"]] = relationship(back_populates="route")  # type: ignore[name-defined]


class RouteBaseline(Base):
    __tablename__ = "route_baselines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    month_start: Mapped[int] = mapped_column(Integer, nullable=False)
    month_end: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    route: Mapped["Route"] = relationship(back_populates="baselines")

    def matches_month(self, month: int) -> bool:
        if self.month_start <= self.month_end:
            return self.month_start <= month <= self.month_end
        # Wraps year boundary (e.g. Oct=10 to Feb=2)
        return month >= self.month_start or month <= self.month_end
