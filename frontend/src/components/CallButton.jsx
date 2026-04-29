export default function CallButton({ icon, name, nameHi, number }) {
  const isTBD = !number || number === "TBD";

  const copy = (e) => {
    e.preventDefault();
    if (!isTBD) navigator.clipboard?.writeText(number).catch(() => {});
  };

  return (
    <a
      href={isTBD ? undefined : `tel:${number}`}
      className="call-btn"
      style={isTBD ? { opacity: 0.45, pointerEvents: "none" } : {}}
    >
      <span className="cb-icon">{icon}</span>
      <span className="cb-info">
        <div className="cb-name">{name}</div>
        {nameHi && <div className="cb-name-hi">{nameHi}</div>}
        <div className="cb-number">{isTBD ? "— जल्द आएगा" : number}</div>
      </span>
      {!isTBD && (
        <button className="cb-copy" onClick={copy} title="Copy">📋</button>
      )}
    </a>
  );
}
