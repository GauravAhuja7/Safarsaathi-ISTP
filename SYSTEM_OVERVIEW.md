# SafarSathi — Complete System Overview

**What it is:** A multi-channel mountain travel safety system for the Mandi region of Himachal Pradesh.  
**Who it's for:** First-time visitors (parents visiting IIT Mandi, tourists) + local ground reporters (taxi drivers, dhaba owners, homestay operators).  
**Core idea:** The information exists locally (taxi drivers know when Parashar road washed out). SafarSathi packages and delivers it to tourists before they get on the bus.

---

## 1. The Problem It Solves

Three compounding failures in mountain travel safety:

- **Information asymmetry** — Taxi drivers at Mandi bus stand know the Parashar road is washed out. The parent arriving from Delhi does not.
- **Accessibility gap** — HP SDMA and IMD publish warnings on government websites. A 55-year-old from Lucknow will never find them.
- **Connectivity trap** — The routes where safety information matters most are exactly where internet access is zero.

---

## 2. The Three Routes Covered

| Route | Distance | Max Altitude | High-Risk Season |
|-------|----------|--------------|-----------------|
| Mandi → Parashar Lake | 63 km | 2,730 m | June–September |
| Mandi → Barot Valley | 65 km | 1,800 m | June–September |
| Mandi → Kullu/Manali (NH-3) | 170 km | 2,050 m | June–September |

---

## 3. Channels (How Users Reach SafarSathi)

### Channel 1: Telegram Bot — `@Safarsaathibot` (Primary for demo)
- Tourist sends route name → gets full risk brief
- Reporter sends `/report` → guides through condition submission (photo/video supported)
- Long-polling architecture (dev) / webhook (production)

### Channel 2: WhatsApp Bot (same logic, pending Meta API approval)
- Identical keyword matching and reporter flow
- Meta Cloud API for sending, webhook for receiving

### Channel 3: PWA Web App (offline-first)
- Works in airplane mode after first load
- Route risk page, offline checklists, emergency contacts, altitude guide, offline map
- `/report` page for website-based condition submissions

### Channel 4: SMS (stubbed)
- Codes: P1 / B1 / K1 / E / W
- Responses under 160 chars

### Channel 5: Physical (designed, not printed yet)
- Laminated wallet cards with QR code + emergency numbers
- A4 posters at Mandi ISBT and taxi stands

---

## 4. Data Sources the System Aggregates

| Source | What it provides | Scrape interval | Staleness threshold |
|--------|-----------------|-----------------|---------------------|
| IMD Mausam API | Weather forecast, rainfall alerts for Mandi district | Every 6 hours | 12 hours |
| HP SDMA (hpsdma.nic.in) | Disaster warnings, district-level alerts | Every 6 hours | 8 hours |
| HP PWD (hppwd.hp.gov.in) | Road closure announcements | Every 6 hours | 8 hours |
| Trusted reporter network | Ground-truth road conditions, photos | Real-time (on message) | 2 hours (fresh) / 24 hours (expire) |

All scrapers run on startup and every 6 hours via APScheduler. Each feeds into the risk engine.

---

## 5. The Risk Engine — How It Scores

Every route query runs `calculate_risk()` which combines six factors:

```
TOTAL SCORE = seasonal_baseline + weather + official_alerts + reporter + time_of_day + route_static
```

### Factor breakdown

| Factor | Range | Details |
|--------|-------|---------|
| **Seasonal baseline** | 1–5 | HIGH season (monsoon) = 5, MEDIUM (winter) = 3, LOW (spring) = 1 |
| **Weather score** | 0–5 | Red alert / very heavy rain = 5, Heavy rain = 5, Moderate = 3, Fog = 3, Snowfall = 4, Clear = 0, Stale data = 2 |
| **Official alerts** | 0–5 | Road officially closed = 5 + auto-HIGH override, Disaster warning = 4, Landslide = 3 |
| **Reporter score** | 0–3 | Blocked = 3, Rough = 1, Clear = 0, No reports = 1 (uncertainty penalty) |
| **Time of day** | 0–2 | Night (7PM–5AM) = 2, Dusk/dawn = 1, Daytime = 0 |
| **Route static risk** | 0–2 | Parashar = 2 (last 10km always rough), Barot = 2 (gorge road), NH-3 = 0 |

### Risk levels

| Level | Score | Colour |
|-------|-------|--------|
| 🔴 HIGH | ≥ 12 | Red |
| 🟡 MEDIUM | 7–11 | Amber |
| 🟢 LOW | ≤ 6 | Green |
| ⚫ UNKNOWN | — | Grey |

### Auto-override rules (bypass the score entirely)

1. **Official road closure alert** → always HIGH (score shown as 23)
2. **Fresh reporter "blocked" report (< 2 hours old)** → always HIGH (score shown as 20)
3. **Score = 11 during monsoon months (Jun–Sep)** → rounds up to HIGH (safety-first)
4. **Weather stale AND no recent reports AND not monsoon AND baseline ≠ HIGH** → UNKNOWN (never show false LOW)

---

## 6. The Reporter Network

### Who they are
10–15 in-person-verified locals: taxi drivers, dhaba owners, homestay operators along the three routes.

### How a reporter submits via Telegram

```
Reporter sends: /report
Bot: "Which route? 1=Parashar 2=Barot 3=Kullu-Manali"
Reporter sends: 1
Bot: "Condition? 1=Blocked 2=Rough 3=Clear 4=Other"
Reporter sends: 1
Bot: "Add a note or photo. Reply SKIP to finish."
Reporter sends: [photo of blocked road]
Bot: "Report saved. Thank you."
```

The report is saved with: route, condition, description, photo_url, source (telegram/whatsapp/website), reporter_id (if registered) or submitted_by (anonymous).

### Report lifecycle

| Age | How it's treated |
|-----|-----------------|
| < 2 hours + blocked | Auto-HIGH risk override |
| < 2 hours | Shown prominently as "very recent ✓" |
| 2–6 hours | Shown with "verify before travel" |
| 6–24 hours | Shown with "conditions may have changed" |
| > 24 hours | Expired — not used in scoring or display |

### How to add a registered reporter (admin API)

```bash
curl -X POST http://localhost:8000/reporters \
  -H "x-admin-key: safarsaathi-admin-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sharma Ji",
    "phone": "+919876543210",
    "role": "taxi_driver",
    "location_name": "Baggi village taxi stand",
    "route_slug": "parashar",
    "telegram_chat_id": 123456789,
    "consent_given": true
  }'
```

---

## 7. What a Tourist Sees (Full Telegram Flow)

**Tourist sends:** `Parashar`

**Bot replies:**
```
SafarSathi — Mandi to Parashar Lake
Risk Level: 🔴 HIGH

Road reported BLOCKED by local contact (0h ago)

Seasonal baseline: LOW | Road reported BLOCKED by local contact (0h ago)

Weather: Checking with IMD — call before travel
Local report: Road blocked  ← 0h ago

Nearest hospital: Mandi Zonal Hospital
📞 01905-222380

For current road status, call:
  • Sharma Ji (taxi driver): +919876543210

Reply checklist for pre-trip prep
Reply emergency for all emergency numbers
```

**If reporter sent a photo**, the bot sends a second message: the photo with caption "📸 Road condition photo from local reporter".

---

## 8. PWA (Web App) — What It Contains

| Page | What it shows | Works offline? |
|------|--------------|---------------|
| Home (Route List) | 3 route cards with current risk badge, monsoon alert | ✅ (cached) |
| Route Risk | Full risk brief — score, weather, local report, hospital, reporter contacts, share button | ✅ (localStorage fallback) |
| Checklist | Pre-trip 7-point checklist + altitude warning signs (Hindi + English) | ✅ fully offline |
| Emergency | All emergency numbers with search, one-tap call | ✅ fully offline |
| Altitude | AMS symptoms, emergency signs, DESCEND button → dials 108 | ✅ fully offline |
| Map | MapLibre GL map with POI markers (hospital, police, checkpoints) | ✅ hardcoded POIs |
| Report | Submit road condition with route selector, condition picker, photo upload, optional name | Online only (POST /reports) |

---

## 9. Backend Architecture

```
FastAPI (uvicorn, port 8000)
├── /routes              — Route list + risk API
├── /routes/{slug}/risk  — Full risk assessment
├── /weather             — IMD weather data
├── /emergency           — Emergency contacts
├── /reporters           — Reporter CRUD (admin-keyed)
├── /reports             — Public report submission + listing
├── /webhook/whatsapp    — Meta Cloud API webhook
├── /telegram/webhook    — Telegram webhook (production)
├── /health              — DB + scraper status
└── /docs                — Swagger UI

Database: SQLite (dev) / PostgreSQL + PostGIS (production)
Tables: routes, route_baselines, weather_cache, official_alerts,
        reporters, reporter_reports, pois

Scrapers (APScheduler, every 6 hours + on startup):
├── imd.py     — IMD weather API + HTML scrape fallback
├── sdma.py    — HP SDMA disaster alerts
└── pwd.py     — HP PWD road status
```

---

## 10. Running Locally

```bash
# Backend
cd backend
python3 -m uvicorn app.main:app --reload --port 8000

# Telegram bot (polling mode for dev)
cd backend
python3 -m telegram.polling

# Frontend
cd frontend
npm run dev     # http://localhost:5173

# Seed routes data (first time)
cd backend
python3 ../scripts/seed_routes.py
```

### Environment variables needed (backend/.env)

```
DATABASE_URL=sqlite+aiosqlite:///./safarsaathi.db
TELEGRAM_BOT_TOKEN=<your token>
WHATSAPP_ACCESS_TOKEN=<pending approval>
WHATSAPP_PHONE_NUMBER_ID=<pending approval>
WHATSAPP_VERIFY_TOKEN=safarsaathi_verify
IMD_API_KEY=<key>
```

---

## 11. What Is NOT Built Yet

| Feature | Status |
|---------|--------|
| SMS actual sending (MSG91) | Stubbed — returns placeholder |
| Offline map tiles (MBTiles) | POIs hardcoded, no real tile file |
| Hindi audio files | Component built, no audio recorded |
| Reporter onboarding (fieldwork) | Code ready, physical visits not done |
| Integration/load testing | Not done |
| User evaluation (SUS study) | Not done |
| Physical cards / posters | Design not started |
| Production deployment | Not done |

---

## 12. Key Safety Design Decisions

- **UNKNOWN not LOW** — stale data never shows as safe. If IMD data is > 12h old and no reporter has checked in, the route shows ⚫ UNKNOWN.
- **Fresh blocked report = instant HIGH** — a taxi driver reporting a blocked road in the last 2 hours overrides the entire scoring system.
- **Reporter reports expire in 24h** — old unverified reports don't pollute future queries.
- **Offline-first PWA** — emergency contacts and checklists work with zero network. The page that matters most (emergency numbers) has zero API calls.
- **Seasonal baselines as backbone** — the system gives useful guidance even when scrapers fail and no reporters have submitted. Monsoon = HIGH by default for mountain routes.
