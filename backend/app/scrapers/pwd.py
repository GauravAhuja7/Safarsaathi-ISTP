"""HP PWD road status scraper — scrapes HP PWD news for Mandi-region road closures."""
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

HP_PWD_BASE = "https://hppwd.hp.gov.in"

PWD_PAGES = [
    f"{HP_PWD_BASE}",                        # Homepage
    f"{HP_PWD_BASE}/news-press-releases",    # Correct news URL (not /news — that 404s)
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
}

ROAD_CLOSED_KEYWORDS = [
    "road blocked", "road closed", "highway closed", "nh-3 closed", "nh3 closed",
    "nh-21 closed", "manali highway", "chandigarh manali", "route closed",
]
LANDSLIDE_KEYWORDS = ["landslide", "landslip", "debris", "rockfall"]
CONSTRUCTION_KEYWORDS = ["road work", "construction", "maintenance closure", "repair work", "blasting"]

MANDI_KEYWORDS = [
    "mandi", "parashar", "barot", "pandoh", "aut", "larji", "kataula",
    "jogindernagar", "rewalsar", "sundernagar", "nerchowk", "uhl",
    "chandigarh manali", "nh-3", "nh3", "nh-21",
]


def _classify_alert(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ROAD_CLOSED_KEYWORDS):
        return "road_closed"
    if any(k in t for k in LANDSLIDE_KEYWORDS):
        return "landslide"
    if any(k in t for k in CONSTRUCTION_KEYWORDS):
        return "construction"
    return "other"


def _content_hash(text: str) -> str:
    return hashlib.md5(text.strip().lower().encode()).hexdigest()


def _is_mandi_relevant(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in MANDI_KEYWORDS)


def _extract_road_texts(soup: BeautifulSoup) -> list[str]:
    """Extract text items from PWD pages that look like road status updates."""
    candidates = []

    # News tickers / marquee elements
    for el in soup.find_all(["marquee"]):
        candidates.append(el.get_text(" ", strip=True))

    # News section list items
    for li in soup.find_all("li"):
        text = li.get_text(" ", strip=True)
        if len(text) > 30:
            candidates.append(text)

    # Any heading/paragraph with road keywords
    for el in soup.find_all(["p", "div", "span", "td", "h3", "h4"]):
        text = el.get_text(" ", strip=True)
        if len(text) > 30 and len(text) < 800:
            t_lower = text.lower()
            if any(k in t_lower for k in ROAD_CLOSED_KEYWORDS + LANDSLIDE_KEYWORDS + CONSTRUCTION_KEYWORDS + MANDI_KEYWORDS):
                candidates.append(text)

    # Anchor links that mention road closures
    for a in soup.find_all("a"):
        text = a.get_text(" ", strip=True)
        if len(text) > 20:
            t_lower = text.lower()
            if any(k in t_lower for k in ROAD_CLOSED_KEYWORDS + LANDSLIDE_KEYWORDS + MANDI_KEYWORDS):
                candidates.append(text)

    seen = set()
    result = []
    for c in candidates:
        c = c.strip()
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result


async def scrape_pwd_status(db: AsyncSession) -> int:
    """
    Scrape HP PWD pages for Mandi-region road closure/blockage alerts.
    Returns count of new alerts saved.
    """
    raw_items: list[dict] = []

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            for url in PWD_PAGES:
                try:
                    r = await client.get(url)
                    if r.status_code != 200:
                        logger.warning("PWD page %s returned HTTP %d", url, r.status_code)
                        continue
                    soup = BeautifulSoup(r.text, "html.parser")
                    texts = _extract_road_texts(soup)
                    for t in texts:
                        raw_items.append({"text": t, "url": url})
                except Exception as exc:
                    logger.warning("PWD fetch error for %s: %s", url, exc)
    except Exception as exc:
        logger.error("PWD scrape failed: %s", exc)
        return 0

    # Filter for Mandi-relevant road alerts
    mandi_items = [i for i in raw_items if _is_mandi_relevant(i["text"])]

    if not mandi_items:
        logger.info("PWD: no Mandi-relevant road alerts found")
        return 0

    # Deduplicate against last 24 hours
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    existing = await db.execute(
        select(OfficialAlert.description)
        .where(OfficialAlert.source == "HP_PWD")
        .where(OfficialAlert.scraped_at >= cutoff)
    )
    existing_hashes = {_content_hash(row[0] or "") for row in existing.fetchall()}

    saved = 0
    for item in mandi_items:
        text = item["text"].strip()
        if _content_hash(text) in existing_hashes:
            continue

        alert_type = _classify_alert(text)
        record = OfficialAlert(
            route_id=None,
            alert_type=alert_type,
            description=text[:500],
            source="HP_PWD",
            scraped_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db.add(record)
        saved += 1

    if saved > 0:
        await db.commit()
        logger.info("PWD: saved %d new road alerts", saved)
    return saved
