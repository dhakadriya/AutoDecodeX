"use client";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, CheckCircle, Info, Flag, TrendingUp } from "lucide-react";

interface InspectorPanelProps {
  data: {
    fileInfo?: {
      name?: string;
      size?: number;
      type?: string;
    };
    riskScore?: "low" | "medium" | "high";
    detections?: Array<{ type: string; confidence: number }>;
    entropy?: number | string;
    flags?: string[];
    suspicious?: string[];
  } | null;
}

export default function InspectorPanel({ data }: InspectorPanelProps) {
  if (!data) {
    return (
      <div className="h-full bg-theme-surface border-l border-theme-border p-4">
        <div className="flex items-center justify-center h-full text-theme-muted text-sm">
          <div className="text-center space-y-2">
            <Info size={32} className="mx-auto opacity-30 text-theme-secondary" />
            <p className="font-mono text-xs">No active analysis data</p>
          </div>
        </div>
      </div>
    );
  }

  const getRiskColor = (risk?: string) => {
    switch (risk) {
      case "high": return "text-theme-error bg-theme-error/10 border-theme-error/20";
      case "medium": return "text-theme-warning bg-theme-warning/10 border-theme-warning/20";
      case "low": return "text-theme-success bg-theme-success/10 border-theme-success/20";
      default: return "text-theme-secondary bg-theme-hover border-theme-border";
    }
  };

  return (
    <div className="h-full bg-theme-surface border-l border-theme-border overflow-y-auto custom-scrollbar">
      <div className="p-4 border-b border-theme-border sticky top-0 bg-theme-surface/80 backdrop-blur-md z-10 flex items-center justify-between">
        <h3 className="text-xs font-bold text-theme-primary uppercase tracking-wider flex items-center gap-2">
          <TrendingUp size={14} className="text-theme-accent" />
          Inspector
        </h3>
      </div>

      <div className="p-4 space-y-4">
        {/* File Info */}
        {data.fileInfo && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-theme-card rounded-lg p-3 border border-theme-border"
          >
            <h4 className="text-[10px] text-theme-secondary uppercase tracking-wider mb-2 font-mono">File Information</h4>
            <div className="space-y-1.5 text-xs">
              {data.fileInfo.name && (
                <div className="flex justify-between">
                  <span className="text-theme-secondary font-mono">Name:</span>
                  <span className="text-theme-primary font-mono truncate ml-2">{data.fileInfo.name}</span>
                </div>
              )}
              {data.fileInfo.size && (
                <div className="flex justify-between">
                  <span className="text-theme-secondary font-mono">Size:</span>
                  <span className="text-theme-primary font-mono">{(data.fileInfo.size / 1024).toFixed(2)} KB</span>
                </div>
              )}
              {data.fileInfo.type && (
                <div className="flex justify-between">
                  <span className="text-theme-secondary font-mono">Type:</span>
                  <span className="text-theme-primary font-mono">{data.fileInfo.type}</span>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Risk Score */}
        {data.riskScore && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className={`rounded-lg p-3 border ${getRiskColor(data.riskScore)}`}
          >
            <h4 className="text-[10px] uppercase tracking-wider mb-2 opacity-80 font-mono">Risk Assessment</h4>
            <div className="flex items-center gap-2 font-mono">
              <AlertTriangle size={16} />
              <span className="text-sm font-bold uppercase">{data.riskScore} risk</span>
            </div>
          </motion.div>
        )}

        {/* Detections */}
        {data.detections && data.detections.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-theme-card rounded-lg p-3 border border-theme-border"
          >
            <h4 className="text-[10px] text-theme-secondary uppercase tracking-wider mb-3 font-mono">Possible Encodings</h4>
            <div className="space-y-2">
              {data.detections.map((det, i) => (
                <div key={i} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-theme-primary font-mono">{det.type}</span>
                    <span className="text-theme-accent font-bold font-mono">{det.confidence}%</span>
                  </div>
                  <div className="h-1.5 bg-theme-input rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${det.confidence}%` }}
                      transition={{ duration: 0.8, delay: 0.3 + i * 0.1 }}
                      className="h-full bg-theme-gradient"
                    />
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Entropy */}
        {data.entropy !== undefined && (
          (() => {
            const entropyVal = typeof data.entropy === "string" ? parseFloat(data.entropy) : typeof data.entropy === "number" ? data.entropy : NaN;
            if (isNaN(entropyVal)) return null;
            return (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="bg-theme-card rounded-lg p-3 border border-theme-border"
              >
                <h4 className="text-[10px] text-theme-secondary uppercase tracking-wider mb-2 font-mono">Entropy Score</h4>
                <div className="flex items-baseline gap-2 font-mono">
                  <span className="text-2xl font-bold text-theme-primary">{entropyVal.toFixed(3)}</span>
                  <span className="text-xs text-theme-muted">/ 8.0</span>
                </div>
                <div className="mt-2 h-1.5 bg-theme-input rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(entropyVal / 8) * 100}%` }}
                    transition={{ duration: 0.8, delay: 0.4 }}
                    className={`h-full ${
                      entropyVal > 7 ? "bg-theme-error" : 
                      entropyVal > 5 ? "bg-theme-warning" : 
                      "bg-theme-success"
                    }`}
                  />
                </div>
              </motion.div>
            );
          })()
        )}

        {/* Flags Found */}
        <AnimatePresence>
          {data.flags && data.flags.length > 0 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-theme-success/10 rounded-lg p-3 border border-theme-success/30"
            >
              <div className="flex items-center gap-2 mb-2">
                <Flag size={14} className="text-theme-success" />
                <h4 className="text-[10px] text-theme-success uppercase tracking-wider font-bold font-mono">
                  {data.flags.length} Flag{data.flags.length > 1 ? "s" : ""} Detected
                </h4>
              </div>
              <div className="space-y-1.5">
                {data.flags.map((flag, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + i * 0.1 }}
                    className="bg-theme-input rounded px-2 py-1.5 text-xs font-mono text-theme-success break-all border border-theme-success/15"
                  >
                    {flag}
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Suspicious Indicators */}
        {data.suspicious && data.suspicious.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-theme-warning/10 rounded-lg p-3 border border-theme-warning/30"
          >
            <h4 className="text-[10px] text-theme-warning uppercase tracking-wider mb-2 font-mono">Suspicious Indicators</h4>
            <ul className="space-y-1.5">
              {data.suspicious.map((item, i) => (
                <li key={i} className="text-xs text-theme-warning/95 flex items-start gap-2 font-mono">
                  <span className="text-theme-warning mt-0.5">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </div>
    </div>
  );
}
