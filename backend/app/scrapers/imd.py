"""
IMD weather scraper — uses the official IMD API (api.imd.gov.in).

APIs used:
  districtwarning?id=563  → 5-day color-coded warnings for Mandi
  districtnowcast         → current nowcast (filter for Mandi)
  districtrainfall?id=563 → rainfall vs normal

Falls back to HTML scraping if API credentials are not configured.
"""
import asyncio
import logging
import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.weather import WeatherCache
from app.scrapers.imd_auth import get_token, imd_headers

logger = logging.getLogger(__name__)

BASE_URL = "https://api.imd.gov.in/api/v1"
MANDI_DISTRICT_ID = "563"
DISTRICT = "mandi"

# Integer color code from API → severity label
# 1=Green, 2=Yellow, 3=Orange, 4=Red
INT_COLOR = {"1": "green", "2": "yellow", "3": "orange", "4": "red"}

# Warning codes (Day_1 field) → human label
WARNING_CODE = {
    1: "No Warning", 2: "Heavy Rain", 3: "Heavy Snow",
    4: "Thunderstorm & Lightning", 5: "Hailstorm", 6: "Dust Storm",
    7: "Dust Raising Winds", 8: "Strong Surface Winds", 9: "Heat Wave",
    10: "Hot Day", 11: "Warm Night", 12: "Cold Wave", 13: "Cold Day",
    14: "Ground Frost", 15: "Fog", 16: "Very Heavy Rain",
    17: "Extremely Heavy Rain",
}

# Nowcast category → description (cat index is category number)
NOWCAST_CAT = {
    2:  "Light Rain",
    3:  "Light Snow",
    4:  "Light Thunderstorm",
    7:  "Moderate Rain",
    8:  "Moderate Snow",
    9:  "Moderate Thunderstorm",
    11: "Moderate Lightning",
    12: "Heavy Rain",
    13: "Heavy Snow",
    14: "Severe Thunderstorm",
    15: "Very Severe Thunderstorm",
    17: "Thunderstorm with Hail",
    19: "High Lightning probability",
}

ROAD_DANGER_CODES = {2, 3, 4, 5, 12, 13, 14, 15, 16, 17}
MODERATE_CODES    = {8, 9, 11, 15}  # nowcast cats


def _parse_day_codes(raw: str) -> list[str]:
    """Parse '4,8' → ['Thunderstorm & Lightning', 'Strong Surface Winds']"""
    if not raw:
        return []
    labels = []
    for part in str(raw).split(","):
        try:
            code = int(part.strip())
            label = WARNING_CODE.get(code)
            if label and label != "No Warning":
                labels.append(label)
        except ValueError:
            pass
    return labels


def _worst_color(warn: dict) -> str:
    """Return the worst severity across Day1_Color–Day5_Color (integer 1–4)."""
    worst = 0
    for i in range(1, 6):
        val = str(warn.get(f"Day{i}_Color", "0")).strip()
        try:
            worst = max(worst, int(val))
        except ValueError:
            pass
    return INT_COLOR.get(str(worst), "green")


def _today_color(warn: dict) -> str:
    """Return today's (Day1) severity."""
    return INT_COLOR.get(str(warn.get("Day1_Color", "1")).strip(), "green")


def _nowcast_active(now: dict) -> list[str]:
    """Return active nowcast categories for the Mandi entry."""
    active = []
    for i in range(2, 20):
        val = str(now.get(f"cat{i}", "0")).strip()
        if val and val != "0":
            desc = NOWCAST_CAT.get(i)
            if desc:
                active.append(desc)
    return active


def _build_summary(alert_level: str, day1_warnings: list[str], nowcast_active: list[str], rainfall: dict | None) -> str:
    prefix = {
        "red":    "🔴 Red alert",
        "orange": "🟠 Orange alert",
        "yellow": "🟡 Yellow alert",
        "green":  "🟢 No warning",
    }.get(alert_level, "⚫ Unknown")

    # Prioritise the most road-safety-relevant warnings
    all_warnings = day1_warnings + nowcast_active
    for w in all_warnings:
        w_l = w.lower()
        if any(k in w_l for k in ["very heavy", "extremely", "heavy rain", "heavy snow", "hail", "severe thunder"]):
            return f"{prefix}: {w} (IMD Mandi)"
        if any(k in w_l for k in ["thunderstorm", "lightning", "strong wind"]):
            return f"{prefix}: {w} (IMD Mandi)"
        if any(k in w_l for k in ["fog", "cold wave", "frost", "snow"]):
            return f"{prefix}: {w} (IMD Mandi)"

    if rainfall:
        cat = rainfall.get("Daily Category", "")
        dep = rainfall.get("Daily Departure Per", "")
        if cat in ("LE", "E"):
            return f"{prefix}: Excess rainfall ({dep} above normal) (IMD)"

    if alert_level == "green" or not all_warnings:
        return "🟢 No weather warning today (IMD Mandi district)"

    short = ", ".join(all_warnings[:2])
    return f"{prefix}: {short} (IMD Mandi)"


# ── API fetch helpers ──────────────────────────────────────────────────────

async def _fetch_district_warning(client: httpx.AsyncClient) -> dict | None:
    try:
        r = await client.get(f"{BASE_URL}/districtwarning", params={"id": MANDI_DISTRICT_ID}, headers=imd_headers(), timeout=12)
        if r.status_code == 200:
            data = r.json()
            return data[0] if isinstance(data, list) and data else data if isinstance(data, dict) else None
        logger.warning("districtwarning HTTP %d", r.status_code)
    except Exception as e:
        logger.warning("districtwarning error: %s", e)
    return None


async def _fetch_nowcast(client: httpx.AsyncClient) -> dict | None:
    try:
        r = await client.get(f"{BASE_URL}/districtnowcast", headers=imd_headers(), timeout=12)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                for item in data:
                    district = str(item.get("State_District", "") or item.get("Station", "")).upper()
                    if "MANDI" in district:
                        return item
        logger.warning("districtnowcast HTTP %d (or Mandi not found)", r.status_code)
    except Exception as e:
        logger.warning("districtnowcast error: %s", e)
    return None


async def _fetch_rainfall(client: httpx.AsyncClient) -> dict | None:
    try:
        r = await client.get(f"{BASE_URL}/districtrainfall", params={"id": MANDI_DISTRICT_ID}, headers=imd_headers(), timeout=12)
        if r.status_code == 200:
            data = r.json()
            return data[0] if isinstance(data, list) and data else data if isinstance(data, dict) else None
        logger.warning("districtrainfall HTTP %d", r.status_code)
    except Exception as e:
        logger.warning("districtrainfall error: %s", e)
    return None


# ── HTML fallback (no creds needed) ───────────────────────────────────────

_FALLBACK_WARN = "https://mausam.imd.gov.in/imd_latest/contents/districtwise-warning_mc.php?id=3"
_FALLBACK_NOW  = "https://mausam.imd.gov.in/imd_latest/contents/districtwisewarnings_mc.php?id=3"

_HEX_COLOR = {
    "#008000": "green", "#7cfc00": "green",
    "#ffff00": "yellow", "#FFFF00": "yellow",
    "#ffa500": "orange", "#FFA500": "orange",
    "#ff0000": "red",    "#FF0000": "red",
}


def _html_extract_mandi(html: str) -> dict | None:
    import json as _json
    idx = html.find(f'"id": "{MANDI_DISTRICT_ID}"')
    if idx < 0:
        idx = html.find('"MANDI"')
    if idx < 0:
        return None
    start = html.rfind("{", 0, idx)
    end   = html.find("}", idx)
    if start < 0 or end < 0:
        return None
    raw = html[start:end + 1].replace("\\/", "/")
    try:
        return _json.loads(raw)
    except Exception:
        return None


async def _fallback_scrape() -> tuple[str, str, dict]:
    hdrs = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120"}
    async with httpx.AsyncClient(headers=hdrs, timeout=15, follow_redirects=True) as client:
        r_w, r_n = await asyncio.gather(client.get(_FALLBACK_WARN), client.get(_FALLBACK_NOW), return_exceptions=True)

    entry_w = _html_extract_mandi(r_w.text) if not isinstance(r_w, Exception) and r_w.status_code == 200 else None
    entry_n = _html_extract_mandi(r_n.text) if not isinstance(r_n, Exception) and r_n.status_code == 200 else None
    primary = entry_w or entry_n
    if not primary:
        raise RuntimeError("HTML fallback: Mandi entry not found")

    def _clean(e):
        raw = e.get("balloonText") or e.get("info") or ""
        t = BeautifulSoup(raw, "html.parser").get_text(" ").strip()
        t = re.sub(r"^MANDI\s*:?\s*", "", t, flags=re.IGNORECASE).strip()
        t = re.sub(r"\s*(Updated on|Time of issue|Valid upto)\s*:?\s*[\d\-\s:HrsIST]+$", "", t, flags=re.IGNORECASE).strip()
        return t

    warn_text   = _clean(primary)
    alert_level = _HEX_COLOR.get(primary.get("color", "#008000"), "green")
    summary     = _build_summary(alert_level, [warn_text] if warn_text else [], [], None)
    forecast_json = {
        "source": "IMD_HTML_fallback", "district": "MANDI",
        "alert_level": alert_level, "warning_text": warn_text,
        "nowcast_text": _clean(entry_n) if entry_n else "",
    }
    return summary, alert_level, forecast_json


# ── Main ──────────────────────────────────────────────────────────────────

async def scrape_imd_mandi(db: AsyncSession) -> WeatherCache | None:
    """Fetch Mandi district weather from IMD API and persist to DB."""
    summary = alert_level = None
    forecast_json: dict = {}
    use_api = bool(settings.imd_api_key and settings.imd_email and settings.imd_password)

    if use_api:
        try:
            await get_token()
            async with httpx.AsyncClient(timeout=12) as client:
                warn_data, now_data, rain_data = await asyncio.gather(
                    _fetch_district_warning(client),
                    _fetch_nowcast(client),
                    _fetch_rainfall(client),
                    return_exceptions=True,
                )

            if isinstance(warn_data, Exception): warn_data = None
            if isinstance(now_data,  Exception): now_data  = None
            if isinstance(rain_data, Exception): rain_data = None

            if not warn_data:
                raise RuntimeError("District warning returned no data")

            day1_warnings  = _parse_day_codes(warn_data.get("Day_1", ""))
            today_color    = _today_color(warn_data)
            overall_color  = _worst_color(warn_data)
            now_active     = _nowcast_active(now_data) if now_data else []
            alert_level    = today_color  # use today for current risk score

            summary = _build_summary(alert_level, day1_warnings, now_active, rain_data)

            forecast_json = {
                "source":          "IMD_API",
                "district":        "MANDI",
                "district_id":     MANDI_DISTRICT_ID,
                "alert_level":     alert_level,
                "worst_5day":      overall_color,
                "day1_warnings":   day1_warnings,
                "day2_warnings":   _parse_day_codes(warn_data.get("Day_2", "")),
                "day3_warnings":   _parse_day_codes(warn_data.get("Day_3", "")),
                "nowcast_active":  now_active,
                "rainfall_today":  warn_data.get("Daily Actual") if rain_data else None,
                "rainfall_cat":    rain_data.get("Daily Category") if rain_data else None,
                "warning_raw":     warn_data,
                "nowcast_raw":     now_data,
                "rainfall_raw":    rain_data,
                "scraped_at":      datetime.now(timezone.utc).isoformat(),
                "imd_updated_at":  warn_data.get("updated_at"),
            }
            logger.info("IMD API OK — Mandi level=%s day1=%s", alert_level, day1_warnings)

        except Exception as exc:
            logger.error("IMD API failed (%s), falling back to HTML scrape", exc)
            use_api = False

    if not use_api:
        try:
            summary, alert_level, forecast_json = await _fallback_scrape()
            logger.info("IMD HTML fallback OK — level=%s", alert_level)
        except Exception as exc:
            logger.error("IMD HTML fallback failed: %s", exc)
            return None

    await db.execute(delete(WeatherCache).where(WeatherCache.district == DISTRICT))
    record = WeatherCache(
        district=DISTRICT,
        forecast_json=forecast_json,
        summary=summary,
        scraped_at=datetime.now(timezone.utc),
        source=forecast_json.get("source", "IMD"),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record
