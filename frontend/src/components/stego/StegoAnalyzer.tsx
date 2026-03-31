"use client";
import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Eye, Zap, RotateCcw, ScanLine, Layers, FileText } from "lucide-react";

import StegoUploader from "./StegoUploader";
import BitPlaneViewer from "./BitPlaneViewer";
import StegoResults from "./StegoResults";

import {
  stegoAnalyze, stegoBruteForce, stegoBitPlanes, stegoPixelDiff, stegoTextAnalyze,
  type StegoAnalyzeResponse, type StegoBruteResult, type TextStegoResponse,
} from "@/lib/api";

type Tab = "image" | "text";

const LOGS_STEPS = [
  "[*] Loading image data...",
  "[*] Extracting LSB channels...",
  "[*] Running entropy analysis...",
  "[*] Chi-square test on pixel pairs...",
  "[*] Scanning for hidden ASCII...",
  "[*] Checking Base64 patterns...",
  "[*] Running auto-decode pipeline...",
  "[+] Analysis complete.",
];

function TerminalLog({ logs }: { logs: string[] }) {
  return (
    <div className="bg-cyber-card border border-cyber-border rounded-lg p-3 font-mono text-xs space-y-1 max-h-36 overflow-y-auto">
      <AnimatePresence>
        {logs.map((log, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2 }}
            className={log.startsWith("[+]") ? "text-cyber-green" : "text-cyber-muted"}
          >
            {log}
          </motion.div>
        ))}
      </AnimatePresence>
      {logs.length > 0 && logs[logs.length - 1] !== "[+] Analysis complete." && (
        <span className="animate-pulse text-cyber-green">█</span>
      )}
    </div>
  );
}

export default function StegoAnalyzer() {
  const [tab, setTab] = useState<Tab>("image");

  // Image stego state
  const [file, setFile] = useState<File | null>(null);
  const [password, setPassword] = useState("");
  const [bits, setBits] = useState(1);
  const [channels, setChannels] = useState("RGB");
  const [autoDecode, setAutoDecode] = useState(true);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [result, setResult] = useState<StegoAnalyzeResponse | null>(null);
  const [bruteResults, setBruteResults] = useState<StegoBruteResult[] | null>(null);
  const [planes, setPlanes] = useState<Record<string, Record<string, string>> | null>(null);
  const [diffMap, setDiffMap] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Text stego state
  const [textInput, setTextInput] = useState("");
  const [textResult, setTextResult] = useState<TextStegoResponse | null>(null);
  const [textLoading, setTextLoading] = useState(false);

  const pushLog = (msg: string) => setLogs((prev) => [...prev, msg]);

  const handleAnalyze = useCallback(async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setBruteResults(null);
    setPlanes(null);
    setDiffMap(null);
    setLogs([]);

    try {
      for (let i = 0; i < LOGS_STEPS.length - 1; i++) {
        await new Promise((r) => setTimeout(r, 300 + i * 150));
        pushLog(LOGS_STEPS[i]);
      }

      const [analyzeRes, diffRes] = await Promise.all([
        stegoAnalyze(file, bits, channels, password, autoDecode),
        stegoPixelDiff(file),
      ]);

      setResult(analyzeRes);
      setDiffMap(diffRes.diff_map);
      pushLog(LOGS_STEPS[LOGS_STEPS.length - 1]);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }, [file, bits, channels, password, autoDecode]);

  const handleBruteForce = useCallback(async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setBruteResults(null);
    setLogs(["[*] Starting brute-force LSB extraction...", "[*] Trying all channel combinations..."]);

    try {
      const [bruteRes, planesRes] = await Promise.all([
        stegoBruteForce(file, autoDecode),
        stegoBitPlanes(file),
      ]);
      setBruteResults(bruteRes.results);
      setPlanes(planesRes.planes);
      pushLog("[*] Bit-plane analysis complete.");
      pushLog("[+] Brute-force complete.");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Brute-force failed.");
    } finally {
      setLoading(false);
    }
  }, [file, autoDecode]);

  const handleTextAnalyze = useCallback(async () => {
    if (!textInput.trim()) return;
    setTextLoading(true);
    setTextResult(null);
    try {
      const res = await stegoTextAnalyze(textInput);
      setTextResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Text analysis failed.");
    } finally {
      setTextLoading(false);
    }
  }, [textInput]);

  const handleReset = () => {
    setFile(null); setResult(null); setBruteResults(null);
    setPlanes(null); setDiffMap(null); setLogs([]); setError(null);
    setTextResult(null); setTextInput("");
  };

  return (
    <div className="space-y-6">
      {/* Section header */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center gap-3"
      >
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyber-purple to-cyber-pink flex items-center justify-center">
          <Eye size={16} className="text-white" />
        </div>
        <div>
          <h2 className="text-lg font-bold font-mono text-cyber-text">
            Stego <span className="neon-purple">Analyzer</span>
          </h2>
          <p className="text-xs text-cyber-muted">Forensic steganography detection & extraction lab</p>
        </div>
      </motion.div>

      {/* Tab switcher */}
      <div className="flex gap-2">
        {([["image", "Image Stego", ScanLine], ["text", "Text Stego", FileText]] as const).map(([t, label, Icon]) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-xs font-mono transition-all
              ${tab === t
                ? "border-cyber-purple text-cyber-purple bg-cyber-purple/10"
                : "border-cyber-border text-cyber-muted hover:border-cyber-muted"
              }`}
          >
            <Icon size={12} />
            {label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {tab === "image" ? (
          <motion.div
            key="image"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6"
          >
            {/* Left: results */}
            <div className="space-y-4">
              {logs.length > 0 && <TerminalLog logs={logs} />}

              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="p-3 rounded-lg border border-red-500/40 bg-red-500/10 text-red-400 text-xs font-mono"
                  >
                    ⚠ {error}
                  </motion.div>
                )}
              </AnimatePresence>

              <StegoResults result={result} bruteResults={bruteResults} diffMap={diffMap} />

              {planes && (
                <div className="bg-cyber-surface border border-cyber-border rounded-xl p-4">
                  <BitPlaneViewer planes={planes} />
                </div>
              )}
            </div>

            {/* Right: controls */}
            <div className="space-y-4">
              <div className="bg-cyber-surface border border-cyber-border rounded-xl p-4 space-y-4">
                <StegoUploader
                  onFile={setFile}
                  file={file}
                  onClear={() => { setFile(null); setResult(null); setBruteResults(null); setLogs([]); }}
                  password={password}
                  onPasswordChange={setPassword}
                />

                {/* Options */}
                <div className="space-y-3">
                  {/* Bits */}
                  <div>
                    <p className="text-xs text-cyber-muted mb-2">LSB Depth: <span className="text-cyber-blue">{bits} bit(s)</span></p>
                    <input
                      type="range" min={1} max={8} value={bits}
                      onChange={(e) => setBits(Number(e.target.value))}
                      className="w-full accent-cyber-blue"
                    />
                    <div className="flex justify-between text-xs text-cyber-muted mt-1">
                      <span>1</span><span>4</span><span>8</span>
                    </div>
                  </div>

                  {/* Channels */}
                  <div>
                    <p className="text-xs text-cyber-muted mb-2">Channels</p>
                    <div className="flex gap-2">
                      {["R", "G", "B", "RGB"].map((ch) => (
                        <button
                          key={ch}
                          onClick={() => setChannels(ch)}
                          className={`flex-1 py-1.5 text-xs font-mono rounded border transition-all
                            ${channels === ch
                              ? "border-cyber-blue text-cyber-blue bg-cyber-blue/10"
                              : "border-cyber-border text-cyber-muted hover:border-cyber-muted"
                            }`}
                        >
                          {ch}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Auto-decode toggle */}
                  <button
                    onClick={() => setAutoDecode(!autoDecode)}
                    className="flex items-center gap-3 w-full p-3 rounded-lg border border-cyber-border bg-cyber-card"
                  >
                    <span className="text-xs font-mono flex-1 text-left text-cyber-muted">Auto-Decode extracted data</span>
                    <motion.div
                      className={`w-10 h-5 rounded-full relative ${autoDecode ? "bg-cyber-green/30 border border-cyber-green" : "bg-cyber-border"}`}
                    >
                      <motion.div
                        animate={{ x: autoDecode ? 20 : 2 }}
                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        className={`absolute top-0.5 w-4 h-4 rounded-full ${autoDecode ? "bg-cyber-green" : "bg-cyber-muted"}`}
                      />
                    </motion.div>
                  </button>
                </div>

                {/* Action buttons */}
                <div className="space-y-2">
                  <motion.button
                    onClick={handleAnalyze}
                    disabled={!file || loading}
                    whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                    className="w-full py-2.5 rounded-lg font-mono text-xs font-semibold uppercase tracking-widest
                      bg-gradient-to-r from-cyber-purple/20 to-cyber-pink/20
                      border border-cyber-purple/50 text-cyber-purple
                      hover:border-cyber-purple hover:bg-cyber-purple/10
                      disabled:opacity-40 disabled:cursor-not-allowed
                      transition-all flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        className="w-4 h-4 border-2 border-cyber-purple border-t-transparent rounded-full" />
                    ) : <Eye size={13} />}
                    {loading ? "Scanning..." : "Analyze"}
                  </motion.button>

                  <motion.button
                    onClick={handleBruteForce}
                    disabled={!file || loading}
                    whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                    className="w-full py-2.5 rounded-lg font-mono text-xs font-semibold uppercase tracking-widest
                      bg-gradient-to-r from-cyber-pink/20 to-red-500/20
                      border border-cyber-pink/50 text-cyber-pink
                      hover:border-cyber-pink hover:bg-cyber-pink/10
                      disabled:opacity-40 disabled:cursor-not-allowed
                      transition-all flex items-center justify-center gap-2"
                  >
                    <Layers size={13} />
                    Brute Force + Bit Planes
                  </motion.button>

                  {(result || bruteResults) && (
                    <button onClick={handleReset}
                      className="flex items-center gap-2 text-xs text-cyber-muted hover:text-cyber-text transition-colors font-mono mx-auto">
                      <RotateCcw size={11} /> Reset
                    </button>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          /* Text Stego Tab */
          <motion.div
            key="text"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            <div className="bg-cyber-surface border border-cyber-border rounded-xl p-4 space-y-3">
              <p className="text-xs text-cyber-muted uppercase tracking-widest">Paste suspicious text</p>
              <textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Paste text that may contain hidden data (zero-width chars, whitespace encoding, acrostics)..."
                rows={6}
                className="w-full bg-cyber-card border border-cyber-border rounded-lg p-3 text-sm font-mono
                  text-cyber-text outline-none resize-none placeholder-cyber-muted"
              />
              <motion.button
                onClick={handleTextAnalyze}
                disabled={!textInput.trim() || textLoading}
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                className="w-full py-2.5 rounded-lg font-mono text-xs font-semibold uppercase tracking-widest
                  bg-gradient-to-r from-cyber-blue/20 to-cyber-purple/20
                  border border-cyber-blue/50 text-cyber-blue
                  hover:border-cyber-blue disabled:opacity-40 disabled:cursor-not-allowed
                  transition-all flex items-center justify-center gap-2"
              >
                {textLoading
                  ? <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-4 h-4 border-2 border-cyber-blue border-t-transparent rounded-full" />
                  : <Zap size={13} />
                }
                {textLoading ? "Analyzing..." : "Analyze Text"}
              </motion.button>
            </div>

            {/* Text stego results */}
            {textResult && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
                {/* Invisible chars summary */}
                <div className="flex items-center gap-3 p-3 rounded-lg border border-cyber-border bg-cyber-card">
                  <span className="text-xs text-cyber-muted font-mono">
                    Invisible chars found: <span className={textResult.invisible_chars_found > 0 ? "text-red-400" : "text-cyber-green"}>
                      {textResult.invisible_chars_found}
                    </span>
                  </span>
                </div>

                {/* Zero-width */}
                {textResult.zero_width.found && (
                  <div className="bg-cyber-card border border-cyber-purple/40 rounded-xl p-4 space-y-2">
                    <p className="text-xs text-cyber-purple font-mono uppercase tracking-widest">Zero-Width Characters</p>
                    <p className="text-xs text-cyber-muted">Bits: <span className="text-cyber-text font-mono">{textResult.zero_width.bits}</span></p>
                    <p className="text-xs text-cyber-muted">Decoded: <span className="text-cyber-green font-mono">{textResult.zero_width.decoded || "—"}</span></p>
                    {textResult.zero_width.auto_decode && (
                      <p className="text-xs text-cyber-green font-mono">
                        → {textResult.zero_width.auto_decode.final_output}
                        {textResult.zero_width.auto_decode.is_ctf_flag && " 🚩 FLAG"}
                      </p>
                    )}
                  </div>
                )}

                {/* Whitespace */}
                {textResult.whitespace.found && (
                  <div className="bg-cyber-card border border-cyber-blue/40 rounded-xl p-4 space-y-2">
                    <p className="text-xs text-cyber-blue font-mono uppercase tracking-widest">Whitespace Encoding</p>
                    <p className="text-xs text-cyber-muted">Decoded: <span className="text-cyber-text font-mono">{textResult.whitespace.decoded || "—"}</span></p>
                  </div>
                )}

                {/* Acrostic */}
                <div className="bg-cyber-card border border-cyber-border rounded-xl p-4 space-y-2">
                  <p className="text-xs text-cyber-muted font-mono uppercase tracking-widest">Acrostic Analysis</p>
                  <p className="text-xs text-cyber-muted">First letter each line: <span className="text-cyber-text font-mono">{textResult.first_letters.first_letter_each_line}</span></p>
                  <p className="text-xs text-cyber-muted">First letter each word: <span className="text-cyber-text font-mono">{textResult.first_letters.first_letter_each_word}</span></p>
                </div>

                {/* Unicode anomalies */}
                {textResult.unicode_hidden.length > 0 && (
                  <div className="bg-cyber-card border border-amber-400/40 rounded-xl p-4 space-y-2">
                    <p className="text-xs text-amber-400 font-mono uppercase tracking-widest">Unicode Anomalies ({textResult.unicode_hidden.length})</p>
                    {textResult.unicode_hidden.slice(0, 5).map((a, i) => (
                      <p key={i} className="text-xs font-mono text-cyber-muted">
                        pos {a.position}: <span className="text-cyber-text">{a.char}</span> ({a.codepoint})
                      </p>
                    ))}
                  </div>
                )}
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
