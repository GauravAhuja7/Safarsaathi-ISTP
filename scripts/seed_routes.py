"""
Run from the backend/ directory:
    python ../scripts/seed_routes.py

Or with a custom DB URL:
    DATABASE_URL=postgresql+asyncpg://... python ../scripts/seed_routes.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, delete

# Import models to register them with Base
from app.models.route import Route, RouteBaseline
from app.models.poi import POI
from app.models.report import Reporter
from app.db.session import Base
from app.config import settings

ROUTES = [
    {
        "slug": "parashar",
        "name": "Mandi to Parashar Lake",
        "distance_km": 50,
        "max_altitude_m": 2730,
        "last_connectivity_point": "Baggi Village (~km 40)",
        "nearest_hospital_name": "Mandi Zonal Hospital",
        "nearest_hospital_phone": "01905-222380",
        "nearest_hospital_distance_km": 50,
        "baselines": [
            {
                "month_start": 3, "month_end": 5,
                "risk_level": "LOW",
                "reason": "Best travel window. Road dry, visibility good.",
                "notes": "Altitude prep still needed — 2,000m gain in ~2 hours.",
            },
            {
                "month_start": 6, "month_end": 9,
                "risk_level": "HIGH",
                "reason": "Monsoon season — landslide-prone, road past Baggi frequently washed out.",
                "notes": "Do NOT travel without calling a local to verify road status first.",
            },
            {
                "month_start": 10, "month_end": 2,
                "risk_level": "MEDIUM",
                "reason": "Cold with possible snow above 2,500m. Road can be icy and slippery.",
                "notes": "Last 10 km rough even in good conditions. Carry warm clothes.",
            },
        ],
        "pois": [
            {"name": "Mandi Zonal Hospital", "category": "hospital", "phone": "01905-222380", "lat": 31.7058, "lon": 76.9317, "notes": "Main hospital, 50+ km from Parashar Lake"},
            {"name": "Mandi Police Station", "category": "police", "phone": "01905-222100", "lat": 31.7085, "lon": 76.9330, "notes": None},
            {"name": "Baggi Village Checkpoint", "category": "checkpoint", "phone": None, "lat": 31.8450, "lon": 77.0600, "notes": "Last phone signal. Verify road status here before proceeding."},
            {"name": "Petrol Pump — Mandi Town", "category": "petrol", "phone": None, "lat": 31.7100, "lon": 76.9350, "notes": "Last fuel point before Parashar route"},
            {"name": "Parashar Lake Rest House", "category": "checkpoint", "phone": "01905-222380", "lat": 31.9347, "lon": 77.1602, "notes": "HP Tourism rest house at lake. Contact Mandi Zonal Hospital in emergency."},
        ],
    },
    {
        "slug": "barot",
        "name": "Mandi to Barot Valley",
        "distance_km": 65,
        "max_altitude_m": 1800,
        "last_connectivity_point": "Ghatasani (~km 45)",
        "nearest_hospital_name": "Jogindernagar Civil Hospital",
        "nearest_hospital_phone": "01908-222044",
        "nearest_hospital_distance_km": 35,
        "baselines": [
            {
                "month_start": 3, "month_end": 5,
                "risk_level": "LOW",
                "reason": "Best window. River levels manageable, road dry.",
                "notes": "Moderate altitude (1,800m), low AMS risk for most people.",
            },
            {
                "month_start": 6, "month_end": 9,
                "risk_level": "HIGH",
                "reason": "Uhl River floods — road along gorge extremely dangerous, frequent blockages.",
                "notes": "Last 35 km single-lane along river gorge. Absolutely no night travel.",
            },
            {
                "month_start": 10, "month_end": 2,
                "risk_level": "MEDIUM",
                "reason": "Cold, narrow gorge road, limited daylight hours.",
                "notes": "Complete the gorge section before sunset. Road icy in deep winter.",
            },
        ],
        "pois": [
            {"name": "Jogindernagar Civil Hospital", "category": "hospital", "phone": "01908-222044", "lat": 31.9961, "lon": 76.7919, "notes": "Nearest hospital, 35 km from Barot"},
            {"name": "Ghatasani Taxi Stand", "category": "checkpoint", "phone": None, "lat": 31.9200, "lon": 76.8400, "notes": "Call from here to verify road condition past Ghatasani"},
            {"name": "Barot Village", "category": "checkpoint", "phone": None, "lat": 31.9800, "lon": 76.8100, "notes": "Destination. HP Tourism guesthouse available."},
            {"name": "Petrol Pump — Jogindernagar", "category": "petrol", "phone": None, "lat": 31.9970, "lon": 76.7890, "notes": "Last fuel before entering Barot gorge"},
            {"name": "Uhl River Bridge Checkpoint", "category": "checkpoint", "phone": None, "lat": 31.9500, "lon": 76.8200, "notes": "Key flood risk point in monsoon. Road may close here."},
        ],
    },
    {
        "slug": "kullu-manali",
        "name": "Mandi to Kullu / Manali (NH3)",
        "distance_km": 170,
        "max_altitude_m": 2050,
        "last_connectivity_point": "Kullu Town",
        "nearest_hospital_name": "Kullu Regional Hospital",
        "nearest_hospital_phone": "01902-222341",
        "nearest_hospital_distance_km": 110,
        "baselines": [
            {
                "month_start": 3, "month_end": 5,
                "risk_level": "LOW",
                "reason": "Main national highway, well-maintained. Best travel window.",
                "notes": "Heavy tourist traffic in May. Start early to avoid congestion near Kullu.",
            },
            {
                "month_start": 6, "month_end": 9,
                "risk_level": "HIGH",
                "reason": "Pandoh-Aut stretch extremely landslide-prone. NH was closed 3 consecutive days in Aug 2025.",
                "notes": "Check HP PWD / NHAI (1033) before travel. Avoid night travel on Aut-Kullu section.",
            },
            {
                "month_start": 10, "month_end": 2,
                "risk_level": "MEDIUM",
                "reason": "Aut-Kullu stretch prone to black ice. Manali can be snowbound.",
                "notes": "Carry snow chains if going to Manali Dec-Feb. Rohtang closed in heavy snow.",
            },
        ],
        "pois": [
            {"name": "Kullu Regional Hospital", "category": "hospital", "phone": "01902-222341", "lat": 31.9592, "lon": 77.1089, "notes": "Main hospital for Kullu district"},
            {"name": "Manali Civil Hospital", "category": "hospital", "phone": "01902-252379", "lat": 32.2432, "lon": 77.1892, "notes": "Hospital in Manali town"},
            {"name": "Pandoh Dam Police Post", "category": "police", "phone": None, "lat": 31.7838, "lon": 77.0950, "notes": "Key police point on landslide-prone stretch"},
            {"name": "Aut Tunnel Entrance", "category": "checkpoint", "phone": None, "lat": 31.8450, "lon": 77.0450, "notes": "High landslide risk zone Aut-Kullu. Check before proceeding."},
            {"name": "Petrol Pump — Pandoh", "category": "petrol", "phone": None, "lat": 31.7840, "lon": 77.0900, "notes": "Fuel up here before entering mountain section"},
            {"name": "NHAI Helpline", "category": "emergency", "phone": "1033", "lat": None, "lon": None, "notes": "National highway emergency helpline"},
        ],
    },
]

DEMO_REPORTERS = [
    {
        "name": "Ramesh Sharma (Dhaba Owner)",
        "phone": "+919805012345",
        "role": "dhaba_owner",
        "location_name": "Sharma Dhaba, Baggi Village",
        "route_slug": "parashar",
        "consent_given": True,
    },
    {
        "name": "Mohan Taxi (Parashar Taxi Stand)",
        "phone": "+919816098765",
        "role": "taxi_driver",
        "location_name": "Kataula Taxi Stand, Mandi",
        "route_slug": "parashar",
        "consent_given": True,
    },
    {
        "name": "Suresh Homestay (Barot)",
        "phone": "+919816011222",
        "role": "homestay_owner",
        "location_name": "Barot Village Homestay",
        "route_slug": "barot",
        "consent_given": True,
    },
    {
        "name": "Ghatasani Taxi Driver",
        "phone": "+919805099001",
        "role": "taxi_driver",
        "location_name": "Ghatasani, Barot route",
        "route_slug": "barot",
        "consent_given": True,
    },
    {
        "name": "Pandoh Dhaba Owner",
        "phone": "+919816055321",
        "role": "dhaba_owner",
        "location_name": "Pandoh Dam, NH-3",
        "route_slug": "kullu-manali",
        "consent_given": True,
    },
]

UNIVERSAL_POIS = [
    {"name": "Ambulance", "category": "emergency", "phone": "108", "lat": None, "lon": None, "notes": "Universal ambulance service"},
    {"name": "Police", "category": "emergency", "phone": "100", "lat": None, "lon": None, "notes": "Universal police helpline"},
    {"name": "Disaster Helpline", "category": "emergency", "phone": "1077", "lat": None, "lon": None, "notes": "HP disaster control room"},
    {"name": "Mandi District Control Room", "category": "emergency", "phone": "01905-226201", "lat": None, "lon": None, "notes": "24x7 district emergency control"},
    {"name": "Mandi Zonal Hospital", "category": "hospital", "phone": "01905-222380", "lat": 31.7058, "lon": 76.9317, "notes": "Main referral hospital for Mandi district"},
]


async def seed(db_url: str):
    engine = create_async_engine(db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Clear existing data (idempotent re-run)
        await session.execute(delete(POI))
        await session.execute(delete(Reporter))
        await session.execute(delete(RouteBaseline))
        await session.execute(delete(Route))
        await session.commit()

        # Insert universal POIs (no route association)
        for p in UNIVERSAL_POIS:
            poi = POI(
                name=p["name"], category=p["category"], phone=p["phone"],
                latitude=p["lat"], longitude=p["lon"], notes=p["notes"],
            )
            session.add(poi)

        # Insert routes, baselines, and route POIs
        for r in ROUTES:
            route = Route(
                slug=r["slug"],
                name=r["name"],
                distance_km=r["distance_km"],
                max_altitude_m=r["max_altitude_m"],
                last_connectivity_point=r["last_connectivity_point"],
                nearest_hospital_name=r["nearest_hospital_name"],
                nearest_hospital_phone=r["nearest_hospital_phone"],
                nearest_hospital_distance_km=r["nearest_hospital_distance_km"],
            )
            session.add(route)
            await session.flush()  # get route.id

            for b in r["baselines"]:
                session.add(RouteBaseline(
                    route_id=route.id,
                    month_start=b["month_start"],
                    month_end=b["month_end"],
                    risk_level=b["risk_level"],
                    reason=b["reason"],
                    notes=b["notes"],
                ))

            for p in r["pois"]:
                session.add(POI(
                    name=p["name"],
                    category=p["category"],
                    phone=p["phone"],
                    latitude=p["lat"],
                    longitude=p["lon"],
                    route_id=route.id,
                    notes=p["notes"],
                ))

        # Insert demo reporters (slug → route.id lookup)
        slug_to_id: dict[str, int] = {}
        route_result = await session.execute(select(Route))
        for route_obj in route_result.scalars().all():
            slug_to_id[route_obj.slug] = route_obj.id

        for rep in DEMO_REPORTERS:
            route_id = slug_to_id.get(rep["route_slug"])
            session.add(Reporter(
                name=rep["name"],
                phone=rep["phone"],
                role=rep["role"],
                location_name=rep["location_name"],
                route_id=route_id,
                consent_given=rep["consent_given"],
                consent_date=date.today() if rep["consent_given"] else None,
                active=True,
            ))

        await session.commit()
        print(f"✓ Seeded {len(ROUTES)} routes, {sum(len(r['baselines']) for r in ROUTES)} baselines, "
              f"{sum(len(r['pois']) for r in ROUTES) + len(UNIVERSAL_POIS)} POIs, "
              f"{len(DEMO_REPORTERS)} reporters")

    await engine.dispose()


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL", settings.database_url)
    print(f"Seeding database: {db_url.split('@')[-1]}")  # log host only, not credentials
    asyncio.run(seed(db_url))
