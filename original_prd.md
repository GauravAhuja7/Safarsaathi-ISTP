# PRD: SafarSathi -- Mountain Travel Safety System for Mandi Region

**Version:** 2.0 (Original -- As Submitted)
**Team:** Arman Rawat, Gaurav Ahuja, Tanish Kumar, Anuj Aggarwal
**Mentor:** Dr. Mohammad Talha, IIT Mandi

---

## 1. Problem Statement

### 1.1 The Core Problem

First-time visitors to Himachal Pradesh mountain regions make dangerous travel decisions because structured, reliable safety information does not reach them in an accessible form. The information exists (locals know it, government agencies publish it), but the delivery pipeline is broken.

Three failures compound:
- **Information asymmetry:** Taxi drivers at Mandi bus stand know the Parashar road washed out yesterday. The parent arriving from Delhi does not.
- **Accessibility gap:** HP SDMA and IMD publish warnings on government websites. A 55-year-old parent from Lucknow will never find them.
- **Connectivity trap:** The routes where safety information matters most (remote mountain roads) are exactly where internet access is zero.

### 1.2 Real Numbers

- **2,643 road deaths** in HP over 3 years (Tribune India, Jan 2026)
- **448 monsoon deaths** in one season (June-Sept 2025): 261 rain-related + 187 road accidents (Business Standard)
- **Mandi district: 40+ rain fatalities and 24 road deaths** in 2025 monsoon alone
- **346+ roads blocked** during 2025 monsoon; Chandigarh-Manali NH closed for 3 consecutive days
- Parashar Lake road last 10 km described as "treacherous" even in good weather
- Mandi-Barot last 35 km is narrow single-lane along Uhl River gorge

### 1.3 Why Current Solutions Fail

- **Google Maps:** Requires internet. No safety layer. Doesn't know the Parashar road past Baggi is a death trap in monsoon.
- **HP SDMA / IMD websites:** Publish warnings, but in bureaucratic language on gov.in sites no tourist visits.
- **himachalroadstatus.com:** Community-driven road updates for HP -- good effort, but tourist-unfocused, no offline mode, no pre-trip preparation layer.
- **Word-of-mouth:** Taxi drivers give advice, but it's inconsistent ("that road is fine" vs "don't go there") and there's no way to verify it.
- **WhatsApp groups:** IIT Mandi parent groups exist, but information is buried in chat noise, unstructured, and not available to first-time visitors who haven't joined yet.

### 1.4 The Key Insight

**This is not a real-time data problem. It's an information packaging and delivery problem.**

80% of tourist safety incidents stem from bad pre-trip decisions (traveling a monsoon-prone route in July, not carrying warm clothes to 2,730m altitude, not knowing the nearest hospital is 40 km away). This information is static or slow-changing. It doesn't need real-time crowdsourcing. It needs to reach the right person at the right time in a form they can understand.

---

## 2. Target Users

### 2.1 Primary: First-Time Mountain Visitors

- **Representative persona:** Parent (45-65 years) visiting child at IIT Mandi
- **Visits:** 1-2 times per year, 2-4 days each
- **Tech comfort:** WhatsApp daily, basic smartphone use, will NOT install a new app
- **Language:** Hindi primary, functional English
- **Travel mode:** Bus from Delhi/Chandigarh to Mandi ISBT, then taxi to IIT Mandi campus; some take side trips to Parashar, Barot, Manali
- **Core need:** "Just tell me -- is it safe? What should I know before going?"

### 2.2 Secondary: Local Stakeholders (Trusted Reporters)

- **Who:** 10-15 hand-picked, in-person-verified locals -- taxi drivers (3-4 at Mandi bus stand, 2-3 on Parashar route), homestay owners (3-4 near key routes), dhaba owners (2-3 at strategic points like Baggi village, Pandoh)
- **Tech comfort:** WhatsApp daily, comfortable with Hindi voice notes and photos
- **Incentive:** Direct tourist referrals ("A tourist needs a taxi from Mandi to Parashar -- interested?"), not vague "ranking boosts"
- **Reporting channel:** WhatsApp (they already use it), not a separate app

---

## 3. Product Concept: What SafarSathi IS and IS NOT

### What it IS:
- A **pre-trip preparation and local knowledge bridge**
- "Should I travel this route? What should I prepare? Who do I call if something goes wrong?"
- Aggregator of official data (IMD, HP SDMA, HP PWD) presented in tourist-friendly language
- A curated directory of verified local contacts for ground-truth verification
- Offline reference for safety checklists, altitude guidance, emergency protocols, POI maps

### What it IS NOT:
- Not a real-time road traffic feed (that's unsolvable for low-traffic mountain roads)
- Not Waze/Google Maps competitor
- Not a navigation app
- Not a replacement for calling a local to ask "is the road open right now"

---

## 4. Multi-Channel Delivery Architecture

The system reaches tourists through **four channels**, ensuring coverage regardless of tech comfort or connectivity:

### Channel 1: WhatsApp Bot (Primary -- Zero Friction)

**Why:** 100% of the target user group already has WhatsApp. Zero installation. Works on 2G.

**Tourist interactions:**
- Send "Parashar" or "Mandi to Parashar" --> receive route safety brief
- Send "weather" --> receive current IMD forecast for Mandi district
- Send "emergency" --> receive emergency numbers for current area
- Send "checklist" --> receive pre-trip preparation checklist
- Send location pin --> receive nearest hospital, police, mechanic

**Stakeholder interactions:**
- Trusted reporter sends "report" --> prompted to select route, describe condition
- Can send photo + voice note describing road condition
- Receives tourist referral messages when tourists need a taxi/homestay on their route

### Channel 2: PWA (Secondary -- Rich Offline Experience)

**Features:**
- Offline safety checklists with icons and optional voice playback (Hindi)
- Offline maps (MapLibre GL + MBTiles) with emergency POIs
- Route risk dashboard showing seasonal baseline + latest known conditions
- Altitude sickness awareness module
- Emergency protocol cards (visual, icon-based)

**Distribution:** QR codes at Mandi ISBT bus stand, IIT Mandi campus gate, popular dhabas, taxi stands.

### Channel 3: SMS Fallback (Last Resort)

Tourists text a route code ("P1" = Parashar, "B1" = Barot) to receive a <160 char safety summary.

### Channel 4: Physical Safety Cards (Always Works)

- Laminated pocket cards with emergency numbers + QR code + "3 Rules Before Mountain Travel"
- Route safety sheets at taxi stands
- Distributed via IIT Mandi admin, ISBT, taxi stands, campus gate

---

## 5. Feature Specification

### F1: Seasonal Risk Baselines
Pre-defined per-route, per-season risk profiles. Backbone of the system.

### F2: Official Data Aggregator
Scrapes/polls IMD, HP SDMA, HP PWD, himachalroadstatus.com every 6 hours.

### F3: Rule-Based Risk Engine
Combines seasonal baseline + official data + stakeholder reports into LOW/MEDIUM/HIGH/UNKNOWN.

### F4: Trusted Reporter Network
10-15 in-person-verified locals reporting via WhatsApp. Direct tourist referral as incentive.

### F5: Altitude Sickness Module
Pre-trip checklist, route-specific altitude warnings, AMS signs and emergency protocol.

### F6: Emergency Contact Directory
Pre-loaded, offline. Universal numbers + Mandi district + route-specific contacts.

### F7: Offline Maps with POIs
MapLibre GL + MBTiles (OpenStreetMap), 80 km radius from Mandi, 30-50 MB cached.

### F8: Voice Guidance (Hindi)
50-80 pre-recorded Hindi audio clips, 15-30 sec each, fully offline.

---

## 6. Technical Architecture

- **Backend:** Python FastAPI
- **Database:** PostgreSQL + PostGIS
- **Cache:** Redis
- **WhatsApp:** Meta Cloud API
- **SMS:** Twilio / MSG91 / Gupshup
- **PWA Frontend:** Vite + React, service worker
- **Maps:** MapLibre GL JS + MBTiles (OpenStreetMap via tippecanoe)
- **Scraping:** Python httpx + BeautifulSoup + APScheduler
- **Hosting:** DigitalOcean / AWS Lightsail (~$10-20/month)

---

## 7. Research Methodology

- **Phase 1 (Weeks 1-3):** Fieldwork -- surveys with 15-20 parents, interviews with 10-15 local stakeholders
- **Phase 2 (Weeks 3-5):** Thematic analysis, build knowledge base, validate route risk profiles
- **Phase 3 (Weeks 5-9):** Build backend, WhatsApp bot, PWA, physical materials, stakeholder onboarding
- **Phase 4 (Weeks 9-12):** Deploy, evaluate, collect SUS scores, final report

---

## 8. Success Metrics

- Risk comprehension: 80%+ of test users correctly interpret risk levels
- Usability (SUS): Score above 68 (above average)
- Channel reach: 20+ unique tourists interact with WhatsApp bot during evaluation
- Stakeholder activity: 8+ of 10-15 reporters submit at least one report
- Offline reliability: PWA functions fully in airplane mode
- Perceived usefulness: 70%+ rate system as "useful" or "very useful"
- Response latency: WhatsApp bot responds in < 5 seconds

---

## 9. Deliverables

1. Research report: tourist safety challenges in Mandi region
2. Functional WhatsApp bot
3. PWA with offline capabilities
4. Physical safety cards and QR posters
5. Backend with data aggregation and risk engine
6. Active trusted reporter network
7. Evaluation report with SUS scores
8. Presentation/demo of complete system
