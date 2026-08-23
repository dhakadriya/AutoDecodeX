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
    <div className="bg-theme-card border border-theme-border rounded-lg p-3 font-mono text-xs space-y-1 max-h-40 overflow-y-auto">
      <AnimatePresence>
        {logs.map((log, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.15 }}
            className={log.startsWith("[+]") ? "text-theme-success" : "text-theme-secondary"}
          >
            {log}
          </motion.div>
        ))}
      </AnimatePresence>
      {!done && logs.length > 0 && <span className="animate-pulse text-theme-success">█</span>}
    </div>
  );
}

const TABS: Array<{ id: Tab; label: string; icon: React.ElementType; color: string }> = [
  { id: "fullscan", label: "Full Scan", icon: Radar, color: "border-theme-success text-theme-success bg-theme-success/10" },
  { id: "metadata", label: "Metadata", icon: Database, color: "border-theme-accent text-theme-accent bg-theme-accent/10" },
  { id: "image", label: "LSB / Stego", icon: ScanLine, color: "border-theme-accent text-theme-accent bg-theme-accent/10" },
  { id: "text", label: "Text Stego", icon: FileText, color: "border-theme-warning text-theme-warning bg-theme-warning/10" },
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3 select-none">
        <div className="w-10 h-10 rounded-lg bg-theme-gradient flex items-center justify-center shadow-lg shadow-theme-accent/15">
          <Eye size={20} className="text-white" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-theme-primary">
            Stego Analyzer
          </h2>
          <p className="text-xs text-theme-secondary">EXIF Extraction · LSB Analysis · Text Steganography</p>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap select-none">
        {TABS.map(({ id, label, icon: Icon, color }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-xs font-mono transition-all
              ${tab === id ? color : "border-theme-border bg-theme-surface text-theme-secondary hover:border-theme-border/70"}`}
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
            <div className="bg-theme-surface border border-theme-border rounded-xl p-4 space-y-3">
              <p className="text-xs text-theme-secondary uppercase tracking-widest font-mono select-none">Paste suspicious text</p>
              <textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Paste text that may contain hidden data (zero-width chars, whitespace encoding, acrostics)..."
                rows={6}
                className="w-full bg-theme-input border border-theme-border rounded-lg p-3 text-sm font-mono text-theme-primary outline-none resize-none placeholder-theme-muted"
              />
              <motion.button
                onClick={handleTextAnalyze}
                disabled={!textInput.trim() || textLoading}
                whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                className="w-full py-2.5 rounded-lg font-mono text-xs font-bold uppercase tracking-widest
                  bg-theme-gradient hover:opacity-90 border-transparent text-white
                  disabled:opacity-40 disabled:cursor-not-allowed
                  transition-all flex items-center justify-center gap-2 shadow-lg shadow-theme-accent/15"
              >
                {textLoading ? (
                  <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full" />
                ) : (
                  <Zap size={13} />
                )}
                {textLoading ? "Analyzing..." : "Analyze Text"}
              </motion.button>
            </div>

            {textResult && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
                <div className="flex items-center gap-3 p-3 rounded-lg border border-theme-border bg-theme-surface">
                  <span className="text-xs text-theme-secondary font-mono">
                    Invisible chars: <span className={textResult.invisible_chars_found > 0 ? "text-theme-error font-bold" : "text-theme-success font-bold"}>{textResult.invisible_chars_found}</span>
                  </span>
                </div>
                {textResult.zero_width.found && (
                  <div className="bg-theme-surface border border-theme-accent/30 rounded-xl p-4 space-y-2">
                    <p className="text-xs text-theme-accent font-mono uppercase tracking-widest font-bold">Zero-Width Characters</p>
                    <p className="text-xs text-theme-secondary font-mono">Bits: <span className="text-theme-primary font-mono">{textResult.zero_width.bits}</span></p>
                    <p className="text-xs text-theme-secondary font-mono">Decoded: <span className="text-theme-success font-mono font-bold">{textResult.zero_width.decoded || "—"}</span></p>
                    {textResult.zero_width.auto_decode && (
                      <p className="text-xs text-theme-success font-mono font-bold">→ {textResult.zero_width.auto_decode.final_output}{textResult.zero_width.auto_decode.is_ctf_flag && " 🚩 FLAG"}</p>
                    )}
                  </div>
                )}
                {textResult.whitespace.found && (
                  <div className="bg-theme-surface border border-theme-accent/30 rounded-xl p-4 space-y-2">
                    <p className="text-xs text-theme-accent font-mono uppercase tracking-widest font-bold">Whitespace Encoding</p>
                    <p className="text-xs text-theme-secondary font-mono">Decoded: <span className="text-theme-primary font-mono">{textResult.whitespace.decoded || "—"}</span></p>
                  </div>
                )}
                <div className="bg-theme-surface border border-theme-border rounded-xl p-4 space-y-2">
                  <p className="text-xs text-theme-secondary font-mono uppercase tracking-widest">Acrostic Analysis</p>
                  <p className="text-xs text-theme-secondary font-mono">First letter each line: <span className="text-theme-primary font-mono">{textResult.first_letters.first_letter_each_line}</span></p>
                  <p className="text-xs text-theme-secondary font-mono">First letter each word: <span className="text-theme-primary font-mono">{textResult.first_letters.first_letter_each_word}</span></p>
                </div>
                {textResult.unicode_hidden.length > 0 && (
                  <div className="bg-theme-surface border border-theme-warning/30 rounded-xl p-4 space-y-2">
                    <p className="text-xs text-theme-warning font-mono uppercase tracking-widest">Unicode Anomalies ({textResult.unicode_hidden.length})</p>
                    {textResult.unicode_hidden.slice(0, 5).map((a, i) => (
                      <p key={i} className="text-xs font-mono text-theme-secondary">pos {a.position}: <span className="text-theme-primary">{a.char}</span> ({a.codepoint})</p>
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
            className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6"
          >
            {/* Left: results area */}
            <div className="space-y-4">
              {logs.length > 0 && <TerminalLog logs={logs} />}

              <AnimatePresence>
                {error && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                    className="p-3 rounded-lg border border-theme-error/30 bg-theme-error/10 text-theme-error text-xs font-mono">
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
                      animate={{ boxShadow: ["0 0 10px rgba(16,185,129,0.15)", "0 0 25px rgba(16,185,129,0.3)", "0 0 10px rgba(16,185,129,0.15)"] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="p-4 rounded-xl border border-theme-success/40 bg-theme-success/10"
                    >
                      <p className="text-sm font-mono font-bold text-theme-success mb-2">
                        🚩 {fullScanResult.all_flags.length} FLAG{fullScanResult.all_flags.length > 1 ? "S" : ""} DISCOVERED
                      </p>
                      {fullScanResult.all_flags.map((f, i) => (
                        <p key={i} className="text-sm font-mono text-theme-success font-bold">{f}</p>
                      ))}
                    </motion.div>
                  )}
                  {/* Summary stats */}
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { label: "Metadata Fields", value: fullScanResult.summary.total_fields, color: "text-theme-accent" },
                      { label: "Suspicious", value: fullScanResult.summary.suspicious_fields, color: "text-theme-warning" },
                      { label: "Embedded Files", value: fullScanResult.summary.embedded_files_count, color: fullScanResult.summary.embedded_files_count > 0 ? "text-theme-error animate-pulse" : "text-theme-secondary" },
                    ].map((s) => (
                      <div key={s.label} className="bg-theme-surface border border-theme-border rounded-lg p-3 text-center">
                        <p className={`text-lg font-bold font-mono ${s.color}`}>{s.value}</p>
                        <p className="text-xs text-theme-secondary mt-0.5 font-mono">{s.label}</p>
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
                    <div className="bg-theme-surface border border-theme-border rounded-xl p-4">
                      <BitPlaneViewer planes={planes} />
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Right: controls */}
            <div className="space-y-4">
              <div className="bg-theme-surface border border-theme-border rounded-xl p-4 space-y-4">
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
                      <p className="text-xs text-theme-secondary mb-2 font-mono">LSB Depth: <span className="text-theme-accent font-bold">{bits} bit(s)</span></p>
                      <input type="range" min={1} max={8} value={bits}
                        onChange={(e) => setBits(Number(e.target.value))}
                        className="w-full accent-theme-accent h-1.5 bg-theme-border rounded-lg appearance-none cursor-pointer" />
                      <div className="flex justify-between text-xs text-theme-muted mt-1 font-mono"><span>1</span><span>4</span><span>8</span></div>
                    </div>
                    <div>
                      <p className="text-xs text-theme-secondary mb-2 font-mono">Channels</p>
                      <div className="flex gap-2">
                        {["R", "G", "B", "RGB"].map((ch) => (
                          <button key={ch} onClick={() => setChannels(ch)}
                            className={`flex-1 py-1.5 text-xs font-mono rounded border transition-all
                              ${channels === ch ? "border-theme-accent text-theme-accent bg-theme-accent/10 font-bold" : "border-theme-border bg-theme-input text-theme-secondary hover:border-theme-border/70"}`}>
                            {ch}
                          </button>
                        ))}
                      </div>
                    </div>
                    <button onClick={() => setAutoDecode(!autoDecode)}
                      className="flex items-center gap-3 w-full p-3 rounded-lg border border-theme-border bg-theme-card">
                      <span className="text-xs font-mono flex-1 text-left text-theme-secondary">Auto-Decode extracted data</span>
                      <motion.div className={`w-10 h-5 rounded-full relative ${autoDecode ? "bg-theme-success/20 border border-theme-success" : "bg-theme-border"}`}>
                        <motion.div animate={{ x: autoDecode ? 20 : 2 }} transition={{ type: "spring", stiffness: 500, damping: 30 }}
                          className={`absolute top-0.5 w-4 h-4 rounded-full ${autoDecode ? "bg-theme-success" : "bg-theme-muted"}`} />
                      </motion.div>
                    </button>
                  </div>
                )}

                {/* Action buttons per tab */}
                <div className="space-y-2">
                  {tab === "fullscan" && (
                    <motion.button onClick={handleFullScan} disabled={!file || loading}
                      whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                      className="w-full py-2.5 rounded-lg font-mono text-xs font-bold uppercase tracking-widest
                        bg-theme-gradient hover:opacity-90 border-transparent text-white
                        disabled:opacity-40 disabled:cursor-not-allowed
                        transition-all flex items-center justify-center gap-2 shadow-lg shadow-theme-accent/15">
                      {loading ? (
                        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                          className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full" />
                      ) : (
                        <Radar size={13} />
                      )}
                      {loading ? "Scanning..." : "Full Scan"}
                    </motion.button>
                  )}

                  {tab === "metadata" && (
                    <motion.button onClick={handleMetadata} disabled={!file || loading}
                      whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                      className="w-full py-2.5 rounded-lg font-mono text-xs font-bold uppercase tracking-widest
                        bg-theme-gradient hover:opacity-90 border-transparent text-white
                        disabled:opacity-40 disabled:cursor-not-allowed
                        transition-all flex items-center justify-center gap-2 shadow-lg shadow-theme-accent/15">
                      {loading ? (
                        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                          className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full" />
                      ) : (
                        <Database size={13} />
                      )}
                      {loading ? "Extracting..." : "Extract Metadata"}
                    </motion.button>
                  )}

                  {tab === "image" && (
                    <>
                      <motion.button onClick={handleAnalyze} disabled={!file || loading}
                        whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                        className="w-full py-2.5 rounded-lg font-mono text-xs font-bold uppercase tracking-widest
                          bg-theme-gradient hover:opacity-90 border-transparent text-white
                          disabled:opacity-40 disabled:cursor-not-allowed
                          transition-all flex items-center justify-center gap-2 shadow-lg shadow-theme-accent/15">
                        {loading ? (
                          <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                            className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full" />
                        ) : (
                          <Eye size={13} />
                        )}
                        {loading ? "Scanning..." : "Analyze LSB"}
                      </motion.button>
                      
                      <motion.button onClick={handleBruteForce} disabled={!file || loading}
                        whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                        className="w-full py-2.5 rounded-lg font-mono text-xs font-bold uppercase tracking-widest
                          bg-theme-surface hover:bg-theme-hover border border-theme-border text-theme-primary
                          disabled:opacity-40 disabled:cursor-not-allowed
                          transition-all flex items-center justify-center gap-2">
                        <Layers size={13} className="text-theme-accent" />
                        Brute Force + Bit Planes
                      </motion.button>
                    </>
                  )}

                  {(stegoResult || bruteResults || metaResult || fullScanResult) && (
                    <button onClick={handleReset}
                      className="flex items-center gap-2 text-xs text-theme-secondary hover:text-theme-primary transition-colors font-mono mx-auto mt-2 select-none">
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
