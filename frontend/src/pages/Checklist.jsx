import { useState, useEffect } from "react";
import AudioPlayer from "../components/AudioPlayer";
import { PRE_TRIP, ALTITUDE } from "../data/checklists";

const ALL_ITEMS = [...PRE_TRIP, ...ALTITUDE];
const STORAGE_KEY = "ss_checklist_v1";

function loadChecked() {
  try { return new Set(JSON.parse(localStorage.getItem(STORAGE_KEY)) || []); }
  catch {
    return new Set();
  }
}
function saveChecked(set) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify([...set])); }
  catch {
    // Ignore storage failures; the checklist remains usable for this session.
  }
}

function Section({ title, titleHi, items, checked, onToggle }) {
  return (
    <div className="section">
      <div className="section-label">{titleHi} — {title}</div>
      {items.map((item) => {
        const done = checked.has(item.id);
        return (
          <div
            key={item.id}
            className={`checklist-item${done ? " done" : ""}`}
            onClick={() => onToggle(item.id)}
          >
            <input
              type="checkbox"
              checked={done}
              onChange={() => onToggle(item.id)}
              onClick={(e) => e.stopPropagation()}
            />
            <div style={{ flex: 1 }}>
              <div className="ci-en">{item.en}</div>
              <div className="ci-hi">{item.hi}</div>
              {item.detail && <div className="ci-detail">{item.detail}</div>}
              {item.audio && <AudioPlayer src={item.audio} />}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function Checklist() {
  const [checked, setChecked] = useState(() => loadChecked());

  useEffect(() => { saveChecked(checked); }, [checked]);

  const toggle = (id) => {
    setChecked((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const done = ALL_ITEMS.filter((i) => checked.has(i.id)).length;
  const total = ALL_ITEMS.length;
  const pct = Math.round((done / total) * 100);

  return (
    <div className="page">
      <div className="page-hero" style={{ background: "linear-gradient(135deg, #14532d 0%, #16a34a 100%)" }}>
        <h1>यात्रा चेकलिस्ट</h1>
        <p>Pre-trip checklist — {done}/{total} complete ({pct}%)</p>
        <div className="progress-track" style={{ marginTop: 12 }}>
          <div className="progress-fill" style={{ width: `${pct}%` }} />
        </div>
      </div>

      <div className="page-body">
        <Section
          title="Before You Travel"
          titleHi="यात्रा से पहले"
          items={PRE_TRIP}
          checked={checked}
          onToggle={toggle}
        />

        <Section
          title="At High Altitude"
          titleHi="अधिक ऊंचाई पर"
          items={ALTITUDE}
          checked={checked}
          onToggle={toggle}
        />

        <div style={{ display: "flex", gap: 10, marginBottom: 24 }}>
          <button
            onClick={() => setChecked(new Set())}
            style={{
              padding: "12px 20px",
              border: "1.5px solid var(--border)",
              borderRadius: "var(--radius-sm)",
              background: "#fff",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "0.9rem",
              fontFamily: "var(--font)",
            }}
          >
            🔄 Reset
          </button>
          <a
            href={`https://wa.me/?text=${encodeURIComponent(
              "SafarSathi checklist:\n" + PRE_TRIP.map((i) => `${checked.has(i.id) ? "✅" : "⬜"} ${i.en}`).join("\n")
            )}`}
            target="_blank"
            rel="noreferrer"
            className="wa-cta"
            style={{ flex: 1 }}
          >
            <span>📤</span><span>Share</span>
          </a>
        </div>
      </div>
    </div>
  );
}
