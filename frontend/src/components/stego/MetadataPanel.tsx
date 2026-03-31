"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Flag, AlertTriangle, ChevronDown, ChevronUp,
  Copy, Database, FileSearch, Package,
} from "lucide-react";
import type { MetadataResponse, MetadataFinding } from "@/lib/api";

interface Props {
  data: MetadataResponse;
}

function CopyBtn({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
      className="flex items-center gap-1 text-xs text-cyber-muted hover:text-cyber-blue transition-colors shrink-0"
    >
      <Copy size={10} />
      {copied ? "✓" : ""}
    </button>
  );
}

function Collapsible({ title, icon: Icon, iconColor, badge, children, defaultOpen = false }: {
  title: string;
  icon: React.ElementType;
  iconColor: string;
  badge?: string | number;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-xl border border-cyber-border bg-cyber-card overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-4 py-3 bg-cyber-surface hover:bg-cyber-card transition-colors"
      >
        <Icon size={13} className={iconColor} />
        <span className="text-xs font-mono text-cyber-muted uppercase tracking-widest flex-1 text-left">{title}</span>
        {badge !== undefined && (
          <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-cyber-border text-cyber-muted">{badge}</span>
        )}
        {open ? <ChevronUp size={13} className="text-cyber-muted" /> : <ChevronDown size={13} className="text-cyber-muted" />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function FieldRow({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-start gap-3 py-1.5 border-b border-cyber-border/50 last:border-0">
      <span className="text-xs text-cyber-muted font-mono w-40 shrink-0 truncate">{k}</span>
      <span className="text-xs text-cyber-text font-mono flex-1 break-all">{v}</span>
      <CopyBtn text={v} />
    </div>
  );
}

function FindingCard({ finding, index }: { finding: MetadataFinding; index: number }) {
  const [expanded, setExpanded] = useState(finding.flags.length > 0 || !!finding.decode_result);
  const hasFlag = finding.flags.length > 0 || finding.decode_result?.is_ctf_flag;
  const borderColor = hasFlag
    ? "border-cyber-green/60"
    : finding.entropy > 4.5
    ? "border-red-500/40"
    : "border-amber-400/40";
  const bgColor = hasFlag ? "bg-cyber-green/5" : "bg-cyber-card";

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`rounded-lg border ${borderColor} ${bgColor} overflow-hidden`}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-3 py-2.5 text-left"
      >
        {hasFlag
          ? <Flag size={12} className="text-cyber-green shrink-0" />
          : <AlertTriangle size={12} className="text-amber-400 shrink-0" />
        }
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-mono text-cyber-blue">{finding.field}</span>
            <span className="text-xs text-cyber-muted">({finding.section})</span>
            {finding.encoding && "type" in finding.encoding && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-cyber-purple/20 text-cyber-purple font-mono">
                {finding.encoding.type} {Math.round((finding.encoding.confidence ?? 0) * 100)}%
              </span>
            )}
            {hasFlag && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-cyber-green/20 text-cyber-green font-mono">FLAG</span>
            )}
          </div>
          <p className="text-xs text-cyber-muted truncate mt-0.5">{finding.raw_value.slice(0, 60)}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-cyber-muted font-mono">H:{finding.entropy.toFixed(2)}</span>
          {expanded ? <ChevronUp size={12} className="text-cyber-muted" /> : <ChevronDown size={12} className="text-cyber-muted" />}
        </div>
      </button>

      {/* Expanded detail */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden border-t border-cyber-border/50"
          >
            <div className="p-3 space-y-2">
              {/* Raw value */}
              <div className="bg-cyber-surface rounded p-2 border border-cyber-border">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-cyber-muted">Raw Value</span>
                  <CopyBtn text={finding.raw_value} />
                </div>
                <p className="text-xs font-mono text-cyber-text break-all">{finding.raw_value.slice(0, 300)}</p>
              </div>

              {/* Suspicious reasons */}
              {finding.suspicious_reasons.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {finding.suspicious_reasons.map((r, i) => (
                    <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-amber-400/10 border border-amber-400/30 text-amber-400 font-mono">
                      {r}
                    </span>
                  ))}
                </div>
              )}

              {/* Flags */}
              {finding.flags.length > 0 && (
                <div className="space-y-1">
                  {finding.flags.map((f, i) => (
                    <div key={i} className="flex items-center gap-2 px-2 py-1.5 rounded bg-cyber-green/10 border border-cyber-green/40">
                      <Flag size={11} className="text-cyber-green shrink-0" />
                      <span className="text-xs font-mono text-cyber-green neon-green flex-1">{f}</span>
                      <CopyBtn text={f} />
                    </div>
                  ))}
                </div>
              )}

              {/* Decode result */}
              {finding.decode_result && (
                <div className="bg-cyber-surface rounded p-2 border border-cyber-border space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-cyber-muted">{finding.decode_result.path_description}</span>
                    <span className="text-xs text-cyber-yellow">{Math.round(finding.decode_result.total_score * 100)}%</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <p className={`text-xs font-mono break-all flex-1 ${finding.decode_result.is_ctf_flag ? "text-cyber-green neon-green" : "text-cyber-text"}`}>
                      {finding.decode_result.final_output}
                    </p>
                    <CopyBtn text={finding.decode_result.final_output} />
                  </div>
                  {finding.decode_result.steps.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {finding.decode_result.steps.map((s) => (
                        <span key={s.step_number} className="text-xs font-mono text-cyber-purple">
                          {s.encoding_type.toUpperCase()}({Math.round(s.confidence * 100)}%)
                          {s.step_number < finding.decode_result!.steps.length ? " →" : ""}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function MetadataPanel({ data }: Props) {
  const { metadata, analysis, embedded_files, summary } = data;

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 sm:grid-cols-4 gap-3"
      >
        {[
          { label: "Fields Scanned", value: summary.total_fields, color: "text-cyber-blue" },
          { label: "Suspicious", value: summary.suspicious_fields, color: summary.suspicious_fields > 0 ? "text-amber-400" : "text-cyber-green" },
          { label: "Flags Found", value: summary.flags_found.length, color: summary.flags_found.length > 0 ? "text-cyber-green" : "text-cyber-muted" },
          { label: "Embedded Files", value: summary.embedded_files_count, color: summary.embedded_files_count > 0 ? "text-red-400" : "text-cyber-muted" },
        ].map((s) => (
          <div key={s.label} className="bg-cyber-card border border-cyber-border rounded-lg p-3 text-center">
            <p className={`text-lg font-bold font-mono ${s.color}`}>{s.value}</p>
            <p className="text-xs text-cyber-muted mt-0.5">{s.label}</p>
          </div>
        ))}
      </motion.div>

      {/* Flags banner */}
      {summary.flags_found.length > 0 && (
        <motion.div
          animate={{ boxShadow: ["0 0 10px rgba(0,255,136,0.2)", "0 0 25px rgba(0,255,136,0.4)", "0 0 10px rgba(0,255,136,0.2)"] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="p-4 rounded-xl border border-cyber-green/60 bg-cyber-green/10 space-y-2"
        >
          <div className="flex items-center gap-2">
            <Flag size={14} className="text-cyber-green" />
            <span className="text-sm font-mono font-bold text-cyber-green">
              {summary.flags_found.length} FLAG{summary.flags_found.length > 1 ? "S" : ""} FOUND IN METADATA
            </span>
          </div>
          {summary.flags_found.map((f, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="text-sm font-mono text-cyber-green neon-green flex-1">{f}</span>
              <CopyBtn text={f} />
            </div>
          ))}
        </motion.div>
      )}

      {/* Suspicious findings */}
      {analysis.findings.length > 0 && (
        <Collapsible
          title={`Suspicious Fields (${analysis.findings.length})`}
          icon={AlertTriangle}
          iconColor="text-amber-400"
          badge={analysis.findings.length}
          defaultOpen={true}
        >
          <div className="space-y-2">
            {analysis.findings.map((f, i) => (
              <FindingCard key={`${f.section}-${f.field}-${i}`} finding={f} index={i} />
            ))}
          </div>
        </Collapsible>
      )}

      {/* File info */}
      <Collapsible title="File Information" icon={Database} iconColor="text-cyber-blue" defaultOpen={true}>
        <div className="divide-y divide-cyber-border/30">
          {Object.entries(metadata.file_info).map(([k, v]) => (
            <FieldRow key={k} k={k} v={String(v)} />
          ))}
          {summary.has_exif && <FieldRow k="has_exif" v="true" />}
          {summary.has_gps && <FieldRow k="has_gps" v="true" />}
          {summary.has_png_text && <FieldRow k="has_png_text_chunks" v="true" />}
        </div>
      </Collapsible>

      {/* EXIF data */}
      {Object.keys(metadata.exif).length > 0 && (
        <Collapsible
          title="EXIF Data"
          icon={Database}
          iconColor="text-cyber-purple"
          badge={Object.keys(metadata.exif).length}
        >
          <div className="divide-y divide-cyber-border/30">
            {Object.entries(metadata.exif).map(([k, v]) => (
              <FieldRow key={k} k={k} v={v} />
            ))}
          </div>
        </Collapsible>
      )}

      {/* PNG text chunks */}
      {Object.keys(metadata.png_text).length > 0 && (
        <Collapsible
          title="PNG Text Chunks"
          icon={FileSearch}
          iconColor="text-cyber-green"
          badge={Object.keys(metadata.png_text).length}
          defaultOpen={true}
        >
          <div className="divide-y divide-cyber-border/30">
            {Object.entries(metadata.png_text).map(([k, v]) => (
              <FieldRow key={k} k={k} v={v} />
            ))}
          </div>
        </Collapsible>
      )}

      {/* GPS */}
      {Object.keys(metadata.gps).length > 0 && (
        <Collapsible title="GPS Data" icon={Database} iconColor="text-amber-400" badge={Object.keys(metadata.gps).length}>
          <div className="divide-y divide-cyber-border/30">
            {Object.entries(metadata.gps).map(([k, v]) => (
              <FieldRow key={k} k={k} v={v} />
            ))}
          </div>
        </Collapsible>
      )}

      {/* PIL info */}
      {Object.keys(metadata.pil_info).length > 0 && (
        <Collapsible title="Additional Info" icon={Database} iconColor="text-cyber-muted" badge={Object.keys(metadata.pil_info).length}>
          <div className="divide-y divide-cyber-border/30">
            {Object.entries(metadata.pil_info).map(([k, v]) => (
              <FieldRow key={k} k={k} v={v} />
            ))}
          </div>
        </Collapsible>
      )}

      {/* Embedded files */}
      {embedded_files.length > 0 && (
        <Collapsible
          title={`Embedded Files Detected (${embedded_files.length})`}
          icon={Package}
          iconColor="text-red-400"
          badge={embedded_files.length}
          defaultOpen={true}
        >
          <div className="space-y-2">
            {embedded_files.map((ef, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.05 }}
                className="p-3 rounded-lg border border-red-500/30 bg-red-500/5 space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-red-400 font-semibold">{ef.file_type}</span>
                  <span className="text-xs font-mono text-cyber-muted">@ {ef.offset_hex}</span>
                </div>
                <p className="text-xs font-mono text-cyber-muted">
                  Signature: <span className="text-cyber-text">{ef.signature_hex}</span>
                </p>
                <p className="text-xs font-mono text-cyber-muted truncate">
                  Context: <span className="text-cyber-text">{ef.context}</span>
                </p>
              </motion.div>
            ))}
          </div>
        </Collapsible>
      )}
    </div>
  );
}
