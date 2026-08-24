"use client";
import { useState, useCallback, useRef } from "react";
import { motion } from "framer-motion";
import { FileSearch, Upload, Hash, Copy } from "lucide-react";
import type { LogEntry } from "@/components/layout/LiveAnalysisFeed";
import { fileAnalyze } from "@/lib/api";

interface FileAnalyzerWorkspaceProps {
  onInspectorUpdate: (data: any) => void;
  onLog: (type: LogEntry["type"], message: string) => void;
  onClearLogs: () => void;
}

interface FileAnalysis {
  name: string;
  size: number;
  type: string;
  sha256: string;
  md5: string;
  entropy: number;
  strings: string[];
  printableRatio: number;
  magicBytes: string;
}

export default function FileAnalyzerWorkspace({
  onInspectorUpdate,
  onLog,
  onClearLogs,
}: FileAnalyzerWorkspaceProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<FileAnalysis | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const analyzeFile = useCallback(async (fileToAnalyze: File) => {
    setLoading(true);
    onClearLogs();
    onLog("info", `Uploading and analyzing ${fileToAnalyze.name} via backend...`);

    try {
      onLog("info", "Uploading evidence file to secure sandbox...");
      const result = await fileAnalyze(fileToAnalyze);

      setAnalysis(result);
      onLog("success", "Analysis complete");

      if (result.entropy > 7.5) {
        onLog("warning", "⚠️ High entropy detected - possible encryption or compression");
      }

      if (result.printableRatio < 10) {
        onLog("warning", "⚠️ Low printable ratio - likely binary file");
      }

      onInspectorUpdate({
        fileName: result.name,
        fileSize: result.size,
        entropy: result.entropy.toFixed(3),
        sha256: result.sha256.slice(0, 16) + "...",
        stringsFound: result.strings.length,
        printableRatio: result.printableRatio.toFixed(1) + "%",
        riskLevel: result.entropy > 7.5 ? "high" : result.entropy > 6 ? "medium" : "low",
      });
    } catch (error) {
      onLog("error", `Analysis failed: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  }, [onLog, onClearLogs, onInspectorUpdate]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      analyzeFile(droppedFile);
    }
  }, [analyzeFile]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      analyzeFile(selectedFile);
    }
  }, [analyzeFile]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    onLog("info", "Copied to clipboard");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="h-full flex flex-col gap-6"
    >
      {/* Header */}
      <div className="flex items-center gap-3 select-none">
        <div className="w-10 h-10 rounded-lg bg-theme-gradient flex items-center justify-center shadow-lg shadow-theme-accent/15">
          <FileSearch size={20} className="text-white" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-theme-primary">File Analyzer</h2>
          <p className="text-xs text-theme-secondary">Hashes · Entropy · Strings · Magic Bytes</p>
        </div>
      </div>

      {/* Upload Zone */}
      {!analysis && !loading && (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`flex-1 rounded-xl border-2 border-dashed transition-all cursor-pointer select-none
            ${dragActive
              ? "border-theme-accent bg-theme-accent/10"
              : "border-theme-border hover:border-theme-accent/50 bg-theme-surface"
            }`}
        >
          <div className="h-full flex flex-col items-center justify-center gap-4 p-12">
            <motion.div
              animate={dragActive ? { scale: 1.1 } : { scale: 1 }}
              className="w-20 h-20 rounded-full bg-theme-accent/10 border border-theme-accent/20 flex items-center justify-center"
            >
              <Upload size={32} className="text-theme-accent" />
            </motion.div>

            <div className="text-center">
              <h3 className="text-lg font-bold text-theme-primary mb-2 font-mono">
                {dragActive ? "Release evidence file" : "Upload Evidence File"}
              </h3>
              <p className="text-sm text-theme-secondary mb-4 font-mono">
                Any file type · Max 50 MB
              </p>
              <button className="px-6 py-2.5 rounded-lg bg-theme-gradient hover:opacity-90 text-white text-sm font-mono font-bold transition-all shadow-lg shadow-theme-accent/15">
                <Upload size={14} className="inline mr-2" />
                Select File
              </button>
            </div>

            <input
              ref={inputRef}
              type="file"
              onChange={handleFileInput}
              className="hidden"
            />
          </div>
        </div>
      )}

      {/* Loading Progress State */}
      {loading && (
        <div className="flex-1 flex flex-col items-center justify-center p-12 border border-theme-border rounded-xl bg-theme-surface select-none">
          <div className="relative w-16 h-16 mb-4">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 border-4 border-theme-accent/20 border-t-theme-accent rounded-full"
            />
          </div>
          <p className="text-xs font-mono text-theme-secondary tracking-wider uppercase animate-pulse">
            Analyzing evidence structure...
          </p>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && !loading && (
        <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4">
          {/* File Info */}
          <div className="bg-theme-surface rounded-xl border border-theme-border p-4">
            <h3 className="text-sm font-mono text-theme-secondary uppercase tracking-wider mb-3">File Information</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-start gap-4">
                <span className="text-xs text-theme-secondary font-mono">Name:</span>
                <span className="text-xs text-theme-primary font-mono text-right break-all">{analysis.name}</span>
              </div>
              <div className="flex justify-between items-center gap-4">
                <span className="text-xs text-theme-secondary font-mono">Size:</span>
                <span className="text-xs text-theme-accent font-mono">{(analysis.size / 1024).toFixed(2)} KB</span>
              </div>
              <div className="flex justify-between items-center gap-4">
                <span className="text-xs text-theme-secondary font-mono">Type:</span>
                <span className="text-xs text-theme-primary font-mono">{analysis.type}</span>
              </div>
              <div className="flex justify-between items-center gap-4">
                <span className="text-xs text-theme-secondary font-mono">Magic Bytes:</span>
                <span className="text-xs text-theme-accent font-mono">{analysis.magicBytes}</span>
              </div>
            </div>
          </div>

          {/* Hashes */}
          <div className="bg-theme-surface rounded-xl border border-theme-border p-4">
            <div className="flex items-center gap-2 mb-3">
              <Hash size={14} className="text-theme-accent" />
              <h3 className="text-sm font-mono text-theme-secondary uppercase tracking-wider">Cryptographic Hashes</h3>
            </div>
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-theme-secondary font-mono">SHA-256:</span>
                  <button onClick={() => copyToClipboard(analysis.sha256)} className="text-xs text-theme-muted hover:text-theme-accent transition-colors">
                    <Copy size={12} />
                  </button>
                </div>
                <div className="bg-theme-input rounded p-2.5 border border-theme-border">
                  <p className="text-xs text-theme-accent font-mono break-all">{analysis.sha256}</p>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-theme-secondary font-mono">MD5 (SHA-1 Fallback):</span>
                  <button onClick={() => copyToClipboard(analysis.md5)} className="text-xs text-theme-muted hover:text-theme-accent transition-colors">
                    <Copy size={12} />
                  </button>
                </div>
                <div className="bg-theme-input rounded p-2.5 border border-theme-border">
                  <p className="text-xs text-theme-accent font-mono break-all">{analysis.md5}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Entropy */}
          <div className="bg-theme-surface rounded-xl border border-theme-border p-4">
            <h3 className="text-sm font-mono text-theme-secondary uppercase tracking-wider mb-3">Entropy Analysis</h3>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-xs text-theme-secondary font-mono">Entropy Score:</span>
                  <span className={`text-sm font-mono font-bold ${
                    analysis.entropy > 7.5 ? "text-theme-error" : analysis.entropy > 6 ? "text-theme-warning" : "text-theme-success"
                  }`}>
                    {analysis.entropy.toFixed(3)} / 8.000
                  </span>
                </div>
                <div className="h-2 bg-theme-input rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(analysis.entropy / 8) * 100}%` }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                    className={`h-full ${
                      analysis.entropy > 7.5
                        ? "bg-theme-error"
                        : analysis.entropy > 6
                        ? "bg-theme-warning"
                        : "bg-theme-success"
                    }`}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-xs text-theme-secondary font-mono">Printable Ratio:</span>
                  <span className="text-sm font-mono text-theme-accent font-bold">{analysis.printableRatio.toFixed(1)}%</span>
                </div>
                <div className="h-2 bg-theme-input rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${analysis.printableRatio}%` }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                    className="h-full bg-theme-accent"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Strings */}
          <div className="bg-theme-surface rounded-xl border border-theme-border p-4">
            <h3 className="text-sm font-mono text-theme-secondary uppercase tracking-wider mb-3">
              Extracted Strings ({analysis.strings.length})
            </h3>
            <div className="bg-theme-input rounded-lg p-3 max-h-64 overflow-y-auto custom-scrollbar space-y-1.5 border border-theme-border">
              {analysis.strings.length > 0 ? (
                analysis.strings.map((str, idx) => (
                  <div key={idx} className="text-xs text-theme-secondary font-mono hover:text-theme-accent transition-colors break-all">
                    {str}
                  </div>
                ))
              ) : (
                <p className="text-xs text-theme-muted italic font-mono">No printable strings found</p>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <motion.button
              onClick={() => {
                setAnalysis(null);
                setFile(null);
                onClearLogs();
                onInspectorUpdate(null);
              }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex-1 py-2.5 rounded-lg bg-theme-surface hover:bg-theme-hover border border-theme-border text-theme-primary text-sm font-mono transition-all font-bold"
            >
              Analyze New File
            </motion.button>
          </div>
        </div>
      )}
    </motion.div>
  );
}
