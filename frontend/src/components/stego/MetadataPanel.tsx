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
      className="flex items-center gap-1 text-xs text-theme-muted hover:text-theme-accent transition-colors shrink-0 font-mono"
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
    <div className="rounded-xl border border-theme-border bg-theme-card overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-4 py-3 bg-theme-surface hover:bg-theme-hover transition-colors"
      >
        <Icon size={13} className={iconColor} />
        <span className="text-xs font-mono text-theme-secondary uppercase tracking-widest flex-1 text-left">{title}</span>
        {badge !== undefined && (
          <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-theme-input text-theme-secondary border border-theme-border">{badge}</span>
        )}
        {open ? <ChevronUp size={13} className="text-theme-secondary" /> : <ChevronDown size={13} className="text-theme-secondary" />}
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
            <div className="p-4 bg-theme-card">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function FieldRow({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-start gap-3 py-1.5 border-b border-theme-border/50 last:border-0">
      <span className="text-xs text-theme-secondary font-mono w-40 shrink-0 truncate">{k}</span>
      <span className="text-xs text-theme-primary font-mono flex-1 break-all">{v}</span>
      <CopyBtn text={v} />
    </div>
  );
}

function FindingCard({ finding, index }: { finding: MetadataFinding; index: number }) {
  const [expanded, setExpanded] = useState(finding.flags.length > 0 || !!finding.decode_result);
  const hasFlag = finding.flags.length > 0 || finding.decode_result?.is_ctf_flag;
  const borderColor = hasFlag
    ? "border-theme-success/40"
    : finding.entropy > 4.5
    ? "border-theme-error/40"
    : "border-theme-warning/40";
  const bgColor = hasFlag ? "bg-theme-success/5" : "bg-theme-card";

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
          ? <Flag size={12} className="text-theme-success shrink-0" />
          : <AlertTriangle size={12} className="text-theme-warning shrink-0" />
        }
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-mono text-theme-accent font-bold">{finding.field}</span>
            <span className="text-xs text-theme-secondary font-mono">({finding.section})</span>
            {finding.encoding && "type" in finding.encoding && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-theme-accent/10 text-theme-accent font-mono border border-theme-accent/15">
                {finding.encoding.type} {Math.round((finding.encoding.confidence ?? 0) * 100)}%
              </span>
            )}
            {hasFlag && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-theme-success/15 text-theme-success font-mono border border-theme-success/20">FLAG</span>
            )}
          </div>
          <p className="text-xs text-theme-secondary font-mono truncate mt-0.5">{finding.raw_value.slice(0, 60)}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-theme-secondary font-mono">H:{finding.entropy.toFixed(2)}</span>
          {expanded ? <ChevronUp size={12} className="text-theme-secondary" /> : <ChevronDown size={12} className="text-theme-secondary" />}
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
            className="overflow-hidden border-t border-theme-border/50"
          >
            <div className="p-3 space-y-2">
              {/* Raw value */}
              <div className="bg-theme-input rounded p-2 border border-theme-border">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-theme-secondary font-mono">Raw Value</span>
                  <CopyBtn text={finding.raw_value} />
                </div>
                <p className="text-xs font-mono text-theme-primary break-all">{finding.raw_value.slice(0, 300)}</p>
              </div>

              {/* Suspicious reasons */}
              {finding.suspicious_reasons.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {finding.suspicious_reasons.map((r, i) => (
                    <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-theme-warning/10 border border-theme-warning/30 text-theme-warning font-mono">
                      {r}
                    </span>
                  ))}
                </div>
              )}

              {/* Flags */}
              {finding.flags.length > 0 && (
                <div className="space-y-1">
                  {finding.flags.map((f, i) => (
                    <div key={i} className="flex items-center gap-2 px-2 py-1.5 rounded bg-theme-success/10 border border-theme-success/30">
                      <Flag size={11} className="text-theme-success shrink-0" />
                      <span className="text-xs font-mono text-theme-success font-bold flex-1">{f}</span>
                      <CopyBtn text={f} />
                    </div>
                  ))}
                </div>
              )}

              {/* Decode result */}
              {finding.decode_result && (
                <div className="bg-theme-input rounded p-2.5 border border-theme-border space-y-1">
                  <div className="flex items-center justify-between font-mono">
                    <span className="text-xs text-theme-secondary">{finding.decode_result.path_description}</span>
                    <span className="text-xs text-theme-warning font-bold">{Math.round(finding.decode_result.total_score * 100)}%</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <p className={`text-xs font-mono break-all flex-1 ${finding.decode_result.is_ctf_flag ? "text-theme-success font-bold" : "text-theme-primary"}`}>
                      {finding.decode_result.final_output}
                    </p>
                    <CopyBtn text={finding.decode_result.final_output} />
                  </div>
                  {finding.decode_result.steps.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {finding.decode_result.steps.map((s) => (
                        <span key={s.step_number} className="text-xs font-mono text-theme-accent">
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
        className="grid grid-cols-2 sm:grid-cols-4 gap-3 select-none"
      >
        {[
          { label: "Fields Scanned", value: summary.total_fields, color: "text-theme-accent" },
          { label: "Suspicious", value: summary.suspicious_fields, color: summary.suspicious_fields > 0 ? "text-theme-warning" : "text-theme-success" },
          { label: "Flags Found", value: summary.flags_found.length, color: summary.flags_found.length > 0 ? "text-theme-success" : "text-theme-muted" },
          { label: "Embedded Files", value: summary.embedded_files_count, color: summary.embedded_files_count > 0 ? "text-theme-error" : "text-theme-muted" },
        ].map((s) => (
          <div key={s.label} className="bg-theme-surface border border-theme-border rounded-lg p-3 text-center">
            <p className={`text-lg font-bold font-mono ${s.color}`}>{s.value}</p>
            <p className="text-xs text-theme-secondary mt-0.5 font-mono">{s.label}</p>
          </div>
        ))}
      </motion.div>

      {/* Flags banner */}
      {summary.flags_found.length > 0 && (
        <motion.div
          animate={{ boxShadow: ["0 0 10px rgba(16,185,129,0.15)", "0 0 20px rgba(16,185,129,0.3)", "0 0 10px rgba(16,185,129,0.15)"] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="p-4 rounded-xl border border-theme-success/40 bg-theme-success/10 space-y-2 select-none"
        >
          <div className="flex items-center gap-2">
            <Flag size={14} className="text-theme-success" />
            <span className="text-sm font-mono font-bold text-theme-success">
              {summary.flags_found.length} FLAG{summary.flags_found.length > 1 ? "S" : ""} FOUND IN METADATA
            </span>
          </div>
          {summary.flags_found.map((f, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="text-sm font-mono text-theme-success font-bold flex-1">{f}</span>
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
          iconColor="text-theme-warning"
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
      <Collapsible title="File Information" icon={Database} iconColor="text-theme-accent" defaultOpen={true}>
        <div className="divide-y divide-theme-border/55">
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
          iconColor="text-theme-accent"
          badge={Object.keys(metadata.exif).length}
        >
          <div className="divide-y divide-theme-border/55">
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
          iconColor="text-theme-success"
          badge={Object.keys(metadata.png_text).length}
          defaultOpen={true}
        >
          <div className="divide-y divide-theme-border/55">
            {Object.entries(metadata.png_text).map(([k, v]) => (
              <FieldRow key={k} k={k} v={v} />
            ))}
          </div>
        </Collapsible>
      )}

      {/* GPS */}
      {Object.keys(metadata.gps).length > 0 && (
        <Collapsible title="GPS Data" icon={Database} iconColor="text-theme-warning" badge={Object.keys(metadata.gps).length}>
          <div className="divide-y divide-theme-border/55">
            {Object.entries(metadata.gps).map(([k, v]) => (
              <FieldRow key={k} k={k} v={v} />
            ))}
          </div>
        </Collapsible>
      )}

      {/* PIL info */}
      {Object.keys(metadata.pil_info).length > 0 && (
        <Collapsible title="Additional Info" icon={Database} iconColor="text-theme-muted" badge={Object.keys(metadata.pil_info).length}>
          <div className="divide-y divide-theme-border/55">
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
          iconColor="text-theme-error"
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
                className="p-3 rounded-lg border border-theme-error/30 bg-theme-error/5 space-y-1"
              >
                <div className="flex items-center justify-between font-mono">
                  <span className="text-xs text-theme-error font-bold">{ef.file_type}</span>
                  <span className="text-xs text-theme-secondary">offset: {ef.offset_hex}</span>
                </div>
                <p className="text-xs font-mono text-theme-secondary">
                  Signature: <span className="text-theme-primary">{ef.signature_hex}</span>
                </p>
                <p className="text-xs font-mono text-theme-secondary truncate">
                  Context: <span className="text-theme-primary">{ef.context}</span>
                </p>
              </motion.div>
            ))}
          </div>
        </Collapsible>
      )}
    </div>
  );
}
