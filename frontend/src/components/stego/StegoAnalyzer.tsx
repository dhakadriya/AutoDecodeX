"use client";
import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Eye, Zap, RotateCcw, ScanLine, Layers, FileText, Database, Radar } from "lucide-react";

import StegoUploader from "./StegoUploader";
import BitPlaneViewer from "./BitPlaneViewer";
import StegoResults from "./StegoResults";
import MetadataPanel from "./MetadataPanel";

import {
  stegoAnalyze, stegoBruteForce, stegoBitPlanes, stegoPixelDiff,
  stegoTextAnalyze, stegoMetadata, stegoFullScan,
  type StegoAnalyzeResponse, type StegoBruteResult,
  type TextStegoResponse, type MetadataResponse, type FullScanResponse,
} from "@/lib/api";

type Tab = "fullscan" | "image" | "metadata" | "text";

const FULL_SCAN_LOGS = [
  "[*] Loading image...",
  "[*] Extracting EXIF metadata...",
  "[*] Scanning PNG text chunks...",
  "[*] Analyzing metadata fields for encoded content...",
  "[*] Running auto-decode on suspicious fields...",
  "[*] Detecting embedded file signatures...",
  "[*] Extracting LSB steganography...",
  "[*] Running entropy analysis...",
  "[*] Chi-square test on pixel distribution...",
  "[*] Merging all findings...",
  "[+] Full scan complete.",
];

const ANALYZE_LOGS = [
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
  const done = logs.some((l) => l.startsWith("[+]"));
  return (
    <div className="bg-cyber-card border border-cyber-border rounded-lg p-3 font-mono text-xs space-y-1 max-h-40 overflow-y-auto">
      <AnimatePresence>
        {logs.map((log, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.15 }}
            className={log.startsWith("[+]") ? "text-cyber-green" : "text-cyber-muted"}
          >
            {log}
          </motion.div>
        ))}
      </AnimatePresence>
      {!done && logs.length > 0 && <span className="animate-pulse text-cyber-green">█</span>}
    </div>
  );
}

const TABS: Array<{ id: Tab; label: string; icon: React.ElementType; color: string }> = [
  { id: "fullscan", label: "Full Scan", icon: Radar, color: "border-cyber-green text-cyber-green bg-cyber-green/10" },
  { id: "metadata", label: "Metadata", icon: Database, color: "border-cyber-blue text-cyber-blue bg-cyber-blue/10" },
  { id: "image", label: "LSB / Stego", icon: ScanLine, color: "border-cyber-purple text-cyber-purple bg-cyber-purple/10" },
  { id: "text", label: "Text Stego", icon: FileText, color: "border-amber-400 text-amber-400 bg-amber-400/10" },
];

export default function StegoAnalyzer() {
  const [tab, setTab] = useState<Tab>("fullscan");

  // Shared
  const [file, setFile] = useState<File | null>(null);
  const [password, setPassword] = useState("");
  const [bits, setBits] = useState(1);
  const [channels, setChannels] = useState("RGB");
  const [autoDecode, setAutoDecode] = useState(true);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Full scan
  const [fullScanResult, setFullScanResult] = useState<FullScanResponse | null>(null);

  // LSB stego
  const [stegoResult, setStegoResult] = useState<StegoAnalyzeResponse | null>(null);
  const [bruteResults, setBruteResults] = useState<StegoBruteResult[] | null>(null);
  const [planes, setPlanes] = useState<Record<string, Record<string, string>> | null>(null);
  const [diffMap, setDiffMap] = useState<string | null>(null);

  // Metadata
  const [metaResult, setMetaResult] = useState<MetadataResponse | null>(null);

  // Text stego
  const [textInput, setTextInput] = useState("");
  const [textResult, setTextResult] = useState<TextStegoResponse | null>(null);
  const [textLoading, setTextLoading] = useState(false);

  const pushLog = useCallback((msg: string) => setLogs((p) => [...p, msg]), []);

  // ── Full Scan ────────────────────────────────────────────────────────────
  const handleFullScan = useCallback(async () => {
    if (!file) return;
    setLoading(true); setError(null); setFullScanResult(null); setLogs([]);
    try {
      for (let i = 0; i < FULL_SCAN_LOGS.length - 1; i++) {
        await new Promise((r) => setTimeout(r, 250 + i * 120));
        pushLog(FULL_SCAN_LOGS[i]);
      }
      const res = await stegoFullScan(file, bits, channels, password);
      setFullScanResult(res);
      pushLog(FULL_SCAN_LOGS[FULL_SCAN_LOGS.length - 1]);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Full scan failed.");
    } finally {
      setLoading(false);
    }
  }, [file, bits, channels, password, pushLog]);

  // ── Metadata only ────────────────────────────────────────────────────────
  const handleMetadata = useCallback(async () => {
    if (!file) return;
    setLoading(true); setError(null); setMetaResult(null);
    setLogs(["[*] Extracting metadata...", "[*] Scanning for encoded content..."]);
    try {
      const res = await stegoMetadata(file);
      setMetaResult(res);
      pushLog("[+] Metadata extraction complete.");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Metadata extraction failed.");
    } finally {
      setLoading(false);
    }
  }, [file, pushLog]);

  // ── LSB Analyze ──────────────────────────────────────────────────────────
  const handleAnalyze = useCallback(async () => {
    if (!file) return;
    setLoading(true); setError(null); setStegoResult(null);
    setBruteResults(null); setPlanes(null); setDiffMap(null); setLogs([]);
    try {
      for (let i = 0; i < ANALYZE_LOGS.length - 1; i++) {
        await new Promise((r) => setTimeout(r, 300 + i * 150));
        pushLog(ANALYZE_LOGS[i]);
      }
      const [analyzeRes, diffRes] = await Promise.all([
        stegoAnalyze(file, bits, channels, password, autoDecode),
        stegoPixelDiff(file),
      ]);
      setStegoResult(analyzeRes);
      setDiffMap(diffRes.diff_map);
      pushLog(ANALYZE_LOGS[ANALYZE_LOGS.length - 1]);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  }, [file, bits, channels, password, autoDecode, pushLog]);

  // ── Brute Force ──────────────────────────────────────────────────────────
  const handleBruteForce = useCallback(async () => {
    if (!file) return;
    setLoading(true); setError(null); setBruteResults(null);
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
  }, [file, autoDecode, pushLog]);

  // ── Text Analyze ─────────────────────────────────────────────────────────
  const handleTextAnalyze = useCallback(async () => {
    if (!textInput.trim()) return;
    setTextLoading(true); setTextResult(null);
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
    setFile(null); setStegoResult(null); setBruteResults(null); setPlanes(null);
    setDiffMap(null); setLogs([]); setError(null); setMetaResult(null);
    setFullScanResult(null); setTextResult(null); setTextInput("");
  };

  const activeTab = TABS.find((t) => t.id === tab)!;

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyber-purple to-cyber-pink flex items-center justify-center">
          <Eye size={16} className="text-white" />
        </div>
        <div>
          <h2 className="text-lg font-bold font-mono text-cyber-text">
            Stego <span className="neon-purple">Analyzer</span>
          </h2>
          <p className="text-xs text-cyber-muted">ExifTool + LSB Extractor + CTF Forensics Lab</p>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        {TABS.map(({ id, label, icon: Icon, color }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-xs font-mono transition-all
              ${tab === id ? color : "border-cyber-border text-cyber-muted hover:border-cyber-muted"}`}
          >
            <Icon size={12} />
            {label}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {/* ── TEXT STEGO TAB ─────────────────────────────────────────────── */}
        {tab === "text" ? (
          <motion.div key="text" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-4">
            <div className="bg-cyber-surface border border-cyber-border rounded-xl p-4 space-y-3">
              <p className="text-xs text-cyber-muted uppercase tracking-widest">Paste suspicious text</p>
              <textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Paste text that may contain hidden data (zero-width chars, whitespace encoding, acrostics)..."
                rows={6}
                className="w-full bg-cyber-card border border-cyber-border rounded-lg p-3 text-sm font-mono text-cyber-text outline-none resize-none placeholder-cyber-muted"
              />
              <motion.button
                onClick={handleTextAnalyze}
                disabled={!textInput.trim() || textLoading}
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                className="w-full py-2.5 rounded-lg font-mono text-xs font-semibold uppercase tracking-widest
                  bg-gradient-to-r from-amber-400/20 to-cyber-blue/20 border border-amber-400/50 text-amber-400
                  hover:border-amber-400 disabled:opacity-40 disabled:cursor-not-allowed
                  transition-all flex items-center justify-center gap-2"
              >
                {textLoading
                  ? <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full" />
                  : <Zap size={13} />}
                {textLoading ? "Analyzing..." : "Analyze Text"}
              </motion.button>
            </div>

            {textResult && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
                <div className="flex items-center gap-3 p-3 rounded-lg border border-cyber-border bg-cyber-card">
                  <span className="text-xs text-cyber-muted font-mono">
                    Invisible chars: <span className={textResult.invisible_chars_found > 0 ? "text-red-400" : "text-cyber-green"}>{textResult.invisible_chars_found}</span>
                  </span>
                </div>
                {textResult.zero_width.found && (
                  <div className="bg-cyber-card border border-cyber-purple/40 rounded-xl p-4 space-y-2">
                    <p className="text-xs text-cyber-purple font-mono uppercase tracking-widest">Zero-Width Characters</p>
                    <p className="text-xs text-cyber-muted">Bits: <span className="text-cyber-text font-mono">{textResult.zero_width.bits}</span></p>
                    <p className="text-xs text-cyber-muted">Decoded: <span className="text-cyber-green font-mono">{textResult.zero_width.decoded || "—"}</span></p>
                    {textResult.zero_width.auto_decode && (
                      <p className="text-xs text-cyber-green font-mono">→ {textResult.zero_width.auto_decode.final_output}{textResult.zero_width.auto_decode.is_ctf_flag && " 🚩 FLAG"}</p>
                    )}
                  </div>
                )}
                {textResult.whitespace.found && (
                  <div className="bg-cyber-card border border-cyber-blue/40 rounded-xl p-4 space-y-2">
                    <p className="text-xs text-cyber-blue font-mono uppercase tracking-widest">Whitespace Encoding</p>
                    <p className="text-xs text-cyber-muted">Decoded: <span className="text-cyber-text font-mono">{textResult.whitespace.decoded || "—"}</span></p>
                  </div>
                )}
                <div className="bg-cyber-card border border-cyber-border rounded-xl p-4 space-y-2">
                  <p className="text-xs text-cyber-muted font-mono uppercase tracking-widest">Acrostic Analysis</p>
                  <p className="text-xs text-cyber-muted">First letter each line: <span className="text-cyber-text font-mono">{textResult.first_letters.first_letter_each_line}</span></p>
                  <p className="text-xs text-cyber-muted">First letter each word: <span className="text-cyber-text font-mono">{textResult.first_letters.first_letter_each_word}</span></p>
                </div>
                {textResult.unicode_hidden.length > 0 && (
                  <div className="bg-cyber-card border border-amber-400/40 rounded-xl p-4 space-y-2">
                    <p className="text-xs text-amber-400 font-mono uppercase tracking-widest">Unicode Anomalies ({textResult.unicode_hidden.length})</p>
                    {textResult.unicode_hidden.slice(0, 5).map((a, i) => (
                      <p key={i} className="text-xs font-mono text-cyber-muted">pos {a.position}: <span className="text-cyber-text">{a.char}</span> ({a.codepoint})</p>
                    ))}
                  </div>
                )}
              </motion.div>
            )}
          </motion.div>

        ) : (
          /* ── IMAGE TABS (fullscan / metadata / image) ─────────────────── */
          <motion.div
            key={tab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-6"
          >
            {/* Left: results area */}
            <div className="space-y-4">
              {logs.length > 0 && <TerminalLog logs={logs} />}

              <AnimatePresence>
                {error && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="p-3 rounded-lg border border-red-500/40 bg-red-500/10 text-red-400 text-xs font-mono">
                    ⚠ {error}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Full scan results */}
              {tab === "fullscan" && fullScanResult && (
                <div className="space-y-4">
                  {/* All flags banner */}
                  {fullScanResult.all_flags.length > 0 && (
                    <motion.div
                      animate={{ boxShadow: ["0 0 10px rgba(0,255,136,0.2)", "0 0 30px rgba(0,255,136,0.5)", "0 0 10px rgba(0,255,136,0.2)"] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="p-4 rounded-xl border border-cyber-green/60 bg-cyber-green/10"
                    >
                      <p className="text-sm font-mono font-bold text-cyber-green mb-2">
                        🚩 {fullScanResult.all_flags.length} FLAG{fullScanResult.all_flags.length > 1 ? "S" : ""} DISCOVERED
                      </p>
                      {fullScanResult.all_flags.map((f, i) => (
                        <p key={i} className="text-sm font-mono text-cyber-green neon-green">{f}</p>
                      ))}
                    </motion.div>
                  )}
                  {/* Summary stats */}
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { label: "Metadata Fields", value: fullScanResult.summary.total_fields, color: "text-cyber-blue" },
                      { label: "Suspicious", value: fullScanResult.summary.suspicious_fields, color: "text-amber-400" },
                      { label: "Embedded Files", value: fullScanResult.summary.embedded_files_count, color: fullScanResult.summary.embedded_files_count > 0 ? "text-red-400" : "text-cyber-muted" },
                    ].map((s) => (
                      <div key={s.label} className="bg-cyber-card border border-cyber-border rounded-lg p-3 text-center">
                        <p className={`text-lg font-bold font-mono ${s.color}`}>{s.value}</p>
                        <p className="text-xs text-cyber-muted">{s.label}</p>
                      </div>
                    ))}
                  </div>
                  {/* Metadata findings */}
                  <MetadataPanel data={fullScanResult.metadata} />
                  {/* LSB results */}
                  <StegoResults
                    result={{
                      filename: fullScanResult.filename,
                      lsb: fullScanResult.lsb,
                      entropy: fullScanResult.entropy,
                      auto_decode: fullScanResult.lsb_decode,
                    }}
                    bruteResults={null}
                    diffMap={null}
                  />
                </div>
              )}

              {/* Metadata-only results */}
              {tab === "metadata" && metaResult && <MetadataPanel data={metaResult} />}

              {/* LSB stego results */}
              {tab === "image" && (
                <>
                  <StegoResults result={stegoResult} bruteResults={bruteResults} diffMap={diffMap} />
                  {planes && (
                    <div className="bg-cyber-surface border border-cyber-border rounded-xl p-4">
                      <BitPlaneViewer planes={planes} />
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Right: controls */}
            <div className="space-y-4">
              <div className="bg-cyber-surface border border-cyber-border rounded-xl p-4 space-y-4">
                <StegoUploader
                  onFile={setFile} file={file}
                  onClear={() => { setFile(null); setStegoResult(null); setBruteResults(null); setMetaResult(null); setFullScanResult(null); setLogs([]); }}
                  password={password}
                  onPasswordChange={setPassword}
                />

                {/* LSB options (only for image/fullscan tabs) */}
                {(tab === "image" || tab === "fullscan") && (
                  <div className="space-y-3">
                    <div>
                      <p className="text-xs text-cyber-muted mb-2">LSB Depth: <span className="text-cyber-blue">{bits} bit(s)</span></p>
                      <input type="range" min={1} max={8} value={bits}
                        onChange={(e) => setBits(Number(e.target.value))}
                        className="w-full accent-cyber-blue" />
                      <div className="flex justify-between text-xs text-cyber-muted mt-1"><span>1</span><span>4</span><span>8</span></div>
                    </div>
                    <div>
                      <p className="text-xs text-cyber-muted mb-2">Channels</p>
                      <div className="flex gap-2">
                        {["R", "G", "B", "RGB"].map((ch) => (
                          <button key={ch} onClick={() => setChannels(ch)}
                            className={`flex-1 py-1.5 text-xs font-mono rounded border transition-all
                              ${channels === ch ? "border-cyber-blue text-cyber-blue bg-cyber-blue/10" : "border-cyber-border text-cyber-muted hover:border-cyber-muted"}`}>
                            {ch}
                          </button>
                        ))}
                      </div>
                    </div>
                    <button onClick={() => setAutoDecode(!autoDecode)}
                      className="flex items-center gap-3 w-full p-3 rounded-lg border border-cyber-border bg-cyber-card">
                      <span className="text-xs font-mono flex-1 text-left text-cyber-muted">Auto-Decode extracted data</span>
                      <motion.div className={`w-10 h-5 rounded-full relative ${autoDecode ? "bg-cyber-green/30 border border-cyber-green" : "bg-cyber-border"}`}>
                        <motion.div animate={{ x: autoDecode ? 20 : 2 }} transition={{ type: "spring", stiffness: 500, damping: 30 }}
                          className={`absolute top-0.5 w-4 h-4 rounded-full ${autoDecode ? "bg-cyber-green" : "bg-cyber-muted"}`} />
                      </motion.div>
                    </button>
                  </div>
                )}

                {/* Action buttons per tab */}
                <div className="space-y-2">
                  {tab === "fullscan" && (
                    <motion.button onClick={handleFullScan} disabled={!file || loading}
                      whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                      className="w-full py-2.5 rounded-lg font-mono text-xs font-semibold uppercase tracking-widest
                        bg-gradient-to-r from-cyber-green/20 to-cyber-blue/20 border border-cyber-green/50 text-cyber-green
                        hover:border-cyber-green disabled:opacity-40 disabled:cursor-not-allowed
                        transition-all flex items-center justify-center gap-2">
                      {loading
                        ? <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                            className="w-4 h-4 border-2 border-cyber-green border-t-transparent rounded-full" />
                        : <Radar size={13} />}
                      {loading ? "Scanning..." : "Full Scan"}
                    </motion.button>
                  )}

                  {tab === "metadata" && (
                    <motion.button onClick={handleMetadata} disabled={!file || loading}
                      whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                      className="w-full py-2.5 rounded-lg font-mono text-xs font-semibold uppercase tracking-widest
                        bg-gradient-to-r from-cyber-blue/20 to-cyber-purple/20 border border-cyber-blue/50 text-cyber-blue
                        hover:border-cyber-blue disabled:opacity-40 disabled:cursor-not-allowed
                        transition-all flex items-center justify-center gap-2">
                      {loading
                        ? <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                            className="w-4 h-4 border-2 border-cyber-blue border-t-transparent rounded-full" />
                        : <Database size={13} />}
                      {loading ? "Extracting..." : "Extract Metadata"}
                    </motion.button>
                  )}

                  {tab === "image" && (
                    <>
                      <motion.button onClick={handleAnalyze} disabled={!file || loading}
                        whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                        className="w-full py-2.5 rounded-lg font-mono text-xs font-semibold uppercase tracking-widest
                          bg-gradient-to-r from-cyber-purple/20 to-cyber-pink/20 border border-cyber-purple/50 text-cyber-purple
                          hover:border-cyber-purple disabled:opacity-40 disabled:cursor-not-allowed
                          transition-all flex items-center justify-center gap-2">
                        {loading
                          ? <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                              className="w-4 h-4 border-2 border-cyber-purple border-t-transparent rounded-full" />
                          : <Eye size={13} />}
                        {loading ? "Scanning..." : "Analyze LSB"}
                      </motion.button>
                      <motion.button onClick={handleBruteForce} disabled={!file || loading}
                        whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                        className="w-full py-2.5 rounded-lg font-mono text-xs font-semibold uppercase tracking-widest
                          bg-gradient-to-r from-cyber-pink/20 to-red-500/20 border border-cyber-pink/50 text-cyber-pink
                          hover:border-cyber-pink disabled:opacity-40 disabled:cursor-not-allowed
                          transition-all flex items-center justify-center gap-2">
                        <Layers size={13} />
                        Brute Force + Bit Planes
                      </motion.button>
                    </>
                  )}

                  {(stegoResult || bruteResults || metaResult || fullScanResult) && (
                    <button onClick={handleReset}
                      className="flex items-center gap-2 text-xs text-cyber-muted hover:text-cyber-text transition-colors font-mono mx-auto">
                      <RotateCcw size={11} /> Reset
                    </button>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
