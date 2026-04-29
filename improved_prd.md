# PRD: SafarSathi v2.1 -- Mountain Travel Safety System (Validated & Improved)

**Version:** 2.1 (Validated Revision)
**Team:** Arman Rawat, Gaurav Ahuja, Tanish Kumar, Anuj Aggarwal
**Mentor:** Dr. Mohammad Talha, IIT Mandi
**Reviewer Notes:** April 2026

---

## Validation Summary

The original v2.0 PRD is well-scoped and grounded. Key strengths:
- Correctly identifies this as an **information delivery problem**, not a real-time data problem
- Multi-channel architecture is appropriate for low-tech users
- Seasonal baselines as a backbone is the right call (doesn't depend on unreliable crowdsourcing)
- "UNKNOWN not LOW" for stale data is a critical safety insight

**Gaps addressed in this revision:**
1. Missing: WhatsApp Business API approval is not guaranteed -- need a fallback bot strategy
2. Missing: Legal/privacy considerations for sharing reporter phone numbers with tourists
3. Missing: Content moderation and reporter removal workflow
4. Missing: Detailed onboarding funnel for the QR code -> PWA flow
5. Missing: Data retention and GDPR/DPDP compliance notes
6. Underspecified: Risk engine tie-breaker rules
7. Underspecified: What happens when IMD API changes or goes down
8. Added: Phased rollout strategy with MVP definition

---

## 1. Problem Statement (Unchanged -- Validated)

### 1.1 The Core Problem

First-time visitors to Himachal Pradesh mountain regions make dangerous travel decisions because structured, reliable safety information does not reach them in an accessible form. The information exists (locals know it, government agencies publish it), but the delivery pipeline is broken.

Three compounding failures:
- **Information asymmetry:** Taxi drivers at Mandi bus stand know the Parashar road washed out yesterday. The parent arriving from Delhi does not.
- **Accessibility gap:** HP SDMA and IMD publish warnings on government websites. A 55-year-old parent from Lucknow will never find them.
- **Connectivity trap:** The routes where safety information matter most (remote mountain roads) are exactly where internet access is zero.

### 1.2 Real Numbers

- **2,643 road deaths** in HP over 3 years (Tribune India, Jan 2026)
- **448 monsoon deaths** in one season (June-Sept 2025): 261 rain-related + 187 road accidents (Business Standard)
- **Mandi district: 40+ rain fatalities and 24 road deaths** in 2025 monsoon alone
- **346+ roads blocked** during 2025 monsoon; Chandigarh-Manali NH closed for 3 consecutive days
- Parashar Lake road last 10 km: "treacherous" even in good weather
- Mandi-Barot last 35 km: narrow single-lane along Uhl River gorge

### 1.3 Key Insight (Validated and Extended)

**This is not a real-time data problem. It is an information packaging and delivery problem.**

80% of tourist safety incidents stem from bad pre-trip decisions. This information is static or slow-changing. The addition for v2.1: the delivery timing is as important as the content. Information must arrive **before the tourist gets on a bus**, not after they're stranded on a mountain road with no signal.

**New insight:** The IIT Mandi admin email system is an underexploited high-trust channel. Parents already open emails from the institute. A safety briefing embedded in the "your child's semester calendar" email reaches the parent 2-4 weeks before arrival -- the ideal pre-trip window.

---

## 2. Target Users (Refined)

### 2.1 Primary: First-Time Mountain Visitors

- **Representative persona:** Parent (45-65 years) visiting child at IIT Mandi
- **Visits:** 1-2 times per year, 2-4 days each
- **Tech comfort:** WhatsApp daily, basic smartphone, will NOT install a new app
- **Language:** Hindi primary, functional English
- **Travel mode:** Bus from Delhi/Chandigarh to Mandi ISBT, then taxi to IIT Mandi campus
- **Core need:** "Just tell me -- is it safe? What should I know before going?"

**New: User anxiety profile**
Parents' primary fear is not just road accidents -- it's "not knowing what to do if something goes wrong." The system must address both pre-trip preparation AND in-trip emergency response.

### 2.2 Secondary: Local Stakeholders (Trusted Reporters)

- **Who:** 10-15 in-person-verified locals -- taxi drivers, homestay owners, dhaba operators
- **Reporting channel:** WhatsApp (existing behavior)
- **Incentive:** Direct tourist referrals (real business leads)

**Privacy note (new):** Before sharing a reporter's phone number with tourists, obtain explicit written consent. Provide a simple Hindi consent form at onboarding. Reporters can opt out of the referral program while still reporting conditions.

### 2.3 Tertiary (New): IIT Mandi Students

Students help their parents navigate. If the student has the PWA installed, they become the last-mile delivery agent for safety information. Design the PWA "share with parent" flow explicitly.

---

## 3. What SafarSathi IS and IS NOT (Unchanged)

### What it IS:
- A pre-trip preparation and local knowledge bridge
- Aggregator of official data (IMD, HP SDMA, HP PWD) in tourist-friendly language
- A curated directory of verified local contacts
- Offline reference for safety checklists, altitude guidance, emergency protocols, POI maps

### What it IS NOT:
- Not a real-time road traffic feed
- Not Waze/Google Maps competitor
- Not a navigation app
- Not a replacement for calling a local to verify current road status

---

## 4. Multi-Channel Delivery Architecture (Revised)

### Channel 1: WhatsApp Bot (Primary)

**Critical issue to resolve:** WhatsApp Business API approval from Meta requires a registered business entity and can take weeks. Mitigation:

- **Option A (preferred):** Register under IIT Mandi or a faculty-registered entity. Use Meta's free tier for up to 1,000 conversations/month (sufficient for MVP evaluation).
- **Option B (fallback):** Use a third-party WhatsApp gateway (Twilio Conversations, Gupshup) -- faster approval, slightly higher cost.
- **Option C (emergency fallback):** Telegram bot is API-accessible without business approval. Build the same logic for Telegram as a parallel channel during development.

**Tourist interactions (unchanged):**
- "Parashar" → route safety brief
- "weather" → IMD forecast for Mandi district
- "emergency" → emergency numbers
- "checklist" → pre-trip preparation
- Location pin → nearest hospital, police, mechanic

**Language handling (new):** Accept Hindi transliterated in Roman script ("parashar kaise hai?"). Use keyword matching, not NLP -- this keeps it simple and reliable. Build a keyword synonym map (e.g., "barot", "brot", "barod" all map to Barot route).

### Channel 2: PWA (Secondary)

**Onboarding funnel (new, explicit):**
1. Tourist scans QR code at ISBT or campus gate
2. Browser opens PWA URL (instant -- no redirect, no splash screen delay)
3. Within 3 seconds: offline install prompt appears ("Save to home screen for offline use")
4. Within 10 seconds: service worker caches all critical assets (checklists, maps, audio) in background
5. Tourist can immediately use the app -- no forced wait

**Offline-first design rule:** Every user-facing screen must render correctly with zero network. API data (weather, live reports) shows "last updated X hours ago" and gracefully degrades.

### Channel 3: SMS Fallback

Route codes:
- "P1" = Parashar route status
- "B1" = Barot route status
- "K1" = Kullu-Manali route status
- "E" = Emergency numbers
- "W" = Weather summary

Response format (<160 chars):
> PARASHAR: Monsoon HIGH risk. Last 10km treacherous. Call Sharma Dhaba 98765XXXXX before going. Hospital: Mandi Zonal 01905-226201

### Channel 4: Physical Safety Cards

- Laminated pocket cards (credit-card sized) with emergency numbers + QR code + "3 Rules Before Mountain Travel"
- Route safety sheets (A5) at taxi stands with seasonal risk calendar
- **New distribution channel:** IIT Mandi admin includes PDF in parent visit confirmation emails; students encouraged to print and hand to parents on arrival

### Channel 5 (New): IIT Mandi Admin Email Integration

Partner with IIT Mandi student affairs to include a SafarSathi safety briefing (1 paragraph + WhatsApp number + QR code) in:
- Parent day announcement emails
- Semester start parent communications
- Hostel check-in instructions

This reaches parents **2-4 weeks before travel** -- the ideal pre-trip window. No tech barrier; works even for parents without WhatsApp.

---

## 5. Feature Specification (Revised)

### F1: Seasonal Risk Baselines (Unchanged -- Correct)

Pre-defined risk profiles per route per season. Does not require real-time data.

**Mandi to Parashar Lake (50-63 km, 2,730m)**
| Season | Risk | Notes |
|--------|------|-------|
| Oct-Feb | MEDIUM | Cold, possible snow above 2,500m, road slippery |
| Mar-May | LOW | Best window. Road dry, visibility good |
| Jun-Sep | HIGH | Landslide-prone, road past Baggi frequently washed out |

**Mandi to Barot Valley (65 km, ~1,800m)**
| Season | Risk | Notes |
|--------|------|-------|
| Oct-Feb | MEDIUM | Cold, narrow gorge road, limited daylight |
| Mar-May | LOW | Best window. River levels manageable |
| Jun-Sep | HIGH | Uhl River floods, road along gorge extremely dangerous |

**Mandi to Kullu/Manali (NH3)**
| Season | Risk | Notes |
|--------|------|-------|
| Oct-Feb | MEDIUM | Aut-Kullu stretch prone to black ice |
| Mar-May | LOW | Main highway, well-maintained |
| Jun-Sep | HIGH | Pandoh-Aut stretch extremely landslide-prone |

### F2: Official Data Aggregator (Revised -- Resilience Added)

**Sources:**
- IMD Mandi Weather: mausam.imd.gov.in (API + web scrape fallback)
- HP SDMA Alerts: hpsdma.nic.in (web scrape)
- HP PWD Road Status: hppwd.hp.gov.in (web scrape)
- himachalroadstatus.com (web scrape, with attribution)
- MOSDAC Alert Dashboard: mosdac.gov.in/alert-dashboard-beta

**Resilience rules (new):**
- If IMD API returns error → fall back to scraping the IMD web page
- If scrape fails → mark weather data stale, trigger UNKNOWN flag for affected routes
- If ALL sources fail → system still functions on seasonal baselines; show "Official data temporarily unavailable" banner
- Never crash silently. Always degrade gracefully with an honest status message.

**Scraper monitoring (new):** Each scraper sends a heartbeat to a simple health-check endpoint. If a scraper fails for >2 consecutive runs, send alert to team via WhatsApp.

### F3: Risk Engine (Refined -- Tie-breakers Added)

**Score components:**

| Factor | Range | Notes |
|--------|-------|-------|
| SEASONAL_BASELINE | 0-5 | Monsoon=5, Winter=3, Shoulder=2, Best=1 |
| WEATHER_SCORE | 0-5 | Heavy rain=+5, Moderate=+3, Fog=+3, Stale>12h=+2 |
| OFFICIAL_ALERTS | 0-5 | Road closed=+5 (auto-HIGH), Disaster warning=+4, Construction=+3 |
| STAKEHOLDER_REPORTS | 0-3 | Blocked=+3, Rough=+1, No reports=+1, Clear=+0 |
| TIME_OF_DAY | 0-2 | Night=+2, Dusk/dawn=+1, Daytime=+0 |
| ROUTE_STATIC_RISK | 0-3 | Last 10km Parashar=+2, Barot gorge=+2, Unmetalled=+3 |

**Risk levels:**
- HIGH (Red): Total >= 12, OR any official road closure
- MEDIUM (Amber): Total 7-11
- LOW (Green): Total <= 6
- UNKNOWN (Grey): Weather stale AND no stakeholder reports AND not peak monsoon

**Tie-breaker rules (new):**
- Score exactly 11 with active monsoon season → round UP to HIGH (safety-first)
- Score exactly 7 with clear IMD forecast → round DOWN to LOW/MEDIUM at operator's discretion
- Night travel adds +2 regardless of other factors (never show LOW at night on mountain routes)

**Critical rule (unchanged):** NEVER show LOW/Green based on stale data. Stale = UNKNOWN.

### F4: Trusted Reporter Network (Privacy & Moderation Added)

**Onboarding (expanded):**
1. Team physically visits Mandi, meets each potential reporter
2. Collects: name, photo, phone number, location, role (taxi/homestay/dhaba)
3. Explains: how reporting works, what the referral benefit is, how to opt out
4. Gets **written consent** for phone number sharing with tourists
5. Issues a wallet card: "SafarSathi Trusted Reporter" with QR code for quick reporting
6. Adds to WhatsApp group for announcements and feedback

**Reporter removal (new):**
- If a reporter sends 3+ inaccurate reports (verified by conflicting official data or other reporter reports): warning
- If pattern continues: remove from trusted network
- Removal is quiet -- their old reports expire naturally, new reports stop being shown
- Team retains physical record of all reporters for accountability

**Report lifecycle (unchanged):**
- <2 hours: shown prominently
- 2-6 hours: shown with "may have changed" caveat
- 6-24 hours: faded, "conditions may have changed significantly"
- >24 hours: archived, not shown

### F5: Altitude Sickness Module (Unchanged -- Correct)

Pre-trip checklist (offline):
- Drink 4-6 liters of water daily starting the day before
- Avoid alcohol for first 24 hours at altitude
- Carry Diamox (125mg, consult doctor) if going above 2,500m
- Know the signs: headache, nausea, dizziness, breathlessness at rest
- Emergency signs: confusion, inability to walk straight, blue lips, coughing pink sputum → descend IMMEDIATELY

### F6: Emergency Contact Directory (Verified Numbers)

**Universal:**
- Ambulance: 108
- Police: 100
- Fire: 101
- Disaster helpline: 1077
- Women helpline: 1091

**Mandi District:**
- District Control Room: 01905-226201 / 226202 / 226203 / 226204
- Mandi Zonal Hospital: 01905-222380
- Grievance (WhatsApp): 7650025201
- SP Mandi Office: 01905-222402
- HP Tourism Helpline: 0177-2625924

**Note:** All numbers must be verified by calling them before launch. Include a "last verified" date and a process to re-verify quarterly.

### F7: Offline Maps with POIs

- MapLibre GL JS + pre-cached MBTiles (OpenStreetMap)
- Coverage: Mandi + 80 km radius (Parashar, Barot, up to Kullu)
- Zoom levels: 10-15
- Estimated size: 30-50 MB
- POIs: Hospitals, police stations, petrol pumps, mechanics, trusted reporter locations, last connectivity points, hazard zones, altitude markers

**No turn-by-turn navigation.** Just a safety reference map.

### F8: Voice Guidance (Hindi)

- 50-80 pre-recorded Hindi audio clips, 15-30 seconds each
- Fully offline, ~20-30 MB total
- Browser TTS fallback for dynamic content
- **Recording quality note (new):** Record in a quiet room with a native Hindi speaker. Test playback through mobile phone speakers at low volume (how most users will hear it). Avoid background music -- it makes comprehension harder for older users.

### F9 (New): "Share With Parent" Flow

For students using the PWA:
1. Student opens PWA → sees a "Send safety brief to parent" button
2. Enters parent's WhatsApp number or taps "Share via WhatsApp"
3. System generates a pre-written Hindi message: "Mummy/Papa, please save this number: [WhatsApp bot number]. If you travel to Parashar or Barot, send the name of the place and get a safety update. Offline map: [PWA link]"
4. Student taps send

This converts every student into a distribution agent for the system.

---

## 6. Technical Architecture (Revised -- Resilience Focus)

### 6.1 Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend API | Python FastAPI | Async, lightweight, good scraping ecosystem |
| Database | PostgreSQL + PostGIS | Geospatial queries for nearest-POI features |
| Cache | Redis | Weather cache, session state, rate limiting |
| WhatsApp | Meta Cloud API (primary), Twilio fallback | Meta preferred; Twilio as backup during approval wait |
| SMS | MSG91 or Gupshup | Cheaper Indian rates than Twilio for SMS |
| PWA Frontend | Vite + React | Fast build, good service worker support |
| Maps | MapLibre GL JS + MBTiles | Offline-capable, no API key needed for base tiles |
| Scraping | httpx + BeautifulSoup + APScheduler | Standard Python scraping stack |
| Hosting | Railway or Render (free tier for MVP) → DigitalOcean for production | Start free, scale when needed |
| Monitoring | Simple health-check endpoint + WhatsApp alerts to team | Lightweight, no extra infra |

### 6.2 MVP Scope (New -- Phased Rollout)

**MVP (Weeks 5-7 deliverable):**
- WhatsApp bot responds to route name queries with seasonal risk + emergency numbers
- Seasonal baselines for 3 routes (Parashar, Barot, Kullu-Manali) hardcoded in database
- IMD weather data scraped and displayed
- Emergency contact directory via bot

**Beta (Weeks 7-9 deliverable):**
- PWA with offline checklists and emergency contacts
- Trusted reporter network onboarded, reporting via WhatsApp
- Stakeholder reports shown in bot responses
- SMS fallback functional

**V1 (Weeks 9-12 evaluation):**
- Offline maps with POIs
- Voice guidance (Hindi audio)
- Physical cards designed, printed, placed
- Share-with-parent flow

**Do NOT ship in V1:**
- Open crowdsourcing (anyone can report)
- Routing/navigation
- User accounts or logins
- Payment for premium features

### 6.3 Data Flow: Tourist Query (Unchanged -- Correct)

Tourist sends "Parashar" via WhatsApp → Bot fetches route profile + official alerts + stakeholder reports → Risk engine calculates score → Bot returns formatted safety brief with risk level + contacts → If tourist asks "is it open?", bot provides reporter phone number AND sends tourist's number to reporter as a lead.

---

## 7. Legal and Compliance (New Section)

### 7.1 Data Collection

The system collects:
- Reporter phone numbers (stored in DB, shared with tourists with consent)
- Tourist query content via WhatsApp (transient, not persistently stored -- only anonymized route query counts are retained)
- Reporter condition reports (stored, timestamped, associated with reporter)

### 7.2 DPDP Compliance (India's Digital Personal Data Protection Act 2023)

- Collect only minimum necessary data
- Reporter consent must be explicit and documented
- Tourists must be informed their query is being processed (WhatsApp message template handles this)
- Provide a way to request data deletion (reply "DELETE MY DATA" to bot)
- Do not share tourist phone numbers with reporters without tourist's explicit opt-in

### 7.3 Scraping Legality

- IMD: Indian government data, generally permissible for public interest use. Add attribution.
- HP SDMA: Same. Add attribution and do not republish raw data commercially.
- himachalroadstatus.com: Reach out for partnership/attribution agreement before scraping.
- Respect robots.txt on all sites.

---

## 8. Research Methodology (Unchanged -- Validated)

- **Phase 1 (Weeks 1-3):** Fieldwork -- surveys with 15-20 parents, interviews with 10-15 local stakeholders
- **Phase 2 (Weeks 3-5):** Thematic analysis, build knowledge base, validate route risk profiles, select reporters
- **Phase 3 (Weeks 5-9):** Build all channels in parallel (backend, bot, PWA, physical materials, stakeholder onboarding)
- **Phase 4 (Weeks 9-12):** Deploy, evaluate with SUS, collect qualitative feedback, final report

---

## 9. Success Metrics (Revised -- Added Baselines)

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Risk comprehension | 80%+ correctly interpret risk level | Show route + season, ask to select risk level, compare to baseline |
| Usability (SUS) | > 68 (above average) | Standard SUS questionnaire after task completion |
| WhatsApp reach | 20+ unique tourists in evaluation period | Bot conversation count (de-duplicated by phone number) |
| Reporter activity | 8+ of 10-15 reporters submit 1+ report | DB query on reporter_reports table |
| Offline reliability | Full functionality in airplane mode | Test checklist: airplane mode, open PWA, verify all 8 features |
| Perceived usefulness | 70%+ rate "useful" or "very useful" | 5-point Likert scale, post-task survey |
| Response latency | <5 seconds for WhatsApp responses | Server-side timing logs |
| Data freshness | IMD data updated within 8 hours at all times | Scraper heartbeat monitoring |

---

## 10. Risk Register (New Section)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| WhatsApp API approval delayed | HIGH | HIGH | Build Telegram bot in parallel; use Twilio as bridge |
| Gov website structure changes, scraper breaks | MEDIUM | MEDIUM | Health-check alerts; fallback to seasonal baselines |
| Reporter network doesn't sustain beyond evaluation | MEDIUM | HIGH | Direct referral incentive (business leads) is concrete; evaluate incentive sufficiency at week 8 |
| IMD API unavailable | LOW | MEDIUM | Scrape IMD website directly as fallback |
| Tourist ignores HIGH warning, travels anyway | HIGH | N/A (not our failure) | Add explicit disclaimer: "SafarSathi provides information, not guarantees. Always exercise personal judgement." |
| Physical cards not picked up by tourists | MEDIUM | LOW | Supplement with digital delivery; cards are redundant layer, not primary |

---

## 11. Deliverables (Unchanged)

1. Research report: tourist safety challenges in Mandi region (field study findings)
2. Functional WhatsApp bot with route query, risk assessment, and emergency directory
3. PWA with offline checklists, maps, altitude module, voice guidance
4. Physical safety cards and QR posters (designed, printed, placed)
5. Backend with official data aggregation and risk engine
6. Trusted reporter network (onboarded and active)
7. Evaluation report with SUS scores, user feedback, and scaling recommendations
8. Presentation/demo of the complete system

---

## 12. What This Revision Changes

| Area | v2.0 | v2.1 |
|------|------|------|
| WhatsApp API | Assumed straightforward | Explicit fallback (Telegram, Twilio) |
| Reporter privacy | Not addressed | Written consent, opt-out process |
| Reporter moderation | Not addressed | 3-strike removal process |
| Scraper resilience | Not addressed | Health checks, graceful degradation |
| PWA onboarding | Mentioned | Explicit 5-step funnel with timing |
| Legal/compliance | Not addressed | DPDP basics, scraping attribution |
| MVP scope | Not defined | Phased rollout: MVP → Beta → V1 |
| Hindi input | Not addressed | Keyword synonym map for WhatsApp |
| Distribution | 4 channels | 5 channels (adds IIT Mandi email integration) |
| Students | Not mentioned | Explicit "share with parent" flow |
| Risk register | Not addressed | 6 risks with mitigations |
