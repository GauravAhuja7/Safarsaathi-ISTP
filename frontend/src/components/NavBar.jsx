import { NavLink } from "react-router-dom";

const NAV = [
  { to: "/",          icon: "🗺️",  label: "रास्ते",      end: true },
  { to: "/checklist", icon: "✅",  label: "चेकलिस्ट" },
  { to: "/emergency", icon: "🆘",  label: "आपातकाल" },
  { to: "/map",       icon: "📍",  label: "नक्शा" },
  { to: "/report",    icon: "📢",  label: "रिपोर्ट" },
];

export default function NavBar() {
  return (
    <nav className="bottom-nav">
      {NAV.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
        >
          <span className="nav-icon">{item.icon}</span>
          <span className="nav-label">{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
