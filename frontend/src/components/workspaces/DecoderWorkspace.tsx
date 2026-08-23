"use client";
import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, RotateCcw } from "lucide-react";
import { decodeText, detectText, type DecodeResponse, type Detection } from "@/lib/api";
import type { LogEntry } from "@/components/layout/LiveAnalysisFeed";
import PipelineGraph from "@/components/decoder/PipelineGraph";

interface DecoderWorkspaceProps {
  onInspectorUpdate: (data: any) => void;
  onLog: (type: LogEntry["type"], message: string) => void;
  onClearLogs: () => void;
}

const EXAMPLES = [
  { label: "Base64", value: "SGVsbG8gV29ybGQh" },
  { label: "Hex", value: "48656c6c6f20576f726c6421" },
  { label: "Multi-layer", value: "NTM2NTZjNmM2ZjIwNTc2ZjcyNmM2NA==" },
  { label: "CTF Flag", value: "ZmxhZ3t0ZXN0X2ZsYWd9" },
];

export default function DecoderWorkspace({ onInspectorUpdate, onLog, onClearLogs }: DecoderWorkspaceProps) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DecodeResponse | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);

  // Real-time detection
  useEffect(() => {
    if (!input.trim() || input.length < 4) {
      setDetections([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await detectText(input);
        setDetections(res.detections);
        onInspectorUpdate({
          detections: res.detections.slice(0, 3).map(d => ({
            type: d.type,
            confidence: Math.round(d.confidence)
          }))
        });
      } catch {
        // Silent fail
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [input, onInspectorUpdate]);

  const handleDecode = useCallback(async () => {
    // Input validation
    if (!input || !input.trim()) {
      onLog("error", "Input is empty. Please enter text to decode.");
      return;
    }
    
    if (input.length > 100000) {
      onLog("error", "Input too large. Maximum 100,000 characters.");
      return;
    }
    
    setLoading(true);
    setResult(null);
    onClearLogs();
    
    onLog("info", "Starting decode analysis...");
    onLog("info", `Input length: ${input.length} characters`);
    
    try {
      onLog("info", "Running encoding detection...");
      
      let ctfMode = false;
      if (typeof window !== "undefined") {
        const savedSettings = localStorage.getItem("autodecodex_settings");
        if (savedSettings) {
          try {
            const parsed = JSON.parse(savedSettings);
            if (parsed.ctfMode !== undefined) {
              ctfMode = !!parsed.ctfMode;
            }
          } catch {
            // ignore
          }
        }
      }
      
      const res = await decodeText(input, ctfMode);
      
      if (!res || !res.steps) {
        onLog("error", "Invalid response from decoder");
        return;
      }
      
      onLog("success", `Detected ${res.detections?.length || 0} possible encodings`);
      onLog("info", `Processing ${res.steps.length} decoding steps...`);
      
      setResult(res);
      
      if (res.is_ctf_flag) {
        onLog("success", "🚩 CTF FLAG DETECTED!");
      }
      
      onLog("success", `Decode complete. Final score: ${Math.round(res.total_score)}%`);
      
      // Update inspector
      onInspectorUpdate({
        detections: res.detections?.slice(0, 3).map(d => ({
          type: d.type,
          confidence: Math.round(d.confidence)
        })) || [],
        riskScore: res.total_score > 80 ? "low" : res.total_score > 50 ? "medium" : "high",
        flags: res.is_ctf_flag ? [res.final_output] : [],
      });
      
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Unknown error";
      onLog("error", `Decode failed: ${errorMsg}`);
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [input, onLog, onClearLogs, onInspectorUpdate]);

  const handleReset = () => {
    setInput("");
    setResult(null);
    setDetections([]);
    onClearLogs();
    onInspectorUpdate(null);
  };

  const handleExport = (format: "json" | "txt" | "html") => {
    if (!result) return;
    
    let content = "";
    let filename = `autodecodex_report_${Date.now()}`;
    let mimeType = "text/plain";
    
    if (format === "json") {
      content = JSON.stringify({
        input,
        final_output: result.final_output,
        success: result.success,
        total_score: result.total_score,
        steps: result.steps
      }, null, 2);
      filename += ".json";
      mimeType = "application/json";
    } else if (format === "txt") {
      content = `AutoDecodeX Forensic Report\n`;
      content += `===========================\n\n`;
      content += `Input: ${input}\n\n`;
      content += `Final Output: ${result.final_output}\n`;
      content += `Readability Score: ${result.total_score}%\n`;
      content += `Success: ${result.success ? "Yes" : "No"}\n\n`;
      content += `Transformation Steps:\n`;
      result.steps.forEach(s => {
        content += `- Step ${s.step_number} (${s.encoding_type}): ${s.output_text} (confidence: ${Math.round(s.confidence * 100)}%)\n`;
      });
      filename += ".txt";
      mimeType = "text/plain";
    } else if (format === "html") {
      content = `<html>
<head>
  <title>AutoDecodeX Report</title>
  <style>
    body { font-family: monospace; background: #0c0c0e; color: #fff; padding: 20px; }
    h1 { color: #22d3ee; }
    .card { background: #18181b; border: 1px border #27272a; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
    .success { border-color: #4ade80; }
  </style>
</head>
<body>
  <h1>AutoDecodeX Forensic Report</h1>
  <div class="card">
    <p><strong>Input:</strong> ${input}</p>
    <p><strong>Final Output:</strong> ${result.final_output}</p>
    <p><strong>Readability Score:</strong> ${result.total_score}%</p>
  </div>
  <h2>Steps</h2>
  ${result.steps.map(s => `
    <div class="card">
      <h3>Step ${s.step_number}: ${s.encoding_type}</h3>
      <p>Output: ${s.output_text}</p>
    </div>
  `).join("")}
</body>
</html>`;
      filename += ".html";
      mimeType = "text/html";
    }
    
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    onLog("success", `Report exported as ${format.toUpperCase()}`);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6 h-full"
    >
      {/* Input Terminal */}
      <div className="bg-theme-surface rounded-lg border border-theme-border overflow-hidden">
        <div className="px-4 py-2 border-b border-theme-border flex items-center justify-between bg-theme-surface/50 select-none">
          <h3 className="text-xs text-theme-secondary uppercase tracking-wider font-bold font-mono">Input Terminal</h3>
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-theme-error/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-theme-warning/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-theme-success/60" />
          </div>
        </div>
        
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Paste encoded text here... (Base64, Hex, Binary, ROT13, uuencode, gzip, etc.)"
          rows={6}
          className="w-full bg-transparent p-4 text-sm font-mono text-theme-primary placeholder-theme-muted outline-none resize-none"
        />
        
        <div className="px-4 py-3 border-t border-theme-border flex flex-col md:flex-row md:items-center justify-between gap-3 bg-theme-surface/30">
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex.label}
                onClick={() => setInput(ex.value)}
                className="px-3 py-1.5 text-xs font-mono rounded border border-theme-border bg-theme-input hover:bg-theme-hover text-theme-secondary hover:text-theme-primary transition-all"
              >
                {ex.label}
              </button>
            ))}
          </div>
          
          <div className="flex gap-2 justify-end">
            {(result || detections.length > 0) && (
              <button
                onClick={handleReset}
                className="px-3 py-1.5 text-xs font-mono rounded border border-theme-border bg-theme-input hover:bg-theme-hover text-theme-secondary hover:text-theme-primary transition-all flex items-center gap-1.5"
              >
                <RotateCcw size={12} />
                Reset
              </button>
            )}
            
            <button
              onClick={handleDecode}
              disabled={!input.trim() || loading}
              className="px-4 py-1.5 text-xs font-mono font-bold rounded bg-theme-gradient hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all text-white flex items-center gap-2 shadow-lg shadow-theme-accent/15"
            >
              {loading ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-3 h-3 border-2 border-white border-t-transparent rounded-full"
                  />
                  Decoding...
                </>
              ) : (
                <>
                  <Zap size={12} />
                  Decode
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Animated Processing Pipeline during Load */}
      {loading && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-theme-surface rounded-lg border border-theme-border p-6 space-y-4 shadow-lg"
        >
          <div className="flex items-center justify-between border-b border-theme-border pb-3 select-none">
            <h3 className="text-xs font-mono font-bold text-theme-secondary uppercase tracking-wider">
              Forensic Analysis Pipeline Active
            </h3>
            <span className="text-[10px] font-mono text-theme-accent animate-pulse font-bold">
              RUNNING MULTI-LAYER RESOLUTION...
            </span>
          </div>

          <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-theme-border">
            {[
              { label: "Preprocessing & Input Validation", desc: "Verifying input encoding integrity and characters count" },
              { label: "Heuristic Search Phase", desc: "Running frequency distribution and signature validation tests" },
              { label: "Recursive Multi-Layer BFS Search", desc: "Traversing path tree nodes, decoding intermediate states" },
              { label: "Entropy Scoring & Text Ranking", desc: "Scoring plaintexts against natural language distribution rules" },
            ].map((stage, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0.3 }}
                animate={{ opacity: 1 }}
                transition={{ delay: idx * 0.3 }}
                className="relative"
              >
                {/* Node indicator */}
                <span className="absolute -left-6 top-1.5 w-2 h-2 rounded-full bg-theme-accent shadow shadow-theme-accent/50 animate-ping" />
                <span className="absolute -left-6 top-1.5 w-2 h-2 rounded-full bg-theme-accent" />
                
                <h4 className="text-xs font-mono font-bold text-theme-primary">{stage.label}</h4>
                <p className="text-[10px] text-theme-muted mt-0.5 font-mono">{stage.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Detection Cards */}
      {detections.length > 0 && !loading && (
        <div className="space-y-2">
          <h3 className="text-xs text-theme-secondary uppercase tracking-wider font-mono">Detection Confidence</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {detections.slice(0, 4).map((det, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="bg-theme-card rounded-lg p-4 border border-theme-border hover:border-theme-accent/30 transition-all"
              >
                <div className="text-xs text-theme-secondary uppercase tracking-wider mb-2 font-mono truncate">
                  {det.type}
                </div>
                <div className="flex items-baseline gap-1 mb-3">
                  <span className="text-2xl font-bold text-theme-primary font-mono">
                    {Math.round(det.confidence)}
                  </span>
                  <span className="text-sm text-theme-secondary">%</span>
                </div>
                <div className="h-1.5 bg-theme-input rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${det.confidence}%` }}
                    transition={{ duration: 0.8, delay: 0.2 + i * 0.1 }}
                    className="h-full bg-theme-accent"
                  />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {result && result.steps.length > 0 && !loading && (
        <div className="bg-theme-surface rounded-lg border border-theme-border p-6 space-y-6">
          <div>
            <h3 className="text-xs text-theme-secondary uppercase tracking-wider mb-4 font-mono">Visual Pipeline Graph</h3>
            <PipelineGraph steps={result.steps} initialInput={input} isCtfFlag={result.is_ctf_flag} />
          </div>

          <div>
            <h3 className="text-xs text-theme-secondary uppercase tracking-wider mb-4 font-mono">Decoding Steps Details</h3>
            <div className="space-y-3">
              {result.steps.map((step, i) => (
                <div key={i} className="bg-theme-card rounded-lg p-3 border border-theme-border">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-theme-accent uppercase font-mono">
                      Step {step.step_number}: {step.encoding_type}
                    </span>
                    <span className="text-xs text-theme-secondary font-mono">
                      {Math.round(step.confidence)}% confidence
                    </span>
                  </div>
                  <div className="text-sm text-theme-primary font-mono break-all bg-theme-input/50 p-2.5 rounded border border-theme-border/50">
                    {step.output_text.substring(0, 200)}
                    {step.output_text.length > 200 && "..."}
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Final Output */}
          <div className="space-y-4">
            <div className={`rounded-lg p-4 border-2 ${
              result.is_ctf_flag
                ? "bg-theme-success/10 border-theme-success/30"
                : "bg-theme-card border-theme-border"
            }`}>
              {result.is_ctf_flag && (
                <div className="flex items-center gap-2 mb-2 font-mono select-none">
                  <span className="text-2xl">🚩</span>
                  <span className="text-sm font-bold text-theme-success uppercase">CTF FLAG DETECTED</span>
                </div>
              )}
              <div className="text-base text-theme-primary font-mono break-all bg-theme-input/50 p-3 rounded border border-theme-border/50">
                {result.final_output}
              </div>
            </div>

            {/* Export buttons */}
            <div className="flex justify-end gap-2 text-xs font-mono">
              <span className="text-theme-secondary self-center mr-2">Export Report:</span>
              <button
                onClick={() => handleExport("json")}
                className="px-3 py-1.5 rounded border border-theme-border bg-theme-input hover:bg-theme-hover text-theme-secondary hover:text-theme-primary transition-colors"
              >
                JSON
              </button>
              <button
                onClick={() => handleExport("txt")}
                className="px-3 py-1.5 rounded border border-theme-border bg-theme-input hover:bg-theme-hover text-theme-secondary hover:text-theme-primary transition-colors"
              >
                TXT
              </button>
              <button
                onClick={() => handleExport("html")}
                className="px-3 py-1.5 rounded border border-theme-border bg-theme-input hover:bg-theme-hover text-theme-secondary hover:text-theme-primary transition-colors"
              >
                HTML
              </button>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}
