"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { Layers } from "lucide-react";

interface Props {
  planes: Record<string, Record<string, string>> | null;
}

const CHANNEL_COLORS: Record<string, string> = {
  R: "text-red-500 border-red-500/40",
  G: "text-theme-success border-theme-success/40",
  B: "text-theme-accent border-theme-accent/40",
};

export default function BitPlaneViewer({ planes }: Props) {
  const [activeChannel, setActiveChannel] = useState("R");
  const [activeBit, setActiveBit] = useState(0);

  if (!planes) return null;

  const channels = Object.keys(planes);
  const currentPlane = planes[activeChannel]?.[`bit${activeBit}`];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-3 select-none"
    >
      <div className="flex items-center gap-2">
        <Layers size={13} className="text-theme-accent" />
        <span className="text-xs text-theme-secondary uppercase tracking-widest font-mono">Bit-Plane Viewer</span>
      </div>

      {/* Channel selector */}
      <div className="flex gap-2">
        {channels.map((ch) => (
          <button
            key={ch}
            onClick={() => setActiveChannel(ch)}
            className={`px-3 py-1 text-xs font-mono rounded border transition-all
              ${activeChannel === ch
                ? CHANNEL_COLORS[ch] + " bg-theme-accent/10"
                : "border-theme-border text-theme-secondary hover:border-theme-border/70"
              }`}
          >
            {ch}
          </button>
        ))}
      </div>

      {/* Bit selector */}
      <div className="flex gap-1.5 flex-wrap">
        {Array.from({ length: 8 }, (_, i) => (
          <button
            key={i}
            onClick={() => setActiveBit(i)}
            className={`w-8 h-7 text-xs font-mono rounded border transition-all
              ${activeBit === i
                ? "border-theme-accent text-theme-accent bg-theme-accent/10"
                : "border-theme-border text-theme-secondary hover:border-theme-border/70"
              }`}
          >
            {i}
          </button>
        ))}
      </div>

      {/* Plane image */}
      {currentPlane && (
        <motion.div
          key={`${activeChannel}-${activeBit}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="rounded-lg overflow-hidden border border-theme-border bg-theme-card"
        >
          <img
            src={`data:image/png;base64,${currentPlane}`}
            alt={`${activeChannel} bit ${activeBit}`}
            className="w-full object-contain max-h-48"
          />
          <div className="px-3 py-1.5 bg-theme-surface border-t border-theme-border">
            <span className="text-xs text-theme-secondary font-mono">
              Channel: <span className={CHANNEL_COLORS[activeChannel].split(" ")[0]}>{activeChannel}</span>
              {" · "}Bit plane: <span className="text-theme-accent">{activeBit}</span>
              {activeBit === 0 && <span className="text-theme-success ml-2">← LSB (most likely stego)</span>}
            </span>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
