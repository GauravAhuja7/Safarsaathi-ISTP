const CONFIG = {
  HIGH:    { emoji: "🔴", en: "HIGH RISK",  hi: "खतरा" },
  MEDIUM:  { emoji: "🟡", en: "MEDIUM",     hi: "सावधानी" },
  LOW:     { emoji: "🟢", en: "SAFE",       hi: "सुरक्षित" },
  UNKNOWN: { emoji: "⚫", en: "UNKNOWN",    hi: "अज्ञात" },
};

export default function RiskBadge({ level, large = false }) {
  const c = CONFIG[level] ?? CONFIG.UNKNOWN;

  if (large) {
    return (
      <div className={`risk-large-card ${level}`}>
        <div className="risk-emoji">{c.emoji}</div>
        <div className="risk-level-word">{c.en}</div>
        <div className="risk-label-hi">{c.hi}</div>
      </div>
    );
  }

  return (
    <span className={`risk-badge ${level}`}>
      <span className="risk-dot" />
      {c.hi} · {c.en}
    </span>
  );
}
