"use client";
import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Database, Zap } from "lucide-react";
import type { LogEntry } from "@/components/layout/LiveAnalysisFeed";
import StegoUploader from "@/components/stego/StegoUploader";
import MetadataPanel from "@/components/stego/MetadataPanel";
import { stegoMetadata, type MetadataResponse } from "@/lib/api";

interface MetadataWorkspaceProps {
  onInspectorUpdate: (data: any) => void;
  onLog: (type: LogEntry["type"], message: string) => void;
  onClearLogs: () => void;
}

export default function MetadataWorkspace({
  onInspectorUpdate,
  onLog,
  onClearLogs,
}: MetadataWorkspaceProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MetadataResponse | null>(null);

  const handleAnalyze = useCallback(async () => {
    if (!file) return;

    setLoading(true);
    onClearLogs();
    onLog("info", `Analyzing ${file.name}...`);
    onLog("info", "Extracting EXIF metadata...");
    onLog("info", "Scanning PNG text chunks...");
    onLog("info", "Analyzing metadata fields...");

    try {
      const data = await stegoMetadata(file);
      setResult(data);

      onLog("success", `Found ${data.summary.total_fields} metadata fields`);
      
      if (data.summary.suspicious_fields > 0) {
        onLog("warning", `${data.summary.suspicious_fields} suspicious fields detected`);
      }

      if (data.summary.flags_found.length > 0) {
        onLog("success", `🚩 ${data.summary.flags_found.length} flag(s) found!`);
      }

      if (data.summary.embedded_files_count > 0) {
        onLog("warning", `⚠️ ${data.summary.embedded_files_count} embedded file(s) detected`);
      }

      onLog("success", "Metadata extraction complete");

      onInspectorUpdate({
        fileInfo: {
          name: file.name,
          size: file.size,
          type: file.type,
        },
        metadataFields: data.summary.total_fields,
        suspiciousFields: data.summary.suspicious_fields,
        flagsFound: data.summary.flags_found.length,
        embeddedFiles: data.summary.embedded_files_count,
      });
    } catch (error) {
      onLog("error", `Analysis failed: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  }, [file, onLog, onClearLogs, onInspectorUpdate]);

  const handleFileSelect = useCallback((selectedFile: File) => {
    setFile(selectedFile);
    setResult(null);
    onLog("info", `File loaded: ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(2)} KB)`);
    onInspectorUpdate({
      fileInfo: {
        name: selectedFile.name,
        size: selectedFile.size,
        type: selectedFile.type,
      },
    });
  }, [onLog, onInspectorUpdate]);

  const handleClear = useCallback(() => {
    setFile(null);
    setResult(null);
    onClearLogs();
    onInspectorUpdate(null);
  }, [onClearLogs, onInspectorUpdate]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="h-full flex flex-col lg:flex-row gap-6"
    >
      {/* Main Content */}
      <div className="flex-1 space-y-6 overflow-y-auto custom-scrollbar pr-2">
        {/* Header */}
        <div className="flex items-center gap-3 select-none">
          <div className="w-10 h-10 rounded-lg bg-theme-gradient flex items-center justify-center shadow-lg shadow-theme-accent/15">
            <Database size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-theme-primary">Metadata Explorer</h2>
            <p className="text-xs text-theme-secondary">EXIF · GPS · Text Chunks · Embedded Files</p>
          </div>
        </div>

        {/* Results */}
        {result ? (
          <MetadataPanel data={result} />
        ) : (
          <div className="flex items-center justify-center h-64 border border-dashed border-theme-border rounded-xl bg-theme-surface/30 select-none">
            <p className="text-xs font-mono text-theme-secondary">Upload an image to extract metadata</p>
          </div>
        )}
      </div>

      {/* Right Controls */}
      <div className="w-full lg:w-80 space-y-4 shrink-0">
        <div className="bg-theme-surface rounded-xl border border-theme-border p-4 space-y-4">
          <StegoUploader
            onFile={handleFileSelect}
            file={file}
            onClear={handleClear}
            password=""
            onPasswordChange={() => {}}
          />

          <motion.button
            onClick={handleAnalyze}
            disabled={!file || loading}
            whileHover={{ scale: file && !loading ? 1.02 : 1 }}
            whileTap={{ scale: file && !loading ? 0.98 : 1 }}
            className="w-full py-2.5 rounded-lg font-mono text-xs font-bold uppercase tracking-widest
              bg-theme-gradient hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed
              transition-all flex items-center justify-center gap-2 text-white shadow-lg shadow-theme-accent/15"
          >
            {loading ? (
              <>
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full"
                />
                Extracting...
              </>
            ) : (
              <>
                <Zap size={14} />
                Extract Metadata
              </>
            )}
          </motion.button>
        </div>

        {/* Info Card */}
        <div className="bg-theme-info/10 rounded-lg border border-theme-info/20 p-3 select-none">
          <p className="text-xs text-theme-info font-mono leading-relaxed">
            ℹ️ This tool extracts all metadata fields from images, automatically detects encoded payloads inside comments, and scans for hidden file streams.
          </p>
        </div>
      </div>
    </motion.div>
  );
}
