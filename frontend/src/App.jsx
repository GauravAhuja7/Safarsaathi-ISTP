import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import NavBar from "./components/NavBar";
import RouteList from "./pages/RouteList";
import RouteRisk from "./pages/RouteRisk";
import Checklist from "./pages/Checklist";
import Emergency from "./pages/Emergency";
import AltitudePage from "./pages/Altitude";
import MapPage from "./pages/Map";
import "./styles/index.css";
import "maplibre-gl/dist/maplibre-gl.css";

function InstallBanner() {
  const promptRef = useRef(null);
  const [show, setShow] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem("pwa_dismissed");
    if (dismissed && Date.now() - Number(dismissed) < 86400000) return;

    const handler = (e) => {
      e.preventDefault();
      promptRef.current = e;
      setTimeout(() => setShow(true), 5000);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const install = () => {
    promptRef.current?.prompt();
    promptRef.current?.userChoice.then(() => setShow(false));
  };

  const dismiss = () => {
    localStorage.setItem("pwa_dismissed", String(Date.now()));
    setShow(false);
  };

  if (!show) return null;
  return (
    <div className="install-banner">
      <span style={{ fontSize: "1.4rem" }}>📱</span>
      <div className="install-text">Offline के लिए save करें — Add to Home Screen</div>
      <button className="btn-install" onClick={install}>Add</button>
      <button className="btn-dismiss" onClick={dismiss}>✕</button>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RouteList />} />
        <Route path="/route/:slug" element={<RouteRisk />} />
        <Route path="/checklist" element={<Checklist />} />
        <Route path="/emergency" element={<Emergency />} />
        <Route path="/emergency/:routeSlug" element={<Emergency />} />
        <Route path="/altitude" element={<AltitudePage />} />
        <Route path="/map" element={<MapPage />} />
      </Routes>
      <NavBar />
      <InstallBanner />
    </BrowserRouter>
  );
}
