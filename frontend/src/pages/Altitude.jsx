import { useState } from "react";
import AudioPlayer from "../components/AudioPlayer";
import { ALTITUDE, AMS_MILD, AMS_EMERGENCY } from "../data/checklists";
import { ROUTE_META } from "../data/routes";

const SLUGS = ["parashar", "barot", "kullu-manali"];

export default function AltitudePage() {
  const [slug, setSlug] = useState("parashar");
  const meta = ROUTE_META[slug];

  return (
    <div className="page">
      <div className="page-hero" style={{ background: "linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%)" }}>
        <h1>ऊंचाई सुरक्षा</h1>
        <p>Altitude sickness guide — fully offline</p>
      </div>

      <div className="page-body">
        {/* Route selector */}
        <div className="section">
          <div className="section-label">रास्ता चुनें — Select route</div>
          <div className="pill-group">
            {SLUGS.map((s) => (
              <button key={s} className={`pill${slug === s ? " active" : ""}`} onClick={() => setSlug(s)}>
                {ROUTE_META[s].nameHi.split("→")[1]?.trim()}
              </button>
            ))}
          </div>

          {/* Route altitude card */}
          <div className="altitude-info-card">
            <div style={{ fontSize: "1.25rem", fontWeight: 800, color: "#1d4ed8", marginBottom: 6 }}>
              ⛰️ {meta.altitude}
            </div>
            <p style={{ fontWeight: 600, fontSize: "0.95rem" }}>{meta.altitudeNoteHi}</p>
            <p className="text-muted mt-4" style={{ fontSize: "0.82rem" }}>{meta.altitudeNote}</p>
          </div>
        </div>

        {/* Prevention */}
        <div className="section">
          <div className="section-label">रोकथाम — Prevention</div>
          {ALTITUDE.map((item) => (
            <div className="card" key={item.id}>
              <p style={{ fontWeight: 700 }}>{item.en}</p>
              <p className="ci-hi">{item.hi}</p>
              {item.audio && <AudioPlayer src={item.audio} />}
            </div>
          ))}
        </div>

        {/* Mild symptoms */}
        <div className="section">
          <div className="section-label">हल्के लक्षण — Mild Symptoms</div>
          <div className="card" style={{ marginBottom: 10, background: "#fffbeb", border: "1px solid #fcd34d" }}>
            <p style={{ fontSize: "0.85rem", fontWeight: 600 }}>
              ➡️ आराम करें, और ऊपर न जाएं, पानी पिएं। 1 घंटे में ठीक न हो तो नीचे उतरें।
            </p>
          </div>
          {AMS_MILD.map((item) => (
            <div className="card" key={item.id}>
              <div style={{ fontWeight: 700, marginBottom: 4 }}>{item.en} <span style={{ fontWeight: 400, color: "var(--text-muted)" }}>· {item.hi}</span></div>
              <div style={{ fontSize: "0.85rem", borderTop: "1px solid var(--border)", paddingTop: 8, marginTop: 4 }}>
                <p>→ {item.action}</p>
                <p className="text-muted mt-4">{item.actionHi}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Emergency */}
        <div className="section">
          <div className="ams-emergency">
            <h2>🚨 EMERGENCY — तुरंत नीचे उतरें</h2>
            <p style={{ fontSize: "0.875rem", marginBottom: 12 }}>
              इनमें से कोई भी लक्षण दिखे — <strong>फ़ौरन नीचे उतरें।</strong> रुकें नहीं।
            </p>
            <ul>
              {AMS_EMERGENCY.map((item, i) => (
                <li key={i}>
                  {item.en}
                  <div className="li-hi">{item.hi}</div>
                </li>
              ))}
            </ul>
            <p style={{ marginTop: 14, fontSize: "0.875rem", fontWeight: 700 }}>
              नियम: 1 घंटे में ठीक न हो → नीचे उतरो। ऊपर मत जाओ।
            </p>
            <a href="tel:108" className="descend-btn">
              🚑 नीचे उतरें और 108 कॉल करें
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
