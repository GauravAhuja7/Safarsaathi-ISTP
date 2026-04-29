# SafarSathi: Technical Implementation Plan

**Version:** 1.0
**Date:** April 2026
**Purpose:** Sprint-by-sprint build guide for the engineering team

---

## Repository Structure

```
safarsaathi/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── api/
│   │   │   ├── routes.py            # /routes/{route_id}/risk
│   │   │   ├── weather.py           # /weather/mandi
│   │   │   ├── emergency.py         # /emergency/{area}
│   │   │   └── reporters.py         # /reporters/report (intake)
│   │   ├── scrapers/
│   │   │   ├── imd.py               # IMD weather scraper
│   │   │   ├── sdma.py              # HP SDMA alerts scraper
│   │   │   ├── pwd.py               # HP PWD road status scraper
│   │   │   └── himachalroadstatus.py
│   │   ├── engine/
│   │   │   └── risk.py              # Risk score calculator
│   │   ├── models/
│   │   │   ├── route.py
│   │   │   ├── report.py
│   │   │   └── weather.py
│   │   └── db/
│   │       ├── session.py
│   │       └── seed_data.sql        # Static route baselines
│   ├── whatsapp/
│   │   ├── webhook.py               # Meta Cloud API webhook handler
│   │   ├── handlers/
│   │   │   ├── tourist.py           # Tourist message handlers
│   │   │   └── reporter.py          # Reporter report intake
│   │   ├── formatter.py             # Format risk response for WA
│   │   └── keywords.py              # Keyword → route mapping
│   └── sms/
│       └── gateway.py               # MSG91/Twilio SMS handler
├── frontend/                        # PWA
│   ├── public/
│   │   ├── manifest.json
│   │   └── sw.js                    # Service worker
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── RouteRisk.jsx
│   │   │   ├── Checklists.jsx
│   │   │   ├── Maps.jsx
│   │   │   ├── Emergency.jsx
│   │   │   └── Altitude.jsx
│   │   ├── components/
│   │   │   ├── RiskBadge.jsx
│   │   │   ├── AudioPlayer.jsx
│   │   │   └── OfflineMap.jsx
│   │   └── hooks/
│   │       └── useOfflineData.js
│   └── tiles/                       # MBTiles for offline maps
│       └── mandi-region.mbtiles
├── scripts/
│   ├── seed_routes.py               # Populate route baselines
│   ├── export_tiles.sh              # Generate MBTiles from OSM
│   └── verify_contacts.py           # Verify emergency numbers
└── docker-compose.yml               # Local dev: FastAPI + Postgres + Redis
```

---

## Sprint 1 (Week 5): Foundation

**Goal:** Backend running locally, seasonal baselines seeded, WhatsApp bot responds to route queries.

### Tasks

#### 1.1 Database Setup
```sql
-- routes table
CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,   -- 'parashar', 'barot', 'kullu-manali'
    name VARCHAR(100) NOT NULL,
    distance_km INTEGER,
    max_altitude_m INTEGER,
    last_connectivity_point VARCHAR(100),
    nearest_hospital_name VARCHAR(100),
    nearest_hospital_phone VARCHAR(20),
    nearest_hospital_distance_km INTEGER
);

-- route_baselines table (static seasonal risk)
CREATE TABLE route_baselines (
    id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES routes(id),
    month_start INTEGER,   -- 6 for June
    month_end INTEGER,     -- 9 for September
    risk_level VARCHAR(10),  -- 'LOW', 'MEDIUM', 'HIGH'
    reason TEXT,
    notes TEXT
);

-- weather_cache table
CREATE TABLE weather_cache (
    id SERIAL PRIMARY KEY,
    district VARCHAR(50),
    forecast_json JSONB,
    scraped_at TIMESTAMP,
    source VARCHAR(50)
);

-- official_alerts table
CREATE TABLE official_alerts (
    id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES routes(id),
    alert_type VARCHAR(50),   -- 'road_closed', 'disaster_warning', 'construction'
    description TEXT,
    source VARCHAR(50),
    scraped_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- reporters table
CREATE TABLE reporters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    phone VARCHAR(20) UNIQUE,
    role VARCHAR(50),   -- 'taxi_driver', 'dhaba_owner', 'homestay_owner'
    location_name VARCHAR(100),
    location GEOGRAPHY(POINT, 4326),
    route_id INTEGER REFERENCES routes(id),
    consent_given BOOLEAN DEFAULT FALSE,
    consent_date DATE,
    active BOOLEAN DEFAULT TRUE,
    strike_count INTEGER DEFAULT 0
);

-- reporter_reports table
CREATE TABLE reporter_reports (
    id SERIAL PRIMARY KEY,
    reporter_id INTEGER REFERENCES reporters(id),
    route_id INTEGER REFERENCES routes(id),
    condition VARCHAR(20),  -- 'blocked', 'rough', 'clear', 'other'
    description TEXT,
    photo_url VARCHAR(255),
    reported_at TIMESTAMP DEFAULT NOW()
);

-- pois table (points of interest for offline maps)
CREATE TABLE pois (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    category VARCHAR(50),   -- 'hospital', 'police', 'petrol', 'mechanic', 'reporter'
    phone VARCHAR(20),
    location GEOGRAPHY(POINT, 4326),
    route_id INTEGER REFERENCES routes(id),
    notes TEXT
);
```

#### 1.2 Seed Route Baselines
```python
# scripts/seed_routes.py
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
            {"month_start": 10, "month_end": 2, "risk_level": "MEDIUM",
             "reason": "Cold, possible snow above 2,500m, road slippery",
             "notes": "Last 10km rough even in good conditions"},
            {"month_start": 3, "month_end": 5, "risk_level": "LOW",
             "reason": "Best window. Road dry, visibility good.",
             "notes": "Altitude prep still needed"},
            {"month_start": 6, "month_end": 9, "risk_level": "HIGH",
             "reason": "Landslide-prone, road past Baggi frequently washed out",
             "notes": "Do NOT travel without calling ahead"},
        ]
    },
    # ... Barot, Kullu-Manali
]
```

#### 1.3 Risk Engine
```python
# app/engine/risk.py

SEASONAL_SCORES = {"HIGH": 5, "MEDIUM": 3, "LOW": 1}

def calculate_risk(route_id: int, current_month: int, current_hour: int, db) -> dict:
    baseline = get_seasonal_baseline(route_id, current_month, db)
    weather = get_latest_weather(db)
    alerts = get_active_alerts(route_id, db)
    reports = get_recent_reports(route_id, db)

    # Auto-HIGH if road officially closed
    if any(a.alert_type == "road_closed" for a in alerts):
        return {"level": "HIGH", "reason": "Road officially closed by HP PWD/SDMA"}

    score = SEASONAL_SCORES[baseline.risk_level]

    # Weather score
    if weather and is_fresh(weather.scraped_at, hours=12):
        score += weather_score(weather.forecast_json)
    else:
        score += 2  # Stale data uncertainty penalty

    # Official alerts score
    score += alerts_score(alerts)

    # Stakeholder reports
    recent_reports = [r for r in reports if hours_ago(r.reported_at) < 24]
    if recent_reports:
        score += reporter_score(recent_reports)
    else:
        score += 1  # No reports uncertainty penalty

    # Time of day
    if current_hour >= 19 or current_hour < 5:
        score += 2
    elif current_hour in [5, 6, 18]:
        score += 1

    # Route static risk (hardcoded per route)
    score += route_static_risk(route_id)

    # Determine level
    if score >= 12:
        level = "HIGH"
    elif score >= 7:
        level = "MEDIUM"
    elif score <= 6:
        level = "LOW"

    # UNKNOWN override: stale weather AND no reports AND not monsoon
    if not is_fresh(weather, 12) and not recent_reports and baseline.risk_level != "HIGH":
        level = "UNKNOWN"

    # Safety tie-breaker: score 11 in monsoon → HIGH
    if score == 11 and current_month in range(6, 10):
        level = "HIGH"

    return {"level": level, "score": score, "baseline": baseline.risk_level}
```

#### 1.4 WhatsApp Bot Keyword Map
```python
# whatsapp/keywords.py

ROUTE_KEYWORDS = {
    "parashar": ["parashar", "prashar", "parshar", "parashar lake", "parashar jheel"],
    "barot": ["barot", "brot", "barod", "barot valley", "barot ghati"],
    "kullu": ["kullu", "manali", "kullu manali", "nh3", "nh 3", "nh21", "national highway"],
}

INTENT_KEYWORDS = {
    "weather": ["weather", "mausam", "barish", "rain", "baarish"],
    "emergency": ["emergency", "help", "hospital", "ambulance", "doctor", "accident"],
    "checklist": ["checklist", "prepare", "taiyari", "kya lana", "what to bring"],
    "report": ["report", "condition", "road", "rasta", "block", "band"],
}
```

---

## Sprint 2 (Week 6): Scrapers & WhatsApp Responses

**Goal:** IMD data flowing into DB. WhatsApp bot returns formatted responses with real weather data.

### 2.1 IMD Scraper
```python
# app/scrapers/imd.py
import httpx
from bs4 import BeautifulSoup

IMD_MANDI_URL = "https://mausam.imd.gov.in/responsive/districtforecastmain.php?id=HP"

async def scrape_imd_mandi():
    """Scrapes IMD district forecast for Mandi. Falls back to web page if API unavailable."""
    try:
        # Try API first
        async with httpx.AsyncClient() as client:
            r = await client.get(IMD_API_URL, timeout=10)
            if r.status_code == 200:
                return parse_imd_api(r.json())
    except Exception:
        pass

    # Fallback: scrape webpage
    async with httpx.AsyncClient() as client:
        r = await client.get(IMD_MANDI_URL, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        return parse_imd_html(soup)
```

### 2.2 WhatsApp Response Formatter
```python
# whatsapp/formatter.py

RISK_EMOJI = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢", "UNKNOWN": "⚫"}

def format_route_response(route, risk, weather, latest_report, reporters_on_route) -> str:
    lines = [
        f"*SafarSathi -- {route.name}*",
        f"Risk Level: {RISK_EMOJI[risk['level']]} *{risk['level']}*",
        "",
    ]

    if risk["level"] == "HIGH":
        lines.append("⚠️ HIGH RISK: Use extra caution. Consider postponing or calling ahead.")
    elif risk["level"] == "UNKNOWN":
        lines.append("⚫ Current conditions not verified. Call a local before traveling.")

    if weather and is_fresh(weather):
        lines.append(f"🌦 Weather: {weather.summary} (IMD, {hours_ago(weather.scraped_at)}h ago)")

    if latest_report:
        lines.append(f"📍 Local report: {latest_report.condition_display} ({hours_ago(latest_report.reported_at)}h ago)")

    lines.extend([
        "",
        f"🏥 Nearest Hospital: {route.nearest_hospital_name}",
        f"📞 {route.nearest_hospital_phone}",
        "",
        "For current road status, call:",
    ])

    for r in reporters_on_route[:2]:  # Max 2 reporters shown
        lines.append(f"  • {r.name} ({r.role}): {r.phone}")

    lines.extend([
        "",
        "Reply *checklist* for pre-trip prep",
        "Reply *emergency* for all emergency numbers",
    ])

    return "\n".join(lines)
```

---

## Sprint 3 (Week 7): PWA Core

**Goal:** PWA loads, installs offline, shows route risk and checklists without internet.

### 3.1 Service Worker Strategy
```javascript
// frontend/public/sw.js

const STATIC_CACHE = 'safarsaathi-static-v1';
const DATA_CACHE = 'safarsaathi-data-v1';

// Cache on install -- everything needed for offline
const STATIC_ASSETS = [
    '/',
    '/checklists',
    '/emergency',
    '/altitude',
    '/audio/checklist-water-hi.mp3',
    // ... all audio files
    '/tiles/mandi-region.mbtiles',
];

// Cache-first for static, network-first-with-fallback for API
self.addEventListener('fetch', (event) => {
    if (event.request.url.includes('/api/')) {
        event.respondWith(networkFirstWithFallback(event.request));
    } else {
        event.respondWith(cacheFirst(event.request));
    }
});
```

### 3.2 Offline Map Setup
```bash
# scripts/export_tiles.sh
# Generate MBTiles from OpenStreetMap data for Mandi region

# Download HP region OSM data
wget https://download.geofabrik.de/asia/india/himachal-pradesh-latest.osm.pbf

# Convert to MBTiles (zoom 10-15, Mandi bbox)
tippecanoe \
    --output=frontend/tiles/mandi-region.mbtiles \
    --minimum-zoom=10 \
    --maximum-zoom=15 \
    --clip-bounding-box=76.8,31.5,77.6,32.2 \
    himachal-pradesh.geojson
```

### 3.3 Checklist Data (Offline JSON)
```json
// frontend/src/data/checklists.json
{
  "pre_trip": [
    {
      "id": "water",
      "text": "Drink 4-6 liters of water daily starting the day before",
      "hindi": "यात्रा से एक दिन पहले से 4-6 लीटर पानी पियें",
      "audio": "/audio/checklist-water-hi.mp3",
      "icon": "💧"
    },
    {
      "id": "alcohol",
      "text": "Avoid alcohol for first 24 hours at altitude",
      "hindi": "पहाड़ पर पहले 24 घंटे शराब न पियें",
      "audio": "/audio/checklist-alcohol-hi.mp3",
      "icon": "🚫"
    }
    // ... more items
  ],
  "emergency_signs": [
    {
      "id": "ams_mild",
      "text": "Mild AMS: Headache, nausea, dizziness -- rest and drink water",
      "hindi": "हल्की तकलीफ: सिरदर्द, मतली -- आराम करें और पानी पियें",
      "audio": "/audio/ams-mild-hi.mp3",
      "icon": "⚠️"
    },
    {
      "id": "ams_severe",
      "text": "SEVERE: Confusion, blue lips, can't walk straight -- DESCEND IMMEDIATELY",
      "hindi": "गंभीर: भ्रम, नीले होंठ, सीधे न चल पाएं -- तुरंत नीचे उतरें",
      "audio": "/audio/ams-severe-hi.mp3",
      "icon": "🆘"
    }
  ]
}
```

---

## Sprint 4 (Week 8): Reporter Network & SMS

**Goal:** Reporters can submit via WhatsApp. SMS fallback live.

### 4.1 Reporter Report Intake Flow
```
Reporter sends "report" to bot
    ↓
Bot: "Kaunsa rasta? 1=Parashar, 2=Barot, 3=Kullu-Manali, 4=Aur"
    ↓
Reporter sends "1"
    ↓
Bot: "Raste ki halat? 1=Band hai, 2=Khula par khatarnak, 3=Theek hai, 4=Kuch aur"
    ↓
Reporter sends "2"
    ↓
Bot: "Photo ya voice note bhej sakte hain (optional). Warna kuch bhi bhejein aage badhne ke liye."
    ↓
Reporter sends photo (or "ok")
    ↓
Bot: "Shukriya! Parashar route report darj ho gayi: Khula par khatarnak. Tourists ko yeh jaankari milegi."
    ↓
DB: INSERT into reporter_reports
```

### 4.2 Tourist-Reporter Lead System
```python
# whatsapp/handlers/tourist.py

async def handle_route_query(tourist_phone: str, route: Route, risk: dict, db):
    # Send safety response to tourist
    response = format_route_response(route, risk, ...)
    await send_whatsapp(tourist_phone, response)

    # If HIGH risk, also offer to connect with a reporter
    if risk["level"] in ["HIGH", "UNKNOWN"]:
        active_reporters = get_active_reporters_for_route(route.id, db)
        if active_reporters:
            reporter = active_reporters[0]  # Primary reporter for this route
            if reporter.consent_given:
                # Notify reporter of tourist lead
                lead_msg = (
                    f"SafarSathi: Ek tourist {route.name} ke baare mein puch raha hai. "
                    f"Unhe taxi/madad chahiye ho sakti hai. "
                    f"Unka number: {tourist_phone}"
                )
                await send_whatsapp(reporter.phone, lead_msg)
```

### 4.3 SMS Gateway
```python
# sms/gateway.py

ROUTE_CODES = {
    "P1": "parashar", "B1": "barot", "K1": "kullu-manali",
    "E": "emergency", "W": "weather"
}

async def handle_sms(from_number: str, body: str) -> str:
    code = body.strip().upper()
    if code not in ROUTE_CODES:
        return "SafarSathi: P1=Parashar, B1=Barot, K1=Kullu-Manali, E=Emergency, W=Weather"

    if code == "E":
        return "EMERGENCY: Ambulance 108 | Police 100 | Disaster 1077 | Mandi Hospital 01905-222380"

    if code == "W":
        weather = get_latest_weather()
        return f"MANDI WEATHER: {weather.sms_summary} (IMD, {hours_ago(weather.scraped_at)}h ago)"

    route_slug = ROUTE_CODES[code]
    risk = calculate_risk_for_sms(route_slug)
    return format_sms_response(route_slug, risk)  # Must be < 160 chars
```

---

## Sprint 5 (Week 9): Polish, Physical Materials, Deploy

**Goal:** Everything working end-to-end. Physical cards designed and sent to print.

### 5.1 Health Check Monitoring
```python
# app/api/health.py

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    issues = []

    # Check weather data freshness
    weather = await get_latest_weather(db)
    if not weather or hours_ago(weather.scraped_at) > 8:
        issues.append("IMD weather data stale")
        # Alert team via WhatsApp
        await send_whatsapp(TEAM_ADMIN_PHONE, f"⚠️ SafarSathi Alert: IMD data stale ({hours_ago(weather.scraped_at)}h old)")

    # Check DB connection
    try:
        await db.execute("SELECT 1")
    except Exception:
        issues.append("Database unreachable")

    return {"status": "ok" if not issues else "degraded", "issues": issues}
```

### 5.2 Physical Card Content

**Front (wallet card):**
```
SafarSathi -- Mountain Safety

EMERGENCY:
Ambulance: 108
Police: 100
Disaster: 1077
Mandi Hospital: 01905-222380

3 Rules Before Mountain Travel:
1. Check weather (WhatsApp: [bot number])
2. Tell someone your route and ETA
3. Carry water + a warm layer

[QR CODE → WhatsApp Bot]
```

**Back:**
```
Route Quick Reference:
Parashar: Last 10km rough | Baggi = last phone signal
Barot: 35km narrow gorge | No overtaking
NH3 Manali: Pandoh-Aut = landslide zone

Altitude Sickness (above 2,500m):
Headache + nausea = Rest, drink water
Confusion + blue lips = DESCEND NOW, call 108
```

### 5.3 Deployment Checklist
- [ ] Railway/Render account created, backend deployed
- [ ] PostgreSQL (Supabase free tier or Railway Postgres) provisioned and seeded
- [ ] Redis (Upstash free tier) connected
- [ ] WhatsApp Business API number verified and templates approved
- [ ] Meta webhook URL configured and verified
- [ ] IMD scraper running on schedule (every 6 hours)
- [ ] SDMA scraper running on schedule (every 6 hours)
- [ ] SMS gateway (MSG91) account funded and number registered
- [ ] PWA deployed to Vercel/Netlify with HTTPS (required for service worker)
- [ ] MBTiles served from CDN (or bundled in PWA)
- [ ] All emergency numbers verified by calling them
- [ ] Hindi audio files recorded, reviewed by native speaker, uploaded
- [ ] Physical cards PDF sent to print shop
- [ ] QR code posters placed at ISBT and campus gate
- [ ] 10-15 reporters onboarded, consent forms signed, test reports submitted

---

## Testing Plan

### Unit Tests
- Risk engine: test all score combinations, verify HIGH threshold, verify UNKNOWN conditions
- Keyword matcher: test all route name variants including typos
- SMS formatter: verify all responses are < 160 characters
- Report time-decay: verify reports fade at correct intervals

### Integration Tests
- WhatsApp webhook → bot response (use test phone number)
- IMD scraper → DB insert → risk engine reads fresh data
- Reporter report → DB → tourist sees updated report
- Airplane mode → PWA loads all checklists, emergency contacts, map

### User Acceptance Tests (Week 9-12)
- Give test users a route + season scenario, ask them to find the risk level (via bot or PWA)
- Measure: time to correct answer, errors made, SUS score after 3 tasks
- Ask: "Would you use this before a mountain trip?" (Likert 1-5)

---

## Known Limitations (Document Honestly in Final Report)

1. **No true real-time road status.** The system provides the best available information, not live traffic. Users must call a local for definitive current status.
2. **Reporter network sustainability.** The 10-15 reporters onboarded for evaluation may not continue reporting after the project ends without ongoing relationship management.
3. **WhatsApp dependency.** If Meta changes API pricing or terms, the primary channel breaks. Telegram and SMS are partial fallbacks.
4. **Scraper fragility.** Gov websites change structure without notice. Scrapers require maintenance.
5. **Coverage limited to 3 routes.** Expanding to more routes requires more fieldwork and reporter onboarding.
6. **Language.** Hindi + basic English. Tourists speaking other languages (South Indian tourists are also common in HP) are underserved.
