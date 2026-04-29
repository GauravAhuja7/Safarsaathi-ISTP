from __future__ import annotations
from dataclasses import dataclass
from app.models.weather import WeatherCache, OfficialAlert
from app.models.report import ReporterReport
from app.models.route import RouteBaseline

# Static risk penalty per route slug (terrain difficulty that never changes)
ROUTE_STATIC_RISK: dict[str, int] = {
    "parashar": 2,       # Last 10 km very rough even in good weather
    "barot": 2,          # 35 km narrow gorge road along Uhl River
    "kullu-manali": 0,   # Main national highway
}

SEASONAL_BASE_SCORE: dict[str, int] = {"HIGH": 5, "MEDIUM": 3, "LOW": 1}

MONSOON_MONTHS = range(6, 10)  # June-September


@dataclass
class RiskResult:
    level: str          # HIGH | MEDIUM | LOW | UNKNOWN
    score: int
    baseline: str       # seasonal baseline used
    reason: str         # human-readable explanation


def _weather_score(weather: WeatherCache | None) -> tuple[int, str]:
    """Return (score 0-5, reason string) from weather cache."""
    if weather is None:
        return 2, "No weather data available"

    if not weather.is_fresh(12):
        return 2, f"Weather data stale ({weather.hours_old():.0f}h old)"

    forecast = weather.forecast_json or {}
    summary_text = (weather.summary or "").lower()
    raw = str(forecast).lower()

    # Check for severe alerts in forecast JSON or summary
    if any(kw in raw or kw in summary_text for kw in ["red alert", "very heavy", "extremely heavy", "thunderstorm warning"]):
        return 5, "Severe weather warning (IMD red/orange alert)"
    if any(kw in raw or kw in summary_text for kw in ["heavy rain", "heavy rainfall", "orange alert"]):
        return 5, "Heavy rainfall warning (IMD)"
    if any(kw in raw or kw in summary_text for kw in ["moderate rain", "yellow alert", "light rain"]):
        return 3, "Moderate rainfall forecast (IMD)"
    if any(kw in raw or kw in summary_text for kw in ["fog", "low visibility", "mist"]):
        return 3, "Low visibility warning (IMD)"
    if any(kw in raw or kw in summary_text for kw in ["snow", "snowfall", "blizzard"]):
        return 4, "Snowfall forecast (IMD)"
    if any(kw in raw or kw in summary_text for kw in ["clear", "sunny", "fair", "no warning"]):
        return 0, "Clear weather (IMD)"

    return 1, "Partly cloudy / no specific warning (IMD)"


def _alerts_score(alerts: list[OfficialAlert]) -> tuple[int, str, bool]:
    """Return (score 0-5, reason, is_road_closed). is_road_closed triggers auto-HIGH."""
    if not alerts:
        return 0, "No official alerts", False

    for alert in alerts:
        if alert.alert_type == "road_closed":
            return 5, f"Road officially closed: {alert.description or alert.source}", True

    max_score = 0
    reasons = []
    for alert in alerts:
        if alert.alert_type == "disaster_warning":
            max_score = max(max_score, 4)
            reasons.append("Disaster warning active")
        elif alert.alert_type in ("landslide", "construction"):
            max_score = max(max_score, 3)
            reasons.append(f"{alert.alert_type.replace('_', ' ').title()} alert")
        else:
            max_score = max(max_score, 1)
            reasons.append("Official advisory")

    return max_score, "; ".join(reasons), False


def _reporter_score(recent_reports: list[ReporterReport]) -> tuple[int, str]:
    """Return (score 0-3, description) from recent (< 24h) reports."""
    if not recent_reports:
        return 1, "No recent reporter updates (uncertainty penalty)"

    # Prioritize the most recent report
    latest = min(recent_reports, key=lambda r: r.hours_old())

    if latest.condition == "blocked":
        return 3, f"Road blocked (reporter, {latest.hours_old():.0f}h ago)"
    if latest.condition == "rough":
        return 1, f"Road open but rough (reporter, {latest.hours_old():.0f}h ago)"
    if latest.condition == "clear":
        return 0, f"Road clear (reporter, {latest.hours_old():.0f}h ago)"
    return 1, f"Conditions reported ({latest.hours_old():.0f}h ago)"


def _time_score(hour: int) -> tuple[int, str]:
    if hour >= 19 or hour < 5:
        return 2, "Night travel (7 PM–5 AM)"
    if hour in (5, 6, 18):
        return 1, "Dusk/dawn conditions"
    return 0, ""


def _stale_and_unknown(
    weather: WeatherCache | None,
    recent_reports: list[ReporterReport],
    baseline_risk: str,
    current_month: int,
) -> bool:
    """True when we genuinely don't know the current conditions."""
    weather_stale = weather is None or not weather.is_fresh(12)
    no_reports = len(recent_reports) == 0
    not_monsoon = current_month not in MONSOON_MONTHS
    return weather_stale and no_reports and not_monsoon and baseline_risk != "HIGH"


def calculate_risk(
    route_slug: str,
    current_month: int,
    current_hour: int,
    baseline: RouteBaseline,
    weather: WeatherCache | None,
    alerts: list[OfficialAlert],
    recent_reports: list[ReporterReport],
) -> RiskResult:
    """
    Pure function. Combine all risk factors into a single level.
    Never returns LOW or MEDIUM on stale data when conditions are uncertain.
    """
    w_score, w_reason = _weather_score(weather)
    a_score, a_reason, road_closed = _alerts_score(alerts)
    r_score, r_reason = _reporter_score(recent_reports)
    t_score, t_reason = _time_score(current_hour)
    static = ROUTE_STATIC_RISK.get(route_slug, 0)
    base_score = SEASONAL_BASE_SCORE[baseline.risk_level]

    # Auto-HIGH: official road closure overrides everything
    if road_closed:
        return RiskResult(
            level="HIGH",
            score=23,
            baseline=baseline.risk_level,
            reason=a_reason,
        )

    total = base_score + w_score + a_score + r_score + t_score + static

    if total >= 12:
        level = "HIGH"
    elif total >= 7:
        level = "MEDIUM"
    else:
        level = "LOW"

    # Safety tie-breaker: score exactly 11 during monsoon → bump to HIGH
    if total == 11 and current_month in MONSOON_MONTHS:
        level = "HIGH"

    # UNKNOWN override: genuinely no current data and not a high-risk season
    if _stale_and_unknown(weather, recent_reports, baseline.risk_level, current_month):
        level = "UNKNOWN"

    reason_parts = [f"Seasonal baseline: {baseline.risk_level} ({baseline.reason})"]
    if w_reason:
        reason_parts.append(w_reason)
    if a_reason:
        reason_parts.append(a_reason)
    if r_reason:
        reason_parts.append(r_reason)
    if t_reason:
        reason_parts.append(t_reason)

    return RiskResult(
        level=level,
        score=total,
        baseline=baseline.risk_level,
        reason=" | ".join(reason_parts),
    )
