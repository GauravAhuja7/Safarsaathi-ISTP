"""HP SDMA alert scraper — scrapes HPSDMA news/press releases for Mandi alerts."""
import re
import hashlib
import logging
from datetime import datetime, timezone, timedelta

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weather import OfficialAlert

logger = logging.getLogger(__name__)

HP_SDMA_BASE = "https://hpsdma.nic.in"

# Pages likely to carry disaster alerts relevant to Mandi
SDMA_PAGES = [
    f"{HP_SDMA_BASE}/Index1.aspx?lsid=39&lev=1&lid=34&langid=1",  # Reports section
    f"{HP_SDMA_BASE}",  # Homepage (marquee/news tickers)
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
}

# Keywords indicating a road/disaster alert relevant to mountain travel
ROAD_BLOCK_KEYWORDS = ["road blocked", "road closed", "highway closed", "nh closed", "route blocked", "traffic blocked"]
DISASTER_KEYWORDS = ["landslide", "flash flood", "flood warning", "red alert", "orange alert", "cloudburst", "bridge damaged", "road washed"]
MANDI_KEYWORDS = ["mandi", "parashar", "barot", "pandoh", "jogindernagar", "rewalsar", "sundernagar"]

# Navigation/menu text that appears on SDMA website — must be rejected
NAV_GARBAGE_PATTERNS = [
    "citizen corner", "repository", "iec material", "safe construction",
    "earthquake repository", "guidelines for", "safety tips", "home page",
    "contact us", "about us", "sitemap", "press release list", "gallery",
    "annual report", "relief manual", "ddma", "sdma act",
]


def _classify_alert(text: str) -> str:
    """Return alert_type for the OfficialAlert model."""
    t = text.lower()
    if any(k in t for k in ROAD_BLOCK_KEYWORDS):
        return "road_closed"
    if "landslide" in t:
        return "landslide"
    if any(k in t for k in DISASTER_KEYWORDS):
        return "disaster_warning"
    return "other"


def _content_hash(text: str) -> str:
    return hashlib.md5(text.strip().lower().encode()).hexdigest()


async def scrape_sdma_alerts(db: AsyncSession) -> int:
    """
    Scrape HP SDMA pages for Mandi-relevant disaster alerts.
    Returns count of new alerts saved to DB.
    """
    raw_alerts: list[dict] = []

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            for url in SDMA_PAGES:
                try:
                    r = await client.get(url)
                    if r.status_code != 200:
                        logger.warning("SDMA page %s returned HTTP %d", url, r.status_code)
                        continue

                    soup = BeautifulSoup(r.text, "html.parser")
                    texts = _extract_alert_texts(soup)
                    for t in texts:
                        raw_alerts.append({"text": t, "url": url})
                except Exception as exc:
                    logger.warning("SDMA fetch error for %s: %s", url, exc)
    except Exception as exc:
        logger.error("SDMA scrape failed: %s", exc)
        return 0

    # Filter for Mandi-relevant alerts — reject nav garbage first
    mandi_alerts = []
    for a in raw_alerts:
        t = a["text"].lower()
        # Reject navigation/menu text
        if any(nav in t for nav in NAV_GARBAGE_PATTERNS):
            continue
        # Must have either a location keyword OR a disaster keyword AND be long enough to be real content
        has_location = any(k in t for k in MANDI_KEYWORDS)
        has_disaster = any(k in t for k in DISASTER_KEYWORDS + ROAD_BLOCK_KEYWORDS)
        # Real alerts are usually sentences, not just keyword lists
        is_sentence = len(a["text"].split()) >= 8
        if has_disaster and (has_location or is_sentence):
            mandi_alerts.append(a)

    if not mandi_alerts:
        logger.info("SDMA: no Mandi-relevant alerts found (this is normal outside monsoon)")
        return 0

    # Deduplicate against existing alerts saved in the last 24 hours
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    existing = await db.execute(
        select(OfficialAlert.description)
        .where(OfficialAlert.source == "HP_SDMA")
        .where(OfficialAlert.scraped_at >= cutoff)
    )
    existing_hashes = {_content_hash(row[0] or "") for row in existing.fetchall()}

    saved = 0
    for alert in mandi_alerts:
        text = alert["text"].strip()
        if _content_hash(text) in existing_hashes:
            continue  # already in DB

        alert_type = _classify_alert(text)
        record = OfficialAlert(
            route_id=None,  # Not route-specific unless we can parse it
            alert_type=alert_type,
            description=text[:500],
            source="HP_SDMA",
            scraped_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
        )
        db.add(record)
        saved += 1

    if saved > 0:
        await db.commit()
        logger.info("SDMA: saved %d new alerts", saved)
    return saved


def _extract_alert_texts(soup: BeautifulSoup) -> list[str]:
    """Pull all potentially relevant text fragments from an SDMA page."""
    candidates = []

    # News tickers / marquee
    for el in soup.find_all(["marquee", "ticker"]):
        candidates.append(el.get_text(" ", strip=True))

    # List items that look like news
    for li in soup.find_all("li"):
        text = li.get_text(" ", strip=True)
        if len(text) > 30:
            candidates.append(text)

    # Table rows with alert-like content
    for td in soup.find_all("td"):
        text = td.get_text(" ", strip=True)
        if len(text) > 40 and any(k in text.lower() for k in MANDI_KEYWORDS + DISASTER_KEYWORDS + ROAD_BLOCK_KEYWORDS):
            candidates.append(text)

    # Anchor link text
    for a in soup.find_all("a"):
        text = a.get_text(" ", strip=True)
        if len(text) > 25 and any(k in text.lower() for k in MANDI_KEYWORDS + DISASTER_KEYWORDS + ROAD_BLOCK_KEYWORDS):
            candidates.append(text)

    # Deduplicate while preserving order
    seen = set()
    result = []
    for c in candidates:
        c = c.strip()
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result
