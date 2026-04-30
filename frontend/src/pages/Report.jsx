import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

const ROUTES = [
  { slug: "parashar", label: "Parashar Lake", labelHi: "परासर झील" },
  { slug: "barot", label: "Barot Valley", labelHi: "बरोट घाटी" },
  { slug: "kullu-manali", label: "Kullu-Manali (NH-3)", labelHi: "कुल्लू-मनाली" },
];

const CONDITIONS = [
  { value: "blocked", label: "Road BLOCKED", labelHi: "रास्ता बंद", emoji: "🚫", color: "#dc2626" },
  { value: "rough", label: "Road ROUGH — open but dangerous", labelHi: "रास्ता खुला पर खतरनाक", emoji: "⚠️", color: "#d97706" },
  { value: "clear", label: "Road CLEAR — normal conditions", labelHi: "रास्ता ठीक है", emoji: "✅", color: "#16a34a" },
  { value: "other", label: "Other / not sure", labelHi: "अन्य / पता नहीं", emoji: "❓", color: "#6b7280" },
];

export default function Report() {
  const navigate = useNavigate();
  const fileRef = useRef(null);

  const [routeSlug, setRouteSlug] = useState("");
  const [condition, setCondition] = useState("");
  const [description, setDescription] = useState("");
  const [name, setName] = useState("");
  const [photo, setPhoto] = useState(null);      // File object
  const [photoPreview, setPhotoPreview] = useState(null);
  const [status, setStatus] = useState("idle");  // idle | submitting | success | error
  const [errorMsg, setErrorMsg] = useState("");

  function handlePhotoChange(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setPhoto(file);
    setPhotoPreview(URL.createObjectURL(file));
  }

  function removePhoto() {
    setPhoto(null);
    setPhotoPreview(null);
    if (fileRef.current) fileRef.current.value = "";
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!routeSlug || !condition) return;

    setStatus("submitting");
    setErrorMsg("");

    try {
      // Upload photo first if present (base64 data URL for simplicity)
      let photoUrl = null;
      if (photo) {
        photoUrl = await fileToDataUrl(photo);
      }

      const payload = {
        route_slug: routeSlug,
        condition,
        description: description.trim() || null,
        photo_url: photoUrl,
        submitted_by: name.trim() || null,
        source: "website",
      };

      const res = await fetch("/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.detail || `Error ${res.status}`);
      }

      setStatus("success");
    } catch (err) {
      setStatus("error");
      setErrorMsg(err.message || "Submission failed. Please try again.");
    }
  }

  if (status === "success") {
    const chosen = CONDITIONS.find((c) => c.value === condition);
    const chosenRoute = ROUTES.find((r) => r.slug === routeSlug);
    return (
      <div className="page">
        <div className="page-hero" style={{ background: "linear-gradient(135deg, #14532d 0%, #16a34a 100%)" }}>
          <h1>Report Submitted</h1>
          <p>रिपोर्ट भेज दी गई — धन्यवाद!</p>
        </div>
        <div className="page-body">
          <div className="card" style={{ textAlign: "center", padding: "32px 20px" }}>
            <div style={{ fontSize: "3rem", marginBottom: 12 }}>✅</div>
            <h2 style={{ fontSize: "1.2rem", marginBottom: 8 }}>Thank you!</h2>
            <p style={{ color: "var(--text-muted)", marginBottom: 20 }}>
              Your report for <strong>{chosenRoute?.label}</strong> has been saved.<br />
              Condition: {chosen?.emoji} <strong>{chosen?.label}</strong>
            </p>
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: 24 }}>
              Your report helps tourists make safer travel decisions.
            </p>
            <button className="btn-submit" style={{ width: "100%" }} onClick={() => navigate("/")}>
              Back to Home
            </button>
          </div>

          <div className="card" style={{ marginTop: 16 }}>
            <div className="section-label" style={{ padding: 0, marginBottom: 8 }}>Also report via Telegram / WhatsApp</div>
            <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
              Send <strong>report</strong> to SafarSathiBot on Telegram to submit future reports directly from your phone — you can also attach photos and videos.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-hero" style={{ background: "linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
          <button
            className="back-btn"
            style={{ background: "rgba(255,255,255,0.15)", border: "none", color: "#fff" }}
            onClick={() => navigate("/")}
          >←</button>
          <h1 style={{ color: "#fff" }}>Road Condition Report</h1>
        </div>
        <p>रास्ते की जानकारी दें — Help other travelers</p>
      </div>

      <div className="page-body">
        <form onSubmit={handleSubmit}>

          {/* Route selector */}
          <div className="section">
            <div className="section-label">1. Select route — रास्ता चुनें *</div>
            {ROUTES.map((r) => (
              <label
                key={r.slug}
                className="card"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  cursor: "pointer",
                  marginBottom: 10,
                  border: routeSlug === r.slug ? "2px solid var(--blue)" : "1px solid var(--border)",
                  background: routeSlug === r.slug ? "#eff6ff" : "var(--white)",
                  padding: "14px 16px",
                }}
              >
                <input
                  type="radio"
                  name="route"
                  value={r.slug}
                  checked={routeSlug === r.slug}
                  onChange={() => setRouteSlug(r.slug)}
                  style={{ accentColor: "var(--blue)", width: 20, height: 20, flexShrink: 0 }}
                />
                <div>
                  <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>{r.labelHi}</div>
                  <div style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>{r.label}</div>
                </div>
              </label>
            ))}
          </div>

          {/* Condition selector */}
          <div className="section">
            <div className="section-label">2. Road condition — रोड की स्थिति *</div>
            {CONDITIONS.map((c) => (
              <label
                key={c.value}
                className="card"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  cursor: "pointer",
                  marginBottom: 10,
                  border: condition === c.value ? `2px solid ${c.color}` : "1px solid var(--border)",
                  background: condition === c.value ? `${c.color}11` : "var(--white)",
                  padding: "14px 16px",
                }}
              >
                <input
                  type="radio"
                  name="condition"
                  value={c.value}
                  checked={condition === c.value}
                  onChange={() => setCondition(c.value)}
                  style={{ accentColor: c.color, width: 20, height: 20, flexShrink: 0 }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>
                    {c.emoji} {c.label}
                  </div>
                  <div style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>{c.labelHi}</div>
                </div>
              </label>
            ))}
          </div>

          {/* Photo / video upload */}
          <div className="section">
            <div className="section-label">3. Photo or video — फोटो / वीडियो (optional)</div>
            <div
              className="card"
              style={{
                border: "2px dashed var(--border)",
                textAlign: "center",
                padding: "20px 16px",
                cursor: "pointer",
                background: "var(--white)",
              }}
              onClick={() => fileRef.current?.click()}
            >
              {photoPreview ? (
                <div>
                  <img
                    src={photoPreview}
                    alt="Preview"
                    style={{ maxWidth: "100%", maxHeight: 200, borderRadius: 10, objectFit: "cover" }}
                  />
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); removePhoto(); }}
                    style={{
                      marginTop: 10,
                      display: "block",
                      width: "100%",
                      padding: "8px",
                      background: "var(--red-light)",
                      color: "var(--red)",
                      border: "none",
                      borderRadius: 8,
                      cursor: "pointer",
                      fontWeight: 600,
                    }}
                  >
                    Remove photo
                  </button>
                </div>
              ) : (
                <div>
                  <div style={{ fontSize: "2.5rem", marginBottom: 8 }}>📷</div>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>Tap to add photo</div>
                  <div style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                    फोटो या वीडियो जोड़ें — Helps verify road conditions
                  </div>
                </div>
              )}
            </div>
            <input
              ref={fileRef}
              type="file"
              accept="image/*,video/*"
              capture="environment"
              style={{ display: "none" }}
              onChange={handlePhotoChange}
            />
          </div>

          {/* Optional description */}
          <div className="section">
            <div className="section-label">4. Additional details — अतिरिक्त जानकारी (optional)</div>
            <textarea
              className="card"
              style={{
                width: "100%",
                minHeight: 100,
                fontFamily: "inherit",
                fontSize: "0.95rem",
                padding: "14px 16px",
                border: "1px solid var(--border)",
                resize: "vertical",
                color: "var(--text)",
                background: "var(--white)",
              }}
              placeholder="E.g. Landslide past Baggi village, road open with caution..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={500}
            />
            <div style={{ textAlign: "right", fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 4 }}>
              {description.length}/500
            </div>
          </div>

          {/* Name (optional) */}
          <div className="section">
            <div className="section-label">5. Your name — आपका नाम (optional)</div>
            <input
              type="text"
              className="card"
              style={{
                width: "100%",
                fontFamily: "inherit",
                fontSize: "0.95rem",
                padding: "14px 16px",
                border: "1px solid var(--border)",
                color: "var(--text)",
                background: "var(--white)",
              }}
              placeholder="Name or location (e.g. Baggi dhaba owner)"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={100}
            />
          </div>

          {/* Error */}
          {status === "error" && (
            <div
              className="card"
              style={{ background: "var(--red-light)", border: "1px solid #fca5a5", color: "var(--red)", marginBottom: 16 }}
            >
              {errorMsg}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            className="btn-submit"
            disabled={!routeSlug || !condition || status === "submitting"}
            style={{
              width: "100%",
              padding: "16px",
              fontSize: "1rem",
              fontWeight: 700,
              background: !routeSlug || !condition ? "var(--gray)" : "var(--blue)",
              color: "#fff",
              border: "none",
              borderRadius: "var(--radius)",
              cursor: !routeSlug || !condition ? "not-allowed" : "pointer",
              marginBottom: 32,
              opacity: status === "submitting" ? 0.7 : 1,
            }}
          >
            {status === "submitting" ? "Submitting…" : "📤 Submit Report"}
          </button>
        </form>
      </div>
    </div>
  );
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
