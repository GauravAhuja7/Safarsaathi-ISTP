import { useState } from "react";
import CallButton from "../components/CallButton";
import { UNIVERSAL, MANDI, ROUTE_SPECIFIC } from "../data/emergency";

export default function Emergency() {
  const [query, setQuery] = useState("");

  const all = [...UNIVERSAL, ...MANDI];
  const filtered = query.trim()
    ? all.filter(
        (c) =>
          c.name.toLowerCase().includes(query.toLowerCase()) ||
          c.number.includes(query) ||
          (c.nameHi || "").includes(query)
      )
    : null;

  return (
    <div className="page">
      <div className="page-hero" style={{ background: "linear-gradient(135deg, #7f1d1d 0%, #dc2626 100%)" }}>
        <h1>आपातकालीन नंबर</h1>
        <p>Emergency contacts — works offline, no internet needed</p>
      </div>

      <div className="page-body">
        <input
          type="search"
          className="search-bar"
          placeholder="🔍 नाम या नंबर खोजें — Search…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />

        {filtered ? (
          <div className="section">
            {filtered.length === 0
              ? <p className="text-muted">No results.</p>
              : filtered.map((c, i) => (
                  <CallButton key={i} icon={c.icon} name={c.name} nameHi={c.nameHi} number={c.number} />
                ))}
          </div>
        ) : (
          <>
            <div className="section">
              <div className="section-label">🆘 Universal Emergency</div>
              {UNIVERSAL.map((c) => (
                <CallButton key={c.number} icon={c.icon} name={c.name} nameHi={c.nameHi} number={c.number} />
              ))}
            </div>

            <div className="section">
              <div className="section-label">🏛️ Mandi District — मंडी जिला</div>
              {MANDI.map((c) => (
                <CallButton key={c.number} icon={c.icon} name={c.name} nameHi={c.nameHi} number={c.number} />
              ))}
            </div>

            <div className="section">
              <div className="section-label">🛣️ Route-specific — रास्ते के नंबर</div>
              {Object.entries(ROUTE_SPECIFIC).map(([slug, contacts]) => (
                <div key={slug} style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: "0.8rem", fontWeight: 700, color: "var(--green)", marginBottom: 8, textTransform: "capitalize" }}>
                    {slug.replace("-", " → ")}
                  </div>
                  {contacts.map((c, i) => (
                    <CallButton key={i} icon={c.icon} name={c.name} nameHi={c.nameHi} number={c.number} />
                  ))}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
