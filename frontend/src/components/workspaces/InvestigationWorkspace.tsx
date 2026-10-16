"use client";
/**
 * InvestigationWorkspace – Case-based forensic investigation UI.
 *
 * Features:
 *  - File upload → creates a case via POST /api/cases
 *  - Evidence integrity summary (SHA-256, MD5, format, size)
 *  - Tabbed results: File Analysis, Metadata, Steganalysis, Decoder, Correlations
 *  - Severity and status indicators for each finding
 *  - Transformation graph (recursive decoding steps)
 *  - JSON and PDF report download buttons
 *  - Clear warnings for incomplete/unsupported analysis
 *  - No fabricated data — all data comes from the backend
 */
import { useState, useCallback, useRef } from "react";
import {
  Upload, Shield, AlertTriangle, CheckCircle2, Info,
  Download, ChevronDown, ChevronRight, Loader2, Trash2,
  GitBranch, FileSearch, Database, Eye, Code2, Link2,
} from "lucide-react";
import {
  createCase,
  getCases,
  deleteCase,
  getJsonReportUrl,
  getPdfReportUrl,
  type CaseData,
  type CaseFinding,
  type CorrelationResult,
  type CaseSummary,
  type FindingStatus,
  type Severity,
} from "@/lib/api";
import type { LogEntry } from "@/components/layout/LiveAnalysisFeed";

interface InvestigationWorkspaceProps {
  onLog: (type: LogEntry["type"], message: string) => void;
  onClearLogs: () => void;
}

const SEVERITY_COLORS: Record<Severity, string> = {
  critical: "text-red-500 bg-red-500/10 border-red-500/30",
  high: "text-orange-400 bg-orange-400/10 border-orange-400/30",
  medium: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30",
  low: "text-blue-400 bg-blue-400/10 border-blue-400/30",
  informational: "text-theme-muted bg-theme-surface border-theme-border",
};

const STATUS_ICONS: Record<FindingStatus, React.ReactNode> = {
  CONFIRMED_ARTIFACT: <CheckCircle2 className="w-4 h-4 text-green-400" />,
  SUSPICIOUS_INDICATOR: <AlertTriangle className="w-4 h-4 text-yellow-400" />,
  NO_INDICATOR_DETECTED: <Shield className="w-4 h-4 text-theme-muted" />,
  INCONCLUSIVE: <Info className="w-4 h-4 text-blue-400" />,
};

type Tab = "file" | "metadata" | "steganalysis" | "decoder" | "correlations" | "graph";

export default function InvestigationWorkspace({
  onLog,
  onClearLogs,
}: InvestigationWorkspaceProps) {
  const [loading, setLoading] = useState(false);
  const [caseData, setCaseData] = useState<CaseData | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("file");
  const [error, setError] = useState<string | null>(null);
  const [recentCases, setRecentCases] = useState<CaseSummary[]>([]);
  const [showRecent, setShowRecent] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    setCaseData(null);
    onClearLogs();
    onLog("info", `Starting investigation: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);

    try {
      onLog("info", "Computing evidence hashes...");
      onLog("info", "Running analysis pipeline...");
      const result = await createCase(file);
      setCaseData(result);
      onLog("success", `Case created: ${result.case_id.slice(0, 8)}...`);
      onLog("success", `SHA-256: ${result.sha256.slice(0, 16)}...`);
      onLog("info", `Modules completed: ${result.completed_modules.join(", ")}`);
      if (result.errors.length > 0) {
        result.errors.forEach((e) => onLog("error", e));
      }
      if (result.warnings.length > 0) {
        result.warnings.forEach((w) => onLog("warning", w));
      }
      const flagFindings = result.findings.filter(
        (f) => f.evidence_details?.is_ctf_flag
      );
      if (flagFindings.length > 0) {
        onLog("success", `🚩 ${flagFindings.length} CTF flag(s) detected!`);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setError(msg);
      onLog("error", `Investigation failed: ${msg}`);
    } finally {
      setLoading(false);
    }
  }, [onLog, onClearLogs]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
  }, [handleFileUpload]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileUpload(file);
  };

  const loadRecentCases = async () => {
    try {
      const res = await getCases(10, 0);
      setRecentCases(res.cases);
      setShowRecent(true);
    } catch {}
  };

  const handleDeleteCase = async (caseId: string) => {
    try {
      await deleteCase(caseId);
      setRecentCases((prev) => prev.filter((c) => c.case_id !== caseId));
      if (caseData?.case_id === caseId) setCaseData(null);
    } catch {}
  };

  const findingsByTab = (tab: Tab): CaseFinding[] => {
    if (!caseData) return [];
    return caseData.findings.filter((f) => f.category === tab);
  };

  const tabCount = (tab: Tab) => {
    if (!caseData) return 0;
    if (tab === "correlations") return caseData.correlations.length;
    if (tab === "graph") return caseData.transformation_graph.length;
    return findingsByTab(tab).length;
  };

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "file", label: "File", icon: <FileSearch className="w-3.5 h-3.5" /> },
    { id: "metadata", label: "Metadata", icon: <Database className="w-3.5 h-3.5" /> },
    { id: "steganalysis", label: "Stego", icon: <Eye className="w-3.5 h-3.5" /> },
    { id: "decoder", label: "Decoder", icon: <Code2 className="w-3.5 h-3.5" /> },
    { id: "correlations", label: "Correlations", icon: <Link2 className="w-3.5 h-3.5" /> },
    { id: "graph", label: "Graph", icon: <GitBranch className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="h-full flex flex-col gap-4 overflow-hidden">
      {/* Upload + controls row */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <div
          className="flex-1 border-2 border-dashed border-theme-border rounded-xl p-4 flex items-center gap-3 cursor-pointer hover:border-cyan-500/50 transition-colors"
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => fileInputRef.current?.click()}
        >
          {loading ? (
            <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
          ) : (
            <Upload className="w-5 h-5 text-theme-muted" />
          )}
          <span className="text-sm text-theme-muted">
            {loading ? "Analysing..." : "Drop a file or click to start an investigation"}
          </span>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={handleFileChange}
            accept="*/*"
          />
        </div>

        <button
          onClick={loadRecentCases}
          className="px-3 py-2 text-xs border border-theme-border rounded-lg text-theme-muted hover:text-theme-text hover:border-theme-muted transition-colors"
        >
          Recent Cases
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex-shrink-0 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Recent cases list */}
      {showRecent && !caseData && (
        <div className="flex-shrink-0 border border-theme-border rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2 bg-theme-surface border-b border-theme-border">
            <span className="text-xs font-medium text-theme-muted">Recent Investigations</span>
            <button onClick={() => setShowRecent(false)} className="text-xs text-theme-muted hover:text-theme-text">
              Close
            </button>
          </div>
          {recentCases.length === 0 ? (
            <div className="px-4 py-3 text-xs text-theme-muted">No cases found.</div>
          ) : (
            <div className="divide-y divide-theme-border max-h-48 overflow-y-auto">
              {recentCases.map((c) => (
                <div
                  key={c.case_id}
                  className="flex items-center gap-3 px-4 py-2 hover:bg-theme-surface/50 cursor-pointer"
                >
                  <div className="flex-1 min-w-0" onClick={async () => {
                    try {
                      const { getCase } = await import("@/lib/api");
                      const full = await getCase(c.case_id);
                      setCaseData(full);
                      setShowRecent(false);
                    } catch {}
                  }}>
                    <div className="text-xs font-medium text-theme-text truncate">{c.original_filename}</div>
                    <div className="text-xs text-theme-muted">
                      {c.finding_count} findings · {c.sha256.slice(0, 12)}...
                    </div>
                  </div>
                  <StatusBadge status={c.status} />
                  <button
                    onClick={() => handleDeleteCase(c.case_id)}
                    className="text-theme-muted hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
          <div className="px-4 py-2 bg-theme-surface/30 border-t border-theme-border text-xs text-theme-muted">
            ⚠ Cases are in-memory only and are lost on server restart.
          </div>
        </div>
      )}

      {/* Case results */}
      {caseData && (
        <div className="flex-1 flex flex-col gap-3 overflow-hidden min-h-0">
          {/* Evidence integrity banner */}
          <EvidenceBanner caseData={caseData} />

          {/* Tabs */}
          <div className="flex-shrink-0 flex items-center gap-1 border-b border-theme-border pb-2 overflow-x-auto">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap ${
                  activeTab === t.id
                    ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                    : "text-theme-muted hover:text-theme-text"
                }`}
              >
                {t.icon}
                {t.label}
                {tabCount(t.id) > 0 && (
                  <span className="bg-theme-border text-theme-muted rounded px-1 text-[10px]">
                    {tabCount(t.id)}
                  </span>
                )}
              </button>
            ))}
            {/* Report download */}
            <div className="ml-auto flex items-center gap-2">
              <a
                href={getJsonReportUrl(caseData.case_id)}
                download={`report_${caseData.case_id.slice(0, 8)}.json`}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs border border-theme-border text-theme-muted hover:text-theme-text hover:border-theme-muted transition-colors"
              >
                <Download className="w-3.5 h-3.5" /> JSON
              </a>
              <a
                href={getPdfReportUrl(caseData.case_id)}
                download={`report_${caseData.case_id.slice(0, 8)}.pdf`}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs border border-theme-border text-theme-muted hover:text-theme-text hover:border-theme-muted transition-colors"
              >
                <Download className="w-3.5 h-3.5" /> PDF
              </a>
            </div>
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto min-h-0 space-y-3">
            {/* Module status warnings */}
            {caseData.module_results
              .filter((m) => m.status === "not_applicable" || m.errors.length > 0)
              .map((m) => (
                <div
                  key={m.module_name}
                  className="p-3 rounded-lg bg-yellow-500/5 border border-yellow-500/20 text-xs text-yellow-400 flex items-start gap-2"
                >
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <div>
                    <strong>{m.module_name}</strong>:{" "}
                    {m.status === "not_applicable"
                      ? m.warnings[0] || "Not applicable for this file type."
                      : m.errors.join("; ")}
                  </div>
                </div>
              ))}

            {activeTab !== "correlations" && activeTab !== "graph" && (
              <FindingsList findings={findingsByTab(activeTab)} />
            )}

            {activeTab === "correlations" && (
              <CorrelationsList correlations={caseData.correlations} />
            )}

            {activeTab === "graph" && (
              <TransformationGraph steps={caseData.transformation_graph} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}


// ── Sub-components ─────────────────────────────────────────────────────────

function EvidenceBanner({ caseData }: { caseData: CaseData }) {
  return (
    <div className="flex-shrink-0 p-3 rounded-xl border border-theme-border bg-theme-surface/50">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-medium text-theme-text">Evidence Integrity</span>
        </div>
        <StatusBadge status={caseData.status} />
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <EvidField label="File" value={caseData.original_filename} />
        <EvidField label="Size" value={`${caseData.file_size_bytes.toLocaleString()} bytes`} />
        <EvidField label="Format" value={caseData.detected_format || "Unknown"} />
        <EvidField label="Findings" value={String(caseData.findings.length)} />
        <div className="col-span-2">
          <EvidField label="SHA-256" value={caseData.sha256} mono />
        </div>
        <div className="col-span-2">
          <EvidField label="MD5 (non-crypto ID)" value={caseData.md5} mono />
        </div>
      </div>
      <div className="mt-2 text-[10px] text-theme-muted bg-yellow-500/5 border border-yellow-500/20 rounded px-2 py-1">
        ⚠ Hashes computed from actual uploaded bytes. No formal chain-of-custody. Cases are ephemeral.
      </div>
    </div>
  );
}

function EvidField({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <span className="text-theme-muted">{label}: </span>
      <span className={`text-theme-text ${mono ? "font-mono break-all" : ""}`}>{value}</span>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: "bg-green-500/10 text-green-400 border-green-500/30",
    completed_with_warnings: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
    running: "bg-blue-500/10 text-blue-400 border-blue-500/30",
    queued: "bg-theme-surface text-theme-muted border-theme-border",
    failed: "bg-red-500/10 text-red-400 border-red-500/30",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] border font-medium ${colors[status] || colors.queued}`}>
      {status.replace("_", " ").toUpperCase()}
    </span>
  );
}

function FindingsList({ findings }: { findings: CaseFinding[] }) {
  if (findings.length === 0) {
    return (
      <div className="text-center py-8 text-theme-muted text-sm">
        <Shield className="w-8 h-8 mx-auto mb-2 opacity-30" />
        No findings in this category.
      </div>
    );
  }
  return (
    <div className="space-y-2">
      {findings.map((f) => (
        <FindingCard key={f.finding_id} finding={f} />
      ))}
    </div>
  );
}

function FindingCard({ finding }: { finding: CaseFinding }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`rounded-xl border transition-colors ${SEVERITY_COLORS[finding.severity]}`}>
      <button
        className="w-full text-left px-4 py-3 flex items-start gap-3"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="mt-0.5 flex-shrink-0">{STATUS_ICONS[finding.status]}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-theme-text">{finding.title}</span>
            <SeverityBadge severity={finding.severity} />
            <StatusLabel status={finding.status} />
          </div>
          <div className="text-xs text-theme-muted mt-0.5 truncate">{finding.summary}</div>
        </div>
        {expanded ? <ChevronDown className="w-4 h-4 flex-shrink-0" /> : <ChevronRight className="w-4 h-4 flex-shrink-0" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-current/10">
          {finding.observed_value && (
            <DetailRow label="Observed" value={finding.observed_value} mono />
          )}
          {finding.expected_value && (
            <DetailRow label="Expected" value={finding.expected_value} />
          )}
          <DetailRow label="Method" value={finding.detection_method} />
          <DetailRow label="Explanation" value={finding.explanation} />
          <div className="p-2 rounded bg-yellow-500/5 border border-yellow-500/20 text-xs">
            <span className="text-yellow-400 font-medium">Limitations: </span>
            <span className="text-theme-muted">{finding.limitations}</span>
          </div>
          {finding.recommended_next_step && (
            <div className="p-2 rounded bg-cyan-500/5 border border-cyan-500/20 text-xs">
              <span className="text-cyan-400 font-medium">Next Step: </span>
              <span className="text-theme-muted">{finding.recommended_next_step}</span>
            </div>
          )}
          {finding.evidence_details && (
            <details className="text-xs">
              <summary className="cursor-pointer text-theme-muted hover:text-theme-text">
                Technical details
              </summary>
              <pre className="mt-2 p-2 bg-theme-surface rounded overflow-x-auto text-[10px] text-theme-muted">
                {JSON.stringify(finding.evidence_details, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}

function CorrelationsList({ correlations }: { correlations: CorrelationResult[] }) {
  if (correlations.length === 0) {
    return (
      <div className="text-center py-8 text-theme-muted text-sm">
        <Link2 className="w-8 h-8 mx-auto mb-2 opacity-30" />
        No correlation rules fired.
      </div>
    );
  }
  return (
    <div className="space-y-2">
      {correlations.map((c) => (
        <CorrelationCard key={c.correlation_id} corr={c} />
      ))}
    </div>
  );
}

function CorrelationCard({ corr }: { corr: CorrelationResult }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className={`rounded-xl border ${SEVERITY_COLORS[corr.severity]}`}>
      <button
        className="w-full text-left px-4 py-3 flex items-start gap-3"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="mt-0.5">{STATUS_ICONS[corr.status]}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-mono text-theme-muted">{corr.rule_id}</span>
            <SeverityBadge severity={corr.severity} />
          </div>
          <div className="text-sm font-medium text-theme-text mt-0.5 line-clamp-2">
            {corr.rule_description}
          </div>
        </div>
        {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>
      {expanded && (
        <div className="px-4 pb-4 space-y-2 border-t border-current/10">
          <DetailRow label="Why Triggered" value={corr.match_reason} />
          <DetailRow label="Supporting Evidence" value={corr.supporting_evidence} />
          <div className="p-2 rounded bg-yellow-500/5 border border-yellow-500/20 text-xs">
            <span className="text-yellow-400 font-medium">Does NOT Prove: </span>
            <span className="text-theme-muted">{corr.what_this_does_not_prove}</span>
          </div>
          <div className="p-2 rounded bg-cyan-500/5 border border-cyan-500/20 text-xs">
            <span className="text-cyan-400 font-medium">Next Step: </span>
            <span className="text-theme-muted">{corr.next_step}</span>
          </div>
          <div className="text-xs text-theme-muted">
            Triggered by {corr.triggered_by_finding_ids.length} finding(s)
          </div>
        </div>
      )}
    </div>
  );
}

function TransformationGraph({ steps }: { steps: CaseData["transformation_graph"] }) {
  if (steps.length === 0) {
    return (
      <div className="text-center py-8 text-theme-muted text-sm">
        <GitBranch className="w-8 h-8 mx-auto mb-2 opacity-30" />
        No transformation steps recorded.
      </div>
    );
  }
  return (
    <div className="space-y-2">
      {steps.map((step, idx) => (
        <div key={step.step_id} className="flex items-center gap-3 p-3 rounded-xl border border-theme-border bg-theme-surface/50 text-xs">
          <div className="w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center text-cyan-400 font-mono flex-shrink-0">
            {step.recursion_depth}
          </div>
          <div className="flex-1 min-w-0">
            <span className="font-medium text-theme-text">{step.decoder_name}</span>
            <span className="text-theme-muted ml-2">
              {step.input_size_bytes}B → {step.output_size_bytes}B
            </span>
          </div>
          <div className={`px-2 py-0.5 rounded text-[10px] ${
            step.status === "success" ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"
          }`}>
            {step.status}
          </div>
          <div className="text-theme-muted">{step.duration_ms.toFixed(1)}ms</div>
        </div>
      ))}
    </div>
  );
}

function SeverityBadge({ severity }: { severity: Severity }) {
  const labels: Record<Severity, string> = {
    critical: "CRIT",
    high: "HIGH",
    medium: "MED",
    low: "LOW",
    informational: "INFO",
  };
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium border ${SEVERITY_COLORS[severity]}`}>
      {labels[severity]}
    </span>
  );
}

function StatusLabel({ status }: { status: FindingStatus }) {
  const labels: Record<FindingStatus, string> = {
    CONFIRMED_ARTIFACT: "Confirmed",
    SUSPICIOUS_INDICATOR: "Suspicious",
    NO_INDICATOR_DETECTED: "No Indicator",
    INCONCLUSIVE: "Inconclusive",
  };
  return <span className="text-[10px] text-theme-muted">{labels[status]}</span>;
}

function DetailRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="text-xs">
      <span className="text-theme-muted font-medium">{label}: </span>
      <span className={`text-theme-text ${mono ? "font-mono break-all" : ""}`}>{value}</span>
    </div>
  );
}
