import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import RiskBadge from "../components/RiskBadge";
import { apiUrl } from "../api";
import { ROUTE_META } from "../data/routes";

// Static fallback — shown when backend is offline.
// Risk based on current month (Apr–May = LOW, Jun–Sep = HIGH, rest = MEDIUM)
function getSeasonalRisk() {
  const m = new Date().getMonth() + 1;
  if (m >= 6 && m <= 9) return "HIGH";
  if ((m >= 3 && m <= 5)) return "LOW";
  return "MEDIUM";
}

const STATIC_ROUTES = [
  { slug: "parashar",     name: "Mandi → Parashar Lake",       distance_km: 63, max_altitude_m: 2730 },
  { slug: "barot",        name: "Mandi → Barot Valley",        distance_km: 65, max_altitude_m: 1800 },
  { slug: "kullu-manali", name: "Mandi → Kullu / Manali (NH-3)", distance_km: 170, max_altitude_m: 2050 },
].map((r) => ({ ...r, current_risk: getSeasonalRisk(), seasonal_baseline: getSeasonalRisk() }));

const CACHE_KEY = "ss_routes_v1";

function loadCache() {
  try { return JSON.parse(localStorage.getItem(CACHE_KEY)); }
  catch {
    return null;
  }
}
function saveCache(data) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({ data, ts: Date.now() }));
  } catch {
    // Ignore storage failures; static fallback still works.
  }
}

export default function RouteList() {
  const [routes, setRoutes] = useState(() => loadCache()?.data || STATIC_ROUTES);
  const [source, setSource] = useState(() => (loadCache() ? "cache" : "static")); // "live" | "cache" | "static"

  useEffect(() => {
    const cached = loadCache();

    fetch(apiUrl("/routes"), { signal: AbortSignal.timeout(5000) })
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((data) => {
        setRoutes(data);
        saveCache(data);
        setSource("live");
      })
      .catch(() => {
        if (!cached) setSource("static");
      });
  }, []);

  const month = new Date().getMonth() + 1;
  const isMonsoon = month >= 6 && month <= 9;

  return (
    <div className="page">
      {/* Hero */}
      <div className="page-hero">
        <h1>SafarSathi</h1>
        <p>मंडी क्षेत्र — यात्रा सुरक्षा जानकारी</p>
        <p style={{ opacity: 0.7, fontSize: "0.8rem", marginTop: 4 }}>
          Mandi region mountain travel safety
        </p>
      </div>

      <div className="page-body">
        {/* Offline / source indicator */}
        {source === "static" && (
          <div className="offline-banner mb-16">
            ⚠️ Backend offline — showing seasonal baseline data
          </div>
        )}
        {source === "cache" && (
          <div className="offline-banner mb-16" style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", color: "#15803d" }}>
            📦 Cached data — connect to server for live updates
          </div>
        )}

        {/* Monsoon alert */}
        {isMonsoon && (
          <div className="monsoon-card mb-16">
            <strong>⚠️ मानसून सीज़न सक्रिय (June–September)</strong>
            <p style={{ fontSize: "0.875rem" }}>
              All mountain routes carry elevated risk. Verify road status before every trip.
            </p>
          </div>
        )}

        {/* Routes */}
        <div className="section">
          <div className="section-label">रास्ता चुनें — Select a route</div>

          {routes.map((route) => {
            const meta = ROUTE_META[route.slug] || {};
            return (
              <Link key={route.slug} to={`/route/${route.slug}`} className="route-card">
                <div className={`route-card-stripe ${route.current_risk}`} />
                <div className="route-card-body">
                  <div className="route-card-top">
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div className="route-name-hi">{meta.nameHi || route.name}</div>
                      <div className="route-name-en">{route.name}</div>
                    </div>
                    <RiskBadge level={route.current_risk} />
                  </div>
                  <div className="route-meta-row">
                    {meta.distance && (
                      <span className="route-meta-chip">📏 {meta.distance}</span>
                    )}
                    {meta.altitude && (
                      <span className="route-meta-chip">⛰️ {meta.altitude}</span>
                    )}
                    <span className="route-meta-chip">
                      Seasonal: {route.seasonal_baseline}
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>

        {/* Quick access */}
        <div className="section">
          <div className="section-label">Quick access</div>
          <a
            href="https://wa.me/91XXXXXXXXXX?text=Parashar"
            className="wa-cta"
            target="_blank"
            rel="noreferrer"
          >
            <span style={{ fontSize: "1.5rem" }}>💬</span>
            <span>WhatsApp पर पूछें — "Parashar" भेजें</span>
          </a>
          <Link
            to="/report"
            className="wa-cta"
            style={{ background: "#1e3a5f", marginTop: 10 }}
          >
            <span style={{ fontSize: "1.5rem" }}>📢</span>
            <span>रास्ते की जानकारी दें — Report road condition</span>
          </Link>
        </div>

        {/* Season info strip */}
        <div className="card" style={{ textAlign: "center", marginBottom: 24 }}>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
            SafarSathi provides pre-trip safety information for mountain routes near Mandi, HP.
            Always verify current road status with a local contact before traveling.
          </p>
        </div>
      </div>
    </div>
  );
}
