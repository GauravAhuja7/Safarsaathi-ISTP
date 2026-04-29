import math
from sqlalchemy import Integer, String, Text, Double, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class POI(Base):
    __tablename__ = "pois"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    latitude: Mapped[float | None] = mapped_column(Double)
    longitude: Mapped[float | None] = mapped_column(Double)
    route_id: Mapped[int | None] = mapped_column(ForeignKey("routes.id", ondelete="SET NULL"))
    notes: Mapped[str | None] = mapped_column(Text)

    route: Mapped["Route"] = relationship(back_populates="pois")  # type: ignore[name-defined]

    def distance_km_to(self, lat: float, lon: float) -> float:
        """Haversine distance in km."""
        R = 6371
        lat1, lon1 = math.radians(self.latitude or 0), math.radians(self.longitude or 0)
        lat2, lon2 = math.radians(lat), math.radians(lon)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))
