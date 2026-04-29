import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import RiskBadge from "../components/RiskBadge";
import CallButton from "../components/CallButton";
import { ROUTE_META } from "../data/routes";

function cacheKey(slug) { return `ss_risk_${slug}`; }
function loadCache(slug) {
  try { return JSON.parse(localStorage.getItem(cacheKey(slug))); }
  catch {
    return null;
  }
}
function saveCache(slug, data) {
  try {
    localStorage.setItem(cacheKey(slug), JSON.stringify({ data, ts: Date.now() }));
  } catch {
    // Ignore storage failures; live fetch or empty state still handles the view.
  }
}

export default function RouteRisk() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const cachedRisk = loadCache(slug);
  const [risk, setRisk] = useState(() => cachedRisk?.data || null);
  const [loading, setLoading] = useState(() => !cachedRisk);
  const [offline, setOffline] = useState(() => Boolean(cachedRisk));
  const meta = ROUTE_META[slug] || {};

  useEffect(() => {
    const cached = loadCache(slug);

    fetch(`/routes/${slug}/risk`, { signal: AbortSignal.timeout(5000) })
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((data) => { setRisk(data); saveCache(slug, data); setOffline(false); setLoading(false); })
      .catch(() => { if (!cached) setLoading(false); });
  }, [slug]);

  const isMonsoon = [6,7,8,9].includes(new Date().getMonth() + 1);

  if (loading) {
    return (
      <div className="page">
        <div className="spinner"><div className="spin-ring" /><span>Loading…</span></div>
      </div>
    );
  }

  if (!risk) {
    return (
      <div className="page">
        <div className="page-header">
          <button className="back-btn" onClick={() => navigate("/")}>←</button>
          <h1>Route not found</h1>
        </div>
        <div className="page-body">
          <div className="card">
            <p className="text-muted">No data available. Backend may be offline.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <button className="back-btn" onClick={() => navigate("/")}>←</button>
        <div>
          <h1 style={{ fontSize: "1.2rem" }}>{meta.nameHi || risk.name}</h1>
          <div className="text-muted" style={{ fontSize: "0.8rem" }}>{risk.name}</div>
        </div>
      </div>

      <div className="page-body">
        {offline && (
          <div className="offline-banner mb-16">⚠️ Offline — last saved data</div>
        )}

        <RiskBadge level={risk.risk_level} large />

        {/* Reason */}
        <div className="card mb-16">
          <div className="section-label" style={{ padding: 0, marginBottom: 8 }}>Why this level?</div>
          <p className="reason-text">{risk.reason}</p>
        </div>

        {/* Monsoon warning */}
        {isMonsoon && meta.monsoonNoteHi && (
          <div className="monsoon-card">
            <strong>⚠️ मानसून सीज़न</strong>
            <p style={{ fontSize: "0.875rem" }}>{meta.monsoonNoteHi}</p>
            <p className="text-muted mt-4" style={{ fontSize: "0.8rem" }}>{meta.monsoonNote}</p>
          </div>
        )}

        {/* Weather */}
        <div className="card">
          <div className="section-label" style={{ padding: 0, marginBottom: 8 }}>मौसम / Weather — IMD Shimla</div>
          {risk.weather_summary
            ? <p style={{ fontSize: "0.95rem" }}>{risk.weather_summary}</p>
            : <p className="text-muted">No weather data yet</p>}
          {risk.weather_hours_old != null && (
            <p className="text-muted mt-4" style={{ fontSize: "0.78rem" }}>
              {risk.weather_is_fresh ? `✓ Updated ${risk.weather_hours_old}h ago` : `⚠ Data ${risk.weather_hours_old}h old — may be stale`}
            </p>
          )}
        </div>

        {/* Local report */}
        {risk.latest_report && (
          <div className="card">
            <div className="section-label" style={{ padding: 0, marginBottom: 8 }}>स्थानीय रिपोर्ट / Local Report</div>
            <p style={{ fontSize: "0.95rem", fontWeight: 600 }}>{risk.latest_report}</p>
            {risk.report_hours_old && (
              <p className="text-muted mt-4" style={{ fontSize: "0.78rem" }}>
                {risk.report_hours_old < 2 ? "Very recent ✓"
                  : risk.report_hours_old < 6 ? `${risk.report_hours_old}h ago — verify before travel`
                  : `${risk.report_hours_old}h ago — conditions may have changed`}
              </p>
            )}
          </div>
        )}

        {/* Route info */}
        <div className="card">
          <div className="section-label" style={{ padding: 0, marginBottom: 4 }}>Route details</div>
          {meta.distance && <div className="info-row"><span className="ir-label">Distance</span><span className="ir-value">{meta.distance}</span></div>}
          {meta.altitude && <div className="info-row"><span className="ir-label">Max altitude</span><span className="ir-value">{meta.altitude}</span></div>}
          {meta.lastConnectivity && <div className="info-row"><span className="ir-label">Last network</span><span className="ir-value">{meta.lastConnectivity}</span></div>}
          {meta.altitudeNoteHi && (
            <p style={{ fontSize: "0.85rem", color: "#374151", marginTop: 10 }}>⛰️ {meta.altitudeNoteHi}</p>
          )}
        </div>

        {/* Hospital */}
        <div className="section mt-8">
          <div className="section-label" style={{ padding: 0 }}>नज़दीकी अस्पताल / Nearest Hospital</div>
          {risk.nearest_hospital_name
            ? <CallButton icon="🏥" name={risk.nearest_hospital_name} number={risk.nearest_hospital_phone} />
            : <div className="card"><p className="text-muted">Hospital info not available</p></div>}
        </div>

        {/* Reporters */}
        {risk.reporters?.length > 0 && (
          <div className="section">
            <div className="section-label" style={{ padding: 0 }}>रास्ता verify करें — Ground truth</div>
            {risk.reporters.slice(0, 2).map((r, i) => (
              <CallButton
                key={i}
                icon={r.role === "taxi_driver" ? "🚕" : r.role === "dhaba_owner" ? "🍽️" : "🏠"}
                name={`${r.name} · ${(r.role || "local").replace("_", " ")}`}
                nameHi={r.location}
                number={r.phone}
              />
            ))}
          </div>
        )}

        {/* Share */}
        <a
          href={`https://wa.me/?text=${encodeURIComponent(`SafarSathi route safety: ${risk.name} — Current risk: ${risk.risk_level}. Check SafarSathi before traveling to mountain areas.`)}`}
          className="wa-cta"
          target="_blank"
          rel="noreferrer"
          style={{ marginBottom: 24 }}
        >
          <span style={{ fontSize: "1.4rem" }}>📤</span>
          <span>परिवार को भेजें — Share safety info</span>
        </a>
      </div>
    </div>
  );
}
