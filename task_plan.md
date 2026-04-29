# SafarSathi: Detailed Task Plan (Phase-by-Phase)

**Version:** 1.0
**Date:** April 2026
**Team:** Arman Rawat, Gaurav Ahuja, Tanish Kumar, Anuj Aggarwal

---

## How to Read This Plan

- Each task has an **owner** (suggested), **estimated time**, and **done criteria**
- Tasks within a phase can be parallelized unless marked `[BLOCKS NEXT]`
- Mark each task done in your project tracker when the done criteria is met, not when you "think it's done"
- If a task takes 2x estimated time, flag it immediately -- don't silently sl

---

## Phase 0: Project Setup (Week 1, Day 1-2)

These tasks unblock everything else. Do them on day one.

---

### Task 0.1 — Create GitHub Repository
**Owner:** Arman | **Time:** 30 min

Steps:
1. Create a private GitHub repo named `safarsaathi`
2. Add all 4 team members as collaborators
3. Create branch protection on `main`: require PR + 1 review before merge
4. Create branches: `main`, `dev`, `feat/backend`, `feat/whatsapp`, `feat/pwa`
5. Add a `.gitignore` for Python + Node

**Done:** All 4 members can push to `dev`. `main` is protected.

---

### Task 0.2 — Set Up Local Dev Environment (Each Team Member)
**Owner:** All | **Time:** 1 hour per person

Steps:
1. Install Python 3.11+, Node 20+, Docker Desktop
2. Clone the repo
3. Copy `.env.example` to `.env` (create `.env.example` with all required keys listed but empty)
4. Run `docker-compose up` -- confirm PostgreSQL and Redis start
5. Run `python -m pytest` -- confirm test runner works (0 tests, 0 failures)

**Done:** `docker-compose up` starts cleanly on every team member's machine.

---

### Task 0.3 — Create Folder Structure
**Owner:** Gaurav | **Time:** 45 min

Steps:
1. Create the full folder structure as defined in `technical_implementation_plan.md`
2. Add empty `__init__.py` in each Python package folder
3. Add placeholder `README.md` in `backend/`, `frontend/`, `scripts/`
4. Create `docker-compose.yml` with services: `api` (FastAPI), `db` (Postgres 15 + PostGIS), `redis` (Redis 7)
5. Create `requirements.txt`: `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `httpx`, `beautifulsoup4`, `redis`, `apscheduler`, `python-dotenv`
6. Create `frontend/package.json` with: `vite`, `react`, `react-dom`, `maplibre-gl`

**Done:** `docker-compose up` starts all 3 services. `pip install -r requirements.txt` works.

---

### Task 0.4 — Set Up WhatsApp Business API (Start Early -- Takes Time)
**Owner:** Tanish | **Time:** 2-3 days (approval wait)

Steps:
1. Go to developers.facebook.com → create a Meta App of type "Business"
2. Add "WhatsApp" product to the app
3. Use a dedicated phone number (buy a new SIM if needed -- cannot reuse a number already on WhatsApp)
4. Submit for WhatsApp Business API access
5. While waiting: set up the webhook locally using `ngrok` for development testing
6. Document the test phone number and test credentials in the team's shared password manager

**Done:** Can send and receive a WhatsApp message via the Meta Cloud API using `curl`.

> If approval takes > 5 days: proceed with Task 0.4b.

### Task 0.4b — Set Up Telegram Bot (Parallel Fallback)
**Owner:** Tanish | **Time:** 1 hour

Steps:
1. Open Telegram, message `@BotFather`
2. Create a bot named `SafarSathiBot`
3. Get the bot token
4. Set up a webhook endpoint (same logic as WhatsApp webhook)
5. Test: send "parashar" to the bot, confirm it responds

**Done:** Telegram bot responds to messages. Same backend logic as WhatsApp bot.

---

### Task 0.5 — Create Shared `.env` Template
**Owner:** Arman | **Time:** 30 min

Create `.env.example` with all keys needed (empty values):
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/safarsaathi
REDIS_URL=redis://localhost:6379
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
TELEGRAM_BOT_TOKEN=
MSG91_API_KEY=
TEAM_ADMIN_PHONE=
```

**Done:** `.env.example` committed to repo. `.env` added to `.gitignore`.

---

## Phase 1: Database & Backend Foundation (Week 5, Days 1-3)

---

### Task 1.1 — Write Database Schema (SQL)
**Owner:** Gaurav | **Time:** 2 hours
**Blocks:** Task 1.2, 1.3, 1.4

Steps:
1. Create `backend/app/db/schema.sql` with all 7 tables:
   - `routes`
   - `route_baselines`
   - `weather_cache`
   - `official_alerts`
   - `reporters`
   - `reporter_reports`
   - `pois`
2. Add indexes:
   - `reporter_reports(route_id, reported_at DESC)` -- for fetching recent reports per route
   - `official_alerts(route_id, expires_at)` -- for active alert queries
   - `weather_cache(district, scraped_at DESC)` -- for latest weather per district
3. Add a `CREATE EXTENSION IF NOT EXISTS postgis;` at the top
4. Test: run the schema against a fresh Postgres+PostGIS container, confirm all tables create without errors

**Done:** `psql < schema.sql` runs with 0 errors on a fresh DB.

---

### Task 1.2 — Set Up SQLAlchemy Models
**Owner:** Gaurav | **Time:** 2 hours
**Depends on:** Task 1.1

Steps:
1. Create `backend/app/db/session.py` -- async SQLAlchemy engine + session factory
2. Create `backend/app/models/route.py` -- `Route` and `RouteBaseline` ORM models
3. Create `backend/app/models/weather.py` -- `WeatherCache` and `OfficialAlert` ORM models
4. Create `backend/app/models/report.py` -- `Reporter` and `ReporterReport` ORM models
5. Create `backend/app/models/poi.py` -- `POI` ORM model
6. Write a migration script or use `schema.sql` directly (Alembic is optional for MVP -- direct SQL is fine)

**Done:** Can `from app.models.route import Route` in a Python shell without import errors.

---

### Task 1.3 — Seed Static Route Data
**Owner:** Arman | **Time:** 3 hours
**Depends on:** Task 1.2

Steps:
1. Create `scripts/seed_routes.py`
2. Add complete data for Route 1: Mandi → Parashar Lake
   - Route record + 3 seasonal baselines (LOW/MEDIUM/HIGH)
   - 5+ POIs: Mandi Zonal Hospital, Baggi village checkpoint, nearest mechanic, petrol pump, police post
3. Add complete data for Route 2: Mandi → Barot Valley
   - Route record + 3 seasonal baselines
   - 4+ POIs: Jogindernagar Hospital, Ghatasani taxi stand, fuel point, police post
4. Add complete data for Route 3: Mandi → Kullu/Manali (NH3)
   - Route record + 3 seasonal baselines
   - 5+ POIs: Pandoh police post, Aut mechanic, Kullu hospital, NHAI helpline
5. Add the 6 universal emergency contacts as POIs (type = `emergency`)
6. Run the seed script against the dev DB
7. Verify with a SQL query: `SELECT slug, risk_level FROM routes JOIN route_baselines ...`

**Done:** DB has 3 routes, 9 baselines, 20+ POIs. All verify correctly with SQL queries.

---

### Task 1.4 — Build FastAPI Entry Point
**Owner:** Arman | **Time:** 2 hours
**Depends on:** Task 1.2

Steps:
1. Create `backend/app/main.py`
   - Initialize FastAPI app
   - Include routers (placeholder routes for now): `/routes`, `/weather`, `/emergency`, `/reporters`, `/health`
   - Add CORS middleware (allow all origins for MVP)
   - Connect to DB on startup via `lifespan` event
2. Create `backend/app/api/health.py` -- GET `/health` that checks DB and Redis connectivity
3. Test: run `uvicorn app.main:app --reload`, hit `localhost:8000/health`, confirm 200 response

**Done:** `GET /health` returns `{"status": "ok"}`. Swagger UI at `/docs` shows all routes.

---

### Task 1.5 — Build Risk Engine
**Owner:** Tanish | **Time:** 4 hours
**Depends on:** Task 1.3

Steps:
1. Create `backend/app/engine/risk.py`
2. Implement `get_seasonal_baseline(route_id, month, db)` -- query route_baselines for current month
3. Implement `weather_score(forecast_json)` -- parse IMD JSON, return 0-5 score
4. Implement `alerts_score(alerts)` -- return 0-5 based on active alert types
5. Implement `reporter_score(reports)` -- return 0-3 based on most recent report condition
6. Implement `route_static_risk(route_id)` -- hardcoded per-route values (Parashar=2, Barot=2, NH3=0)
7. Implement `calculate_risk(route_id, month, hour, db)` -- main function combining all scores
8. Write unit tests in `tests/test_risk_engine.py`:
   - Test: Parashar + July + night + heavy rain → HIGH
   - Test: Parashar + April + daytime + clear → LOW
   - Test: stale weather + no reports + not monsoon → UNKNOWN
   - Test: official road closure → HIGH regardless of other scores
   - Test: score=11 in monsoon → HIGH (tie-breaker)
   - Test: score=11 in April → MEDIUM (no tie-breaker)
9. Run tests: `pytest tests/test_risk_engine.py -v`

**Done:** All 6 unit tests pass. Risk engine correctly calculates scores for all test scenarios.

---

### Task 1.6 — Build Route Risk API Endpoint
**Owner:** Tanish | **Time:** 2 hours
**Depends on:** Task 1.5

Steps:
1. Create `backend/app/api/routes.py`
2. Implement `GET /routes` -- list all routes with slug, name, distance, max altitude
3. Implement `GET /routes/{slug}/risk` -- returns full risk assessment for a route:
   ```json
   {
     "route": "parashar",
     "risk_level": "HIGH",
     "score": 14,
     "seasonal_baseline": "HIGH",
     "weather_summary": "Heavy rainfall warning (IMD, 3h ago)",
     "latest_report": "Road rough past Baggi (2h ago)",
     "nearest_hospital": "Mandi Zonal Hospital — 01905-222380",
     "reporters": [{"name": "Sharma Dhaba", "phone": "98765XXXXX"}]
   }
   ```
4. Test with curl: `curl localhost:8000/routes/parashar/risk`

**Done:** API returns correct risk level and all required fields. Responds in < 500ms.

---

## Phase 2: Data Scrapers (Week 5, Days 3-5)

---

### Task 2.1 — Build IMD Weather Scraper
**Owner:** Gaurav | **Time:** 4 hours

Steps:
1. Create `backend/app/scrapers/imd.py`
2. Investigate IMD API at `mausam.imd.gov.in/responsive/apis.php` -- try to get a Mandi district response
3. If API works: implement `parse_imd_api(json_response)` → extract temperature, rainfall forecast, alerts
4. If API fails or requires registration: implement HTML scraper using BeautifulSoup
5. Implement `scrape_imd_mandi()` -- tries API first, falls back to HTML scraper
6. Implement `weather_to_summary(parsed_data)` → returns a human-readable string: "Heavy rain expected in next 24h"
7. Implement `save_weather_to_db(parsed_data, db)` -- upsert into `weather_cache` table
8. Test: run manually, confirm data saves to DB with correct timestamp
9. Test: manually set `scraped_at` to 13 hours ago, confirm `is_fresh()` returns False

**Done:** Running `python -c "from scrapers.imd import scrape_imd_mandi; import asyncio; asyncio.run(scrape_imd_mandi())"` saves a weather record to the DB with `scraped_at` set to now.

---

### Task 2.2 — Build HP SDMA Alert Scraper
**Owner:** Gaurav | **Time:** 3 hours

Steps:
1. Create `backend/app/scrapers/sdma.py`
2. Visit `hpsdma.nic.in` manually -- identify where district alerts appear on the page
3. Implement HTML scraper: fetch page, find Mandi-relevant alert elements
4. Implement `parse_sdma_alerts(soup)` → list of `{type, description, district, date}`
5. Implement `filter_mandi_alerts(alerts)` -- keep only alerts mentioning "Mandi" or relevant route names
6. Implement `save_alerts_to_db(alerts, db)` -- insert new alerts, skip duplicates (check description hash)
7. Test: run scraper, check DB for any alerts (may be empty if no current alerts -- that's fine)
8. Add scraper to health check: if scraper hasn't run in > 8 hours, add to issues list

**Done:** Scraper runs without error. Saves 0 or more alerts to DB depending on current HP situation.

---

### Task 2.3 — Build HP PWD Road Status Scraper
**Owner:** Arman | **Time:** 3 hours

Steps:
1. Create `backend/app/scrapers/pwd.py`
2. Visit `hppwd.hp.gov.in` manually -- find road status / road closure announcements
3. Implement HTML scraper targeting road status announcements
4. Filter for Mandi district roads (Parashar, Barot, Pandoh, NH3/NH21)
5. Classify each item as: `road_closed`, `construction`, `landslide`, `other`
6. Save to `official_alerts` table with `source = "HP_PWD"`
7. Test: run scraper manually, verify no crashes

**Done:** Scraper runs without error. Any found road statuses appear in `official_alerts` table.

---

### Task 2.4 — Build Scheduler (Run Scrapers Every 6 Hours)
**Owner:** Arman | **Time:** 2 hours
**Depends on:** Task 2.1, 2.2, 2.3

Steps:
1. Add APScheduler to `requirements.txt`
2. In `backend/app/main.py`, add scheduler startup in the `lifespan` event:
   ```python
   scheduler.add_job(scrape_imd_mandi, 'interval', hours=6)
   scheduler.add_job(scrape_sdma_alerts, 'interval', hours=6)
   scheduler.add_job(scrape_pwd_status, 'interval', hours=6)
   scheduler.start()
   ```
3. Also add a scraper run on app startup (so data is fresh immediately after deploy)
4. Add scheduler status to `/health` endpoint: report last run time for each scraper
5. Test: set interval to 1 minute temporarily, confirm all 3 scrapers run on schedule

**Done:** `/health` shows `last_imd_scrape`, `last_sdma_scrape`, `last_pwd_scrape` with timestamps.

---

## Phase 3: WhatsApp Bot (Week 6)

---

### Task 3.1 — Build WhatsApp Webhook Handler
**Owner:** Tanish | **Time:** 3 hours

Steps:
1. Create `backend/whatsapp/webhook.py`
2. Implement `GET /webhook` -- Meta webhook verification (echo `hub.challenge` if `hub.verify_token` matches)
3. Implement `POST /webhook` -- receive incoming messages, parse sender phone + message body
4. Route incoming messages:
   - Identify if sender is a tourist or a registered reporter (check `reporters` table by phone)
   - If reporter: route to `reporter.py` handler
   - If tourist: route to `tourist.py` handler
5. Add webhook URL to FastAPI router in `main.py`
6. Test using `ngrok http 8000` + configure Meta webhook URL to ngrok tunnel
7. Send a test message to the bot number, confirm it appears in server logs

**Done:** Sending "hello" to the bot number appears as a parsed message in server logs.

---

### Task 3.2 — Build Keyword Router
**Owner:** Tanish | **Time:** 2 hours

Steps:
1. Create `backend/whatsapp/keywords.py`
2. Define `ROUTE_KEYWORDS` dict with all spelling variants (see technical plan)
3. Define `INTENT_KEYWORDS` for weather, emergency, checklist, report
4. Implement `match_route(message_text)` → returns route slug or None
5. Implement `match_intent(message_text)` → returns intent string or None
6. Handle case-insensitive matching, strip punctuation, strip leading/trailing spaces
7. Write unit tests:
   - "Parashar" → "parashar"
   - "parashar lake" → "parashar"
   - "prashar" → "parashar" (typo)
   - "barot ghati" → "barot"
   - "mausam" → intent: "weather"
   - "hospital" → intent: "emergency"
   - "xyz" → None, None

**Done:** All keyword unit tests pass.

---

### Task 3.3 — Build Tourist Message Handler
**Owner:** Arman | **Time:** 4 hours
**Depends on:** Task 3.2, Task 1.6

Steps:
1. Create `backend/whatsapp/handlers/tourist.py`
2. Implement `handle_tourist_message(phone, message, db)`:
   - Match route → call `/routes/{slug}/risk` logic internally
   - Match intent → call appropriate handler
   - If no match: return help message listing available commands
3. Implement `handle_route_query(phone, route_slug, db)`:
   - Get risk assessment
   - Format WhatsApp response via `formatter.py`
   - Send to tourist via Meta API
   - If risk is HIGH or UNKNOWN: also send tourist's number to the primary reporter on that route
4. Implement `handle_weather_intent(phone, db)`:
   - Get latest IMD weather from DB
   - If fresh: send summary
   - If stale: send "Weather data updating, check back in 1 hour. For current status: IMD Mandi 0177-2629747"
5. Implement `handle_emergency_intent(phone)`:
   - Send static emergency contact list (no DB needed -- hardcoded)
6. Implement `handle_checklist_intent(phone)`:
   - Send the 8-item pre-trip checklist as a formatted WhatsApp message
7. Implement `handle_location_pin(phone, lat, lon, db)`:
   - Query `pois` table using PostGIS: find nearest hospital, police station, mechanic within 50 km
   - Return top result for each category

**Done:** Send "Parashar" to bot → receive formatted risk response with risk level, weather, reporter contact.

---

### Task 3.4 — Build Response Formatter
**Owner:** Arman | **Time:** 2 hours
**Depends on:** Task 3.3

Steps:
1. Create `backend/whatsapp/formatter.py`
2. Implement `format_route_response(route, risk, weather, report, reporters)` → WhatsApp-formatted string
3. Rules:
   - Total message length < 1000 chars (WhatsApp readable limit)
   - Bold (`*text*`) for route name and risk level
   - Emoji risk indicators: HIGH=🔴, MEDIUM=🟡, LOW=🟢, UNKNOWN=⚫
   - Always include hospital name + phone number
   - Always include "Reply emergency for all numbers"
   - If reporters available: include max 2 reporter contacts
4. Implement `format_checklist()` → Hindi + English checklist as WhatsApp message
5. Implement `format_emergency()` → all emergency numbers formatted
6. Test: generate sample responses for each route × each risk level, review formatting manually

**Done:** Sample messages reviewed by team -- readable, clear, under 1000 chars each.

---

### Task 3.5 — Build Reporter Intake Handler
**Owner:** Tanish | **Time:** 3 hours
**Depends on:** Task 3.1

Steps:
1. Create `backend/whatsapp/handlers/reporter.py`
2. Implement a stateful conversation flow using Redis to track conversation state per reporter phone:
   - State: `IDLE` → `AWAITING_ROUTE` → `AWAITING_CONDITION` → `AWAITING_DETAILS` → `DONE`
3. Implement each state handler:
   - `IDLE` + "report": → send route selection menu, set state to `AWAITING_ROUTE`
   - `AWAITING_ROUTE` + "1"/"2"/"3": → set route, send condition menu, set state to `AWAITING_CONDITION`
   - `AWAITING_CONDITION` + "1"/"2"/"3"/"4": → set condition, ask for optional photo/voice note, set state to `AWAITING_DETAILS`
   - `AWAITING_DETAILS` + any message/media: → save report to DB, send confirmation, reset state to `IDLE`
4. Handle timeout: if state doesn't progress in 30 minutes, reset to `IDLE` automatically
5. Test: simulate full flow via WhatsApp, confirm report appears in `reporter_reports` DB table

**Done:** A registered reporter can complete the full report flow via WhatsApp. Report saved to DB with correct route, condition, and timestamp.

---

### Task 3.6 — Build WhatsApp API Sender
**Owner:** Gaurav | **Time:** 2 hours

Steps:
1. Create `backend/whatsapp/client.py`
2. Implement `send_whatsapp(to_phone: str, message: str)` -- POST to Meta Cloud API
3. Handle errors: rate limit (wait + retry), invalid number (log + skip), API down (log + return False)
4. Implement `send_whatsapp_template(to_phone, template_name, params)` -- for approved Meta templates
5. Add a simple rate limiter: max 10 messages per second, queue overflow
6. Test: send a test message to a real phone number

**Done:** `send_whatsapp("+91XXXXXXXXXX", "test message")` delivers a WhatsApp message.

---

## Phase 4: PWA Frontend (Week 7)

---

### Task 4.1 — Set Up Vite + React PWA Project
**Owner:** Anuj | **Time:** 2 hours

Steps:
1. In `frontend/`, run: `npm create vite@latest . -- --template react`
2. Install: `npm install maplibre-gl react-router-dom`
3. Install PWA plugin: `npm install vite-plugin-pwa`
4. Configure `vite.config.js` with PWA plugin:
   - `registerType: 'autoUpdate'`
   - `workbox.globPatterns` to cache all assets including audio files
5. Create `public/manifest.json`:
   ```json
   {
     "name": "SafarSathi",
     "short_name": "SafarSathi",
     "description": "Mountain travel safety for Mandi region",
     "start_url": "/",
     "display": "standalone",
     "theme_color": "#1a6b3c",
     "background_color": "#ffffff",
     "icons": [...]
   }
   ```
6. Run `npm run dev`, confirm app opens in browser

**Done:** `npm run dev` starts app. `npm run build` produces a `dist/` folder. Lighthouse PWA score ≥ 80 on the dev build.

---

### Task 4.2 — Build Route Risk Page (Core Feature)
**Owner:** Anuj | **Time:** 4 hours
**Depends on:** Task 4.1, Task 1.6

Steps:
1. Create `src/pages/RouteRisk.jsx`
2. Build route selector: 3 cards for Parashar, Barot, Kullu-Manali with route image + distance + max altitude
3. On route selection: fetch `GET /routes/{slug}/risk` from backend API
4. While loading: show skeleton loader (not a blank screen)
5. Show risk badge: large colored circle (Red/Yellow/Green/Grey) with risk level text
6. Show weather summary with staleness indicator ("updated 3h ago")
7. Show latest reporter report with time decay label ("reported 2h ago")
8. Show hospital name + clickable phone number (tel: link)
9. Show reporter contacts with clickable phone numbers
10. If offline: show cached risk data with "OFFLINE -- showing last known data" banner
11. Cache API response in localStorage for offline fallback

**Done:** User can tap "Parashar", see the risk level, and tap the hospital phone number to call it. Works in airplane mode after first visit.

---

### Task 4.3 — Build Offline Checklists Page
**Owner:** Anuj | **Time:** 3 hours
**Depends on:** Task 4.1

Steps:
1. Create `src/data/checklists.json` with all checklist items (pre-trip, emergency signs)
2. Create `src/pages/Checklists.jsx`
3. Two sections: "Before You Travel" and "At High Altitude"
4. Each item: icon + English text + Hindi text + audio play button
5. Build `src/components/AudioPlayer.jsx`:
   - Tap to play/pause pre-recorded Hindi audio
   - Show loading indicator while audio loads
   - Handle error: if audio file missing, show text only (no crash)
6. Checkboxes: user can check off items as they prepare (saved to localStorage, not to server)
7. "Share checklist" button: generates a WhatsApp share link with the safety checklist text

**Done:** All checklist items render. Tapping audio button plays Hindi audio. Works in airplane mode.

---

### Task 4.4 — Build Emergency Contacts Page
**Owner:** Anuj | **Time:** 2 hours
**Depends on:** Task 4.1

Steps:
1. Create `src/pages/Emergency.jsx`
2. Two sections: "Universal Emergency" and "Mandi District"
3. Each contact: icon + name + clickable phone number (large tap target, minimum 44px)
4. All data hardcoded in the component (no API call -- this page must work completely offline)
5. Add a "Copy number" button next to each contact (copies to clipboard)
6. At top of page: prominent search bar to filter contacts by name

**Done:** Page loads instantly, all numbers are tappable. Works in airplane mode with zero API calls.

---

### Task 4.5 — Build Altitude Sickness Page
**Owner:** Anuj | **Time:** 2 hours
**Depends on:** Task 4.1

Steps:
1. Create `src/pages/Altitude.jsx`
2. Three sections:
   - "Before You Go" (preparation tips)
   - "Mild Symptoms" (headache, nausea -- rest and hydrate)
   - "EMERGENCY Signs" (red background, bold -- confusion, blue lips -- DESCEND NOW)
3. Each section has an audio play button for Hindi audio
4. Route-specific altitude warnings: dropdown to select route, shows relevant altitude data
5. Prominent "DESCEND AND CALL 108" button in the emergency section (opens phone dialer)

**Done:** Emergency section is visually distinct and alarming. "DESCEND AND CALL 108" button opens phone dialer. Works offline.

---

### Task 4.6 — Build Offline Maps Page
**Owner:** Gaurav | **Time:** 5 hours
**Depends on:** Task 4.1

Steps:
1. Download HP region OSM data from Geofabrik
2. Run `tippecanoe` to generate `mandi-region.mbtiles` (zoom 10-15, Mandi bbox: 76.8,31.5,77.6,32.2)
3. Place MBTiles file in `frontend/public/tiles/`
4. Create `src/pages/Maps.jsx`
5. Initialize MapLibre GL JS map centered on Mandi (77.0,31.7, zoom 10)
6. Load MBTiles as the map source (via a local tile server or directly from the file)
7. Add POI markers from the hardcoded POI list (hospitals=red cross, police=blue, petrol=orange, mechanic=grey)
8. On marker tap: show popup with name + phone number (clickable)
9. Add "My Location" button -- uses browser geolocation to center the map
10. Route overlays: tap "Show Parashar Route" to highlight the road on the map

**Done:** Map loads offline, all POI markers appear, tapping a hospital marker shows the phone number.

---

### Task 4.7 — Build Service Worker (Full Offline)
**Owner:** Gaurav | **Time:** 3 hours
**Depends on:** Task 4.1, 4.2, 4.3, 4.4, 4.5, 4.6

Steps:
1. Configure Workbox in `vite.config.js`:
   - Cache-first for all static assets (JS, CSS, images, audio)
   - Network-first with localStorage fallback for API calls
   - Pre-cache: `manifest.json`, all pages, all audio files, MBTiles
2. Implement cache size limit (max 100 MB) with LRU eviction
3. Test offline:
   - Build app: `npm run build`
   - Serve: `npx serve dist`
   - Open in browser, load all pages
   - Enable airplane mode in browser DevTools
   - Reload -- confirm every page works
4. Test cache invalidation: update a file, rebuild, confirm browser gets the new version (not stale cache)

**Done:** All 5 pages (Risk, Checklists, Emergency, Altitude, Maps) work fully in airplane mode after first visit.

---

### Task 4.8 — PWA Install Prompt
**Owner:** Anuj | **Time:** 1 hour
**Depends on:** Task 4.7

Steps:
1. Intercept the `beforeinstallprompt` event in the app
2. Show a custom banner: "Save SafarSathi for offline use → Add to Home Screen" (appears after 5 seconds on first visit)
3. "Add" button: triggers the browser install prompt
4. "Not now" button: dismisses for 24 hours (stored in localStorage)
5. Test on Android Chrome (actual device or DevTools mobile simulation)

**Done:** Install prompt appears after 5 seconds on Android Chrome. Tapping "Add" installs the PWA.

---

## Phase 5: SMS Gateway (Week 7, parallel to PWA)

---

### Task 5.1 — Set Up MSG91 / Twilio SMS
**Owner:** Arman | **Time:** 2 hours

Steps:
1. Create a MSG91 account at msg91.com (or Twilio if MSG91 registration fails)
2. Buy an Indian SMS number or use sender ID (requires DLT registration for Indian SMS -- start early)
3. Register templates for each SMS response type with TRAI DLT portal
4. Store API key in `.env`
5. Test: send a test SMS to your own phone

**Done:** Can send an SMS to an Indian number via the MSG91 API.

> Note: DLT registration for Indian SMS sender IDs can take 3-7 days. Do this in Phase 0 if possible.

---

### Task 5.2 — Build SMS Handler
**Owner:** Arman | **Time:** 2 hours
**Depends on:** Task 5.1, Task 1.5

Steps:
1. Create `backend/sms/gateway.py`
2. Implement `handle_inbound_sms(from_number, body)` → returns response string
3. Parse route codes: P1/B1/K1/E/W
4. Route to risk engine for route codes, return hardcoded for E/W
5. Ensure all responses are < 160 characters (add a test assertion for this)
6. Implement `send_sms(to_number, message)` using MSG91 API
7. Add SMS webhook endpoint to FastAPI: `POST /sms/inbound`
8. Test: send "P1" via SMS, confirm risk response received on phone

**Done:** Texting "P1" to the SafarSathi number returns a < 160 char Parashar risk summary via SMS.

---

## Phase 6: Reporter Network Onboarding (Week 7-8, parallel)

---

### Task 6.1 — Create Reporter Registration Form
**Owner:** Tanish | **Time:** 2 hours

Steps:
1. Create a simple HTML form (can be a Google Form for MVP) to collect reporter info during fieldwork:
   - Name
   - Phone number
   - Role (taxi driver / dhaba owner / homestay owner / other)
   - Location name (e.g., "Baggi Village Dhaba")
   - Route (Parashar / Barot / Kullu-Manali)
   - Consent checkbox: "I agree to share my phone number with tourists via SafarSathi"
2. Create an admin API endpoint: `POST /admin/reporters` -- to add a reporter to the DB after fieldwork
3. Protect the admin endpoint with a simple API key (not a full auth system for MVP)

**Done:** Team can add a reporter to the DB via the admin API with a single curl command.

---

### Task 6.2 — Create Reporter Wallet Card (Physical)
**Owner:** Anuj | **Time:** 2 hours

Steps:
1. Design a simple A7 card in Canva or Figma:
   - "SafarSathi Trusted Reporter" title
   - Reporter's name + role
   - QR code linking to the quick report WhatsApp flow
   - Instructions in Hindi: "SafarSathi number pe 'report' bhejein"
2. Export as print-ready PDF (300 DPI, CMYK if possible)
3. Print 20 copies (enough for all reporters + spares)

**Done:** Physical wallet cards ready to hand to reporters during fieldwork.

---

### Task 6.3 — Conduct Reporter Onboarding (Fieldwork)
**Owner:** Full team (on-site in Mandi) | **Time:** 2-3 days in field
**Depends on:** Task 6.1, 6.2

Steps:
1. Visit Mandi bus stand taxi stand -- identify 3-4 drivers willing to participate
2. Visit Parashar route taxi stand (near Rewalsar or Kataula area) -- 2-3 drivers
3. Visit Baggi village dhaba -- 1-2 dhaba owners
4. Visit Ghatasani (Barot route) taxi stand -- 1-2 drivers
5. Visit 2-3 homestay owners near Parashar/Barot
6. For each: explain the system in Hindi, demonstrate the WhatsApp flow, get consent, photograph, collect phone
7. Register each reporter via the admin API on the spot
8. Send them a test WhatsApp message from the bot, confirm they receive it
9. Hand them their wallet card

**Done:** 10+ reporters registered in DB with `consent_given = TRUE`. Each has received and replied to a test WhatsApp message.

---

### Task 6.4 — Test Reporter Submission Flow End-to-End
**Owner:** Tanish | **Time:** 1 hour
**Depends on:** Task 3.5, Task 6.3

Steps:
1. Have 3 reporters (team members acting as reporters, or real reporters) submit test reports
2. Verify each report appears in `reporter_reports` table with correct route, condition, reporter_id, timestamp
3. Query the route risk API -- verify reporter data appears in the response
4. Send "Parashar" as a tourist -- verify the reporter's report shows up in the bot response

**Done:** A reporter submits via WhatsApp → a tourist sees it in the bot response. Full end-to-end verified.

---

## Phase 7: Physical Materials (Week 8)

---

### Task 7.1 — Design Emergency Wallet Card
**Owner:** Anuj | **Time:** 3 hours

Steps:
1. Design front: SafarSathi branding, all 6 universal emergency numbers, Mandi district numbers, QR code to WhatsApp bot
2. Design back: route quick reference (Parashar, Barot, NH3 key facts), altitude sickness emergency protocol
3. Size: credit card (85mm × 54mm) for front/back
4. Typography: large font (min 8pt), high contrast, readable without glasses
5. Language: Hindi primary, English for numbers
6. Get feedback from 2 non-team members (readability check)
7. Export print-ready PDF

**Done:** Print-ready PDF reviewed and approved by team + mentor.

---

### Task 7.2 — Design QR Code Poster (A4)
**Owner:** Anuj | **Time:** 2 hours

Steps:
1. Generate QR code linking to WhatsApp bot (use wa.me link with pre-filled "hi" message)
2. Design A4 poster:
   - Headline in Hindi: "यात्रा से पहले जानें -- क्या रास्ता खुला है?" ("Know before you travel -- is the route open?")
   - Large QR code (minimum 8cm × 8cm for reliable scanning)
   - Instructions in Hindi and English
   - SafarSathi name + SMS number as text fallback
3. Laminate 10 copies for weatherproofing
4. Mount at: Mandi ISBT main entrance, IIT Mandi campus gate, Baggi dhaba, Ghatasani taxi stand

**Done:** 10 laminated posters placed at all target locations.

---

### Task 7.3 — Print and Distribute Wallet Cards
**Owner:** Arman | **Time:** 1 day including travel

Steps:
1. Print 200 wallet cards (cost ~₹500-1000 at a local print shop)
2. Laminate all cards (cost ~₹300-500)
3. Distribute:
   - 50 cards to IIT Mandi Student Affairs for distribution to visiting parents
   - 50 cards to Mandi ISBT information desk
   - 30 cards to each trusted reporter (for them to hand to tourists)
   - 20 cards kept as reserve

**Done:** All 200 cards printed, laminated, and distributed.

---

## Phase 8: Integration Testing (Week 8-9)

---

### Task 8.1 — End-to-End WhatsApp Flow Test
**Owner:** Full team | **Time:** 3 hours

Test all flows using real phones:

| Flow | Input | Expected Output |
|------|-------|-----------------|
| Route query | "parashar" | Risk level + weather + reporter contact + hospital |
| Typo handling | "prashar" | Same as above |
| Weather | "mausam" | IMD forecast summary |
| Emergency | "108 number kya hai" | Emergency contacts list |
| Checklist | "checklist" | Pre-trip checklist in Hindi + English |
| Location pin | Share location in Baggi village | Nearest hospital, police, mechanic |
| Unknown message | "banana" | Help message listing available commands |
| Reporter flow | "report" (from reporter number) | Route selection menu |
| Stale data | (manually set weather to 13h ago) | UNKNOWN risk level shown |

**Done:** All 9 flows produce correct output. Document any failures and fix before next phase.

---

### Task 8.2 — PWA Offline Test
**Owner:** Gaurav | **Time:** 2 hours

Test checklist (run on a real Android phone, not just DevTools simulation):

- [ ] Open PWA on 4G -- all pages load
- [ ] Add to home screen
- [ ] Enable airplane mode
- [ ] Open from home screen icon (not browser bookmark)
- [ ] Route Risk page: shows cached risk data with "offline" banner
- [ ] Checklists page: all items visible, audio plays
- [ ] Emergency page: all numbers visible and tappable
- [ ] Altitude page: all content visible
- [ ] Maps page: map tiles render, POI markers visible
- [ ] Tap a hospital phone number -- dialer opens
- [ ] Restore internet -- verify app fetches fresh data within 30 seconds

**Done:** All 11 offline checklist items pass on a real Android device.

---

### Task 8.3 — SMS Flow Test
**Owner:** Arman | **Time:** 1 hour

Test each SMS code using a real phone (not simulator):

- [ ] "P1" → Parashar risk summary < 160 chars
- [ ] "B1" → Barot risk summary < 160 chars
- [ ] "K1" → Kullu-Manali risk summary < 160 chars
- [ ] "E" → Emergency numbers < 160 chars
- [ ] "W" → Weather summary < 160 chars
- [ ] "xyz" → Help message with valid codes < 160 chars

**Done:** All 6 SMS flows return correct, < 160 char responses on a real phone.

---

### Task 8.4 — Load and Reliability Test
**Owner:** Tanish | **Time:** 2 hours

Steps:
1. Simulate 50 simultaneous WhatsApp messages using a load test script
2. Confirm bot responds to all within 5 seconds (check server logs)
3. Simulate IMD scraper failure (point to a wrong URL)
4. Confirm `/health` returns `degraded` with the issue listed
5. Confirm bot still responds with seasonal baselines + UNKNOWN risk (not crashes)
6. Simulate DB connection loss
7. Confirm bot returns a graceful error message, not a 500 error to the user

**Done:** System degrades gracefully under scraper failure and DB issues. No 500 errors exposed to users.

---

## Phase 9: User Evaluation (Weeks 9-12)

---

### Task 9.1 — Recruit Test Users
**Owner:** Arman | **Time:** 1 week

Steps:
1. Recruit 10-15 test users:
   - 5-7 real parents (IIT Mandi student parents, via students)
   - 3-5 IIT Mandi students acting as parent proxies
   - 2-3 tourists encountered at Mandi ISBT or campus
2. Get WhatsApp number + consent to participate
3. Brief them: "We'll ask you to try finding safety information for a trip. Takes 20 minutes."
4. Schedule sessions across 2 weeks

**Done:** 10+ confirmed participants with scheduled sessions.

---

### Task 9.2 — Design Evaluation Protocol
**Owner:** Tanish | **Time:** 2 hours

Steps:
1. Design 3 tasks for each test user:
   - Task A: "You're planning a trip to Parashar Lake in July. Find out if it's safe to travel."
   - Task B: "You're at Baggi village and your car breaks down. Find the nearest mechanic and hospital."
   - Task C: "Your parent is feeling headache and dizzy at 2,500m altitude. What should they do?"
2. For each task: record time to correct answer (stopwatch), errors made, think-aloud observations
3. After 3 tasks: administer SUS questionnaire (10 standard questions, 1-5 scale)
4. After SUS: 3 open-ended questions:
   - "What was most useful about this system?"
   - "What was confusing or unhelpful?"
   - "Would you use this before a mountain trip? Why or why not?"

**Done:** Evaluation protocol document finalized and reviewed by mentor.

---

### Task 9.3 — Run Evaluation Sessions
**Owner:** Full team (2 people per session) | **Time:** 3 weeks

Steps per session:
1. One team member facilitates (gives tasks, observes)
2. One team member takes notes (time, errors, quotes)
3. Do NOT help the user -- observe what they do naturally
4. After session: immediately write up observations while fresh
5. Upload SUS scores and notes to shared spreadsheet

**Done:** 10+ sessions completed. SUS scores and observations recorded for all participants.

---

### Task 9.4 — Analyze Results and Write Evaluation Report
**Owner:** Tanish + Arman | **Time:** 1 week

Steps:
1. Calculate mean SUS score across all participants
2. Calculate task completion rates for each of the 3 tasks
3. Thematic analysis of qualitative feedback (group similar observations)
4. Identify top 3 usability issues observed (most frequent errors or confusion points)
5. Identify top 3 positive outcomes (what clearly worked well)
6. Write evaluation report sections:
   - Methodology
   - Results (quantitative: SUS, completion rates)
   - Findings (qualitative: themes)
   - Limitations
   - Recommendations for next version

**Done:** Evaluation report complete and submitted to mentor for review.

---

## Phase 10: Final Deliverables (Week 12)

---

### Task 10.1 — Final Demo Preparation
**Owner:** Full team | **Time:** 2 days

Steps:
1. Deploy final version of backend to production (Railway/Render)
2. Deploy final version of PWA to Vercel/Netlify
3. Verify all integrations work in production (not just localhost)
4. Prepare demo script:
   - Live WhatsApp demo: send "Parashar" from a real phone, show response
   - Live PWA demo: show offline maps, checklists, altitude module
   - Show physical card + QR code
   - Walk through the reporter reporting flow
5. Prepare slide deck: Problem → Solution → Architecture → Demo → Results → Limitations → Future Work

**Done:** Live demo works end-to-end on production environment. Slide deck reviewed by mentor.

---

### Task 10.2 — Documentation
**Owner:** Gaurav + Anuj | **Time:** 2 days

Steps:
1. Update `README.md` with:
   - System overview
   - How to run locally (step by step)
   - Environment variables required
   - How to add a new route (step by step)
   - How to add a new reporter (step by step)
2. Document the risk engine scoring in `docs/risk_engine.md`
3. Document the scraper architecture and failure modes in `docs/scrapers.md`
4. Create a `KNOWN_ISSUES.md` with honest list of limitations

**Done:** A new developer can run the system locally in < 30 minutes following the README.

---

## Dependency Map

```
Phase 0 (Setup)
    → Phase 1 (Backend Foundation) [1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 1.6]
    → Phase 2 (Scrapers) [runs parallel to Phase 1, needs 1.2]
    → Phase 3 (WhatsApp Bot) [needs 1.5, 1.6, 2.1]
    → Phase 4 (PWA) [runs parallel to Phase 3]
    → Phase 5 (SMS) [runs parallel to Phase 3 and 4]
    → Phase 6 (Reporter Network) [needs Phase 3 complete]
    → Phase 7 (Physical Materials) [runs parallel to Phase 6]
    → Phase 8 (Integration Testing) [needs Phase 3, 4, 5, 6 complete]
    → Phase 9 (User Evaluation) [needs Phase 8 complete]
    → Phase 10 (Final Deliverables) [needs Phase 9 complete]
```

---

## Team Assignment Summary

| Team Member | Primary Phases |
|-------------|---------------|
| Arman Rawat | Backend foundation (Phase 1), Scrapers (Phase 2), SMS (Phase 5), Reporter onboarding (Phase 6), Distribution |
| Gaurav Ahuja | Database schema (Phase 1), Scrapers (Phase 2), Offline Maps (Phase 4.6), Service Worker (Phase 4.7), Documentation |
| Tanish Kumar | Risk engine (Phase 1.5), WhatsApp webhook (Phase 3), Reporter intake (Phase 3.5), Load testing (Phase 8.4), Evaluation design (Phase 9) |
| Anuj Aggarwal | PWA frontend (Phase 4), Physical materials design (Phase 7), Reporter wallet card (Phase 6.2) |

---

## Total Estimated Timeline

| Phase | Duration | Calendar Weeks |
|-------|----------|----------------|
| Phase 0: Setup | 2 days | Week 1 (start of project) |
| Phase 1: Backend | 3 days | Week 5 |
| Phase 2: Scrapers | 2 days | Week 5 (parallel to Phase 1) |
| Phase 3: WhatsApp Bot | 5 days | Week 6 |
| Phase 4: PWA | 5 days | Week 7 (parallel to Phase 3) |
| Phase 5: SMS | 2 days | Week 7 (parallel) |
| Phase 6: Reporter Onboarding | 3 days field + 1 day tech | Week 7-8 |
| Phase 7: Physical Materials | 3 days | Week 8 (parallel) |
| Phase 8: Integration Testing | 3 days | Week 8-9 |
| Phase 9: User Evaluation | 3 weeks | Weeks 9-12 |
| Phase 10: Deliverables | 2 days | Week 12 |
