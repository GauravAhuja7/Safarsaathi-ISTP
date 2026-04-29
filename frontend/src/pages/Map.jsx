import { useEffect, useRef, useState } from "react";

// Key POIs hardcoded — matches backend seed data, works fully offline
const POIS = [
  { name: "Mandi Zonal Hospital", nameHi: "मंडी जोनल अस्पताल", phone: "01905-222380", cat: "hospital", lat: 31.7083, lng: 76.9319 },
  { name: "District Control Room", nameHi: "जिला नियंत्रण कक्ष", phone: "01905-226201", cat: "police", lat: 31.7090, lng: 76.9340 },
  { name: "SP Mandi Office", nameHi: "SP मंडी कार्यालय", phone: "01905-222402", cat: "police", lat: 31.7072, lng: 76.9350 },
  { name: "Baggi Village Checkpoint", nameHi: "बग्गी गांव चेकपॉइंट (Parashar)", phone: "", cat: "checkpoint", lat: 31.9000, lng: 76.9800 },
  { name: "Ghatasani (Barot route)", nameHi: "घटासणी (बरोट रास्ता)", phone: "", cat: "checkpoint", lat: 31.8500, lng: 76.8000 },
  { name: "Pandoh Dam Police Post", nameHi: "पंडोह पुलिस चौकी (NH-3)", phone: "", cat: "police", lat: 31.6800, lng: 77.0600 },
  { name: "Mandi ISBT Bus Stand", nameHi: "मंडी ISBT बस अड्डा", phone: "", cat: "checkpoint", lat: 31.7083, lng: 76.9250 },
];

const CAT_COLORS = {
  hospital: "#dc2626",
  police: "#2563eb",
  petrol: "#d97706",
  mechanic: "#6b7280",
  checkpoint: "#059669",
};

const CAT_ICONS = {
  hospital: "🏥",
  police: "👮",
  petrol: "⛽",
  mechanic: "🔧",
  checkpoint: "📍",
};

function POIList({ selected, onSelect }) {
  return (
    <div style={{ marginTop: 16 }}>
      <div className="section-title" style={{ marginBottom: 10 }}>Key Locations / प्रमुख स्थान</div>
      {POIS.map((poi, i) => (
        <div
          key={i}
          className="poi-item"
          style={{
            cursor: "pointer",
            borderColor: selected === i ? CAT_COLORS[poi.cat] : undefined,
            background: selected === i ? "#f0fdf4" : undefined,
          }}
          onClick={() => onSelect(selected === i ? null : i)}
        >
          <span className={`poi-dot ${poi.cat}`} style={{ background: CAT_COLORS[poi.cat] }} />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>
              {CAT_ICONS[poi.cat]} {poi.name}
            </div>
            <div className="text-muted" style={{ fontSize: "0.8rem" }}>{poi.nameHi}</div>
          </div>
          {poi.phone && (
            <a
              href={`tel:${poi.phone}`}
              style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--green)", textDecoration: "none" }}
              onClick={(e) => e.stopPropagation()}
            >
              📞
            </a>
          )}
        </div>
      ))}
    </div>
  );
}

export default function MapPage() {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [mapLibre, setMapLibre] = useState(null);
  const [mapError, setMapError] = useState(false);
  const [selectedPOI, setSelectedPOI] = useState(null);

  useEffect(() => {
    let cancelled = false;

    // Dynamically import MapLibre to avoid bundle bloat when not on this page
    import("maplibre-gl")
      .then((ml) => {
        if (cancelled || !mapRef.current) return;

        const map = new ml.default.Map({
          container: mapRef.current,
          // Use OpenFreeMap as the tile source — free, no API key
          style: "https://tiles.openfreemap.org/styles/liberty",
          center: [76.9319, 31.7083], // Mandi
          zoom: 10,
          attributionControl: true,
        });

        map.on("load", () => {
          // Add POI markers
          POIS.forEach((poi) => {
            const el = document.createElement("div");
            el.innerHTML = `<div style="background:${CAT_COLORS[poi.cat]};color:#fff;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:14px;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.3);cursor:pointer;">${CAT_ICONS[poi.cat]}</div>`;

            const popup = new ml.default.Popup({ offset: 16 }).setHTML(
              `<strong>${poi.name}</strong><br>${poi.nameHi}${poi.phone ? `<br><a href="tel:${poi.phone}" style="color:#1a6b3c;font-weight:700;">${poi.phone}</a>` : ""}`
            );

            new ml.default.Marker({ element: el })
              .setLngLat([poi.lng, poi.lat])
              .setPopup(popup)
              .addTo(map);
          });
        });

        map.on("error", () => setMapError(true));
        mapInstanceRef.current = map;
        setMapLibre(map);
      })
      .catch(() => setMapError(true));

    return () => {
      cancelled = true;
      mapInstanceRef.current?.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  const locateMe = () => {
    navigator.geolocation?.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        mapLibre?.flyTo({ center: [longitude, latitude], zoom: 13 });
      },
      () => alert("Location access denied")
    );
  };

  return (
    <div className="page">
      <div style={{ marginBottom: 16 }}>
        <h1>नक्शा / Map</h1>
        <p className="text-muted">Key locations — Mandi region</p>
      </div>

      <div className="map-wrap">
        {mapError ? (
          <div className="map-placeholder">
            <span style={{ fontSize: "3rem" }}>🗺️</span>
            <p style={{ marginTop: 12, fontWeight: 600 }}>Map unavailable offline</p>
            <p className="text-muted">See location list below</p>
          </div>
        ) : (
          <div ref={mapRef} style={{ width: "100%", height: "100%" }} />
        )}
      </div>

      <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
        <button
          onClick={locateMe}
          style={{
            flex: 1,
            padding: "12px",
            background: "var(--green)",
            color: "#fff",
            border: "none",
            borderRadius: "var(--radius)",
            fontWeight: 700,
            cursor: "pointer",
            fontSize: "0.95rem",
          }}
        >
          📍 My Location
        </button>
      </div>

      {/* Legend */}
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 12, fontSize: "0.8rem" }}>
        {Object.entries(CAT_ICONS).map(([cat, icon]) => (
          <span key={cat} style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <span style={{ background: CAT_COLORS[cat], color: "#fff", borderRadius: "50%", width: 18, height: 18, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "10px" }}>{icon}</span>
            {cat}
          </span>
        ))}
      </div>

      <POIList selected={selectedPOI} onSelect={setSelectedPOI} />
    </div>
  );
}
