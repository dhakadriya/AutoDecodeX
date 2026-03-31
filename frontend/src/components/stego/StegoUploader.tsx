"use client";
import { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Image as ImageIcon, X, Lock } from "lucide-react";

interface Props {
  onFile: (file: File) => void;
  file: File | null;
  onClear: () => void;
  password: string;
  onPasswordChange: (v: string) => void;
}

export default function StegoUploader({ onFile, file, onClear, password, onPasswordChange }: Props) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const previewUrl = file ? URL.createObjectURL(file) : null;

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f && f.type.startsWith("image/")) onFile(f);
  }, [onFile]);

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <motion.div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !file && inputRef.current?.click()}
        animate={dragging
          ? { boxShadow: "0 0 0 2px #00ff88, 0 0 30px rgba(0,255,136,0.3)" }
          : { boxShadow: "0 0 0 1px #1e1e3a" }
        }
        className={`relative rounded-xl border border-cyber-border bg-cyber-card
          flex flex-col items-center justify-center gap-3 transition-colors duration-200
          ${file ? "p-3" : "p-10 cursor-pointer hover:border-cyber-green/50"}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg,image/bmp,image/webp"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
        />

        <AnimatePresence mode="wait">
          {file && previewUrl ? (
            <motion.div
              key="preview"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="relative w-full"
            >
              <img
                src={previewUrl}
                alt="Preview"
                className="w-full max-h-48 object-contain rounded-lg border border-cyber-border"
              />
              <button
                onClick={(e) => { e.stopPropagation(); onClear(); }}
                className="absolute top-2 right-2 w-6 h-6 rounded-full bg-cyber-surface border border-cyber-border
                  flex items-center justify-center text-cyber-muted hover:text-red-400 transition-colors"
              >
                <X size={12} />
              </button>
              <div className="mt-2 flex items-center gap-2 px-1">
                <ImageIcon size={12} className="text-cyber-green" />
                <span className="text-xs text-cyber-muted font-mono truncate">{file.name}</span>
                <span className="text-xs text-cyber-muted ml-auto">
                  {(file.size / 1024).toFixed(1)} KB
                </span>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center gap-3 text-center"
            >
              <motion.div
                animate={dragging ? { scale: 1.2, color: "#00ff88" } : { scale: 1 }}
                className="w-12 h-12 rounded-xl border border-cyber-border bg-cyber-surface
                  flex items-center justify-center text-cyber-muted"
              >
                <Upload size={20} />
              </motion.div>
              <div>
                <p className="text-sm text-cyber-text font-mono">Drop image here</p>
                <p className="text-xs text-cyber-muted mt-1">PNG · JPEG · BMP · WebP · max 10MB</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Password field */}
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-cyber-border bg-cyber-card">
        <Lock size={12} className="text-cyber-muted shrink-0" />
        <input
          type="text"
          value={password}
          onChange={(e) => onPasswordChange(e.target.value)}
          placeholder="Password (optional)"
          className="flex-1 bg-transparent text-xs font-mono text-cyber-text outline-none placeholder-cyber-muted"
        />
      </div>
    </div>
  );
}
