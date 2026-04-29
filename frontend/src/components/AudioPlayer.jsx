import { useRef, useState } from "react";

export default function AudioPlayer({ src, label = "सुनें (Listen)" }) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState(false);

  if (error) return null; // If audio file missing, show nothing — don't crash

  const toggle = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) {
      audio.pause();
      audio.currentTime = 0;
      setPlaying(false);
    } else {
      audio.play().catch(() => setError(true));
      setPlaying(true);
    }
  };

  return (
    <>
      <audio
        ref={audioRef}
        src={src}
        onEnded={() => setPlaying(false)}
        onError={() => setError(true)}
        preload="none"
      />
      <button className={`audio-btn ${playing ? "playing" : ""}`} onClick={toggle}>
        {playing ? "⏹ " : "▶ "}{label}
      </button>
    </>
  );
}
